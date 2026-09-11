#!/usr/bin/env python3
"""Local worker dispatch for Codex. Full permissions; explicit task scope + review."""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import tempfile
import time
import uuid

from acp_stdio import ACP


ACTIVE = {"starting", "running", "stopping"}
DEFAULT_MAX_TURNS = 200
NON_SUCCESS_TERMINAL = {"failed", "timed_out", "cancelled", "interrupted"}


def save(path, value):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(f.name, path)


def read(path):
    return json.loads(path.read_text())


def processes():
    text = subprocess.check_output(
        ["ps", "-axo", "pid=,ppid=,pgid=,stat=,lstart="], text=True
    )
    result = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 9:
            result[int(parts[0])] = {"pid": int(parts[0]), "parent": int(parts[1]),
                "group": int(parts[2]), "zombie": parts[3].startswith("Z"),
                "birth": " ".join(parts[4:])}
    return result


def is_alive(identity, table=None):
    if not identity:
        return False
    current = (table if table is not None else processes()).get(identity["pid"])
    return bool(current and not current["zombie"] and current["birth"] == identity["birth"])


def git(cwd, *args):
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True)


def snapshot(cwd):
    files = {}
    for name in set(git(cwd, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")) - {""}:
        path = cwd / name
        try:
            data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
            files[name] = {"sha256": hashlib.sha256(data).hexdigest(),
                           "mode": path.lstat().st_mode}
        except FileNotFoundError:
            files[name] = None
        except IsADirectoryError:
            # A submodule is recorded by its gitlink; its nested work is separate scope.
            files[name] = {"submodule": git(path, "rev-parse", "HEAD").strip()}
    return {"head": git(cwd, "rev-parse", "HEAD").strip(), "files": files}


def changed(before, after):
    a, b = before["files"], after["files"]
    return sorted(name for name in a.keys() | b.keys() if a.get(name) != b.get(name))


def in_scope(name, allowed):
    return any(item == "." or name == item or
               (item.endswith("/") and name.startswith(item)) for item in allowed)


def resolved_max_turns(state, requested):
    """Explicit override wins; otherwise retain the persisted value, defaulting to 200."""
    if requested is not None:
        return requested
    return state.get("max_turns", DEFAULT_MAX_TURNS)


def result_detail(result, limit=400):
    """Compact provider-failure diagnostics; no raw reasoning or synthesized report."""
    if not result:
        return "no provider result event was received"
    parts = []
    if result.get("subtype") is not None:
        parts.append(f"subtype={result['subtype']}")
    parts.append(f"is_error={bool(result.get('is_error'))}")
    text = result.get("errors") or result.get("error") or result.get("result")
    if text:
        parts.append("detail=" + " ".join(str(text).split())[:limit])
    return "; ".join(parts)


def workspace_lock_path(cwd):
    folder = Path.home() / ".local/state/freetoken/locks"
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    return folder / (hashlib.sha256(str(cwd).encode()).hexdigest() + ".json")


@contextmanager
def exclusive(path):
    with path.open("a+") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f"Already active: {path}") from None
        yield f


def lock_record(stream, value):
    stream.seek(0)
    stream.truncate()
    json.dump(value, stream)
    stream.flush()
    os.fsync(stream.fileno())


class Run:
    def __init__(self, folder, state, prompt, budget):
        self.folder, self.state = folder, state
        self.cwd = Path(state["cwd"])
        self.start = time.monotonic()
        self.budget = budget
        self.stop_reason = None
        self.stop_at = None
        self.last_sample = 0
        self.known = {}
        self.proc = None
        self.attempt = folder / "attempts" / f"{state['attempt']:04d}"
        self.attempt.mkdir(parents=True)
        (self.attempt / "raw").mkdir(mode=0o700)
        (self.attempt / "prompt.md").write_text(prompt)
        self.prompt = prompt
        self.before = snapshot(self.cwd)
        save(self.attempt / "before.json", self.before)
        (self.attempt / "before.diff").write_text(git(
            self.cwd, "diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD"))
        state.update(status="starting", controller=processes()[os.getpid()], worker=None,
                     started_at=time.time(), budget_seconds=budget, last_event=None,
                     attempt_dir=str(self.attempt), error=None, known_processes=[],
                     elapsed_s=None, ended_at=None, worker_exit=None,
                     changes=[], out_of_scope=[], cleanup_required=[])
        self.persist()

    def persist(self):
        save(self.folder / "state.json", self.state)

    def event(self, kind, **data):
        event = {"elapsed_s": round(time.monotonic() - self.start, 3), "kind": kind, **data}
        with (self.attempt / "events.jsonl").open("a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        self.state["last_event"] = event
        self.persist()
        print(json.dumps(event, ensure_ascii=False), flush=True)

    def attach(self, process):
        self.proc = process
        self.state["worker"] = processes().get(process.pid)
        self.state["status"] = "running"
        self.persist()
        self.tick()

    def request_stop(self, reason):
        if self.stop_reason is None:
            self.stop_reason, self.stop_at = reason, time.monotonic()
            self.state["status"] = "stopping"
            self.event("stop_requested", reason=reason)

    def tick(self):
        now = time.monotonic()
        cancel = self.folder / "cancel.json"
        if cancel.exists() and read(cancel).get("attempt") == self.state["attempt"]:
            self.request_stop("cancelled")
        if now - self.start >= self.budget:
            self.request_stop("timed_out")
        if self.proc and now - self.last_sample >= 0.5:
            table = processes()
            parents = {pid for pid, ident in self.known.items() if is_alive(ident, table)}
            if is_alive(self.state.get("worker"), table):
                parents.add(self.proc.pid)
            while True:
                found = {pid for pid, item in table.items() if item["parent"] in parents}
                if found <= parents:
                    break
                parents |= found
            for pid in parents:
                if pid in table:
                    self.known[pid] = table[pid]
            self.state["known_processes"] = list(self.known.values())
            self.persist()
            self.last_sample = now

    def cleanup(self):
        """Only signal observed processes whose birth identity still matches."""
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        survivors = [ident for ident in self.known.values() if is_alive(ident)]
        for ident in survivors:
            try:
                os.kill(ident["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass
        if survivors:
            time.sleep(0.2)
        for ident in survivors:
            if is_alive(ident):
                try:
                    os.kill(ident["pid"], signal.SIGKILL)
                except ProcessLookupError:
                    pass
        return survivors


def codebuddy(run):
    state = run.state
    argv = [state["executable"], "--print", "--verbose", "--output-format", "stream-json",
            "--permission-mode", "bypassPermissions", "--max-turns",
            str(state.get("max_turns", DEFAULT_MAX_TURNS))]
    if state.get("model"):
        argv += ["--model", state["model"]]
    if state.get("one_shot"):
        argv += ["--no-session-persistence"]
    argv += ["--session-id" if state["attempt"] == 1 else "--resume", state["session_id"], "--"]
    save(run.attempt / "argv.json", argv)
    with (run.attempt / "raw/stderr.log").open("wb") as err, (run.attempt / "raw/stdout.log").open("wb") as raw:
        p = subprocess.Popen(argv + [run.prompt], cwd=run.cwd, stdout=subprocess.PIPE,
                             stderr=err, start_new_session=True)
        run.attach(p)
        selector = selectors.DefaultSelector()
        selector.register(p.stdout, selectors.EVENT_READ)
        buffer, sent, result = b"", False, None
        try:
            while selector.get_map():
                run.tick()
                if run.stop_reason and not sent:
                    if p.poll() is None:
                        p.send_signal(signal.SIGINT)
                    sent = True
                if sent and time.monotonic() - run.stop_at > 10:
                    raise TimeoutError("CodeBuddy did not settle within cancel grace")
                for key, _ in selector.select(0.2):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    raw.write(data)
                    raw.flush()
                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        try:
                            item = json.loads(line)
                        except ValueError:
                            continue
                        kind = item.get("type")
                        actual_sid = item.get("session_id")
                        if actual_sid and actual_sid != state["session_id"]:
                            raise RuntimeError("CodeBuddy returned a different session ID")
                        if kind == "system" and item.get("subtype") == "init":
                            actual_model = item.get("model")
                            if state.get("model") and actual_model != state["model"]:
                                raise RuntimeError("CodeBuddy returned a different model")
                            state["model"] = actual_model
                            state["session_confirmed"] = bool(actual_sid)
                            run.event("initialized", session_id=actual_sid, model=actual_model)
                        elif kind == "assistant":
                            for block in item.get("message", {}).get("content", []):
                                if block.get("type") == "tool_use":
                                    run.event("tool_started", name=block.get("name"))
                        elif kind == "user":
                            for block in item.get("message", {}).get("content", []):
                                if block.get("type") == "tool_result":
                                    run.event("tool_finished", error=block.get("is_error", False))
                        elif kind == "result":
                            result = item
                            save(run.attempt / "result.json", item)
                            if not item.get("is_error") and item.get("subtype") == "success":
                                (run.attempt / "report.md").write_text(str(item.get("result", "")))
                            save(run.attempt / "usage.json", {
                                "source": "CodeBuddy result; accounting scope not verified",
                                "usage": item.get("usage"), "modelUsage": item.get("modelUsage"),
                                "reported_cost_usd": item.get("total_cost_usd"),
                            })
                            run.event("result", subtype=item.get("subtype"), error=item.get("is_error"))
            state["worker_exit"] = p.wait(timeout=10)
        finally:
            selector.close()
            p.stdout.close()
    if run.stop_reason:
        return run.stop_reason
    if not result or result.get("is_error") or result.get("subtype") != "success" or state["worker_exit"]:
        raise RuntimeError(f"CodeBuddy did not return a successful final result: {result_detail(result)}")
    return "awaiting_review"


def dsh(run):
    state, usage = run.state, []

    def startup_tick():
        run.tick()
        if run.stop_reason:
            raise TimeoutError("dsh stopped before prompt submission")

    def update(params):
        if state.get("session_id") and params["sessionId"] != state["session_id"]:
            raise RuntimeError("dsh update belongs to a different session")
        item = params["update"]
        kind = item["sessionUpdate"]
        if kind == "agent_message_chunk" and item.get("content", {}).get("type") == "text":
            with (run.attempt / "report.md").open("a") as f:
                f.write(item["content"]["text"])
        elif kind in {"tool_call", "tool_call_update"}:
            run.event(kind, name=item.get("title"), status=item.get("status"), tool_id=item.get("toolCallId"))
        elif kind == "usage_update":
            usage.append(item)

    def permission(params):
        # This local workflow is explicitly authorized to inherit full permissions.
        # It does not turn approval callbacks into a sandbox or broaden the task scope.
        run.event("permission", decision="allow_once", tool_id=params["toolCall"]["toolCallId"])
        return True

    with (run.attempt / "raw/stderr.log").open("wb") as err:
        client = ACP([state["executable"], "--profile", "acp"], run.cwd, err, update, permission)
        run.attach(client.process)
        try:
            capabilities = client.initialize(tick=startup_tick)
            save(run.attempt / "initialize.json", capabilities)
            method = "session/new" if not state.get("session_id") else "session/resume"
            params = {"cwd": str(run.cwd), "mcpServers": []}
            if state.get("session_id"):
                params["sessionId"] = state["session_id"]
            startup_tick()
            session = client.call(method, params, tick=startup_tick)
            if method == "session/new":
                state["session_id"] = session["sessionId"]
                state["session_confirmed"] = True
                run.persist()
            options = session.get("configOptions", [])
            model_option = next((x for x in options if x["id"] == "model"), None)
            if state.get("model") and model_option and model_option["currentValue"] != state["model"]:
                session = client.call("session/set_config_option", {
                    "sessionId": state["session_id"], "configId": "model", "value": state["model"],
                }, tick=startup_tick)
                options = session.get("configOptions", [])
            actual = next((x["currentValue"] for x in options if x["id"] == "model"), None)
            if state.get("model") and actual != state["model"]:
                raise RuntimeError("Could not confirm requested dsh model")
            state["model"] = actual
            save(run.attempt / "session.json", session)
            run.event("initialized", session_id=state["session_id"], model=actual)
            sent = False

            def tick():
                nonlocal sent
                run.tick()
                if run.stop_reason and not sent:
                    client.notify("session/cancel", {"sessionId": state["session_id"]})
                    sent = True
                if sent and time.monotonic() - run.stop_at > 10:
                    raise TimeoutError("dsh cancel did not settle within grace")

            startup_tick()
            result = client.call("session/prompt", {
                "sessionId": state["session_id"], "prompt": [{"type": "text", "text": run.prompt}],
            }, timeout=run.budget + 15, tick=tick)
            save(run.attempt / "result.json", result)
            run.event("result", stop_reason=result.get("stopReason"))
        finally:
            save(run.attempt / "usage.json", {"source": "ACP usage_update; accounting scope unverified", "updates": usage})
            try:
                if state.get("session_id"):
                    client.call("session/close", {"sessionId": state["session_id"]}, timeout=10)
            finally:
                state["worker_exit"] = client.shutdown()
    if run.stop_reason:
        return run.stop_reason
    if result.get("stopReason") != "end_turn":
        raise RuntimeError(f"dsh stopped without completion: {result}")
    return "awaiting_review"


def dispatch(args):
    folder = Path(args.task_dir).expanduser().resolve()
    if args.command == "start":
        if args.backend == "dsh" and args.max_turns is not None:
            raise ValueError("--max-turns is only valid for the codebuddy backend")
        cwd = Path(args.cwd).expanduser().resolve()
        if Path(git(cwd, "rev-parse", "--show-toplevel").strip()).resolve() != cwd:
            raise ValueError("Use the root of an explicit Git workspace/worktree")
        if folder == cwd or cwd in folder.parents:
            raise ValueError("Keep task state outside the worker workspace")
        for name in args.allow:
            if not name or Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError("--allow must be a relative file or directory (trailing /)")
        executable = shutil.which(args.executable or args.backend)
        if not executable:
            raise ValueError("Worker executable not found")
        folder.mkdir(parents=True, mode=0o700, exist_ok=False)
        state = {"task_id": folder.name, "cwd": str(cwd), "backend": args.backend,
                 "executable": str(Path(executable).resolve()), "model": args.model,
                 "allow": args.allow, "session_id": str(uuid.uuid4()) if args.backend == "codebuddy" else None,
                 "session_confirmed": False, "attempt": 0, "status": "new", "permission_mode": "full",
                 "one_shot": args.one_shot, "max_attempts": args.max_attempts or 3}
        save(folder / "state.json", state)
    with exclusive(folder / "task.lock"):
        state = read(folder / "state.json")
        if args.command == "resume" and state["backend"] == "dsh" and args.max_turns is not None:
            raise ValueError("--max-turns is only valid for the codebuddy backend")
        if state["status"] in ACTIVE | {"needs_attention", "scope_violation"}:
            raise RuntimeError("Unsettled attempt; inspect status and recover before resuming")
        if state.get("session_closed") or (args.command == "resume" and state.get("one_shot")):
            raise RuntimeError("Session is closed or one-shot; create a new task instead")
        if args.command == "resume" and not state.get("session_confirmed"):
            raise RuntimeError("No confirmed session ID to resume; do not blindly re-submit")
        limit = args.max_attempts or state.get("max_attempts", 3)
        if state["attempt"] >= limit:
            raise RuntimeError("Attempt limit reached; reassess before explicitly raising --max-attempts")
        cwd = Path(state["cwd"])
        with exclusive(workspace_lock_path(cwd)) as lease:
            lease.seek(0)
            previous = lease.read()
            if previous and json.loads(previous).get("active"):
                raise RuntimeError("Workspace has an unsettled prior owner; inspect and recover that task")
            if args.prompt_file:
                prompt = Path(args.prompt_file).read_text()
            elif state["status"] == "needs_work":
                attempt = Path(state["attempt_dir"])
                if snapshot(cwd) != read(attempt / "after.json"):
                    raise RuntimeError("Workspace changed since review; provide updated feedback explicitly")
                prompt = "Fix the following independently reviewed defects in the existing scope:\n" + (attempt / "review.md").read_text()
            else:
                raise ValueError("Provide an explicit decision/instruction via --prompt-file; only needs_work can reuse review")
            if not prompt.strip():
                raise ValueError("Empty prompt")
            if state["status"] == "blocked":
                (Path(state["attempt_dir"]) / "decision.md").write_text(prompt)
            state["attempt"] += 1
            state["max_attempts"] = limit
            if state["backend"] == "codebuddy":
                state["max_turns"] = resolved_max_turns(state, getattr(args, "max_turns", None))
            scope = ", ".join(state["allow"]) or "none (read-only task)"
            prompt += (f"\n\nWorker contract: work only in {cwd}. Preserve existing changes. "
                       f"Allowed changes: {scope}. Do not edit other files, Git metadata, or commit. "
                       "Use existing full permissions only for this task; do not send external messages or deploy. "
                       "Do not spawn additional agents unless the task explicitly requests them. "
                       "Return actual changes, checks with exit results, and remaining blockers. "
                       "The caller owns the objective, plan and final correctness. Follow its plan when provided. "
                       "If a decision or approval is needed, stop the affected work and return the question, "
                       "evidence, options with consequences, and your recommendation; do not assume approval "
                       "or expand scope. Finish the response so the caller can decide. "
                       "Report blockers rather than retrying indefinitely.")
            run = Run(folder, state, prompt, args.budget)
            lock_record(lease, {"active": True, "task_dir": str(folder)})
            old_handlers = {s: signal.signal(s, lambda *_: run.request_stop("cancelled")) for s in (signal.SIGINT, signal.SIGTERM)}
            try:
                status = codebuddy(run) if state["backend"] == "codebuddy" else dsh(run)
            except Exception as error:
                state["error"] = f"{type(error).__name__}: {error}"
                status = run.stop_reason or "failed"
            finally:
                survivors = run.cleanup()
                for sig, handler in old_handlers.items():
                    signal.signal(sig, handler)
            after = snapshot(cwd)
            save(run.attempt / "after.json", after)
            (run.attempt / "changes.diff").write_text(git(cwd, "diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD"))
            changes = changed(run.before, after)
            outside = [name for name in changes if not in_scope(name, state["allow"])]
            if after["head"] != run.before["head"]:
                outside.append("<Git HEAD changed>")
            state.update(status=status, elapsed_s=round(time.monotonic() - run.start, 3),
                         changes=changes, out_of_scope=outside, cleanup_required=survivors,
                         ended_at=time.time())
            if outside:
                state["status"] = "scope_violation"
            remaining = [item for item in run.known.values() if is_alive(item)]
            if remaining:
                state["status"] = "needs_attention"
            elif survivors and status == "awaiting_review":
                state["status"] = "failed"
                state["error"] = "Worker left live observed children; controller cleaned them up"
            run.persist()
            save(run.attempt / "outcome.json", state)
            lock_record(lease, {"active": bool(remaining), "task_dir": str(folder)})
    print(json.dumps({"task_dir": str(folder), "status": state["status"],
                      "session_id": state["session_id"], "attempt": state["attempt"],
                      "report": str(run.attempt / "report.md"), "error": state.get("error")}, ensure_ascii=False))
    return 0 if state["status"] == "awaiting_review" else 2


def inspect_task(args):
    folder = Path(args.task_dir).expanduser().resolve()
    state = read(folder / "state.json")
    if args.command == "status":
        table = processes()
        state["controller_alive"] = is_alive(state.get("controller"), table)
        state["worker_alive"] = is_alive(state.get("worker"), table)
        if state["status"] in ACTIVE and not state["controller_alive"]:
            state["observed_status"] = "unconfirmed; inspect known processes before recover"
        keys = ("task_id", "backend", "status", "observed_status", "model", "session_id",
                "attempt", "attempt_dir", "budget_seconds", "max_turns", "elapsed_s", "last_event",
                "controller_alive", "worker_alive", "changes", "out_of_scope", "error",
                "one_shot", "max_attempts", "session_closed", "cleanup")
        print(json.dumps({key: state[key] for key in keys if key in state}, ensure_ascii=False, indent=2))
    elif args.command == "cancel":
        if state["status"] not in ACTIVE or not is_alive(state.get("controller")):
            raise RuntimeError("No confirmed live controller; inspect status instead of guessing a PID")
        save(folder / "cancel.json", {"attempt": state["attempt"], "requested_at": time.time()})
        print("Cancellation requested; observe status until the attempt is terminal")
    elif args.command == "cleanup":
        with exclusive(folder / "task.lock"), exclusive(workspace_lock_path(Path(state["cwd"]))):
            state = read(folder / "state.json")
            identities = [state.get("controller"), state.get("worker"), *state.get("known_processes", [])]
            if state["status"] in ACTIVE | {"needs_attention", "scope_violation"} or any(is_alive(p) for p in identities):
                raise RuntimeError("Cancel/recover the unsettled task before cleanup")
            # Persist the no-resume boundary before deleting any local logs.
            state["session_closed"] = True
            save(folder / "state.json", state)
            removed = []
            if args.purge_raw:
                for raw in sorted((folder / "attempts").glob("*/raw")):
                    if raw.is_symlink() or raw.resolve().parent.parent != (folder / "attempts").resolve():
                        raise ValueError("Refusing raw cleanup through a symlink or unexpected path")
                    shutil.rmtree(raw)
                    removed.append(str(raw.relative_to(folder)))
            removed = sorted(set(removed) | set(state.get("cleanup", {}).get("removed_raw", [])))
            state["cleanup"] = {"at": time.time(), "removed_raw": removed,
                                "backend_history": "not deleted; CodeBuddy one-shot disables persistence"}
            save(folder / "state.json", state)
            print(json.dumps({"session_closed": True, **state["cleanup"]}))
    else:
        with exclusive(folder / "task.lock"), exclusive(workspace_lock_path(Path(state["cwd"]))) as lease:
            state = read(folder / "state.json")
            note = Path(args.evidence_file).read_text()
            if not note.strip():
                raise ValueError("Evidence file is empty")
            if args.command == "recover":
                identities = [state.get("controller"), state.get("worker"), *state.get("known_processes", [])]
                if any(is_alive(item) for item in identities):
                    raise RuntimeError("An observed process is still alive; do not recover/retry")
                if state["status"] not in ACTIVE | {"needs_attention", "scope_violation"}:
                    raise RuntimeError("Task is already terminal; use resume or review")
                lease.seek(0)
                owner = lease.read()
                if owner and json.loads(owner).get("active") and json.loads(owner).get("task_dir") != str(folder):
                    raise RuntimeError("Workspace lease belongs to a different unsettled task")
                if state["status"] == "scope_violation":
                    before = read(Path(state["attempt_dir"]) / "before.json")
                    current = snapshot(Path(state["cwd"]))
                    for name in state["out_of_scope"]:
                        restored = (current["head"] == before["head"] if name == "<Git HEAD changed>"
                                    else current["files"].get(name) == before["files"].get(name))
                        if not restored:
                            raise RuntimeError(f"Out-of-scope change still unresolved: {name}")
                    state["status"] = "needs_work"
                else:
                    state["status"] = "interrupted"
                lock_record(lease, {"active": False, "task_dir": str(folder)})
            else:
                if state["status"] not in NON_SUCCESS_TERMINAL | {"awaiting_review"}:
                    raise RuntimeError("Only a completed or terminal attempt can enter review")
                if state["status"] in NON_SUCCESS_TERMINAL:
                    if args.decision == "accepted":
                        raise RuntimeError("A failed, timed-out, cancelled or interrupted attempt cannot be accepted as worker success")
                    table = processes()
                    identities = [state.get("controller"), state.get("worker"), *state.get("known_processes", [])]
                    if any(is_alive(item, table) for item in identities):
                        raise RuntimeError("An observed process is still alive; confirm it stopped before review")
                after_path = Path(state["attempt_dir"]) / "after.json"
                if not after_path.is_file():
                    raise RuntimeError("Missing after snapshot; recover or provide an explicit diagnostic before review")
                if snapshot(Path(state["cwd"])) != read(after_path):
                    raise RuntimeError("Workspace changed since worker finished; review evidence is stale")
                state["status"] = args.decision
            (Path(state["attempt_dir"]) / f"{args.command}.md").write_text(note)
            save(folder / "state.json", state)
            print(state["status"])
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "resume", "revise", "status", "cancel", "review", "recover", "cleanup"):
        p = sub.add_parser(name)
        p.add_argument("--task-dir", required=True)
        if name in ("start", "resume", "revise"):
            if name != "revise":
                p.add_argument("--prompt-file", required=name == "start")
            p.add_argument("--budget", type=float, default=300)
            p.add_argument("--max-attempts", type=int, help="Total task attempts; default 3, explicit extension allowed")
            p.add_argument("--max-turns", type=int, help="CodeBuddy turn limit; default 200, retained when omitted, codebuddy only")
        if name == "start":
            p.add_argument("--cwd", required=True)
            p.add_argument("--backend", choices=("codebuddy", "dsh"), required=True)
            p.add_argument("--executable", help="Pin a specific installed executable")
            p.add_argument("--model", help="CodeBuddy model ID; dsh uses its opaque ACP option value")
            p.add_argument("--allow", action="append", default=[], help="Allowed relative file or directory ending /; scope check, not sandbox")
            p.add_argument("--one-shot", action="store_true", help="One submission, still reviewed, never resumable")
        if name in ("review", "recover", "revise"):
            p.add_argument("--evidence-file", required=True)
        if name == "cleanup":
            p.add_argument("--purge-raw", action="store_true", help="Delete this task's raw logs; keep reports and reviews")
        if name == "review":
            p.add_argument("--decision", choices=("accepted", "needs_work", "blocked"), required=True)
    args = parser.parse_args()
    if hasattr(args, "budget") and not (0 < args.budget < 86400):
        parser.error("--budget must be positive and less than one day")
    if getattr(args, "max_attempts", None) is not None and args.max_attempts < 1:
        parser.error("--max-attempts must be positive")
    if getattr(args, "max_turns", None) is not None and args.max_turns < 1:
        parser.error("--max-turns must be positive")
    try:
        if args.command == "revise":
            if getattr(args, "max_turns", None) is not None:
                backend = read(Path(args.task_dir).expanduser().resolve() / "state.json").get("backend")
                if backend == "dsh":
                    raise ValueError("--max-turns is only valid for the codebuddy backend")
            inspect_task(argparse.Namespace(command="review", task_dir=args.task_dir,
                         decision="needs_work", evidence_file=args.evidence_file))
            args.command, args.prompt_file = "resume", None
        return dispatch(args) if args.command in ("start", "resume") else inspect_task(args)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

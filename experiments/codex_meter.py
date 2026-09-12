"""Explicit-file Codex CLI usage collector and opt-in single-caller harness.

No account history discovery, billing conversion, automatic retries or acceptance.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from freetoken import git, is_alive, processes, save, snapshot


FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")


def collect(lines, exit_code=None):
    """Only CLI turn deltas with matched start/end boundaries are supported."""
    turns, issues, thread_ids = [], set(), []
    active = False
    for number, line in enumerate(lines, 1):
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("not an event")
        except (ValueError, TypeError):
            issues.add("invalid_jsonl")
            continue
        kind = event.get("type")
        if kind == "thread.started":
            thread_ids.append(event.get("thread_id"))
            if (len(thread_ids) > 1 or not isinstance(thread_ids[-1], str)
                    or not thread_ids[-1].strip() or active or turns):
                issues.add("ambiguous_thread")
        elif kind == "turn.started":
            if len(thread_ids) != 1:
                issues.add("turn_before_thread")
            if active:
                issues.add("overlapping_turn")
            active = True
        elif kind == "turn.completed":
            if not active:
                issues.add("unmatched_completion_or_duplicate")
            active = False
            usage = event.get("usage")
            if not isinstance(usage, dict):
                usage = {}
                issues.add("missing_usage")
            values = {}
            for field in FIELDS:
                value = usage.get(field)
                valid = type(value) is int and value >= 0
                values[field] = value if valid else None
                if (field in usage and not valid) or (field in ("input_tokens", "output_tokens") and not valid):
                    issues.add("invalid_or_missing_counter")
            for sub, total in (("cached_input_tokens", "input_tokens"),
                               ("reasoning_output_tokens", "output_tokens")):
                if values[sub] is not None and values[total] is not None and values[sub] > values[total]:
                    issues.add("invalid_subcounter")
            turns.append({"line": number, "raw_usage": usage, "counters": values})
        elif kind in ("turn.failed", "error"):
            active = False
            issues.add("failed_event")
        elif "tokenUsage" in event or kind in ("usage_update", "thread/tokenUsage/updated"):
            issues.add("unsupported_accounting_scope")
        elif kind in ("item.started", "item.updated", "item.completed"):
            if not active or len(thread_ids) != 1:
                issues.add("item_outside_turn")
        else:
            issues.add("unsupported_event_type")
    if active:
        issues.add("unfinished_turn")
    if not turns:
        issues.add("no_completed_turn")
    if len(thread_ids) != 1:
        issues.add("missing_or_ambiguous_thread")
    if exit_code != 0:
        issues.add("exit_unverified" if exit_code is None else "nonzero_exit")
    observed = {field: (sum(t["counters"][field] for t in turns)
                       if turns and all(t["counters"][field] is not None for t in turns) else None)
                for field in FIELDS}
    complete = not issues
    totals = observed if complete else dict.fromkeys(FIELDS)
    return {"schema": "freetoken-caller-usage/1", "source": "codex exec --json",
            "accounting_scope": "one CLI invocation; matched turn deltas",
            "measurement_complete": complete, "issues": sorted(issues),
            "exit_code": exit_code, "thread_ids": thread_ids,
            "model_confirmed": None, "turns": turns,
            "observed_counters": observed, "totals": totals,
            "input_plus_output": (totals["input_tokens"] + totals["output_tokens"] if complete else None),
            "independent_acceptance": None, "end_to_end_coverage_verified": False,
            "worker_usage": "separate; not included", "subscription_savings": None}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(manifest_path, output):
    manifest = json.loads(manifest_path.read_text())
    for key in ("case_id", "arm", "workspace", "prompt_file", "model", "reasoning_effort", "sandbox"):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            raise ValueError(f"Manifest requires nonempty {key}")
    if manifest["arm"] not in ("A", "B", "C"):
        raise ValueError("arm must be A (direct), B (baseline), or C (candidate)")
    if manifest["sandbox"] not in ("read-only", "workspace-write", "danger-full-access"):
        raise ValueError("Explicit supported sandbox required")
    budget = manifest.get("timeout_s")
    if type(budget) not in (int, float) or not math.isfinite(budget) or not 0 < budget < 86400:
        raise ValueError("timeout_s must be finite, positive, and less than one day")
    work, prompt = (Path(manifest[key]).expanduser().resolve() for key in ("workspace", "prompt_file"))
    manifest["workspace"], manifest["prompt_file"] = str(work), str(prompt)
    if Path(git(work, "rev-parse", "--show-toplevel").strip()).resolve() != work:
        raise ValueError("Use the root of an explicit Git workspace/worktree")
    if not prompt.is_file() or not prompt.read_text().strip():
        raise ValueError("Nonempty prompt file required")
    if output == work or work in output.parents:
        raise ValueError("Keep measurement output outside the measured workspace")
    executable = shutil.which(manifest.get("executable", "codex"))
    if not executable:
        raise ValueError("Codex executable not found")
    pinned = manifest.get("pinned_files")
    if not isinstance(pinned, list) or not pinned or any(not isinstance(p, str) for p in pinned):
        raise ValueError("pinned_files must explicitly list skill/source/config inputs to hash")
    hashes = {str(Path(p).expanduser().resolve()): digest(Path(p).expanduser().resolve()) for p in pinned}
    argv = [executable, "-a", "never", "exec", "--ignore-user-config", "--ephemeral", "--json",
            "--model", manifest["model"], "--sandbox", manifest["sandbox"],
            "-c", "model_reasoning_effort=" + json.dumps(manifest["reasoning_effort"]),
            "--output-last-message", str(output / "raw/final.txt"), "-"]
    # Hash only explicitly supplied inputs; never inspect auth or global history.
    return {"manifest": manifest, "manifest_sha256": digest(manifest_path),
            "prompt_sha256": digest(prompt), "pinned_sha256": hashes,
            "workspace_before": snapshot(work), "argv": argv,
            "version": subprocess.check_output([executable, "--version"], text=True, timeout=10).strip(),
            "model_requested": manifest["model"], "model_confirmed": None,
            "config_boundary": "ignore user config; project/skill/environment inputs require explicit pinning",
            "end_to_end_coverage_verified": False}


def observe_children(pid, known):
    table = processes()
    parents = {pid} | {p for p, identity in known.items() if is_alive(identity, table)}
    while True:
        found = {p for p, item in table.items() if item["parent"] in parents}
        if found <= parents:
            break
        parents |= found
    known.update({p: table[p] for p in parents if p in table})


def execute(receipt, output):
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    (output / "raw").mkdir(mode=0o700)
    save(output / "receipt.json", receipt)
    manifest, known = receipt["manifest"], {}
    started = time.monotonic()
    interrupted, survivors = False, []
    with Path(manifest["prompt_file"]).expanduser().open("rb") as prompt, \
            (output / "raw/events.jsonl").open("wb") as stdout, \
            (output / "raw/stderr.log").open("wb") as stderr:
        process = subprocess.Popen(receipt["argv"], cwd=manifest["workspace"], stdin=prompt,
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            while process.poll() is None:
                observe_children(process.pid, known)
                if time.monotonic() - started >= manifest["timeout_s"]:
                    interrupted = True
                    break
                time.sleep(.2)
        except KeyboardInterrupt:
            interrupted = True
        finally:
            survivors = [identity for identity in known.values() if is_alive(identity)]
            # Stop only observed identities; detached/unobserved effects remain an explicit limitation.
            for sig in (signal.SIGTERM, signal.SIGKILL):
                for identity in survivors:
                    if is_alive(identity):
                        try:
                            os.kill(identity["pid"], sig)
                        except ProcessLookupError:
                            pass
                if sig == signal.SIGTERM and survivors:
                    time.sleep(.2)
            if process.poll() is None:
                process.kill()
            exit_code = process.wait()
    with (output / "raw/events.jsonl").open() as events:
        ledger = collect(events, exit_code)
    if interrupted or survivors:
        ledger["measurement_complete"] = False
        ledger["issues"].append("interrupted_or_left_live_observed_processes")
        ledger["totals"] = dict.fromkeys(FIELDS)
        ledger["input_plus_output"] = None
    receipt.update(elapsed_s=round(time.monotonic() - started, 3), exit_code=exit_code,
                   interrupted=interrupted, cleanup_observed_pids=[p["pid"] for p in survivors],
                   observed_processes_stopped=not any(is_alive(p) for p in known.values()),
                   unobserved_side_effects_verified=False,
                   workspace_after=snapshot(Path(manifest["workspace"]).expanduser().resolve()))
    ledger["model_requested"] = manifest["model"]
    save(output / "receipt.json", receipt)
    save(output / "caller-usage.json", ledger)
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("collect")
    ingest.add_argument("--events", type=Path, required=True)
    ingest.add_argument("--exit-code", type=int)
    ingest.add_argument("--out", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--execute", action="store_true", help="Explicitly approve this model invocation; default preflight only")
    args = parser.parse_args()
    try:
        if args.command == "collect":
            if args.out.exists():
                raise ValueError("Refusing to overwrite an existing ledger")
            with args.events.open() as lines:
                ledger = collect(lines, args.exit_code)
            save(args.out, ledger)
        else:
            output = args.out.expanduser().resolve()
            if output.exists():
                raise ValueError("Use a fresh output directory")
            receipt = prepare(args.manifest, output)
            if not args.execute:
                print(json.dumps({"status": "preflight_only", "model_called": False,
                                  "manifest_sha256": receipt["manifest_sha256"],
                                  "case_id": receipt["manifest"]["case_id"],
                                  "arm": receipt["manifest"]["arm"], "version": receipt["version"]}))
                return 0
            ledger = execute(receipt, output)
        print(json.dumps({"measurement_complete": ledger["measurement_complete"],
                          "issues": ledger["issues"], "totals": ledger["totals"], "out": str(args.out)}))
        return 0 if ledger["measurement_complete"] else 2
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error)[:400]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

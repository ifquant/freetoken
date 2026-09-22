"""Small offline lifecycle regression: python3 -B scripts/test_freetoken.py."""

import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from freetoken import changed, delta, in_scope, is_alive, processes, requires_takeover, snapshot


RUNNER = Path(__file__).with_name("freetoken.py").resolve()
FAKE = '''#!/usr/bin/env python3
import json, signal, sys, time
from pathlib import Path
args=sys.argv[1:]; prompt=args[-1]
sid=args[args.index('--resume')+1] if '--resume' in args else args[args.index('--session-id')+1]
print(json.dumps({'type':'system','subtype':'init','session_id':sid,'model':'fake'}),flush=True)
if prompt.startswith('hold'):
    signal.signal(signal.SIGINT,lambda *_: sys.exit(0))
    Path('ready').write_text('ready')
    while True: time.sleep(.1)
if prompt.startswith('fail'):
    print(json.dumps({'type':'result','subtype':'error_max_turns','is_error':True,'session_id':sid,'errors':['turn limit reached before completion']}),flush=True)
    sys.exit(0)
Path('out.txt').write_text('repaired' if 'repair-marker' in prompt else 'result')
if prompt.startswith('outside'): Path('keep.txt').write_text('oops')
print(json.dumps({'type':'result','subtype':'success','is_error':False,'session_id':sid,'result':'done'}),flush=True)
'''


with tempfile.TemporaryDirectory(prefix="freetoken-test-") as directory:
    root = Path(directory)
    work = root / "workspace"
    work.mkdir()
    (work / "keep.txt").write_text("base")
    for command in (["git", "init"], ["git", "add", "keep.txt"],
                    ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                     "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                     "commit", "-m", "baseline"]):
        subprocess.run(command, cwd=work, check=True, capture_output=True)
    (work / "keep.txt").write_text("existing dirty work")
    fake = root / "fake"
    fake.write_text(FAKE)
    fake.chmod(0o755)
    prompt = root / "prompt.md"
    evidence = root / "review.md"
    evidence.write_text("Checked out.txt content and preserved keep.txt.")

    def cli(*args, expected=0):
        p = subprocess.run([sys.executable, "-B", str(RUNNER), *map(str, args)],
                           text=True, capture_output=True, timeout=15)
        assert p.returncode == expected, (args, p.returncode, p.stdout, p.stderr)
        return p

    def start_args(task, budget=10):
        return ["start", "--task-dir", task, "--cwd", work, "--backend", "codebuddy",
                "--executable", fake, "--model", "fake", "--prompt-file", prompt,
                "--budget", str(budget), "--allow", "out.txt", "--allow", "ready"]

    def wait_registered_worker(task, process, deadline):
        # Child 'ready' precedes the controller's persisted identity. Killing at
        # that marker alone tests an unobserved launch, not the recorded-writer gate.
        while True:
            assert process.poll() is None and time.monotonic() < deadline
            path = task / "state.json"
            state = json.loads(path.read_text()) if path.exists() else {}
            worker = state.get("worker")
            if (work / "ready").exists() and worker and state.get("session_confirmed") and is_alive(worker):
                return worker
            time.sleep(.01)

    task = root / "success"
    prompt.write_text("success")
    delivered = json.loads(cli(*start_args(task)).stdout)
    assert delivered["report_status"] == "provider_final" and delivered["report_text"] == "done"
    assert delivered["report_requires_full_read"] is False
    assert json.loads(cli("status", "--task-dir", task, "--summary").stdout)["report_text"] is None
    state = json.loads((task / "state.json").read_text())
    assert state["status"] == "awaiting_review" and state["session_confirmed"]
    assert (work / "keep.txt").read_text() == "existing dirty work"
    sid = state["session_id"]
    (work / "out.txt").write_text("changed after run")
    cli("review", "--task-dir", task, "--decision", "accepted", "--evidence-file", evidence, expected=2)
    (work / "out.txt").write_text("result")
    cli("review", "--task-dir", task, "--decision", "blocked", "--evidence-file", evidence)
    cli("resume", "--task-dir", task, "--prompt-file", prompt)
    state = json.loads((task / "state.json").read_text())
    assert state["attempt"] == 2 and state["session_id"] == sid

    evidence.write_text("repair-marker: output must be repaired; verify the actual output.")
    cli("revise", "--task-dir", task, "--evidence-file", evidence)
    state = json.loads((task / "state.json").read_text())
    assert state["attempt"] == 3 and state["session_id"] == sid
    assert (work / "out.txt").read_text() == "repaired"
    cli("review", "--task-dir", task, "--decision", "needs_work", "--evidence-file", evidence)
    cli("resume", "--task-dir", task, expected=2)
    assert json.loads((task / "state.json").read_text())["attempt"] == 3
    (work / "out.txt").write_text("user edited after review")
    cli("resume", "--task-dir", task, "--max-attempts", "4", expected=2)
    (work / "out.txt").write_text("repaired")
    rejected = cli("resume", "--task-dir", task, "--max-attempts", "4", expected=2)
    assert "caller takeover" in rejected.stdout
    assert not (task / "attempts/0004").exists()
    cli("resume", "--task-dir", task, "--prompt-file", prompt, expected=2)
    cli("cleanup", "--task-dir", task, "--purge-raw")
    assert not list((task / "attempts").glob("*/raw"))
    assert (task / "attempts/0003/review.md").is_file()
    assert (task / "attempts/0003/report.md").is_file()
    cli("resume", "--task-dir", task, "--prompt-file", prompt, expected=2)
    cli("cleanup", "--task-dir", task, "--purge-raw")
    assert len(json.loads((task / "state.json").read_text())["cleanup"]["removed_raw"]) == 3
    one = root / "one-shot"
    cli(*start_args(one), "--one-shot")
    assert '--no-session-persistence' in json.loads((one / 'attempts/0001/argv.json').read_text())
    cli("review", "--task-dir", one, "--decision", "accepted", "--evidence-file", evidence)
    cli("resume", "--task-dir", one, "--prompt-file", prompt, expected=2)
    cli("cleanup", "--task-dir", one, "--purge-raw")
    assert json.loads((one / "state.json").read_text())["cleanup"]["backend_history"] == "not deleted; cleanup only removes this tool's local logs"
    outside = root / "external-logs"
    outside.mkdir()
    (outside / "keep").write_text("not owned by cleanup")
    raw_link = one / "attempts/0001/raw"
    raw_link.symlink_to(outside)
    cli("cleanup", "--task-dir", one, "--purge-raw", expected=2)
    assert (outside / "keep").read_text() == "not owned by cleanup"
    raw_link.unlink()

    # TaskSpec acceptance requires a current successful verification receipt.
    (work / "out.txt").unlink(missing_ok=True)
    spec_path = root / "task-spec.json"
    spec_path.write_text(json.dumps({
        "goal": "success spec",
        "scope": {"write": ["out.txt"]},
        "acceptance": {"commands": [[sys.executable, "-c", "from pathlib import Path; assert Path('out.txt').read_text() == 'result'"]]},
        "limits": {"wall_seconds": 10, "check_seconds": 2},
    }))
    spec_task = root / "spec-task"
    cli("start", "--task-dir", spec_task, "--cwd", work, "--backend", "codebuddy",
        "--executable", fake, "--model", "fake", "--spec", spec_path)
    assert not spec_path.with_suffix(".compiled.md").exists()
    cli("review", "--task-dir", spec_task, "--decision", "accepted", "--evidence-file", evidence, expected=2)
    cli("status", "--task-dir", spec_task, "--summary", "--verify")
    verification_path = spec_task / "attempts/0001/verification.json"
    verification = json.loads(verification_path.read_text())
    verification["verification_status"] = "failed"
    verification_path.write_text(json.dumps(verification))
    cli("review", "--task-dir", spec_task, "--decision", "accepted", "--evidence-file", evidence, expected=2)
    cli("status", "--task-dir", spec_task, "--summary", "--verify")
    verification = json.loads(verification_path.read_text())
    verification["spec_sha256"] = "wrong"
    verification_path.write_text(json.dumps(verification))
    cli("review", "--task-dir", spec_task, "--decision", "accepted", "--evidence-file", evidence, expected=2)
    cli("status", "--task-dir", spec_task, "--summary", "--verify")
    cli("review", "--task-dir", spec_task, "--decision", "accepted", "--evidence-file", evidence)
    cli("resume", "--task-dir", spec_task, "--prompt-file", prompt, expected=2)

    blocked = root / "decision-needed"
    cli(*start_args(blocked))
    evidence.write_text("Decision needed: which behavior should the caller choose?")
    cli("review", "--task-dir", blocked, "--decision", "blocked", "--evidence-file", evidence)
    cli("resume", "--task-dir", blocked, expected=2)
    cli("revise", "--task-dir", blocked, "--evidence-file", evidence, expected=2)
    assert json.loads((blocked / "state.json").read_text())["attempt"] == 1
    decision = root / "decision.md"
    decision.write_text("Caller decision: choose repair-marker within the unchanged scope.")
    cli("resume", "--task-dir", blocked, "--prompt-file", decision)
    assert (blocked / "attempts/0001/decision.md").read_text() == decision.read_text()
    assert (work / "out.txt").read_text() == "repaired"

    prompt.write_text("hold")
    task = root / "cancel"
    with (root / "controller.log").open("w") as log:
        process = subprocess.Popen([sys.executable, "-B", str(RUNNER), *map(str, start_args(task))],
                                   stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 10
            while not (work / "ready").exists():
                assert time.monotonic() < deadline and process.poll() is None
                time.sleep(.05)
            assert json.loads(cli("status", "--task-dir", task).stdout)["controller_alive"]
            cli(*start_args(root / "collision"), expected=2)
            cli("resume", "--task-dir", task, "--prompt-file", prompt, expected=2)
            cli("cleanup", "--task-dir", task, "--purge-raw", expected=2)
            cli("cancel", "--task-dir", task)
            assert process.wait(timeout=15) == 2
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
    state = json.loads((task / "state.json").read_text())
    assert state["status"] == "cancelled"
    cli("review", "--task-dir", task, "--decision", "accepted", "--evidence-file", evidence, expected=2)
    cli("review", "--task-dir", task, "--decision", "needs_work", "--evidence-file", evidence)
    (work / "ready").unlink()
    task = root / "timeout"
    cli(*start_args(task, .6), expected=2)
    assert json.loads((task / "state.json").read_text())["status"] == "timed_out"
    cli("review", "--task-dir", task, "--decision", "accepted", "--evidence-file", evidence, expected=2)
    cli("review", "--task-dir", task, "--decision", "blocked", "--evidence-file", evidence)
    # A stalled ACP startup must consume the same budget and never submit work.
    slow_acp = root / "slow-acp"
    slow_acp.write_text('''#!/usr/bin/env python3
import json, sys, time
from pathlib import Path
for line in sys.stdin:
    request = json.loads(line)
    if request.get('method') == 'session/prompt': Path('unexpected-prompt').touch()
    time.sleep(1.5)
    print(json.dumps({'jsonrpc':'2.0','id':request['id'],'result':{'protocolVersion':1}}),flush=True)
''')
    slow_acp.chmod(0o755)
    task = root / "startup-timeout"
    started = time.monotonic()
    cli("start", "--task-dir", task, "--cwd", work, "--backend", "dsh",
        "--executable", slow_acp, "--prompt-file", prompt, "--budget", ".2", expected=2)
    assert json.loads((task / "state.json").read_text())["status"] == "timed_out"
    assert time.monotonic() - started < 5 and not (work / "unexpected-prompt").exists()
    for command, extra in (("resume", ["--prompt-file", prompt]), ("revise", ["--evidence-file", evidence])):
        cli(command, "--task-dir", task, *extra, "--max-turns", "5", expected=2)
        assert json.loads((task / "state.json").read_text())["status"] == "timed_out"
    # Killing the controller releases flock, but must not release its writer lease.
    (work / "ready").unlink(missing_ok=True)
    task = root / "crashed"
    release_attach = root / "release-attach"
    delayed_controller = root / "delayed-controller.py"
    delayed_controller.write_text(f'''import sys, time
from pathlib import Path
sys.path.insert(0, {str(RUNNER.parent)!r})
import freetoken
original = freetoken.processes
calls = 0
def delayed_processes():
    global calls
    calls += 1
    if calls == 2:  # Run controller identity first, then worker attach.
        deadline = time.monotonic() + 10
        while not Path({str(release_attach)!r}).exists():
            assert time.monotonic() < deadline, 'test did not release attach'
            time.sleep(.01)
    return original()
freetoken.processes = delayed_processes
raise SystemExit(freetoken.main())
''')
    with (root / "crashed.log").open("w") as log:
        process = subprocess.Popen([sys.executable, "-B", str(delayed_controller), *map(str, start_args(task))],
                                   stdout=log, stderr=log)
        worker = None
        try:
            deadline = time.monotonic() + 10
            while not (work / "ready").exists():
                assert process.poll() is None and time.monotonic() < deadline
                time.sleep(.01)
            # Deterministically expose the former race before releasing attach.
            assert json.loads((task / "state.json").read_text())["worker"] is None
            release_attach.touch()
            worker = wait_registered_worker(task, process, deadline)
            process.kill()
            process.wait()
            cli(*start_args(root / "crash-collision"), expected=2)
            cli("recover", "--task-dir", task, "--evidence-file", evidence, expected=2)
            os.kill(worker["pid"], signal.SIGINT)
            while is_alive(worker):
                assert time.monotonic() < deadline
                time.sleep(.05)
            cli("recover", "--task-dir", task, "--evidence-file", evidence)
            assert json.loads((task / "state.json").read_text())["status"] == "interrupted"
            assert json.loads((Path(json.loads((task / "state.json").read_text())["attempt_dir"]) / "recover.json").read_text())["status"] == "interrupted"
            # Recovery proves stopped processes, not a missing worker after-snapshot.
            cli("review", "--task-dir", task, "--decision", "needs_work", "--evidence-file", evidence, expected=2)
        finally:
            release_attach.touch()
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
            if worker and is_alive(worker):
                os.kill(worker["pid"], signal.SIGKILL)
    prompt.write_text("outside")
    task = root / "scope"
    cli(*start_args(task), expected=2)
    assert json.loads((task / "state.json").read_text())["out_of_scope"] == ["keep.txt"]
    cli("resume", "--task-dir", task, "--prompt-file", prompt, expected=2)
    cli("recover", "--task-dir", task, "--evidence-file", evidence, expected=2)
    (work / "keep.txt").write_text("existing dirty work")
    cli("recover", "--task-dir", task, "--evidence-file", evidence)
    assert json.loads((task / "state.json").read_text())["status"] == "needs_work"
    assert not in_scope("src2/a.py", ["src/"]) and in_scope("src/a.py", ["src/"])

    # Turn budget: configured, default, retained and overridden; invalid and dsh rejected.
    (work / "out.txt").unlink(missing_ok=True)
    turns = root / "turns"
    prompt.write_text("success")
    cli(*start_args(turns), "--max-turns", "7", "--effort", "max")
    state = json.loads((turns / "state.json").read_text())
    assert state["max_turns"] == 7 and state["effort"] == "max"
    argv = json.loads((turns / "attempts/0001/argv.json").read_text())
    assert argv[argv.index("--max-turns") + 1] == "7"
    assert argv[argv.index("--effort") + 1] == "max"
    assert json.loads((turns / "attempts/0001/outcome.json").read_text())["max_turns"] == 7
    assert json.loads(cli("status", "--task-dir", turns).stdout)["max_turns"] == 7
    cli("resume", "--task-dir", turns, "--prompt-file", prompt)
    argv = json.loads((turns / "attempts/0002/argv.json").read_text())
    assert argv[argv.index("--max-turns") + 1] == "7"
    assert argv[argv.index("--effort") + 1] == "max"
    assert json.loads((turns / "state.json").read_text())["max_turns"] == 7
    cli("resume", "--task-dir", turns, "--prompt-file", prompt, "--max-turns", "9", "--effort", "high")
    argv = json.loads((turns / "attempts/0003/argv.json").read_text())
    assert argv[argv.index("--max-turns") + 1] == "9"
    assert argv[argv.index("--effort") + 1] == "high"
    assert json.loads((turns / "state.json").read_text())["max_turns"] == 9
    assert json.loads((turns / "state.json").read_text())["effort"] == "high"
    cli("resume", "--task-dir", turns, "--prompt-file", prompt, expected=2)
    cli("resume", "--task-dir", turns, "--prompt-file", prompt, "--max-attempts", "4")

    default_turns = root / "default-turns"
    cli(*start_args(default_turns))
    assert json.loads((default_turns / "state.json").read_text())["max_turns"] == 200
    assert json.loads((default_turns / "state.json").read_text())["effort"] == "high"
    argv = json.loads((default_turns / "attempts/0001/argv.json").read_text())
    assert argv[argv.index("--max-turns") + 1] == "200"
    assert argv[argv.index("--effort") + 1] == "high"
    # A legacy state written before the option existed resumes at the 200-turn default.
    state = json.loads((default_turns / "state.json").read_text())
    del state["max_turns"]
    del state["effort"]
    (default_turns / "state.json").write_text(json.dumps(state))
    cli("resume", "--task-dir", default_turns, "--prompt-file", prompt)
    argv = json.loads((default_turns / "attempts/0002/argv.json").read_text())
    assert argv[argv.index("--max-turns") + 1] == "200"
    assert argv[argv.index("--effort") + 1] == "high"
    assert json.loads((default_turns / "state.json").read_text())["max_turns"] == 200

    cli(*start_args(root / "invalid-turns"), "--max-turns", "0", expected=2)
    cli(*start_args(root / "invalid-turns"), "--max-turns", "-3", expected=2)
    cli(*start_args(root / "invalid-turns"), "--max-turns", "nope", expected=2)
    cli("start", "--task-dir", root / "dsh-turns", "--cwd", work, "--backend", "dsh",
        "--executable", fake, "--prompt-file", prompt, "--max-turns", "5", expected=2)
    for invalid_budget in ("nan", "inf", "0", "86400"):
        cli(*start_args(root / f"invalid-budget-{invalid_budget}"), "--budget", invalid_budget, expected=2)

    # Non-success terminal attempts can be reviewed, but never accepted as worker success.
    feedback = root / "feedback.md"
    feedback.write_text("Provider halted at the turn limit; verify the missing output and retry.")
    (work / "out.txt").unlink(missing_ok=True)
    failed = root / "failed"
    prompt.write_text("fail")
    cli(*start_args(failed), expected=2)
    state = json.loads((failed / "state.json").read_text())
    assert state["status"] == "failed"
    provider = json.loads((failed / "attempts/0001/result.json").read_text())
    assert provider["is_error"] and provider["subtype"] == "error_max_turns"
    assert "error_max_turns" in state["error"] and "turn limit reached" in state["error"]
    assert not (failed / "attempts/0001/report.md").exists()
    cli("review", "--task-dir", failed, "--decision", "accepted", "--evidence-file", feedback, expected=2)
    assert json.loads((failed / "state.json").read_text())["status"] == "failed"

    # A live observed process blocks review even though the attempt is terminal.
    live = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        state = json.loads((failed / "state.json").read_text())
        state["known_processes"] = [processes()[live.pid]]
        (failed / "state.json").write_text(json.dumps(state))
        cli("review", "--task-dir", failed, "--decision", "needs_work",
            "--evidence-file", feedback, expected=2)
    finally:
        live.kill()
        live.wait()
    state = json.loads((failed / "state.json").read_text())
    state["known_processes"] = []
    (failed / "state.json").write_text(json.dumps(state))

    # A changed workspace also blocks review until it matches after.json again.
    (work / "out.txt").write_text("tampered after failure")
    cli("review", "--task-dir", failed, "--decision", "needs_work",
        "--evidence-file", feedback, expected=2)
    (work / "out.txt").unlink()
    cli("review", "--task-dir", failed, "--decision", "needs_work", "--evidence-file", feedback)
    assert json.loads((failed / "state.json").read_text())["status"] == "needs_work"
    outcome = json.loads((failed / "attempts/0001/outcome.json").read_text())
    assert outcome["status"] == "failed" and outcome["error"]
    # One failed attempt may retry without a progress percentage or exception.
    cli("resume", "--task-dir", failed)
    state = json.loads((failed / "state.json").read_text())
    assert state["attempt"] == 2 and state["status"] == "awaiting_review"

    # Failed -> blocked also flows through the same gate, then requires a decision.
    (work / "out.txt").unlink(missing_ok=True)
    blocked_fail = root / "failed-blocked"
    prompt.write_text("fail")
    cli(*start_args(blocked_fail), expected=2)
    cli("review", "--task-dir", blocked_fail, "--decision", "blocked", "--evidence-file", feedback)
    assert json.loads((blocked_fail / "state.json").read_text())["status"] == "blocked"
    cli("resume", "--task-dir", blocked_fail, expected=2)
    prompt.write_text("success")
    cli("resume", "--task-dir", blocked_fail, "--prompt-file", prompt)
    assert json.loads((blocked_fail / "state.json").read_text())["status"] == "awaiting_review"

    # Failed -> revise reuses the same review gate (needs_work) before resubmitting.
    (work / "out.txt").unlink(missing_ok=True)
    revised = root / "failed-revise"
    prompt.write_text("fail")
    cli(*start_args(revised), expected=2)
    cli("revise", "--task-dir", revised, "--evidence-file", feedback, "--max-turns", "11")
    state = json.loads((revised / "state.json").read_text())
    assert state["attempt"] == 2 and state["status"] == "awaiting_review"
    assert state["max_turns"] == 11
    assert (revised / "attempts/0001/review.md").read_text() == feedback.read_text()

    # Runtime failure plus a rejected candidate counts once per attempt;
    # revise saves the second review but must not launch a third worker.
    rejected = cli("revise", "--task-dir", revised, "--evidence-file", feedback,
                   "--max-attempts", "9", expected=2)
    assert "caller takeover" in rejected.stdout
    assert json.loads((revised / "state.json").read_text())["status"] == "needs_work"
    assert json.loads((revised / "attempts/0002/review.json").read_text())["decision"] == "needs_work"
    assert not (revised / "attempts/0003").exists()

    # Each progress exception needs fresh caller evidence and >=80% resolution.
    # The exception raises the default total to four, never beyond four.
    progress_file = root / "progress.json"
    progress = {"attempt": 2, "previous_issues": 10, "resolved_issues": 8,
                "verification": "Caller reran checks for issues 1-8; see review.md.",
                "remaining_work": "Issues 9-10 still require the scoped correction."}
    for changes in ({"previous_issues": 100, "resolved_issues": 79}, {"attempt": 1}, {"previous_issues": True},
                    {"previous_issues": 0}, {"resolved_issues": 11}, {"verification": ""},
                    {"remaining_work": None}):
        progress_file.write_text(json.dumps({**progress, **changes}))
        cli("resume", "--task-dir", revised, "--progress-retry-evidence", progress_file, expected=2)
        assert not (revised / "attempts/0003").exists()
    progress_file.write_text(json.dumps(progress))
    prior_output = (work / "out.txt").read_text()
    (work / "out.txt").write_text("changed since caller review")
    cli("resume", "--task-dir", revised, "--prompt-file", prompt,
        "--progress-retry-evidence", progress_file, expected=2)
    (work / "out.txt").write_text(prior_output)
    cli("resume", "--task-dir", revised, "--progress-retry-evidence", progress_file)
    assert json.loads((revised / "state.json").read_text())["attempt"] == 3
    assert json.loads((revised / "state.json").read_text())["max_attempts"] == 4
    assert json.loads((revised / "attempts/0002/progress-retry.json").read_text()) == progress
    cli("revise", "--task-dir", revised, "--evidence-file", feedback,
        "--progress-retry-evidence", progress_file, expected=2)
    assert not (revised / "attempts/0004").exists()  # Old attempt-2 evidence is stale.
    progress["attempt"] = 3
    progress_file.write_text(json.dumps(progress))
    cli("resume", "--task-dir", revised, "--progress-retry-evidence", progress_file,
        "--max-attempts", "9")
    assert json.loads((revised / "state.json").read_text())["attempt"] == 4
    assert json.loads((revised / "state.json").read_text())["max_attempts"] == 4
    progress["attempt"] = 4
    progress_file.write_text(json.dumps(progress))
    cli("revise", "--task-dir", revised, "--evidence-file", feedback,
        "--progress-retry-evidence", progress_file, "--max-attempts", "9", expected=2)
    assert not (revised / "attempts/0005").exists()
    assert (revised / "attempts/0004/review.json").is_file()

    # Progress evidence does not silently raise an explicit (or legacy unknown)
    # cap; only a new --max-attempts choice can raise that saved limit.
    prompt.write_text("success")
    for cap, legacy in ((2, False), (3, False), (3, True)):
        capped = root / f"explicit-cap-{cap}-{legacy}"
        cli(*start_args(capped), "--max-attempts", cap)
        cli("revise", "--task-dir", capped, "--evidence-file", feedback)
        cli("review", "--task-dir", capped, "--decision", "needs_work", "--evidence-file", feedback)
        state_path = capped / "state.json"
        if legacy:
            state = json.loads(state_path.read_text())
            state.pop("max_attempts_explicit", None)
            state_path.write_text(json.dumps(state))
        progress["attempt"] = 2
        progress_file.write_text(json.dumps(progress))
        retry = ["resume", "--task-dir", capped, "--progress-retry-evidence", progress_file]
        if cap == 3:
            cli(*retry)
            assert json.loads(state_path.read_text())["max_attempts"] == cap
            cli("review", "--task-dir", capped, "--decision", "needs_work", "--evidence-file", feedback)
            progress["attempt"] = 3
            progress_file.write_text(json.dumps(progress))
        cli(*retry, expected=2)
        assert json.loads(state_path.read_text())["max_attempts"] == cap
        assert not (capped / "attempts" / f"{cap + 1:04d}").exists()
        cli(*retry, "--max-attempts", "4")
        assert json.loads(state_path.read_text())["attempt"] == cap + 1

    # Two provider failures also stop bare resume; blocked review cannot erase
    # the original outcome, and partial progress does not make failure success.
    double_fail = root / "double-fail"
    prompt.write_text("fail")
    cli(*start_args(double_fail), expected=2)
    cli("resume", "--task-dir", double_fail, "--prompt-file", prompt, expected=2)
    cli("review", "--task-dir", double_fail, "--decision", "blocked", "--evidence-file", feedback)
    rejected = cli("resume", "--task-dir", double_fail, "--prompt-file", prompt,
                   "--max-attempts", "9", expected=2)
    assert "caller takeover" in rejected.stdout
    assert json.loads((double_fail / "state.json").read_text())["attempt"] == 2
    assert json.loads((double_fail / "attempts/0001/outcome.json").read_text())["status"] == "failed"
    assert not (double_fail / "attempts/0003").exists()

    # An explicit user exception waives only the percentage, for one named
    # continuation. No invented progress or rewritten failures are required.
    double_fail = root / "user-authorized-retry"
    cli(*start_args(double_fail), expected=2)
    cli("resume", "--task-dir", double_fail, "--prompt-file", prompt, expected=2)
    authorization_file = root / "user-retry.json"
    state_path = double_fail / "state.json"
    state = json.loads(state_path.read_text())
    authorization = {"task_id": state["task_id"], "session_id": state["session_id"],
                     "next_attempt": 3, "user_instruction": "Retry once in this same session.",
                     "instruction_source": "User message in the test conversation"}
    authorization_file.write_text(json.dumps(authorization))
    retry = ["resume", "--task-dir", double_fail,
             "--user-retry-authorization", authorization_file, "--budget", "17"]
    cli(*retry, expected=2)  # A failed run still needs an independent review.
    cli("review", "--task-dir", double_fail, "--decision", "needs_work", "--evidence-file", feedback)
    state = json.loads(state_path.read_text())
    originals = {p: p.read_bytes() for p in (double_fail / "attempts").glob("*/*.json")}
    for invalid in ([], {**authorization, "task_id": "another-task"},
                    {**authorization, "session_id": "another-session"},
                    {**authorization, "next_attempt": True},
                    {**authorization, "next_attempt": 4},
                    {**authorization, "user_instruction": " "},
                    {**authorization, "instruction_source": None}):
        authorization_file.write_text(json.dumps(invalid))
        cli(*retry, expected=2)
        assert not (double_fail / "attempts/0003").exists()
    authorization_file.write_text(json.dumps(authorization))
    cli(*retry, "--progress-retry-evidence", progress_file, expected=2)
    cli(*retry, "--max-attempts", "2", expected=2)
    state_path.write_text(json.dumps({**state, "worker": processes()[os.getpid()]}))
    assert "observed_processes_stopped" in cli(*retry, expected=2).stdout
    state_path.write_text(json.dumps(state))
    original_output = (work / "out.txt").read_bytes()
    (work / "out.txt").write_text("user edited after review")
    assert "workspace_matches_after" in cli(*retry, expected=2).stdout
    (work / "out.txt").write_bytes(original_output)
    cli(*retry)
    resumed = json.loads(state_path.read_text())
    assert resumed["attempt"] == 3 and resumed["session_id"] == state["session_id"]
    assert resumed["model"] == state["model"] and resumed["effort"] == state["effort"]
    assert resumed["max_attempts"] == state["max_attempts"] == 3
    assert resumed["budget_seconds"] == 17
    assert all(p.read_bytes() == content for p, content in originals.items())
    receipt = json.loads((double_fail / "attempts/0003/user-retry-authorization.json").read_text())
    assert all(receipt[k] == v for k, v in authorization.items())
    assert receipt["waived_gate"] == "two-failure progress percentage"
    assert requires_takeover(double_fail, resumed)  # Failure history still counts.
    cli("review", "--task-dir", double_fail, "--decision", "needs_work", "--evidence-file", feedback)
    cli(*retry, "--max-attempts", "4", expected=2)  # Authorization cannot be reused.
    authorization_file.write_text(json.dumps({**authorization, "next_attempt": 4}))
    cli(*retry, expected=2)  # Fresh authorization still cannot raise the saved cap.
    assert not (double_fail / "attempts/0004").exists()
    cli(*retry, "--max-attempts", "4")
    cli("review", "--task-dir", double_fail, "--decision", "needs_work", "--evidence-file", feedback)
    cli(*retry, "--max-attempts", "5", expected=2)  # Fourth authorization is stale.
    authorization_file.write_text(json.dumps({**authorization, "next_attempt": 5}))
    cli(*retry, expected=2)  # Explicit limit still applies beyond four.
    cli(*retry, "--max-attempts", "5")
    fifth = json.loads(state_path.read_text())
    assert fifth["attempt"] == 5 and fifth["session_id"] == state["session_id"]
    assert fifth["max_attempts"] == 5 and fifth["budget_seconds"] == 17
    receipt5 = json.loads((double_fail / "attempts/0005/user-retry-authorization.json").read_text())
    assert receipt5["waived_progress_attempt_ceiling"] is True
    cli("review", "--task-dir", double_fail, "--decision", "needs_work", "--evidence-file", feedback)
    cli(*retry, "--max-attempts", "6", expected=2)  # No reuse for a sixth attempt.

    # A recovered controller crash can lack outcome.json. Its recovery record
    # must survive later handbacks; unreviewed returns do not reset failures.
    history = root / "recovered-history"
    for number, record, data in (
            (1, "recover.json", {"status": "interrupted"}),
            (2, "review.json", {"decision": "blocked"}),
            (3, "outcome.json", {"status": "awaiting_review"}),
            (4, "outcome.json", {"status": "timed_out"})):
        attempt = history / "attempts" / f"{number:04d}"
        attempt.mkdir(parents=True)
        (attempt / record).write_text(json.dumps(data))
        assert requires_takeover(history, {"attempt": number, "status": data.get("status")}) == (number == 4)

    before = snapshot(work)
    (work / "out.txt").unlink()
    assert changed(before, snapshot(work)) == ["out.txt"]
    assert delta(before, snapshot(work))[0]["kind"] == "deleted"
    before = snapshot(work)
    tracked = work / "keep.txt"
    content = tracked.read_text()
    tracked.unlink()
    deleted = snapshot(work)
    assert deleted["files"]["keep.txt"] is None
    assert delta(before, deleted)[0]["kind"] == "deleted"
    tracked.write_text(content)
    assert delta(deleted, snapshot(work))[0]["kind"] == "added"
print("Dispatch lifecycle checks passed")

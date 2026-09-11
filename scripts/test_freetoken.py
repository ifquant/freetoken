"""Small offline lifecycle regression: python3 -B scripts/test_freetoken.py."""

import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from freetoken import changed, in_scope, is_alive, snapshot


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

    task = root / "success"
    prompt.write_text("success")
    cli(*start_args(task))
    state = json.loads((task / "state.json").read_text())
    assert state["status"] == "awaiting_review" and state["session_confirmed"]
    assert (work / "keep.txt").read_text() == "existing dirty work"
    sid = state["session_id"]
    (work / "out.txt").write_text("changed after run")
    cli("review", "--task-dir", task, "--decision", "accepted", "--evidence-file", evidence, expected=2)
    (work / "out.txt").write_text("result")
    cli("review", "--task-dir", task, "--decision", "accepted", "--evidence-file", evidence)
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
    cli("resume", "--task-dir", task, "--max-attempts", "4")
    cli("review", "--task-dir", task, "--decision", "accepted", "--evidence-file", evidence)
    cli("cleanup", "--task-dir", task, "--purge-raw")
    assert not list((task / "attempts").glob("*/raw"))
    assert (task / "attempts/0003/review.md").is_file()
    assert (task / "attempts/0004/report.md").is_file()
    cli("resume", "--task-dir", task, "--prompt-file", prompt, expected=2)
    cli("cleanup", "--task-dir", task, "--purge-raw")
    assert len(json.loads((task / "state.json").read_text())["cleanup"]["removed_raw"]) == 4
    one = root / "one-shot"
    cli(*start_args(one), "--one-shot")
    assert '--no-session-persistence' in json.loads((one / 'attempts/0001/argv.json').read_text())
    cli("review", "--task-dir", one, "--decision", "accepted", "--evidence-file", evidence)
    cli("resume", "--task-dir", one, "--prompt-file", prompt, expected=2)
    cli("cleanup", "--task-dir", one, "--purge-raw")
    outside = root / "external-logs"
    outside.mkdir()
    (outside / "keep").write_text("not owned by cleanup")
    raw_link = one / "attempts/0001/raw"
    raw_link.symlink_to(outside)
    cli("cleanup", "--task-dir", one, "--purge-raw", expected=2)
    assert (outside / "keep").read_text() == "not owned by cleanup"
    raw_link.unlink()

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
    (work / "ready").unlink()
    task = root / "timeout"
    cli(*start_args(task, .6), expected=2)
    assert json.loads((task / "state.json").read_text())["status"] == "timed_out"
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
    # Killing the controller releases flock, but must not release its writer lease.
    (work / "ready").unlink(missing_ok=True)
    task = root / "crashed"
    with (root / "crashed.log").open("w") as log:
        process = subprocess.Popen([sys.executable, "-B", str(RUNNER), *map(str, start_args(task))],
                                   stdout=log, stderr=log)
        worker = None
        try:
            deadline = time.monotonic() + 10
            while not (work / "ready").exists():
                assert process.poll() is None and time.monotonic() < deadline
                time.sleep(.05)
            worker = json.loads((task / "state.json").read_text())["worker"]
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
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
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
    before = snapshot(work)
    (work / "out.txt").unlink()
    assert changed(before, snapshot(work)) == ["out.txt"]
print("Dispatch lifecycle checks passed")

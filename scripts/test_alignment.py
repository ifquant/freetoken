"""Offline alignment and diagnosed-retry checks: python3 -B scripts/test_alignment.py."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile

RUNNER = Path(__file__).with_name("freetoken.py").resolve()
FAKE = '''#!/usr/bin/env python3
import json, sys
from pathlib import Path
args = sys.argv[1:]; prompt = args[-1]
sid = args[args.index('--resume')+1] if '--resume' in args else args[args.index('--session-id')+1]
print(json.dumps(dict(type='system', subtype='init', session_id=sid, model='fake')), flush=True)
failed = 'FAIL_MARKER' in prompt
if 'WRITE_IN_PLAN' in prompt or (not prompt.startswith('ALIGNMENT ONLY:') and not failed):
    Path('out.txt').write_text('result')
print(json.dumps(dict(type='result', subtype='error_during_execution' if failed else 'success',
    is_error=failed, session_id=sid, result='Understanding; next plan; impact; positive/negative/regression.')), flush=True)
'''


with tempfile.TemporaryDirectory(prefix="freetoken-align-") as directory:
    root = Path(directory)
    work = root / "work"
    work.mkdir()
    (work / "keep.txt").write_text("baseline")
    for command in (["git", "init"], ["git", "add", "."],
                    ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                     "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "base"]):
        subprocess.run(command, cwd=work, capture_output=True, check=True)
    fake = root / "fake"
    fake.write_text(FAKE)
    fake.chmod(0o755)
    prompt, review, assessment_file = (root / name for name in ("prompt.md", "review.md", "assessment.json"))
    prompt.write_text("Implement the outcome.")
    review.write_text("Independent review: output needs a scoped correction and regression checks.")

    def cli(*args, expected=0):
        result = subprocess.run([sys.executable, "-B", str(RUNNER), *map(str, args)],
                                capture_output=True, text=True, timeout=15)
        assert result.returncode == expected, (args, result.stdout, result.stderr)
        return result

    def start(task, *options, expected=0):
        return cli("start", "--task-dir", task, "--cwd", work, "--backend", "codebuddy",
                   "--executable", fake, "--model", "fake", "--prompt-file", prompt,
                   "--allow", "out.txt", "--budget", 10, *options, expected=expected)

    def state(task):
        return json.loads((task / "state.json").read_text())

    def reject(task):
        cli("review", "--task-dir", task, "--decision", "needs_work", "--evidence-file", review)

    task = root / "aligned"
    start(task, "--align")
    first = state(task)
    assert first["status"] == "blocked" and first["alignment_ready"] and first["max_attempts"] == 4
    assert not (work / "out.txt").exists()
    assert json.loads(cli("status", "--task-dir", task, "--verify", "--summary").stdout)["alignment_pending"]
    cli("review", "--task-dir", task, "--decision", "accepted", "--evidence-file", review, expected=2)
    cli("resume", "--task-dir", task, expected=2)
    (work / "keep.txt").write_text("intervening user change")
    cli("resume", "--task-dir", task, "--prompt-file", prompt, expected=2)
    (work / "keep.txt").write_text("baseline")
    prompt.write_text("Confirmed. Implement with positive, negative and regression checks.")
    cli("resume", "--task-dir", task, "--prompt-file", prompt)
    second = state(task)
    assert second["session_id"] == first["session_id"] and second["attempt"] == 2
    assert not second["alignment_pending"] and second["status"] == "awaiting_review"
    assert (task / "attempts/0001/decision.md").read_text() == prompt.read_text()
    assert (work / "out.txt").read_text() == "result"

    # Two rejected implementations require an actual changed approach. The plan
    # uses a metered invocation, but neither resets failures nor counts as one.
    reject(task)
    cli("resume", "--task-dir", task)
    reject(task)
    cli("resume", "--task-dir", task, "--max-attempts", 8, expected=2)
    assessment = dict(task_id=task.name, session_id=first["session_id"], next_attempt=4,
                      cause="understanding", diagnosis="Missed legitimate path", evidence="review.md",
                      adjustment="Preserve current owner; reject stale owner", remaining_work="Ownership check",
                      verification="Positive, negative, affected integration and regression")
    for field, value in (("session_id", "wrong"), ("next_attempt", 3), ("adjustment", ""), ("cause", "unknown")):
        assessment_file.write_text(json.dumps({**assessment, field: value}))
        cli("resume", "--task-dir", task, "--retry-assessment", assessment_file, expected=2)
    assessment_file.write_text(json.dumps(assessment))
    (work / "keep.txt").write_text("intervening user change")
    cli("resume", "--task-dir", task, "--retry-assessment", assessment_file, expected=2)
    (work / "keep.txt").write_text("baseline")
    cli("resume", "--task-dir", task, "--retry-assessment", assessment_file)
    assert state(task)["attempt"] == 4
    assert json.loads((task / "attempts/0004/retry-assessment.json").read_text()) == assessment
    assert assessment["adjustment"] in (task / "attempts/0004/prompt.md").read_text()
    reject(task)
    assessment_file.write_text(json.dumps({**assessment, "next_attempt": 5}))
    cli("resume", "--task-dir", task, "--retry-assessment", assessment_file, "--max-attempts", 8, expected=2)

    start(root / "invalid-one-shot", "--align", "--one-shot", expected=2)
    start(root / "invalid-limit", "--align", "--max-attempts", 1, expected=2)
    assert not (root / "invalid-one-shot").exists()
    (work / "out.txt").unlink()
    prompt.write_text("FAIL_MARKER")
    failed = root / "failed-plan"
    start(failed, "--align", expected=2)
    assert state(failed)["alignment_pending"] and not state(failed)["alignment_ready"]
    reject(failed)
    prompt.write_text("Read and plan, service recovered.")
    cli("resume", "--task-dir", failed, "--prompt-file", prompt)
    assert state(failed)["alignment_ready"] and not (work / "out.txt").exists()

    # TaskSpec commands must not run while the worker is only proposing a plan.
    spec = root / "spec.json"
    spec.write_text(json.dumps(dict(goal="Plan", scope={"write": ["out.txt"]},
        acceptance={"commands": [[sys.executable, "-c", "raise RuntimeError('must not run in alignment')"]]},
        limits={"wall_seconds": 10})))
    planned = root / "spec-plan"
    start(planned, "--align", "--spec", spec)
    verified = json.loads(cli("status", "--task-dir", planned, "--verify", "--summary").stdout)
    assert verified["acceptance_checks"]["count"] == 0

    # A later allowlist is not permission to edit during the initial handshake.
    prompt.write_text("WRITE_IN_PLAN")
    violation = root / "bad-plan"
    start(violation, "--align", expected=2)
    assert state(violation)["status"] == "scope_violation"
    assert state(violation)["out_of_scope"] == ["out.txt"]
    cli("status", "--task-dir", violation, "--verify", expected=2)
    cli("resume", "--task-dir", violation, "--prompt-file", prompt, expected=2)
    (work / "out.txt").unlink()

    # Restoring a forbidden edit must not require matching the violating after
    # snapshot on the next assessed continuation. Keep that old evidence intact.
    prompt.write_text("FAIL_MARKER")
    recovered = root / "recovered-plan"
    start(recovered, "--align", expected=2)
    reject(recovered)
    prompt.write_text("WRITE_IN_PLAN")
    cli("resume", "--task-dir", recovered, "--prompt-file", prompt, expected=2)
    failed_after = (recovered / "attempts/0002/after.json").read_bytes()
    (work / "out.txt").unlink()
    cli("recover", "--task-dir", recovered, "--evidence-file", review)
    recovered_state = state(recovered)
    fresh = {**assessment, "task_id": recovered.name, "session_id": recovered_state["session_id"],
             "next_attempt": 3, "cause": "scope", "adjustment": "Read only until caller confirms"}
    assessment_file.write_text(json.dumps(fresh))
    prompt.write_text("Read and plan only.")
    (work / "keep.txt").write_text("post-recovery drift")
    cli("resume", "--task-dir", recovered, "--prompt-file", prompt,
        "--retry-assessment", assessment_file, expected=2)
    (work / "keep.txt").write_text("baseline")
    cli("resume", "--task-dir", recovered, "--prompt-file", prompt, "--retry-assessment", assessment_file)
    assert state(recovered)["alignment_ready"]
    assert (recovered / "attempts/0002/after.json").read_bytes() == failed_after
    assert "recovered_snapshot_sha256" not in state(recovered)
    # A valid alignment handback does not erase earlier failures, but a fresh
    # assessment plus confirmation must still permit the bounded implementation.
    assessment_file.write_text(json.dumps({**fresh, "next_attempt": 4}))
    prompt.write_text("Confirmed; implement the bounded outcome.")
    cli("resume", "--task-dir", recovered, "--prompt-file", prompt, "--retry-assessment", assessment_file)
    assert state(recovered)["status"] == "awaiting_review"

print("PASS: alignment, confirmation, unchanged-workspace checks, diagnosed retry, caps and legacy opt-in boundaries")

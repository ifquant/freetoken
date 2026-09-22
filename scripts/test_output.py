"""Offline compact status, complete handback and dsh report-framing checks."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from freetoken import ACTIVE, final_report, processes, report_signals, snapshot, summary
from task_spec import load as load_spec


OPEN, CLOSE = "<freetoken-report>", "</freetoken-report>"
assert final_report(["progress", OPEN + "done" + CLOSE]) == ("framed", "done")
assert final_report([OPEN + "a", "b" + CLOSE]) == ("invalid", None)
assert final_report([OPEN + "complete" + CLOSE, "later: the check failed"]) == ("invalid", None)
assert final_report([OPEN + "complete" + CLOSE + "later: the check failed"]) == ("invalid", None)
for text in (OPEN + CLOSE, OPEN + "a" + CLOSE + OPEN + "b" + CLOSE,
             CLOSE + "bad" + OPEN):
    assert final_report([text]) == ("invalid", None)
for body in ("x" * 6001, " " * 6000 + "a", "中" * 2001):
    assert final_report([OPEN + body + CLOSE]) == ("framed", body.strip())
assert final_report(["no explicit final report"]) == ("unstructured", None)
state = {"changes": ["x" * 2000] * 10000, "out_of_scope": ["y" * 2000] * 10000,
         "error": "e" * 100000, "model": "m" * 100000, "session_id": "s" * 100000}
compact = summary(state, "/task")
assert len(json.dumps(compact)) < 5000
assert compact["changes_count"] == 10000 and len(compact["changes_sample"]) == 5
assert compact["independent_verification"] is None
assert compact["report_bytes"] is None
assert compact["report_text"] is None and compact["report_requires_full_read"] is True
assert compact["report_warnings"] == []
assert compact["report_signals"] == {"unrun_checks": "unknown", "decision_required": "unknown", "pending_work": "unknown", "clarification_required": "unknown"}

with tempfile.TemporaryDirectory(prefix="freetoken-handback-") as directory:
    report = Path(directory) / "report.md"
    for text in ("short report", "HEAD-" + "x" * 9000 + "-TAIL", "开头" + "中" * 3000 + "结尾"):
        report.write_text(text)
        state = {"attempt_dir": str(report.parent), "status": "awaiting_review", "report_status": "framed"}
        compact = summary(state, "/task")
        assert compact["report_text"] is None and len(json.dumps(compact)) < 5000
        assert compact["report_bytes"] == len(text.encode("utf-8"))
        assert compact["report_requires_full_read"] is True
        delivered = summary(state, "/task", include_report=True)
        assert delivered["report_text"] == text and delivered["report_requires_full_read"] is False
        for active in ACTIVE:
            running = summary({**state, "status": active}, "/task", include_report=True)
            assert running["report_text"] is None and running["report_bytes"] is None
            assert set(running["report_signals"].values()) == {"unknown"}
            assert running["report_warnings"] == []
    report.write_text("UNRUN_CHECKS: none\nDECISION_REQUIRED: choose A\nPENDING_WORK: docs\nCLARIFICATION_REQUIRED: yes")
    assert report_signals(report) == {"unrun_checks": "none_declared", "decision_required": "present", "pending_work": "present", "clarification_required": "present"}
    declarations = "UNRUN_CHECKS: none\nDECISION_REQUIRED: none\nPENDING_WORK: none\nCLARIFICATION_REQUIRED: no"
    for text, warnings in (
        ("status: complete\n" + declarations, []),
        ("status: complete\n" + declarations.replace("PENDING_WORK: none", "PENDING_WORK: required delayed-write proof"),
         ["completion_claim_with_declared_gaps"]),
        ("STATUS: complete (caller acceptance pending)\n" + declarations.replace("UNRUN_CHECKS: none", "UNRUN_CHECKS: required integration"),
         ["completion_claim_with_declared_gaps"]),
        ("status: complete\n" + declarations.replace("DECISION_REQUIRED: none", "DECISION_REQUIRED: choose contract"),
         ["completion_claim_with_declared_gaps"]),
        ("status: complete", ["completion_claim_without_required_declarations"]),
        ("status: needs_work\n" + declarations.replace("PENDING_WORK: none", "PENDING_WORK: required proof"), []),
        ("status: blocked\n" + declarations.replace("DECISION_REQUIRED: none", "DECISION_REQUIRED: authorize next stage"), []),
    ):
        report.write_text(text)
        for include_report in (False, True):
            delivered = summary(state, "/task", include_report=include_report)
            assert delivered["report_warnings"] == warnings, (text, delivered)
            assert delivered["status"] == "awaiting_review"
            assert delivered["independent_verification"] is None
            assert delivered["report_text"] == (text if include_report else None)
        for active in ACTIVE:
            assert summary({**state, "status": active}, "/task")["report_warnings"] == []

RUNNER = Path(__file__).with_name("freetoken.py")
with tempfile.TemporaryDirectory(prefix="freetoken-output-") as directory:
    root = Path(directory)
    work = root / "work"
    work.mkdir()
    for argv in (["git", "init"], ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                 "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "fixture"]):
        subprocess.run(argv, cwd=work, check=True, capture_output=True)
    prompt = root / "prompt.md"
    fake = root / "fake-acp"
    fake.write_text('''#!/usr/bin/env python3
import json, sys
def emit(value): print(json.dumps(value), flush=True)
def text(value, msg=None):
    update = {'sessionUpdate':'agent_message_chunk','content':{'type':'text','text':value}}
    if msg is not None: update['msgId'] = msg
    emit({'jsonrpc':'2.0','method':'session/update','params':{'sessionId':'offline','update':update}})
for line in sys.stdin:
    request = json.loads(line)
    method, result = request['method'], {}
    if method == 'initialize': result = {'protocolVersion':1}
    elif method in ('session/new','session/resume'):
        result = {'sessionId':'offline','configOptions':[{'id':'model','currentValue':'fake'},
            {'id':'reasoning_effort','currentValue':'high'}]}
    elif method == 'session/set_config_option':
        result = {'sessionId':'offline','configOptions':[{'id':'model','currentValue':'fake'},
            {'id':'reasoning_effort','currentValue':request['params']['value']}]}
    elif method == 'session/prompt':
        prompt = request['params']['prompt'][0]['text']
        assert '<freetoken-report>' in prompt
        # Verify the transmitted protocol matches the declarations parsed by status.
        for declaration in ('UNRUN_CHECKS:', 'DECISION_REQUIRED:', 'PENDING_WORK:', 'CLARIFICATION_REQUIRED:'):
            assert declaration in prompt
        mode = 'oversized' if 'oversized' in prompt.splitlines() else prompt.splitlines()[0]
        text('private progress, not the final delivery\\n', 'progress')
        for i in range(100):
            emit({'jsonrpc':'2.0','method':'session/update','params':{'sessionId':'offline','update':{
                'sessionUpdate':'tool_call_update','toolCallId':str(i),'title':'large private tool title','status':'completed'}}})
        if mode == 'missing': text('ordinary unframed text')
        elif mode == 'multiple': text('<freetoken-report>a</freetoken-report><freetoken-report>b</freetoken-report>')
        elif mode == 'oversized':
            text('<freetoken-report>HEAD-' + '中'*1500 + '\\nDECISION_REQUIRED: choose A\\n' +
                 '中'*1500 + '-TAIL</freetoken-report>')
        elif mode == 'incomplete':
            text('<freetoken-report>status: complete\\nUNRUN_CHECKS: required recovery test\\n'
                 'DECISION_REQUIRED: none\\nPENDING_WORK: required proof\\n'
                 'CLARIFICATION_REQUIRED: no</freetoken-report>')
        elif mode == 'split-id':
            text('<freetoken-report>a','one'); text('b</freetoken-report>','two')
        elif mode == 'interleaved':
            text('<freetoken-report>done','final'); text('more progress','progress'); text('</freetoken-report>','final')
        elif mode == 'late-message':
            text('<freetoken-report>done</freetoken-report>','final'); text('later: the check failed','late')
        elif mode == 'late-same':
            text('<freetoken-report>done</freetoken-report>','final'); text('later: the check failed','final')
        else:
            for chunk in ('<free','token-report>','done','</freetoken-','report>'): text(chunk)
        result = {'stopReason':'cancelled' if mode == 'failed' else 'end_turn'}
    if 'id' in request: emit({'jsonrpc':'2.0','id':request['id'],'result':result})
''')
    fake.chmod(0o755)

    def cli(*args, expected=0):
        result = subprocess.run([sys.executable, "-B", str(RUNNER), *map(str, args)],
                                capture_output=True, text=True, timeout=15)
        assert result.returncode == expected, (args, result.stdout, result.stderr)
        return result.stdout

    for mode, status in (("valid", "framed"), ("interleaved", "framed"), ("missing", "unstructured"),
                         ("multiple", "invalid"), ("oversized", "framed"), ("split-id", "invalid"),
                         ("late-message", "invalid"), ("late-same", "invalid"), ("incomplete", "framed"), ("failed", "missing")):
        task = root / mode
        prompt.write_text(mode + "\n")
        stdout = cli("start", "--task-dir", task, "--cwd", work, "--backend", "dsh", "--model", "fake",
                     "--executable", fake, "--prompt-file", prompt, "--budget", "5", expected=2 if mode == "failed" else 0)
        assert len(stdout.splitlines()) == 1 and "private progress" not in stdout and "large private" not in stdout
        result = json.loads(stdout)
        assert result["report_status"] == status
        assert result["independent_verification"] is None
        attempt = task / "attempts/0001"
        assert "private progress" in (attempt / "raw/assistant-stream.txt").read_text()
        chunks = [json.loads(line) for line in (attempt / "raw/assistant-chunks.jsonl").read_text().splitlines()]
        assert chunks[0]["msgId"] == "progress"
        if mode == "split-id":
            assert [chunk["msgId"] for chunk in chunks[1:]] == ["one", "two"]
        assert len((attempt / "events.jsonl").read_text().splitlines()) >= 100
        if status == "framed":
            expected_report = ("HEAD-" + "中" * 1500 + "\nDECISION_REQUIRED: choose A\n" +
                               "中" * 1500 + "-TAIL") if mode == "oversized" else "done"
            if mode == "incomplete":
                expected_report = ("status: complete\nUNRUN_CHECKS: required recovery test\n"
                                   "DECISION_REQUIRED: none\nPENDING_WORK: required proof\n"
                                   "CLARIFICATION_REQUIRED: no")
                assert result["report_warnings"] == ["completion_claim_with_declared_gaps"]
                assert result["status"] == "awaiting_review"
            assert (attempt / "report.md").read_text() == expected_report
            assert (attempt / "attempt-delta.json").is_file()
            assert result["report_bytes"] == len(expected_report.encode("utf-8"))
            assert result["report_text"] == expected_report
            assert result["report_requires_full_read"] is False
            if mode == "oversized":
                assert "choose A" in result["report_text"]
                assert result["report_signals"]["decision_required"] == "present"
                assert result["status"] == "awaiting_review"
        else:
            assert not (attempt / "report.md").exists() and result["report"] is None
            assert result["report_bytes"] is None
            assert result["report_text"] is None and result["report_requires_full_read"] is True
        compact = cli("status", "--task-dir", task, "--summary")
        assert len(compact.splitlines()) == 1 and json.loads(compact)["report_status"] == status
        assert json.loads(compact)["report_text"] is None
        assert json.loads(compact)["report_requires_full_read"] is True
        if mode == "incomplete":
            assert json.loads(compact)["report_warnings"] == ["completion_claim_with_declared_gaps"]
            assert json.loads(compact)["status"] == "awaiting_review"
        if mode == "oversized":
            assert len(compact.encode("utf-8")) < 5000
            assert json.loads(compact)["report_signals"]["decision_required"] == "present"
    # The shared alignment gate also preserves the dsh ACP session and framing.
    aligned = root / "aligned-dsh"
    prompt.write_text("oversized\n")
    planned = json.loads(cli("start", "--task-dir", aligned, "--cwd", work, "--backend", "dsh",
                             "--model", "fake", "--executable", fake, "--prompt-file", prompt,
                             "--budget", "5", "--align"))
    assert planned["status"] == "blocked" and planned["alignment_ready"]
    assert planned["report_status"] == "framed"
    assert len(planned["report_text"].encode("utf-8")) > 6000 and "choose A" in planned["report_text"]
    cli("resume", "--task-dir", aligned, expected=2)
    implemented = json.loads(cli("resume", "--task-dir", aligned, "--prompt-file", prompt))
    assert implemented["session_id"] == planned["session_id"] == "offline"
    assert implemented["status"] == "awaiting_review" and not implemented["alignment_pending"]
    assert implemented["report_text"] == planned["report_text"]

    task = root / "valid"
    prompt.write_text("valid\n")
    stdout = cli("resume", "--task-dir", task, "--prompt-file", prompt, "--output", "events")
    assert len(stdout.splitlines()) >= 100 and 'tool_call_update' in stdout
    evidence = root / "review.md"
    evidence.write_text("Independent fake check, request correction within unchanged scope.")
    stdout = cli("revise", "--task-dir", task, "--evidence-file", evidence)
    assert len(stdout.splitlines()) == 1 and json.loads(stdout)["attempt"] == 3
    assert json.loads(stdout)["report_text"] == "done"

    # Verify is read-only and mechanical: passing checks must not accept a failed worker.
    task = root / "evidence"
    attempt = task / "attempts/0001"
    attempt.mkdir(parents=True)
    preexisting = work / "user.txt"
    preexisting.write_text("existing dirty user content")
    before = snapshot(work)
    target = work / "allowed.txt"
    target.write_text("worker change")
    after = snapshot(work)
    state = {"status": "failed", "cwd": str(work), "attempt_dir": str(attempt),
             "allow": ["allowed.txt"], "changes": ["allowed.txt"], "out_of_scope": []}
    state_path = task / "state.json"

    def write_evidence():
        state_path.write_text(json.dumps(state))
        (attempt / "before.json").write_text(json.dumps(before))
        (attempt / "after.json").write_text(json.dumps(after))

    def verify(expected=0):
        return json.loads(cli("status", "--task-dir", task, "--summary", "--verify", expected=expected))

    write_evidence()
    state_bytes = state_path.read_bytes()
    result = verify()
    assert all(result["evidence_checks"].values()) and result["status"] == "failed"
    assert result["independent_verification"] is None and state_path.read_bytes() == state_bytes
    assert preexisting.read_text() == "existing dirty user content"
    target.write_text("later edit")
    assert not verify(2)["evidence_checks"]["workspace_matches_after"]
    target.write_text("worker change")
    state["changes"] = []
    write_evidence()
    assert not verify(2)["evidence_checks"]["recorded_changes_match"]
    state["changes"] = ["allowed.txt"]
    state["allow"] = []
    write_evidence()
    assert not verify(2)["evidence_checks"]["within_scope"]
    state["allow"] = ["allowed.txt"]
    state["known_processes"] = [processes()[os.getpid()]]
    write_evidence()
    assert not verify(2)["evidence_checks"]["observed_processes_stopped"]
    state["known_processes"] = []
    before["head"] = "different-head"
    write_evidence()
    assert not verify(2)["evidence_checks"]["head_unchanged"]
    before["head"] = after["head"]
    state["status"] = "running"
    write_evidence()
    assert "terminal" in verify(2)["error"]
    state["status"] = "failed"
    write_evidence()
    # One bounded response covers approved commands, including failures and effects.
    spec_path = root / "acceptance-spec.json"
    spec = {"goal": "verify", "scope": {"write": ["allowed.txt"]},
            "acceptance": {"commands": [[sys.executable, "-B", "-c", "print('private check output'); raise SystemExit(5)"]]},
            "limits": {"check_seconds": 2}}

    def freeze_spec():
        spec_path.write_text(json.dumps(spec))
        state.update(spec_path=str(spec_path), spec_sha256=load_spec(spec_path)[1])
        write_evidence()

    freeze_spec()
    result = verify(2)
    assert all(result["evidence_checks"].values()) and result["verification_status"] == "failed"
    assert result["acceptance_checks"]["failed_sample"] == [{"index": 0, "exit_code": 5, "timed_out": False}]
    assert "private check output" not in json.dumps(result)
    spec["acceptance"]["commands"] = [[sys.executable, "-B", "-c", "pass"]]
    freeze_spec()
    result = verify()
    assert result["acceptance_checks"] == {"count": 1, "failed_count": 0, "failed_sample": []}
    assert result["status"] == "failed" and result["independent_verification"] is None
    spec["acceptance"]["commands"] = [[sys.executable, "-B", "-c", "from pathlib import Path; Path('allowed.txt').write_text('check changed file')"]]
    spec_path.write_text(json.dumps(spec))
    assert "TaskSpec changed" in verify(2)["error"]
    assert target.read_text() == "worker change"  # Modified spec was not executed.
    freeze_spec()
    assert not verify(2)["evidence_checks"]["workspace_matches_after"]
    target.write_text("worker change")
    (attempt / "after.json").unlink()
    assert "error" in verify(2)

print("PASS: compact status, complete handbacks, framing, lifecycle and mechanical evidence checks")

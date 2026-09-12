"""Offline bounded output and dsh report-framing integration checks."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile

from freetoken import final_report, summary


OPEN, CLOSE = "<freetoken-report>", "</freetoken-report>"
assert final_report(["progress", OPEN + "done" + CLOSE]) == ("framed", "done")
assert final_report([OPEN + "a", "b" + CLOSE]) == ("invalid", None)
assert final_report([OPEN + "complete" + CLOSE, "later: the check failed"]) == ("invalid", None)
assert final_report([OPEN + "complete" + CLOSE + "later: the check failed"]) == ("invalid", None)
for text in (OPEN + CLOSE, OPEN + "a" + CLOSE + OPEN + "b" + CLOSE,
             OPEN + "x" * 6001 + CLOSE, OPEN + " " * 6000 + "a" + CLOSE,
             CLOSE + "bad" + OPEN, OPEN + "中" * 2001 + CLOSE):
    assert final_report([text]) == ("invalid", None)
assert final_report(["no explicit final report"]) == ("unstructured", None)
state = {"changes": ["x" * 2000] * 10000, "out_of_scope": ["y" * 2000] * 10000,
         "error": "e" * 100000, "model": "m" * 100000, "session_id": "s" * 100000}
compact = summary(state, "/task")
assert len(json.dumps(compact)) < 5000
assert compact["changes_count"] == 10000 and len(compact["changes_sample"]) == 5
assert compact["independent_verification"] is None

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
        result = {'sessionId':'offline','configOptions':[{'id':'model','currentValue':'fake'}]}
    elif method == 'session/prompt':
        prompt = request['params']['prompt'][0]['text']
        assert '<freetoken-report>' in prompt and '6000' in prompt
        mode = prompt.splitlines()[0]
        text('private progress, not the final delivery\\n', 'progress')
        for i in range(100):
            emit({'jsonrpc':'2.0','method':'session/update','params':{'sessionId':'offline','update':{
                'sessionUpdate':'tool_call_update','toolCallId':str(i),'title':'large private tool title','status':'completed'}}})
        if mode == 'missing': text('ordinary unframed text')
        elif mode == 'multiple': text('<freetoken-report>a</freetoken-report><freetoken-report>b</freetoken-report>')
        elif mode == 'oversized': text('<freetoken-report>' + 'x'*6001 + '</freetoken-report>')
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
                         ("multiple", "invalid"), ("oversized", "invalid"), ("split-id", "invalid"),
                         ("late-message", "invalid"), ("late-same", "invalid"), ("failed", "missing")):
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
            assert (attempt / "report.md").read_text() == "done"
        else:
            assert not (attempt / "report.md").exists() and result["report"] is None
        compact = cli("status", "--task-dir", task, "--summary")
        assert len(compact.splitlines()) == 1 and json.loads(compact)["report_status"] == status
    task = root / "valid"
    prompt.write_text("valid\n")
    stdout = cli("resume", "--task-dir", task, "--prompt-file", prompt, "--output", "events")
    assert len(stdout.splitlines()) >= 100 and 'tool_call_update' in stdout
    evidence = root / "review.md"
    evidence.write_text("Independent fake check, request correction within unchanged scope.")
    stdout = cli("revise", "--task-dir", task, "--evidence-file", evidence)
    assert len(stdout.splitlines()) == 1 and json.loads(stdout)["attempt"] == 3

print("PASS: bounded summaries, event opt-in, dsh framing and legacy lifecycle integration")

"""Offline accounting and fake-process checks; never calls a model."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from codex_meter import collect


def lines(*events):
    return [json.dumps(event) for event in events]


thread = {"type": "thread.started", "thread_id": "fake-thread"}
start = {"type": "turn.started"}
end = {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 20,
       "output_tokens": 10, "reasoning_output_tokens": 5}}
valid = lines(thread, start, end)
assert collect(valid, 0)["input_plus_output"] == 110
assert collect(lines(thread, start, end, start, end), 0)["input_plus_output"] == 220
assert collect(valid)["input_plus_output"] is None
assert collect(valid, 1)["totals"]["input_tokens"] is None
for events in (lines(thread, end), lines(thread, start), lines(thread, start, end, end),
               lines(start, end, thread), lines({"type": "thread.started", "thread_id": ""}, start, end),
               lines({"type": "thread.started", "thread_id": "  "}, start, end),
               lines(thread, start, start, end), lines(thread, start, end, thread),
               valid + ["truncated{"], lines(thread, start, {"type": "turn.failed"}),
               lines(thread, start, end, {"type": "usage_update", "used": 100}),
               valid + lines({"method": "thread/tokenUsage/updated", "params": {"tokenUsage": {}}}),
               valid + lines({"type": "model.changed", "model": "other"}),
               valid + lines({"type": "item.started", "item": {}}),
               lines(thread, start, {"type": "turn.completed", "usage": {"input_tokens": True}})):
    assert not collect(events, 0)["measurement_complete"], events
for value in (-1, True, 2.5, "100", None):
    event = {"type": "turn.completed", "usage": {"input_tokens": value, "output_tokens": 1}}
    assert collect(lines(thread, start, event), 0)["input_plus_output"] is None
minimal = {"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": 2}}
assert collect(lines(thread, start, minimal), 0)["totals"]["cached_input_tokens"] is None
assert collect(lines(thread, start, minimal), 0)["measurement_complete"]
bad_sub = {"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 2, "output_tokens": 0}}
assert not collect(lines(thread, start, bad_sub), 0)["measurement_complete"]

script = Path(__file__).with_name("codex_meter.py")
with tempfile.TemporaryDirectory(prefix="caller-meter-") as directory:
    root = Path(directory)
    work = root / "work"
    work.mkdir()
    prompt = root / "prompt.md"
    prompt.write_text("Entire task including caller review and repair.")
    for command in (["git", "init"], ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                    "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "fixture"]):
        subprocess.run(command, cwd=work, check=True, capture_output=True)
    fake = root / "fake-codex"
    fake.write_text("#!/usr/bin/env python3\n" + '''
import json, os, sys, time
from pathlib import Path
if '--version' in sys.argv:
    print('fake-codex offline')
    sys.exit(0)
assert '-a' in sys.argv and sys.argv[sys.argv.index('-a')+1] == 'never'
assert '--ignore-user-config' in sys.argv and '--ephemeral' in sys.argv
assert sys.stdin.read().startswith('Entire task')
Path('called').write_text('fake only')
print(json.dumps({'type':'thread.started','thread_id':'fake'}), flush=True)
print(json.dumps({'type':'turn.started'}), flush=True)
if os.environ.get('METER_FAKE_HOLD'):
    time.sleep(30)
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':7,'output_tokens':3}}), flush=True)
''')
    fake.chmod(0o755)
    manifest = root / "manifest.json"
    spec = {"case_id": "fake", "arm": "A", "workspace": str(work), "prompt_file": str(prompt),
            "model": "offline-fake", "reasoning_effort": "high", "sandbox": "read-only", "timeout_s": 3,
            "executable": str(fake), "pinned_files": [str(prompt), str(fake)]}
    manifest.write_text(json.dumps(spec))

    def run(out, *extra, expected=0, env=None):
        result = subprocess.run([sys.executable, "-B", str(script), "run", "--manifest", str(manifest),
                                 "--out", str(out), *extra], capture_output=True, text=True, timeout=10, env=env)
        assert result.returncode == expected, (result.stdout, result.stderr)
        return json.loads(result.stdout)

    out = root / "result"
    assert run(out)["model_called"] is False
    assert not out.exists() and not (work / "called").exists()
    assert run(out, "--execute")["measurement_complete"]
    receipt = json.loads((out / "receipt.json").read_text())
    ledger = json.loads((out / "caller-usage.json").read_text())
    assert ledger["input_plus_output"] == 10 and ledger["model_confirmed"] is None
    assert not ledger["end_to_end_coverage_verified"] and ledger["independent_acceptance"] is None
    assert receipt["observed_processes_stopped"] and receipt["workspace_after"] != receipt["workspace_before"]
    run(out, "--execute", expected=2)
    run(work / "forbidden", expected=2)
    nested = work / "nested"
    nested.mkdir()
    spec["workspace"] = str(nested)
    manifest.write_text(json.dumps(spec))
    run(root / "nested-result", expected=2)
    spec["workspace"] = str(work)
    held = root / "held"
    spec["timeout_s"] = .4
    manifest.write_text(json.dumps(spec))
    assert not run(held, "--execute", expected=2, env={**os.environ, "METER_FAKE_HOLD": "1"})["measurement_complete"]
    receipt = json.loads((held / "receipt.json").read_text())
    assert receipt["interrupted"] and receipt["observed_processes_stopped"]
    for value in (-1, 0, True, "1", float("nan")):
        spec["timeout_s"] = value
        manifest.write_text(json.dumps(spec))
        run(root / "invalid", expected=2)

print("PASS: offline Codex caller meter, boundaries, preflight, fake execution and timeout")

"""Run: python3 scripts/test_acp_stdio.py (no provider or model calls)."""

import subprocess
import sys
import tempfile
from pathlib import Path

from acp_stdio import ACP


FAKE = '''
import json, sys
def emit(message):
    print(json.dumps(message), flush=True)
for line in sys.stdin:
    request = json.loads(line)
    if request.get("method") == "session/prompt":
        emit({"jsonrpc":"2.0", "method":"session/update", "params":{"sessionId":"s", "update":{"sessionUpdate":"agent_message_chunk"}}})
        emit({"jsonrpc":"2.0", "id":99, "method":"session/request_permission", "params":{"options":[{"kind":"reject_once", "optionId":"deny"}]}})
        reply = json.loads(next(sys.stdin))
        assert reply["result"]["outcome"]["optionId"] == "deny"
        emit({"jsonrpc":"2.0", "id":request["id"], "result":{"stopReason":"end_turn"}})
    elif request.get("method") == "never":
        pending = request["id"]
    elif request.get("method") == "session/cancel":
        emit({"jsonrpc":"2.0", "id":pending, "result":{"stopReason":"cancelled"}})
    elif "id" in request:
        emit({"jsonrpc":"2.0", "id":request["id"], "result":{"protocolVersion":1}})
'''


with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "fake.py"
    path.write_text(FAKE)
    events = []
    client = ACP([sys.executable, "-u", str(path)], directory, subprocess.DEVNULL,
                 on_update=events.append)
    try:
        assert client.initialize()["protocolVersion"] == 1
        assert client.call("session/prompt", {})["stopReason"] == "end_turn"
        assert len(events) == 1
        request_id = client.begin("never", {})
        try:
            client.wait(request_id, timeout=0.05)
        except TimeoutError:
            pass
        else:
            raise AssertionError("Expected an observation timeout")
        assert client.process.poll() is None
        client.notify("session/cancel", {})
        assert client.wait(request_id)["stopReason"] == "cancelled"
    finally:
        assert client.shutdown() == 0
print("ACP transport checks passed")

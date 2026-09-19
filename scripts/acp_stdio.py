"""Small stdlib ACP transport. Policy and task decisions belong to the caller."""

import json
import os
import selectors
import signal
import subprocess
import time


class ACP:
    def __init__(self, argv, cwd, stderr, on_update=None, on_permission=None):
        worker_env = os.environ.copy()
        worker_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
        self.process = subprocess.Popen(
            argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=stderr, start_new_session=True, env=worker_env,
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.buffer = b""
        self.responses = {}
        self.next_id = 0
        self.on_update = on_update or (lambda params: None)
        self.on_permission = on_permission or (lambda params: False)

    def send(self, message):
        self.process.stdin.write((json.dumps(message) + "\n").encode())
        self.process.stdin.flush()

    def notify(self, method, params):
        self.send({"jsonrpc": "2.0", "method": method, "params": params})

    def begin(self, method, params):
        self.next_id += 1
        self.send({"jsonrpc": "2.0", "id": self.next_id,
                   "method": method, "params": params})
        return self.next_id

    def poll(self, timeout=0.2):
        if not self.selector.select(timeout):
            return
        data = os.read(self.process.stdout.fileno(), 65536)
        if not data:
            raise EOFError("ACP stdout closed")
        self.buffer += data
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            message = json.loads(line)
            if not isinstance(message, dict):
                raise ValueError("ACP frame must be an object")
            method = message.get("method")
            if method == "session/update":
                self.on_update(message["params"])
            elif method == "session/request_permission":
                params = message["params"]
                kind = "allow_once" if self.on_permission(params) else "reject_once"
                option = next((x for x in params["options"] if x["kind"] == kind), None)
                outcome = ({"outcome": "selected", "optionId": option["optionId"]}
                           if option else {"outcome": "cancelled"})
                self.send({"jsonrpc": "2.0", "id": message["id"],
                           "result": {"outcome": outcome}})
            elif method and "id" in message:
                self.send({"jsonrpc": "2.0", "id": message["id"],
                           "error": {"code": -32601, "message": "Unsupported client method"}})
            elif not method and "id" in message:
                self.responses[message["id"]] = message

    def wait(self, request_id, timeout=30, tick=None):
        deadline = time.monotonic() + timeout
        while request_id not in self.responses:
            if tick:
                tick()
            if time.monotonic() >= deadline:
                # An observation timeout does not cancel or retry a submitted request.
                raise TimeoutError(f"ACP request {request_id} still unconfirmed")
            self.poll(min(0.2, max(0, deadline - time.monotonic())))
        response = self.responses.pop(request_id)
        if "error" in response:
            raise RuntimeError(f"ACP error: {response['error']}")
        return response["result"]

    def call(self, method, params, timeout=30, tick=None):
        return self.wait(self.begin(method, params), timeout, tick)

    def initialize(self, tick=None):
        return self.call("initialize", {
            "protocolVersion": 1, "clientCapabilities": {},
            "clientInfo": {"name": "freetoken", "version": "0.1"},
        }, tick=tick)

    def shutdown(self, grace=10):
        """EOF first; only terminate this transport's process group if needed."""
        try:
            self.process.stdin.close()
            self.process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGTERM)
            try:
                self.process.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait()
        finally:
            self.process.stdout.close()
            self.selector.close()
        return self.process.returncode

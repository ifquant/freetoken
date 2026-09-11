"""Controlled cancellation probe; only writes markers in its working directory."""

import json
import os
from pathlib import Path
import sys
import tempfile
import time


def finish(folder):
    if not (folder / "started").is_file():
        raise RuntimeError("No checkpoint; refusing to finish")
    try:
        with (folder / "finished").open("x") as stream:
            stream.write("completed\n")
    except FileExistsError:
        print("Already finished", flush=True)
    else:
        print("Finished once", flush=True)


def start(folder, delay=45):
    with (folder / "started").open("x") as stream:
        json.dump({"pid": os.getpid(), "pgid": os.getpgrp(),
                   "started_at": time.time(), "delay_seconds": delay}, stream)
    print("Checkpoint saved; waiting", flush=True)
    time.sleep(delay)
    finish(folder)


def self_check():
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        try:
            finish(folder)
        except RuntimeError:
            pass
        else:
            raise AssertionError("finish must require a checkpoint")
        start(folder, delay=0)
        before = (folder / "finished").stat().st_mtime_ns
        finish(folder)
        assert (folder / "finished").stat().st_mtime_ns == before
        assert (folder / "finished").read_text() == "completed\n"
        try:
            start(folder, delay=0)
        except FileExistsError:
            pass
        else:
            raise AssertionError("start must reject a duplicate checkpoint")
    print("Self-check passed")


if __name__ == "__main__":
    if sys.argv[1:] == ["start"]:
        start(Path.cwd())
    elif sys.argv[1:] == ["finish"]:
        finish(Path.cwd())
    elif sys.argv[1:] == ["--self-check"]:
        self_check()
    else:
        raise SystemExit("Usage: slow_operation.py start|finish|--self-check")

"""Independent mechanical verification receipt; semantic acceptance stays external."""
import os, signal, subprocess, time

def check(argv, cwd, timeout):
    started = time.time()
    process = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        exit_code = process.wait(timeout=timeout)
        return {"argv": list(argv), "cwd": str(cwd), "exit_code": exit_code,
                "timed_out": False, "elapsed_s": round(time.time()-started, 3)}
    except subprocess.TimeoutExpired:
        try: os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError: pass
        time.sleep(.2)
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        except PermissionError:
            if process.poll() is None: raise
        try: process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        return {"argv": list(argv), "cwd": str(cwd), "exit_code": None,
                "timed_out": True, "elapsed_s": round(time.time()-started, 3)}

def receipt(task_id, attempt_id, before, after, checks, scope_ok, risks=None):
    return {"schema_version": 1, "task_id": task_id, "attempt_id": attempt_id,
            "baseline": before, "after": after, "checks": checks,
            "scope_ok": bool(scope_ok), "verification_status":
            "awaiting_review" if scope_ok and all(x["exit_code"] == 0 and not x["timed_out"] for x in checks) else "failed",
            "remaining_risks": risks or ["semantic acceptance remains caller-owned"]}

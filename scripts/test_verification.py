from pathlib import Path
import sys, tempfile, time
from verification import check, receipt

def main():
    with tempfile.TemporaryDirectory() as d:
        ok = check([sys.executable, "-c", "pass"], d, 2)
        bad = check([sys.executable, "-c", "raise SystemExit(2)"], d, 2)
        assert receipt("t", "a", {"files":{}}, {"files":{}}, [ok], True)["verification_status"] == "awaiting_review"
        assert receipt("t", "a", {"files":{}}, {"files":{}}, [bad], True)["verification_status"] == "failed"
        marker = Path(d) / "descendant-survived"
        child = f"import time; from pathlib import Path; time.sleep(.6); Path({str(marker)!r}).write_text('alive')"
        timed = check([sys.executable, "-c",
                       f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(30)"], d, .1)
        time.sleep(.8)
        assert timed["timed_out"] and not marker.exists()
    print("Verification checks passed")

if __name__ == "__main__": main()

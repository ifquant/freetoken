import json, tempfile
from pathlib import Path
from task_spec import load

def rejected(path, value):
    path.write_text(json.dumps(value))
    try: load(path)
    except ValueError: return
    raise AssertionError(f"invalid spec accepted: {value!r}")

def main():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "spec.json"
        p.write_text(json.dumps({"goal":"x","scope":{"write":["a.py"]},"acceptance":{"commands":[["python3","-B","check.py"]]},"limits":{"wall_seconds":30}}))
        spec, digest = load(p)
        assert spec["schema_version"] == 1 and len(digest) == 64
        base = {"goal":"x","scope":{"write":["a.py"]},"acceptance":{"commands":[["true"]]},"limits":{}}
        for value in ("", 3): rejected(p, {**base, "goal": value})
        rejected(p, {**base, "scope": {}})
        rejected(p, {**base, "scope": {"write": "a.py"}})
        rejected(p, {**base, "scope": {"write": ["../x"]}})
        for key in ("workspace", "baseline_ref"):
            for value in ("", 3): rejected(p, {**base, key: value})
        for key in ("wall_seconds", "check_seconds"):
            for value in (True, 0, 86400, float("nan"), float("inf")):
                rejected(p, {**base, "limits": {key: value}})
    print("TaskSpec checks passed")

if __name__ == "__main__":
    import subprocess, sys
    probe = subprocess.run([sys.executable, "scripts/freetoken.py", "start", "--task-dir", "/tmp/freetoken-probe", "--cwd", "/tmp", "--backend", "codebuddy", "--spec", "/tmp/missing-spec.json"], text=True, capture_output=True)
    assert "the following arguments are required: --prompt-file" not in probe.stderr
    main()

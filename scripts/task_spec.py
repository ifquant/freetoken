"""Small, deterministic task contract and verification receipt helpers."""
import hashlib, json, math
from pathlib import Path

SCHEMA_VERSION = 1

def _seconds(limits, name):
    if name not in limits:
        return
    value = limits[name]
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not 0 < value < 86400):
        raise ValueError(f"limits.{name} must be finite, positive and less than one day")

def normalize(value):
    if not isinstance(value, dict): raise ValueError("TaskSpec must be an object")
    required = ("goal", "scope", "acceptance", "limits")
    if any(k not in value for k in required): raise ValueError("TaskSpec requires goal, scope, acceptance and limits")
    goal = value["goal"]
    if not isinstance(goal, str) or not goal.strip(): raise ValueError("goal must be a non-empty string")
    scope = value["scope"]
    if not isinstance(scope, dict) or "write" not in scope or not isinstance(scope["write"], list): raise ValueError("scope.write must be a list")
    for path in scope["write"]:
        if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError("scope.write must contain safe relative paths")
    acceptance = value["acceptance"]
    if not isinstance(acceptance, dict) or not isinstance(acceptance.get("commands"), list): raise ValueError("acceptance.commands must be explicit")
    if any(not isinstance(c, list) or not c or any(not isinstance(x, str) for x in c) for c in acceptance["commands"]):
        raise ValueError("acceptance.commands must contain argv lists")
    limits = value["limits"]
    if not isinstance(limits, dict): raise ValueError("limits must be an object")
    _seconds(limits, "wall_seconds")
    _seconds(limits, "check_seconds")
    result = {"schema_version": SCHEMA_VERSION, "goal": goal, "scope": scope,
              "acceptance": acceptance, "limits": value["limits"]}
    context = value.get("context_files", [])
    if not isinstance(context, list) or any(not isinstance(p, str) or not p or Path(p).is_absolute() or ".." in Path(p).parts for p in context):
        raise ValueError("context_files must contain safe relative paths")
    if context: result["context_files"] = context
    if "workspace" in value:
        if not isinstance(value["workspace"], str) or not value["workspace"].strip(): raise ValueError("workspace must be a non-empty path string")
        result["workspace"] = value["workspace"]
    if "baseline_ref" in value:
        if not isinstance(value["baseline_ref"], str) or not value["baseline_ref"].strip(): raise ValueError("baseline_ref must be a non-empty string")
        result["baseline_ref"] = value["baseline_ref"]
    return result

def load(path):
    raw = json.loads(Path(path).read_text())
    spec = normalize(raw)
    encoded = json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return spec, hashlib.sha256(encoded).hexdigest()

def receipt(spec, task_id, attempt_id, before, after, checks, status="awaiting_review", risks=None, spec_sha256=None):
    changed = sorted(k for k in before["files"].keys() | after["files"].keys() if before["files"].get(k) != after["files"].get(k))
    allowed = spec["scope"].get("write", [])
    outside = [p for p in changed if not any(x == "." or p == x or x.endswith("/") and p.startswith(x) for x in allowed)]
    return {"schema_version": 1, "task_id": task_id, "attempt_id": attempt_id,
            "spec_sha256": spec_sha256,
            "baseline": before, "after": after, "changed_files": changed,
            "scope_ok": not outside, "out_of_scope": outside, "checks": checks,
            "verification_status": status if not outside else "failed",
            "remaining_risks": risks or ["semantic acceptance remains caller-owned"]}

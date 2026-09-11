import json


def summarize(lines):
    rows = [json.loads(line) for line in lines]
    return {"total": len(rows), "invalid": 0, "levels": {}}

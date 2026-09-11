from rollup import summarize
rows = ['{"level":"debug"}', '{}', '{"level":"warning"}', '{"level":"error"}', 'bad']
assert summarize(rows, min_level=" WARNING ") == {"total": 2, "invalid": 1, "levels": {"warning": 1, "error": 1}}
assert summarize(rows, min_level="error") == {"total": 1, "invalid": 1, "levels": {"error": 1}}
assert summarize(rows)["total"] == 4
try:
    summarize([], min_level="unknown")
except ValueError:
    pass
else:
    raise AssertionError("Invalid threshold must fail")
print("Log threshold incremental checks passed")

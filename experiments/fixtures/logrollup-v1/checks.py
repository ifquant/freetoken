import json
import subprocess
import sys

from rollup import summarize


if __name__ == "__main__":
    assert summarize(iter([])) == {"total": 0, "invalid": 0, "levels": {}}
    lines = ['{"level":" ERROR "}\n', '{"level":"info"}', '{}', '', '  ',
             'broken', 'null', '[]', '{"level":12}', '{"level":""}',
             '{"level":"verbose"}', '{"level":"warning"}']
    expected = {"total": 4, "invalid": 6, "levels": {"error": 1, "info": 2, "warning": 1}}
    assert summarize(iter(lines)) == expected
    assert summarize(['{"level":"debug"}', '{"level":"debug"}'])["levels"] == {"debug": 2}
    process = subprocess.run([sys.executable, '-B', 'cli.py'], input='\n'.join(lines),
                             capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout) == expected
    print("Log rollup function + CLI checks passed")

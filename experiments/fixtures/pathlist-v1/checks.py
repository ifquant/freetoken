import json
from pathlib import Path
import subprocess
import sys
import tempfile

from indexer import collect_paths


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        root = base / "input"
        (root / "sub").mkdir(parents=True)
        (root / ".hidden").mkdir()
        for name in ('z.py', 'a.txt', 'sub/b.py', 'sub/c.PY', '.hidden/h.py', 'sub/.secret.py'):
            (root / name).write_text('data')
        (base / 'outside.py').write_text('external')
        (root / 'linked.py').symlink_to(base / 'outside.py')
        (root / 'linked-dir').symlink_to(root / 'sub', target_is_directory=True)
        assert collect_paths(root, ['py', '.py']) == ['sub/b.py', 'z.py']
        assert collect_paths(root, []) == ['a.txt', 'sub/b.py', 'sub/c.PY', 'z.py']
        assert collect_paths(root, ['.PY']) == ['sub/c.PY']
        process = subprocess.run([sys.executable, '-B', 'cli.py', str(root), 'py'],
                                 capture_output=True, text=True)
        assert process.returncode == 0, process.stderr
        assert json.loads(process.stdout) == ['sub/b.py', 'z.py']
    print('Path index function + CLI checks passed')

from pathlib import Path
import tempfile
from indexer import collect_paths
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / '.hidden').mkdir()
    for name in ['a.py', '.top.py', '.hidden/b.py']:
        (root / name).write_text('x')
    (root / 'link.py').symlink_to(root / 'a.py')
    assert collect_paths(root, ['py']) == ['a.py']
    assert collect_paths(root, ['py'], include_hidden=True) == ['.hidden/b.py', '.top.py', 'a.py']
print("Hidden-file opt-in incremental checks passed")

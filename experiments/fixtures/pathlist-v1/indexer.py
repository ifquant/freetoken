from pathlib import Path


def collect_paths(root, suffixes):
    return [str(path) for path in Path(root).iterdir()]

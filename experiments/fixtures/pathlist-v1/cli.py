import json
import sys

from indexer import collect_paths


if __name__ == "__main__":
    print(json.dumps(collect_paths(sys.argv[1], sys.argv[2:])))

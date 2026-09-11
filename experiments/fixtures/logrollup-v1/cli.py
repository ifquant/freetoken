import json
import sys

from rollup import summarize


if __name__ == "__main__":
    print(json.dumps(summarize(sys.stdin), sort_keys=True))

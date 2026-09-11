"""Frozen round-one acceptance checks; workers must not edit this file."""

from tags import normalize_tags


CASES = [
    ("", []),
    (" a, b,a, ,c ", ["a", "b", "c"]),
    ("A,a,A", ["A", "a"]),
    (",,", []),
]


if __name__ == "__main__":
    failures = 0
    for text, expected in CASES:
        actual = normalize_tags(text)
        if actual != expected:
            failures += 1
            print(f"FAIL {text!r}: expected {expected!r}, got {actual!r}")
        else:
            print(f"PASS {text!r}")
    print(f"{len(CASES) - failures}/{len(CASES)} passed")
    raise SystemExit(1 if failures else 0)

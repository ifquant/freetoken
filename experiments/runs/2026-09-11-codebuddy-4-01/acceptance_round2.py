from tags import normalize_tags

if __name__ == "__main__":
    actual = normalize_tags(" a，b,a ")
    expected = ["a", "b"]
    if actual != expected:
        print(f"FAIL Chinese comma: expected {expected!r}, got {actual!r}")
        raise SystemExit(1)
    print("PASS Chinese comma: 1/1 passed")

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "fixtures" / "time-compression-cases.json"


def main():
    payload = json.loads(CASES.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if len(cases) < 5:
        raise AssertionError("expected at least 5 benchmark cases")
    required = {"id", "fixture", "mode", "expected_path_decision", "time_compression_claim"}
    for case in cases:
        missing = sorted(required - set(case))
        if missing:
            raise AssertionError("benchmark case missing fields: {} {}".format(case.get("id"), missing))
        fixture = ROOT / case["fixture"]
        if not fixture.exists():
            raise AssertionError("benchmark fixture missing: " + str(fixture))
    print(json.dumps({"status": "ok", "benchmark_cases": len(cases)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "microcosm.py"
FIXTURES = ROOT / "tests" / "fixtures"

CASES = [
    ("forbidden-edge", "authority-violation", "critical"),
    ("multiple-writers", "multiple-writers", "high"),
    ("cyclic-dependency", "cyclic-dependency", "high"),
]


def run_case(name, category, severity):
    project = FIXTURES / name
    out_dir = project / ".microcosm" / "reports"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "inspect", "--project", str(project)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "scripts"), "PYTHONHASHSEED": "random", "PYTHONIOENCODING": "utf-8"},
    )
    if proc.returncode != 0:
        raise AssertionError(f"{name} failed: {proc.stderr}")
    payload = json.loads(proc.stdout)
    findings_path = Path(payload["report_dir"]) / "findings.json"
    findings = json.loads(findings_path.read_text(encoding="utf-8"))["findings"]
    matches = [f for f in findings if f["category"] == category]
    if not matches:
        raise AssertionError(f"{name}: missing category {category}; got {findings}")
    hit = matches[0]
    if hit["severity"] != severity:
        raise AssertionError(f"{name}: expected severity {severity}, got {hit['severity']}")
    if not hit["evidence_refs"]:
        raise AssertionError(f"{name}: finding has no evidence_refs")
    if hit["confidence"] < 0.85:
        raise AssertionError(f"{name}: confidence too low: {hit['confidence']}")
    return {"case": name, "finding": hit["id"], "category": hit["category"], "severity": hit["severity"]}


def main():
    results = [run_case(*case) for case in CASES]
    print(json.dumps({"status": "ok", "cases": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "microcosm.py"
FIXTURES = ROOT / "tests" / "fixtures"
ENV = {"PYTHONPATH": str(ROOT / "scripts")}


def run(args, cwd=None):
    proc = subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=cwd or str(ROOT), text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env={**ENV, **dict(__import__("os").environ)})
    return proc


def clean_reports(name):
    shutil.rmtree(FIXTURES / name / ".microcosm" / "reports", ignore_errors=True)


def case_recovery():
    name = "plan-recovery"
    clean_reports(name)
    proc = run(["plan-change", "--project", str(FIXTURES / name), "--plan", str(FIXTURES / name / "change-plan.yaml")])
    if proc.returncode != 0:
        raise AssertionError("plan-recovery failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if not any(fid.startswith("finding.authority-violation.") for fid in payload["resolved_preview"]):
        raise AssertionError("plan-recovery expected authority-violation resolved, got: " + json.dumps(payload))
    if payload["new_preview"]:
        raise AssertionError("plan-recovery should not introduce new findings, got: " + json.dumps(payload))
    summary = json.loads((Path(payload["report_dir"]) / "plan-change.json").read_text(encoding="utf-8"))
    if summary["actions_planned"] != 1:
        raise AssertionError("plan-recovery expected 1 action, got: " + str(summary["actions_planned"]))
    return {"case": name, "resolved": payload["resolved_preview"], "new": payload["new_preview"]}


def case_introduce_violation():
    name = "plan-introduce-violation"
    clean_reports(name)
    proc = run(["plan-change", "--project", str(FIXTURES / name), "--plan", str(FIXTURES / name / "change-plan.yaml")])
    if proc.returncode != 0:
        raise AssertionError("plan-introduce-violation failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if not any(fid.startswith("finding.authority-violation.") for fid in payload["new_preview"]):
        raise AssertionError("plan-introduce-violation expected authority-violation new, got: " + json.dumps(payload))
    return {"case": name, "new": payload["new_preview"]}


def case_add_writer():
    name = "plan-add-writer"
    clean_reports(name)
    proc = run(["plan-change", "--project", str(FIXTURES / name), "--plan", str(FIXTURES / name / "change-plan.yaml")])
    if proc.returncode != 0:
        raise AssertionError("plan-add-writer failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if not any(fid.startswith("finding.multiple-writers.") for fid in payload["new_preview"]):
        raise AssertionError("plan-add-writer expected multiple-writers new, got: " + json.dumps(payload))
    return {"case": name, "new": payload["new_preview"]}


def case_neutral():
    name = "plan-neutral"
    clean_reports(name)
    proc = run(["plan-change", "--project", str(FIXTURES / name), "--plan", str(FIXTURES / name / "change-plan.yaml")])
    if proc.returncode != 0:
        raise AssertionError("plan-neutral failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if payload["new_preview"] or payload["resolved_preview"]:
        raise AssertionError("plan-neutral should not change findings, got: " + json.dumps(payload))
    return {"case": name, "new": payload["new_preview"], "resolved": payload["resolved_preview"]}


def main():
    results = [case_recovery(), case_introduce_violation(), case_add_writer(), case_neutral()]
    print(json.dumps({"status": "ok", "plan_cases": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

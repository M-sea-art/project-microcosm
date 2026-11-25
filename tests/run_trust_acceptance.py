import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "microcosm.py"
FIXTURES = ROOT / "tests" / "fixtures"
UNIT_DIR = ROOT / "tests" / "unit"
ENV = {"PYTHONPATH": str(ROOT / "scripts")}


def run(args, cwd=None):
    proc = subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=cwd or str(ROOT), text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env={**ENV, **dict(__import__("os").environ)})
    return proc


def run_unit():
    proc = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests.unit.test_trust"],
                          cwd=str(ROOT), text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env={**ENV, **dict(__import__("os").environ)})
    if proc.returncode != 0:
        raise AssertionError("unit tests failed: " + proc.stderr + "\n" + proc.stdout)
    return proc.stdout


def case_decision_pass():
    fixture = FIXTURES / "trust-decision-pass"
    shutil.rmtree(fixture / ".microcosm" / "reports", ignore_errors=True)
    proc = run(["inspect", "--project", str(fixture)])
    if proc.returncode != 0:
        raise AssertionError("decision-pass failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if payload.get("findings", 0) != 0:
        raise AssertionError("decision-pass expected zero findings, got: " + json.dumps(payload))
    manifest = json.loads((Path(payload["report_dir"]) / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("decision") != "PASS":
        raise AssertionError("decision-pass expected decision=PASS, got: " + json.dumps(manifest))
    return {"case": "trust-decision-pass", "decision": manifest["decision"]}


def case_decision_fail():
    fixture = FIXTURES / "trust-decision-fail"
    shutil.rmtree(fixture / ".microcosm" / "reports", ignore_errors=True)
    proc = run(["inspect", "--project", str(fixture)])
    if proc.returncode != 0:
        raise AssertionError("decision-fail failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if payload["findings"] < 1:
        raise AssertionError("decision-fail expected at least 1 finding, got: " + json.dumps(payload))
    manifest = json.loads((Path(payload["report_dir"]) / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("decision") != "FAIL":
        raise AssertionError("decision-fail expected decision=FAIL, got: " + json.dumps(manifest))
    summary = (Path(payload["report_dir"]) / "summary.md").read_text(encoding="utf-8")
    if "## Decision" not in summary or "## Risk" not in summary:
        raise AssertionError("summary.md missing decision/risk sections")
    queue = json.loads((Path(payload["report_dir"]) / "queue-eligibility.json").read_text(encoding="utf-8"))
    if not queue["queue"]["confirmed_findings"]:
        raise AssertionError("queue-eligibility should mark confirmed finding, got: " + json.dumps(queue))
    next_actions = json.loads((Path(payload["report_dir"]) / "next-actions.json").read_text(encoding="utf-8"))
    if not next_actions["next_actions"] or next_actions["next_actions"][0]["owner_expert"] != "human-agent-decision-expert":
        raise AssertionError("next-actions should route authority violation to human-agent decision expert, got: " + json.dumps(next_actions))
    if "deferred_consequence" not in next_actions["next_actions"][0]:
        raise AssertionError("next-actions should explain deferred consequence, got: " + json.dumps(next_actions))
    return {"case": "trust-decision-fail", "decision": manifest["decision"], "findings": payload["findings"]}


def case_risk_critical():
    fixture = FIXTURES / "trust-risk-critical"
    shutil.rmtree(fixture / ".microcosm" / "reports", ignore_errors=True)
    proc = run(["inspect", "--project", str(fixture)])
    if proc.returncode != 0:
        raise AssertionError("risk-critical failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    summary = (Path(payload["report_dir"]) / "summary.md").read_text(encoding="utf-8")
    if "level: critical" not in summary and "level: high" not in summary:
        raise AssertionError("risk-critical expected high/critical level, summary head: " + summary[:800])
    return {"case": "trust-risk-critical", "summary_head": summary.split("## Risk", 1)[1][:200]}


def case_validation_report():
    fixture = FIXTURES / "trust-decision-fail"
    shutil.rmtree(fixture / ".microcosm" / "reports", ignore_errors=True)
    run(["inspect", "--project", str(fixture)])
    reports = list((fixture / ".microcosm" / "reports").glob("run-*"))
    if not reports:
        raise AssertionError("validation report missing")
    validation = json.loads((reports[0] / "validation.json").read_text(encoding="utf-8"))
    if "issues" not in validation:
        raise AssertionError("validation.json should have issues field, got: " + json.dumps(validation))
    return {"case": "trust-validation-report", "issue_count": validation.get("issue_count", -1)}


def main():
    unit_log = run_unit()
    cases = [case_decision_pass(), case_decision_fail(), case_risk_critical(), case_validation_report()]
    print(json.dumps({
        "status": "ok",
        "trust_cases": cases,
        "unit_tail": unit_log.strip().splitlines()[-1:],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

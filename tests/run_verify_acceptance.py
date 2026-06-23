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
                          env={**__import__("os").environ, **ENV, "PYTHONHASHSEED": "random", "PYTHONIOENCODING": "utf-8"})
    return proc


def case_recovery():
    name = "verify-recovery"
    fixture = FIXTURES / name
    # Baseline: forbidden edge present
    shutil.rmtree(fixture / ".microcosm" / "reports", ignore_errors=True)
    (fixture / "edges.microcosm.json").write_text(
        (FIXTURES / name / "edges.microcosm.json").read_text(encoding="utf-8")
        if (FIXTURES / name / "edges.microcosm.json").exists() else "[]",
        encoding="utf-8",
    )
    # restore broken state
    (fixture / "edges.microcosm.json").write_text(
        '[{"id":"edge.executor-memory","from":"agent.executor","to":"memory.long-term","relation":"writes","attributes":{},"evidence_refs":["evidence.fixture.executor-memory"]}]',
        encoding="utf-8",
    )
    # 1) First verify: against baseline with same finding
    proc = run(["verify", "--project", str(fixture), "--against", "run-baseline"])
    if proc.returncode != 0:
        raise AssertionError("recovery stage 1 failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if payload["new_findings"] != [] or payload["resolved_findings"] != []:
        raise AssertionError("recovery stage 1 expected no diff, got: " + json.dumps(payload))
    # 2) Apply the fix
    (fixture / "edges.microcosm.json").write_text("[]", encoding="utf-8")
    proc = run(["verify", "--project", str(fixture), "--against", "run-baseline"])
    if proc.returncode != 0:
        raise AssertionError("recovery stage 2 failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if not any(fid.startswith("finding.authority-violation.") for fid in payload["resolved_findings"]):
        raise AssertionError("recovery stage 2 expected authority-violation resolved, got: " + json.dumps(payload))
    return {"case": name, "resolved": payload["resolved_findings"], "new": payload["new_findings"]}


def case_regression():
    name = "verify-regression"
    fixture = FIXTURES / name
    shutil.rmtree(fixture / ".microcosm" / "reports", ignore_errors=True)
    # restore clean state
    (fixture / "edges.microcosm.json").write_text(
        '[{"id":"edge.primary-state","from":"service.primary","to":"store.state","relation":"writes","attributes":{},"evidence_refs":["evidence.fixture.primary"]}]',
        encoding="utf-8",
    )
    proc = run(["verify", "--project", str(fixture), "--against", "run-baseline"])
    if proc.returncode != 0:
        raise AssertionError("regression stage 1 failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if payload["new_findings"] != []:
        raise AssertionError("regression stage 1 expected clean, got: " + json.dumps(payload))
    # introduce regression
    (fixture / "edges.microcosm.json").write_text(
        '['
        '{"id":"edge.primary-state","from":"service.primary","to":"store.state","relation":"writes","attributes":{},"evidence_refs":["evidence.fixture.primary"]},'
        '{"id":"edge.secondary-state","from":"service.secondary","to":"store.state","relation":"writes","attributes":{},"evidence_refs":["evidence.fixture.secondary"]}'
        ']',
        encoding="utf-8",
    )
    proc = run(["verify", "--project", str(fixture), "--against", "run-baseline"])
    if proc.returncode != 0:
        raise AssertionError("regression stage 2 failed: " + proc.stderr)
    payload = json.loads(proc.stdout)
    if not any(fid.startswith("finding.multiple-writers.") for fid in payload["new_findings"]):
        raise AssertionError("regression stage 2 expected multiple-writers new, got: " + json.dumps(payload))
    diff_path = Path(payload["report_dir"]) / "geometry-diff.json"
    diff = json.loads(diff_path.read_text(encoding="utf-8"))
    if "edge.secondary-state" not in diff["diff"]["geometry"]["added_edges"]:
        raise AssertionError("regression stage 2 expected added_edge reported, got: " + json.dumps(diff))
    temporal = json.loads((Path(payload["report_dir"]) / "temporal-report.json").read_text(encoding="utf-8"))
    if temporal["mode"] != "verify":
        raise AssertionError("verify temporal-report expected verify mode, got: " + json.dumps(temporal))
    if not temporal.get("forecast_check", {}).get("unpredicted_new_findings"):
        raise AssertionError("verify temporal-report should mark unpredicted new findings, got: " + json.dumps(temporal))
    if temporal["forecast"].get("smallest_fastest_path", {}).get("decision") != "STOP_AND_MINIMAL_FIX":
        raise AssertionError("verify temporal-report should choose stop/minimal-fix path, got: " + json.dumps(temporal))
    if not temporal["forecast"].get("smallest_fastest_path", {}).get("proof_needed_after_execution"):
        raise AssertionError("verify temporal-report should name proof needed after execution, got: " + json.dumps(temporal))
    return {"case": name, "new": payload["new_findings"], "added_edges": diff["diff"]["geometry"]["added_edges"]}


def case_version_mismatch():
    name = "verify-version-mismatch"
    fixture = FIXTURES / name
    proc = run(["verify", "--project", str(fixture), "--against", "run-baseline"])
    if proc.returncode == 0:
        raise AssertionError("version mismatch should have failed but exited 0")
    if "schema_version" not in proc.stderr and "schema_version" not in proc.stdout:
        raise AssertionError("version mismatch should mention schema_version, got stderr=" + proc.stderr)
    return {"case": name, "status": "rejected", "message": proc.stderr.strip().splitlines()[-1] if proc.stderr else "ok"}


def main():
    mutable_fixtures = [
        FIXTURES / "verify-recovery" / "edges.microcosm.json",
        FIXTURES / "verify-regression" / "edges.microcosm.json",
    ]
    originals = {path: path.read_bytes() for path in mutable_fixtures}
    try:
        results = [case_recovery(), case_regression(), case_version_mismatch()]
    finally:
        for path, content in originals.items():
            path.write_bytes(content)
    print(json.dumps({"status": "ok", "verify_cases": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

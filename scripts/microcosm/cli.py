import argparse
import json
import sys
from pathlib import Path
from .bootstrap import bootstrap, build_mir
from .config import load_invariants
from .geometry.engine import run_invariants
from .plan_change import run_plan_change
from .reporting import write_reports
from .temporal.engine import simulate as temporal_simulate
from .validate import validate_mir, write_validation_report
from .verify import run_verify


def _trust_pipeline(mir, scan, project_root, invariants, verify_diff=None, base_unresolved=None, decision_override=None, risk=None):
    ok, issues, delta, normalized = validate_mir(mir)
    if normalized:
        mir["findings"] = normalized
    validation_payload = write_validation_report(project_root, mir["meta"]["run_id"], ok, issues, delta)
    report_dir = write_reports(
        project_root,
        mir["meta"]["run_id"],
        mir,
        scan["active_adapters"],
        scan["inferred"],
        scan["proposed"],
        base_unresolved=base_unresolved,
        verify_diff=verify_diff,
        validation_payload=validation_payload,
        decision_override=decision_override,
        risk=risk,
    )
    return ok, issues, delta, validation_payload, report_dir


def cmd_bootstrap(args):
    mir, scan, report_dir = bootstrap(args.project)
    print(json.dumps({
        "mode": "bootstrap",
        "run_id": mir["meta"]["run_id"],
        "active_adapters": scan["active_adapters"],
        "report_dir": str(report_dir),
    }, ensure_ascii=False))
    return 0


def cmd_inspect(args):
    mir, scan = build_mir(args.project)
    invariants = load_invariants(args.project)
    mir["findings"] = run_invariants(mir, invariants)
    ok, issues, delta, validation_payload, report_dir = _trust_pipeline(
        mir, scan, args.project, invariants
    )
    print(json.dumps({
        "mode": "inspect",
        "run_id": mir["meta"]["run_id"],
        "invariants": len(invariants),
        "findings": len(mir["findings"]),
        "schema_mismatch_findings": len(delta),
        "validation_ok": ok,
        "report_dir": str(report_dir),
    }, ensure_ascii=False))
    return 0


def cmd_verify(args):
    mir, scan, diff = _run_verify_pipeline(args.project, against=args.against)
    finding_diff = diff.get("findings", {})
    geometry = diff.get("geometry", {})
    print(json.dumps({
        "mode": "verify",
        "run_id": mir["meta"]["run_id"],
        "against": diff.get("before_run"),
        "added_nodes": len(geometry.get("added_nodes", [])),
        "deleted_nodes": len(geometry.get("deleted_nodes", [])),
        "added_edges": len(geometry.get("added_edges", [])),
        "deleted_edges": len(geometry.get("deleted_edges", [])),
        "resolved_findings": finding_diff.get("resolved", []),
        "new_findings": finding_diff.get("new", []),
        "still_open_findings": finding_diff.get("still_open", []),
        "report_dir": str(diff.get("report_dir")),
    }, ensure_ascii=False))
    return 0


def _run_verify_pipeline(project_root, against=None):
    from .verify import resolve_baseline_snapshot
    from .diff import compare_snapshots
    baseline_path = resolve_baseline_snapshot(project_root, against)
    mir, scan = build_mir(project_root)
    invariants = load_invariants(project_root)
    mir["findings"] = run_invariants(mir, invariants)
    diff = compare_snapshots(baseline_path, mir)
    ok, issues, delta, validation_payload, report_dir = _trust_pipeline(
        mir, scan, project_root, invariants, verify_diff=diff
    )
    diff["report_dir"] = str(report_dir)
    return mir, scan, diff


def cmd_plan_change(args):
    summary, report_dir = run_plan_change(args.project, args.plan)
    print(json.dumps({
        "mode": "plan-change",
        "plan_id": summary["plan_id"],
        "actions_planned": summary["actions_planned"],
        "project_edges_before": summary["project_edges_before"],
        "project_edges_after": summary["project_edges_after"],
        "findings_before": len(summary["findings_before"]),
        "findings_after": len(summary["findings_after"]),
        "resolved_preview": [f["id"] for f in summary["preview_diff"]["resolved"]],
        "new_preview": [f["id"] for f in summary["preview_diff"]["new"]],
        "still_open_preview": [f["id"] for f in summary["preview_diff"]["still_open"]],
        "report_dir": str(report_dir),
    }, ensure_ascii=False))
    return 0


def cmd_simulate(args):
    print(temporal_simulate())
    return 0


def cmd_compat(args):
    root = Path(args.project).resolve()
    adapter_dir = root / "scripts" / "microcosm" / "adapters"
    checks = {
        "python": sys.version_info >= (3, 10),
        "skill_md": (root / "SKILL.md").is_file(),
        "scripts": (root / "scripts" / "microcosm.py").is_file(),
        "schemas": len(list((root / "schemas").glob("*.schema.json"))) >= 1,
        "platform_adapters": all(
            (adapter_dir / name).is_file()
            for name in ("agent_skills.py", "codegraph.py", "codex.py", "hermes.py", "openclaw.py")
        ),
    }
    status = "ok" if all(checks.values()) else "failed"
    print(json.dumps({"mode": "compat-check", "checks": checks, "status": status}, ensure_ascii=False))
    return 0 if status == "ok" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="microcosm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ["bootstrap", "inspect", "verify", "plan-change", "simulate", "compat-check"]:
        sp = sub.add_parser(name)
        sp.add_argument("--project", default=".")
        if name == "verify":
            sp.add_argument("--against", default=None)
        if name == "plan-change":
            sp.add_argument("--plan", required=True)
    args = parser.parse_args(argv)
    return {
        "bootstrap": cmd_bootstrap,
        "inspect": cmd_inspect,
        "verify": cmd_verify,
        "plan-change": cmd_plan_change,
        "simulate": cmd_simulate,
        "compat-check": cmd_compat,
    }[args.cmd](args)

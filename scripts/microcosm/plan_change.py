import json
from copy import deepcopy
from pathlib import Path
from .bootstrap import build_mir
from .config import load_change_plan, load_invariants
from .geometry.engine import run_invariants
from .reporting import write_reports
from .versioning import MICROCOSM_VERSION, SCHEMA_VERSION, GENERATOR_VERSION


SUPPORTED_ACTIONS = {"add_edge", "remove_edge", "add_node", "remove_node"}


def _as_set(value):
    if value is None:
        return set()
    if isinstance(value, list):
        return set(value)
    return {value}


def _summarize_finding(finding):
    return {
        "id": finding["id"],
        "category": finding["category"],
        "severity": finding["severity"],
        "subject_ref": finding["subject_ref"],
    }


def _findings_by_subject(findings):
    bucket = {}
    for finding in findings:
        bucket.setdefault(finding["subject_ref"], []).append(finding)
    return bucket


def simulate_change(mir, plan, invariants):
    """Return a structured preview without mutating the project."""
    base = deepcopy(mir)
    if plan:
        for action in plan.get("actions", []):
            kind = action.get("kind")
            if kind not in SUPPORTED_ACTIONS:
                raise ValueError("unsupported action kind: " + str(kind))
    if plan:
        for action in plan.get("actions", []):
            kind = action["kind"]
            if kind == "add_edge":
                edge = action.get("edge") or {}
                base["edges"].append(edge)
            elif kind == "remove_edge":
                target = action.get("id") or (action.get("match") or {})
                base["edges"] = [e for e in base["edges"] if not _edge_matches(e, target)]
            elif kind == "add_node":
                node = action.get("node") or {}
                base["nodes"].append(node)
            elif kind == "remove_node":
                node_id = action.get("id")
                base["nodes"] = [n for n in base["nodes"] if n.get("id") != node_id]
                base["edges"] = [e for e in base["edges"] if e.get("from") != node_id and e.get("to") != node_id]
    base["findings"] = run_invariants(base, invariants)
    return base


def _edge_matches(edge, target):
    if not target:
        return False
    if "id" in target and edge.get("id") == target["id"]:
        return True
    return all(edge.get(k) == v for k, v in target.items() if k != "id")


def diff_findings(before, after):
    before_by = _findings_by_subject(before)
    after_by = _findings_by_subject(after)
    resolved = []
    new = []
    still_open = []
    for subject, findings in before_by.items():
        if subject not in after_by:
            resolved.extend(_summarize_finding(f) for f in findings)
        else:
            still_open.extend(_summarize_finding(f) for f in findings)
    for subject, findings in after_by.items():
        if subject not in before_by:
            new.extend(_summarize_finding(f) for f in findings)
    return {"resolved": resolved, "new": new, "still_open": still_open}


def run_plan_change(project_root, plan_path):
    plan = load_change_plan(plan_path)
    mir, scan = build_mir(project_root)
    invariants = load_invariants(project_root)
    before_findings = run_invariants(mir, invariants)
    projected = simulate_change(mir, plan, invariants)
    preview_diff = diff_findings(before_findings, projected["findings"])
    preview_summary = {
        "microcosm_version": MICROCOSM_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "mode": "plan-change",
        "project_root": str(project_root),
        "plan_path": str(plan_path),
        "plan_id": plan.get("id"),
        "plan_description": plan.get("description"),
        "actions_planned": len(plan.get("actions", [])) if plan else 0,
        "invariants_evaluated": len(invariants),
        "project_edges_before": len(mir["edges"]),
        "project_edges_after": len(projected["edges"]),
        "project_nodes_before": len(mir["nodes"]),
        "project_nodes_after": len(projected["nodes"]),
        "findings_before": [_summarize_finding(f) for f in before_findings],
        "findings_after": [_summarize_finding(f) for f in projected["findings"]],
        "preview_diff": preview_diff,
    }
    base = Path(project_root) / ".microcosm"
    report_dir = base / "reports" / mir["meta"]["run_id"]
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "plan-change.json").write_text(json.dumps(preview_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_reports(project_root, mir["meta"]["run_id"], mir, scan["active_adapters"], scan["inferred"], scan["proposed"], base_unresolved=[
        "plan-change is a structural preview only; it does not modify project source code",
        "Runtime activity graph unavailable in V0.1",
        "Temporal engine unavailable in V0.1",
    ])
    return preview_summary, report_dir

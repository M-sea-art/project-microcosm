"""报告输出与决策、风险评分、queue eligibility。"""

import json
from pathlib import Path
from .versioning import MICROCOSM_VERSION, SCHEMA_VERSION, GENERATOR_VERSION

DEFAULT_UNRESOLVED = [
    "Runtime activity graph unavailable in V0.1",
    "Temporal engine unavailable in V0.1",
]

QUEUE_CONFIRMED = "confirmed_findings"
QUEUE_PROBABLE = "probable_findings"
QUEUE_CONCERN = "concern_findings"
QUEUE_HYPOTHESIS = "hypothesis_findings"
QUEUE_SCHEMA = "schema_mismatch_findings"


def compute_decision(findings, validation_delta, adapters):
    schema_mismatch = [f for f in findings if f.get("category") == "schema-mismatch"]
    if not adapters:
        return "UNAVAILABLE"
    if any(f.get("severity") in {"critical", "high"} and f.get("category") not in {"schema-mismatch"} for f in findings):
        return "FAIL"
    if schema_mismatch or validation_delta:
        return "WARN"
    if any(f.get("severity") == "medium" for f in findings):
        return "WARN"
    return "PASS"


def compute_risk(findings, geometry_diff):
    structural = 0
    if geometry_diff:
        structural = len(geometry_diff.get("added_nodes", [])) + len(geometry_diff.get("deleted_nodes", [])) + len(geometry_diff.get("added_edges", [])) + len(geometry_diff.get("deleted_edges", []))
    structural_impact = min(5, structural // 2)
    state_persistence = sum(1 for f in findings if f.get("category") in {"multiple-writers", "evidence-missing"} and f.get("severity") in {"high", "critical"})
    permission_change = sum(1 for f in findings if f.get("category") == "authority-violation" and f.get("severity") in {"high", "critical"})
    irreversibility = min(5, structural_impact + permission_change)
    external_dependency = 0
    for _f in findings:
        actual = _f.get("actual")
        if isinstance(actual, dict) and actual.get("external"):
            external_dependency += 1
    uncertainty = sum(1 for f in findings if f.get("band") in {"concern", "hypothesis"})
    high_severity = sum(1 for f in findings if f.get("severity") in {"high", "critical"} and f.get("band") == "confirmed")
    score = structural_impact + state_persistence + permission_change + uncertainty + high_severity
    if score >= 4:
        level = "critical"
    elif score >= 3:
        level = "high"
    elif score >= 2:
        level = "medium"
    else:
        level = "low"
    return {
        "structural_impact": structural_impact,
        "state_persistence": state_persistence,
        "permission_change": permission_change,
        "irreversibility": irreversibility,
        "external_dependency": external_dependency,
        "uncertainty": uncertainty,
        "high_severity_confirmed": high_severity,
        "score": score,
        "level": level,
    }


def compute_queue_eligibility(findings):
    return {
        QUEUE_CONFIRMED: [f["id"] for f in findings if f.get("band") == "confirmed" and f.get("category") != "schema-mismatch"],
        QUEUE_PROBABLE: [f["id"] for f in findings if f.get("band") == "probable" and f.get("category") != "schema-mismatch"],
        QUEUE_CONCERN: [f["id"] for f in findings if f.get("band") == "concern"],
        QUEUE_HYPOTHESIS: [f["id"] for f in findings if f.get("band") == "hypothesis"],
        QUEUE_SCHEMA: [f["id"] for f in findings if f.get("category") == "schema-mismatch"],
    }


EXPERT_BY_CATEGORY = {
    "architecture-drift": "agent-runtime-architect",
    "undeclared-edge": "adapter-integration-expert",
    "missing-required-path": "geometry-invariant-expert",
    "authority-violation": "safety-permissions-expert",
    "multiple-writers": "geometry-invariant-expert",
    "cyclic-dependency": "geometry-invariant-expert",
    "excessive-fanout": "geometry-invariant-expert",
    "unverified-inference": "agent-runtime-architect",
    "schema-mismatch": "mir-evidence-schema-expert",
    "adapter-failure": "adapter-integration-expert",
    "evidence-missing": "mir-evidence-schema-expert",
}


def _priority_for_severity(severity):
    return {
        "critical": "P0",
        "high": "P1",
        "medium": "P2",
        "low": "P3",
        "info": "P4",
    }.get(severity, "P3")


def _mode_for_category(category):
    if category in {"architecture-drift", "authority-violation", "multiple-writers", "cyclic-dependency"}:
        return "plan-change"
    if category == "schema-mismatch":
        return "compat-check"
    return "inspect"


def compute_next_actions(findings, validation_delta, decision):
    actions = []
    for finding in findings + validation_delta:
        finding_id = finding.get("id")
        category = finding.get("category", "unverified-inference")
        severity = finding.get("severity", "low")
        actions.append({
            "id": "action." + str(finding_id or category).replace("finding.", ""),
            "priority": _priority_for_severity(severity),
            "owner_expert": EXPERT_BY_CATEGORY.get(category, "agent-runtime-architect"),
            "finding_refs": [finding_id] if finding_id else [],
            "recommended_mode": _mode_for_category(category),
            "requires_human_approval": severity in {"critical", "high"} or decision == "FAIL",
            "summary": finding.get("message") or category,
        })
    if not actions and decision == "PASS":
        actions.append({
            "id": "action.normal-review",
            "priority": "P4",
            "owner_expert": "developer-experience-expert",
            "finding_refs": [],
            "recommended_mode": "inspect",
            "requires_human_approval": False,
            "summary": "No critical/high findings detected; continue normal review.",
        })
    return sorted(actions, key=lambda item: item["priority"])


def write_reports(project_root, run_id, mir, active_adapters, inferred=None, proposed=None, unresolved=None, verify_diff=None, base_unresolved=None, validation_payload=None, decision_override=None, risk=None):
    base = Path(project_root) / ".microcosm"
    report_dir = base / "reports" / run_id
    snap_dir = base / "snapshots"
    mir_dir = base / "mir"
    report_dir.mkdir(parents=True, exist_ok=True)
    snap_dir.mkdir(parents=True, exist_ok=True)
    mir_dir.mkdir(parents=True, exist_ok=True)
    (mir_dir / "current.json").write_text(json.dumps(mir, indent=2, ensure_ascii=False), encoding="utf-8")
    (snap_dir / (run_id + ".json")).write_text(json.dumps(mir, indent=2, ensure_ascii=False), encoding="utf-8")

    findings = mir.get("findings", [])
    validation_delta = (validation_payload or {}).get("schema_mismatch_findings", [])
    queue = compute_queue_eligibility(findings + validation_delta)
    geometry_diff_only = (verify_diff or {}).get("geometry", {})
    risk = risk or compute_risk(findings, geometry_diff_only)
    decision = decision_override or compute_decision(findings + validation_delta, validation_delta, active_adapters)
    next_actions = compute_next_actions(findings, validation_delta, decision)

    (report_dir / "findings.json").write_text(json.dumps({
        "microcosm_version": MICROCOSM_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "run_id": run_id,
        "decision": decision,
        "findings": findings,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    (report_dir / "queue-eligibility.json").write_text(json.dumps({
        "microcosm_version": MICROCOSM_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "run_id": run_id,
        "decision": decision,
        "queue": queue,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    if verify_diff is not None:
        (report_dir / "geometry-diff.json").write_text(json.dumps({
            "microcosm_version": MICROCOSM_VERSION,
            "schema_version": SCHEMA_VERSION,
            "generator_version": GENERATOR_VERSION,
            "run_id": run_id,
            "decision": decision,
            "diff": verify_diff,
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    (report_dir / "next-actions.json").write_text(json.dumps({
        "microcosm_version": MICROCOSM_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "run_id": run_id,
        "decision": decision,
        "next_actions": next_actions,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    unresolved_list = list(unresolved) if unresolved is not None else list(DEFAULT_UNRESOLVED)
    base_unresolved_list = list(base_unresolved or DEFAULT_UNRESOLVED)
    for item in base_unresolved_list:
        if item not in unresolved_list:
            unresolved_list.append(item)
    if verify_diff is not None:
        still_open = verify_diff.get("findings", {}).get("still_open", [])
        new_findings = verify_diff.get("findings", {}).get("new", [])
        if still_open:
            unresolved_list.append("Findings that did not change since the compared run: " + ", ".join(still_open))
        if new_findings:
            unresolved_list.append("New findings not yet confirmed: " + ", ".join(new_findings))
    (report_dir / "unresolved.json").write_text(json.dumps({
        "microcosm_version": MICROCOSM_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "run_id": run_id,
        "unresolved": unresolved_list,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Project Microcosm Summary",
        "",
        "run_id: " + run_id,
        "microcosm_version: " + MICROCOSM_VERSION,
        "schema_version: " + SCHEMA_VERSION,
        "generator_version: " + GENERATOR_VERSION,
        "",
        "## Decision",
        decision,
        "",
        "## Risk",
        "score: " + str(risk["score"]),
        "level: " + risk["level"],
        "structural_impact: " + str(risk["structural_impact"]),
        "state_persistence: " + str(risk["state_persistence"]),
        "permission_change: " + str(risk["permission_change"]),
        "irreversibility: " + str(risk["irreversibility"]),
        "external_dependency: " + str(risk["external_dependency"]),
        "uncertainty: " + str(risk["uncertainty"]),
        "high_severity_confirmed: " + str(risk.get("high_severity_confirmed", 0)),
        "",
        "## Queue eligibility",
        "confirmed: " + (", ".join(queue[QUEUE_CONFIRMED]) or "(none)"),
        "probable: " + (", ".join(queue[QUEUE_PROBABLE]) or "(none)"),
        "concern: " + (", ".join(queue[QUEUE_CONCERN]) or "(none)"),
        "hypothesis: " + (", ".join(queue[QUEUE_HYPOTHESIS]) or "(none)"),
        "schema_mismatch: " + (", ".join(queue[QUEUE_SCHEMA]) or "(none)"),
        "",
        "## Analyzed scope",
        str(project_root),
        "",
        "## Active adapters",
        ", ".join(active_adapters) or "none",
        "",
        "## Model resolution",
        "L0 + L1 by default; L2 for detected modules.",
        "",
        "## Observed structure",
        "nodes: " + str(len(mir.get("nodes", []))),
        "edges: " + str(len(mir.get("edges", []))),
        "observations: " + str(len(mir.get("observations", []))),
        "assertions: " + str(len(mir.get("assertions", []))),
        "policies: " + str(len(mir.get("policies", []))),
        "",
        "## Inferred structure",
        "inferred: " + str(len(inferred or [])),
        "proposed: " + str(len(proposed or [])),
        "",
        "## Invariant violations",
        "findings: " + str(len(findings)),
    ]
    for item in findings:
        lines.append("- {id} [{sev}/{band}] {cat} conf={conf} sub={sub}".format(
            id=item["id"], sev=item["severity"], band=item["band"], cat=item["category"], conf=item["confidence"], sub=item["subject_ref"]))

    if validation_delta:
        lines += ["", "## Schema-mismatch findings (auto-added by validator)"]
        for item in validation_delta:
            lines.append("- {id} [{sev}/{band}] {cat} msg={msg}".format(
                id=item["id"], sev=item["severity"], band=item["band"], cat=item["category"], msg=item.get("message", "")))

    lines += ["", "## Evidence levels", "V0.1 primarily emits E3, E2, and E1 evidence."]

    if verify_diff is not None:
        g = verify_diff.get("geometry", {})
        f = verify_diff.get("findings", {})
        lines += [
            "",
            "## Verify diff",
            "against_run: " + str(verify_diff.get("before_run")),
            "added_nodes: " + str(len(g.get("added_nodes", []))),
            "deleted_nodes: " + str(len(g.get("deleted_nodes", []))),
            "added_edges: " + str(len(g.get("added_edges", []))),
            "deleted_edges: " + str(len(g.get("deleted_edges", []))),
            "resolved_findings: " + ", ".join(f.get("resolved", [])) or "(none)",
            "new_findings: " + ", ".join(f.get("new", [])) or "(none)",
            "still_open_findings: " + ", ".join(f.get("still_open", [])) or "(none)",
        ]

    lines += ["", "## Unresolved uncertainties"]
    for item in unresolved_list:
        lines.append("- " + item)

    lines += ["", "## Recommended next action"]
    if decision == "FAIL":
        lines.append("Stop merging. Inspect critical/high findings above and decide whether to fix, accept, or escalate.")
    elif decision == "WARN":
        lines.append("Proceed with caution. Review probable/medium findings and confirm before merging.")
    elif decision == "UNAVAILABLE":
        lines.append("No active adapters produced evidence. Check that the project root contains supported code or fixtures.")
    else:
        lines.append("No critical/high findings detected. Safe to proceed with normal review.")

    lines += ["", "## Machine-readable next actions", "See `next-actions.json`."]

    (report_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest_files = ["summary.md", "findings.json", "queue-eligibility.json", "next-actions.json", "unresolved.json"]
    if verify_diff is not None:
        manifest_files.insert(2, "geometry-diff.json")
    (report_dir / "manifest.json").write_text(json.dumps({
        "microcosm_version": MICROCOSM_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "run_id": run_id,
        "decision": decision,
        "next_actions": next_actions,
        "files": manifest_files,
    }, indent=2), encoding="utf-8")
    return report_dir

"""MIR 校验器。

校验规则见 trust 阶段设计表：
- meta 必填且版本字段一致
- 各列表的 id 全局唯一
- 字段 enum 校验
- subject_ref / evidence_refs 解析
- finding 必须有 evidence_ref（除非 band=hypothesis 且 severity<=low）
- finding.band 与 confidence 一致
- schema-mismatch 单独产出 finding
"""

import json
import re
import hashlib
from pathlib import Path

from .versioning import MICROCOSM_VERSION, SCHEMA_VERSION


NODE_KINDS = {
    "project", "package", "module", "symbol", "service", "agent", "skill", "tool",
    "mcp-server", "workflow", "memory", "store", "policy", "queue",
    "external-service", "human-gate", "resource",
}
EDGE_RELATIONS = {
    "contains", "imports", "calls", "reads", "writes", "delegates", "submits-to",
    "validates", "approves", "activates", "inhibits", "observes", "publishes",
    "subscribes", "owns", "depends-on", "transitions-to",
}
POLICY_DECISIONS = {"allowed", "denied", "approval-required", "unspecified"}
OBSERVATION_LAYERS = {"static", "runtime", "configuration", "test"}
ASSERTION_LAYERS = {"target", "authority", "architecture", "ownership"}
FINDING_CATEGORIES = {
    "architecture-drift", "undeclared-edge", "missing-required-path",
    "authority-violation", "multiple-writers", "cyclic-dependency",
    "excessive-fanout", "unverified-inference", "schema-mismatch",
    "adapter-failure", "evidence-missing",
}
FINDING_SEVERITIES = {"critical", "high", "medium", "low", "info"}
FINDING_BANDS = {"confirmed", "probable", "concern", "hypothesis"}
EVIDENCE_LEVELS = {"E4", "E3", "E2", "E1", "E0"}


def compute_band(confidence):
    if confidence >= 0.85:
        return "confirmed"
    if confidence >= 0.60:
        return "probable"
    if confidence >= 0.30:
        return "concern"
    return "hypothesis"


_SIGNIFICANT_ACTUAL_KEYS = {"observed_edge", "observed_writers", "paths", "cycle", "operator", "actual"}
_EDGE_SEMANTIC_KEYS = {"id", "from", "to", "relation"}


def _normalize_edge(value):
    if isinstance(value, dict):
        return {k: v for k, v in value.items() if k in _EDGE_SEMANTIC_KEYS}
    if isinstance(value, list):
        return [_normalize_edge(item) for item in value]
    return value


def _normalize_actual(actual):
    if not isinstance(actual, dict):
        return actual
    normalized = {}
    for key, value in actual.items():
        if key not in _SIGNIFICANT_ACTUAL_KEYS:
            continue
        if key == "observed_edge":
            normalized[key] = _normalize_edge(value)
        elif key == "observed_writers" and isinstance(value, list):
            normalized[key] = sorted([v if isinstance(v, str) else v for v in value])
        else:
            normalized[key] = value
    return normalized


def stable_finding_id(category, subject_ref, expected, actual):
    payload = json.dumps({
        "category": category,
        "subject_ref": subject_ref,
        "expected": expected or {},
        "actual": _normalize_actual(actual) or {},
    }, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:8]
    return "finding." + category + "." + digest


def stable_message(category, subject_ref, expected, actual):
    return category + " on " + subject_ref


def _iter_ids(items):
    for item in items or []:
        iid = item.get("id")
        if iid:
            yield iid


def _build_id_index(*collections):
    index = {}
    duplicates = []
    for coll in collections:
        for iid in _iter_ids(coll):
            if iid in index:
                duplicates.append(iid)
            else:
                index[iid] = True
    return index, duplicates


def _resolve(ref, id_index):
    return ref in id_index


def _coerce_subject_refs(mir):
    return set(mir.get("nodes", []) and [n.get("id") for n in mir.get("nodes", [])] or []) | \
           set([e.get("id") for e in mir.get("edges", [])])


def validate_mir(mir):
    """校验 MIR；返回 (ok, issues, findings_delta)。"""
    issues = []
    if not isinstance(mir, dict):
        return False, [{"code": "mir-not-object", "message": "MIR must be a dict"}], []
    meta = mir.get("meta") or {}
    for field in ("microcosm_version", "schema_version", "run_id", "generated_at", "generator_version"):
        if not meta.get(field):
            issues.append({"code": "meta-missing", "field": field, "message": "meta." + field + " is required"})
    if meta.get("microcosm_version") and meta["microcosm_version"] != MICROCOSM_VERSION:
        issues.append({"code": "meta-version-mismatch", "field": "microcosm_version", "expected": MICROCOSM_VERSION, "actual": meta["microcosm_version"]})
    if meta.get("schema_version") and meta["schema_version"] != SCHEMA_VERSION:
        issues.append({"code": "meta-version-mismatch", "field": "schema_version", "expected": SCHEMA_VERSION, "actual": meta["schema_version"]})

    nodes = mir.get("nodes", [])
    edges = mir.get("edges", [])
    assertions = mir.get("assertions", [])
    observations = mir.get("observations", [])
    policies = mir.get("policies", [])
    evidence = mir.get("evidence", [])
    findings = mir.get("findings", [])

    id_index, duplicates = _build_id_index(nodes, edges, assertions, observations, policies, evidence, findings)
    for dup in duplicates:
        issues.append({"code": "duplicate-id", "id": dup, "message": "duplicate id: " + dup})

    subject_refs = _coerce_subject_refs(mir)

    for node in nodes:
        if node.get("kind") not in NODE_KINDS:
            issues.append({"code": "node-kind-invalid", "id": node.get("id"), "actual": node.get("kind")})
        for ref in node.get("evidence_refs") or []:
            if not _resolve(ref, id_index):
                issues.append({"code": "evidence-missing", "subject": node.get("id"), "ref": ref})

    node_id_set = {n.get("id") for n in nodes}
    for edge in edges:
        if edge.get("relation") not in EDGE_RELATIONS:
            issues.append({"code": "edge-relation-invalid", "id": edge.get("id"), "actual": edge.get("relation")})
        if edge.get("from") not in node_id_set:
            issues.append({"code": "edge-from-unresolved", "id": edge.get("id"), "from": edge.get("from")})
        if edge.get("to") not in node_id_set:
            issues.append({"code": "edge-to-unresolved", "id": edge.get("id"), "to": edge.get("to")})
        for ref in edge.get("evidence_refs") or []:
            if not _resolve(ref, id_index):
                issues.append({"code": "evidence-missing", "subject": edge.get("id"), "ref": ref})

    for obs in observations:
        if obs.get("layer") not in OBSERVATION_LAYERS:
            issues.append({"code": "observation-layer-invalid", "id": obs.get("id"), "actual": obs.get("layer")})
        if obs.get("subject_ref") not in subject_refs:
            issues.append({"code": "subject-ref-unresolved", "kind": "observation", "id": obs.get("id"), "subject_ref": obs.get("subject_ref")})
        for ref in obs.get("evidence_refs") or []:
            if not _resolve(ref, id_index):
                issues.append({"code": "evidence-missing", "subject": obs.get("id"), "ref": ref})

    for ass in assertions:
        if ass.get("layer") not in ASSERTION_LAYERS:
            issues.append({"code": "assertion-layer-invalid", "id": ass.get("id"), "actual": ass.get("layer")})
        if ass.get("subject_ref") not in subject_refs:
            issues.append({"code": "subject-ref-unresolved", "kind": "assertion", "id": ass.get("id"), "subject_ref": ass.get("subject_ref")})
        for ref in ass.get("evidence_refs") or []:
            if not _resolve(ref, id_index):
                issues.append({"code": "evidence-missing", "subject": ass.get("id"), "ref": ref})

    for pol in policies:
        if pol.get("decision") not in POLICY_DECISIONS:
            issues.append({"code": "policy-decision-invalid", "id": pol.get("id"), "actual": pol.get("decision")})
        if pol.get("subject_ref") not in subject_refs:
            issues.append({"code": "subject-ref-unresolved", "kind": "policy", "id": pol.get("id"), "subject_ref": pol.get("subject_ref")})
        for ref in pol.get("evidence_refs") or []:
            if not _resolve(ref, id_index):
                issues.append({"code": "evidence-missing", "subject": pol.get("id"), "ref": ref})

    for ev in evidence:
        if ev.get("level") not in EVIDENCE_LEVELS:
            issues.append({"code": "evidence-level-invalid", "id": ev.get("id"), "actual": ev.get("level")})

    normalized_findings = []
    for f in findings:
        normalized, f_issues = _normalize_finding(f, evidence, subject_refs)
        normalized_findings.append(normalized)
        issues.extend(f_issues)

    delta = []
    for issue in issues:
        if issue.get("code") in {"node-kind-invalid", "edge-relation-invalid", "policy-decision-invalid",
                                  "observation-layer-invalid", "assertion-layer-invalid", "evidence-level-invalid",
                                  "subject-ref-unresolved", "duplicate-id", "meta-version-mismatch"}:
            delta.append(_make_schema_mismatch_finding(issue))

    ok = not any(i.get("code") in {"meta-missing", "meta-version-mismatch", "duplicate-id",
                                    "edge-relation-invalid", "policy-decision-invalid", "evidence-level-invalid"}
                 for i in issues)
    return ok, issues, delta, normalized_findings


def _normalize_finding(finding, evidence, subject_refs):
    issues = []
    category = finding.get("category")
    severity = finding.get("severity")
    confidence = finding.get("confidence")
    subject_ref = finding.get("subject_ref")
    expected = finding.get("expected") or {}
    actual = finding.get("actual") or {}
    if category not in FINDING_CATEGORIES:
        issues.append({"code": "finding-category-invalid", "id": finding.get("id"), "actual": category})
    if severity not in FINDING_SEVERITIES:
        issues.append({"code": "finding-severity-invalid", "id": finding.get("id"), "actual": severity})
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
        issues.append({"code": "finding-confidence-invalid", "id": finding.get("id")})
    band = compute_band(confidence)
    expected_band = finding.get("band")
    if expected_band and expected_band not in FINDING_BANDS:
        issues.append({"code": "finding-band-invalid", "id": finding.get("id"), "actual": expected_band})
    elif expected_band and expected_band != band:
        issues.append({"code": "finding-band-mismatch", "id": finding.get("id"), "expected": expected_band, "actual": band})

    if not finding.get("evidence_refs"):
        if band != "hypothesis" or severity in {"critical", "high"}:
            issues.append({"code": "evidence-required", "id": finding.get("id")})
            if category != "evidence-missing":
                issues.append({"code": "evidence-required", "id": finding.get("id"), "message": "finding without evidence is forced to hypothesis/low"})

    if subject_ref and subject_ref not in subject_refs:
        issues.append({"code": "subject-ref-unresolved", "kind": "finding", "id": finding.get("id"), "subject_ref": subject_ref})

    stable_id = stable_finding_id(category, subject_ref, expected, actual)
    normalized = {
        "id": stable_id,
        "category": category,
        "severity": severity,
        "band": band,
        "confidence": confidence,
        "subject_ref": subject_ref,
        "expected": expected,
        "actual": actual,
        "evidence_refs": list(finding.get("evidence_refs") or []),
        "message": finding.get("message") or stable_message(category, subject_ref, expected, actual),
    }
    if not normalized["evidence_refs"]:
        normalized["band"] = "hypothesis"
        if normalized["severity"] in {"critical", "high"}:
            normalized["severity"] = "low"
    return normalized, issues


def _make_schema_mismatch_finding(issue):
    subject_ref = issue.get("id") or issue.get("subject_ref") or "schema:" + issue.get("code", "unknown")
    return {
        "id": stable_finding_id("schema-mismatch", subject_ref, {"code": issue.get("code")}, {"actual": issue.get("actual")}),
        "category": "schema-mismatch",
        "severity": "high",
        "band": "confirmed",
        "confidence": 1.0,
        "subject_ref": subject_ref,
        "expected": {"code": issue.get("code")},
        "actual": {"actual": issue.get("actual")},
        "evidence_refs": [],
        "message": "schema-mismatch: " + issue.get("message", issue.get("code")),
    }


def write_validation_report(project_root, run_id, ok, issues, delta):
    base = Path(project_root) / ".microcosm"
    report_dir = base / "reports" / run_id
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "microcosm_version": MICROCOSM_VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "ok": ok,
        "issue_count": len(issues),
        "issues": issues,
        "schema_mismatch_findings": delta,
    }
    (report_dir / "validation.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload

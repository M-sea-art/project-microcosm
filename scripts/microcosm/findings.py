"""Finding 构造器。

V0.1 trust 阶段：
- id 改用 stable hash：finding.<category>.<8hex>
- band 由 confidence 自动推导
- evidence_refs 为空时强制降级到 hypothesis + severity<=low
- message 必填
"""

from .validate import compute_band, stable_finding_id, stable_message


class FindingBuilder:
    def __init__(self):
        self.counts = {}

    def make(self, category, severity, confidence, subject_ref, expected, actual, evidence_refs, message=None):
        confidence = _coerce_confidence(confidence)
        band = compute_band(confidence)
        evidence_refs = list(evidence_refs or [])
        severity = severity or "info"
        if not evidence_refs:
            band = "hypothesis"
            if severity in {"critical", "high"}:
                severity = "low"
        finding_id = stable_finding_id(category, subject_ref, expected or {}, actual or {})
        prefix = _category_prefix(category)
        self.counts[prefix] = self.counts.get(prefix, 0) + 1
        return {
            "id": finding_id,
            "category": category,
            "severity": severity,
            "band": band,
            "confidence": confidence,
            "subject_ref": subject_ref,
            "expected": expected or {},
            "actual": actual or {},
            "evidence_refs": evidence_refs,
            "message": message or stable_message(category, subject_ref, expected, actual),
        }


def _coerce_confidence(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _category_prefix(category):
    return {
        "authority-violation": "AUTH",
        "multiple-writers": "WRITER",
        "cyclic-dependency": "CYCLE",
        "missing-required-path": "PATH",
        "excessive-fanout": "FANOUT",
        "undeclared-edge": "EDGE",
        "schema-mismatch": "SCHEMA",
        "evidence-missing": "EVIDENCE",
    }.get(category, "FINDING")

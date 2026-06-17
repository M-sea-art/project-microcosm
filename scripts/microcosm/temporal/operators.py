CATEGORY_CONSEQUENCE = {
    "architecture-drift": "If deferred, the project model and intended design keep drifting apart.",
    "undeclared-edge": "If deferred, hidden coupling can spread before ownership is reviewed.",
    "missing-required-path": "If deferred, required mediation or review paths may be bypassed later.",
    "authority-violation": "If deferred, an unauthorized path can become normal project behavior.",
    "multiple-writers": "If deferred, persistent state can diverge or be overwritten by competing writers.",
    "cyclic-dependency": "If deferred, local changes can turn into broad refactor or release risk.",
    "excessive-fanout": "If deferred, blast radius grows and future changes become harder to isolate.",
    "unverified-inference": "If deferred, future decisions may be based on an unproven assumption.",
    "schema-mismatch": "If deferred, agents may misread report data or skip important findings.",
    "adapter-failure": "If deferred, part of the project timeline remains invisible to Microcosm.",
    "evidence-missing": "If deferred, the forecast remains a hypothesis rather than a decision basis.",
}


EXPERTS = [
    "temporal-microcosm-architect",
    "causal-chain-expert",
    "scenario-rehearsal-expert",
    "state-snapshot-expert",
    "evidence-confidence-expert",
    "risk-visibility-expert",
    "human-agent-decision-expert",
]


def finding_delta_ids(delta):
    return {
        "resolved": _ids((delta or {}).get("resolved", [])),
        "new": _ids((delta or {}).get("new", [])),
        "still_open": _ids((delta or {}).get("still_open", [])),
    }


def summarize_findings(findings):
    out = []
    for finding in findings or []:
        out.append({
            "id": finding.get("id"),
            "category": finding.get("category"),
            "severity": finding.get("severity"),
            "band": finding.get("band"),
            "confidence": finding.get("confidence"),
            "subject_ref": finding.get("subject_ref"),
            "message": finding.get("message"),
        })
    return out


def forecast_from_findings(mode, decision, risk, finding_delta, after_findings=None):
    delta_ids = finding_delta_ids(finding_delta)
    new_findings = list((finding_delta or {}).get("new", []))
    still_open = list((finding_delta or {}).get("still_open", []))
    resolved = list((finding_delta or {}).get("resolved", []))
    after_by_id = {f.get("id"): f for f in after_findings or [] if isinstance(f, dict)}

    visible_risks = []
    for item in new_findings + still_open:
        category = item.get("category") if isinstance(item, dict) else after_by_id.get(item, {}).get("category")
        ref = item.get("id") if isinstance(item, dict) else item
        visible_risks.append({
            "finding_ref": ref,
            "category": category,
            "deferred_consequence": CATEGORY_CONSEQUENCE.get(category, "If deferred, future project state becomes less certain."),
        })

    confidence = _forecast_confidence(_finding_objects(new_findings + still_open + resolved, after_by_id))
    return {
        "mode": mode,
        "decision": decision,
        "risk_level": (risk or {}).get("level", "low"),
        "finding_delta": delta_ids,
        "risk_visibility": visible_risks,
        "minimum_safe_next_step": minimum_safe_next_step(mode, decision, delta_ids),
        "verification_points": verification_points(mode, delta_ids),
        "confidence": confidence,
        "band": _band(confidence),
    }


def verify_forecast_check(project_root, verify_diff):
    before_run = (verify_diff or {}).get("before_run")
    report = _load_prior_temporal_report(project_root, before_run)
    actual = finding_delta_ids((verify_diff or {}).get("findings", {}))
    if not report:
        return {
            "prior_forecast_found": False,
            "actual_finding_delta": actual,
            "matched_predicted_new_findings": [],
            "matched_predicted_resolved_findings": [],
            "unpredicted_new_findings": actual["new"],
            "unmet_predicted_new_findings": [],
            "unmet_predicted_resolved_findings": [],
        }
    predicted = ((report.get("forecast") or {}).get("finding_delta") or {})
    predicted_new = set(predicted.get("new", []))
    predicted_resolved = set(predicted.get("resolved", []))
    actual_new = set(actual["new"])
    actual_resolved = set(actual["resolved"])
    return {
        "prior_forecast_found": True,
        "prior_run": before_run,
        "actual_finding_delta": actual,
        "matched_predicted_new_findings": sorted(predicted_new & actual_new),
        "matched_predicted_resolved_findings": sorted(predicted_resolved & actual_resolved),
        "unpredicted_new_findings": sorted(actual_new - predicted_new),
        "unmet_predicted_new_findings": sorted(predicted_new - actual_new),
        "unmet_predicted_resolved_findings": sorted(predicted_resolved - actual_resolved),
    }


def expert_judgments(mode, forecast, forecast_check=None):
    new_count = len((forecast.get("finding_delta") or {}).get("new", []))
    still_open_count = len((forecast.get("finding_delta") or {}).get("still_open", []))
    risk_level = forecast.get("risk_level")
    low_confidence = forecast.get("band") in {"concern", "hypothesis"}
    unpredicted = len((forecast_check or {}).get("unpredicted_new_findings", []))
    return [
        _judgment("temporal-microcosm-architect", "PASS", "Current and projected states are represented as temporal states."),
        _judgment("causal-chain-expert", "WARN" if new_count or unpredicted else "PASS", _causal_summary(new_count, unpredicted)),
        _judgment("scenario-rehearsal-expert", "WARN" if mode == "plan-change" and (new_count or still_open_count) else "PASS", _scenario_summary(mode, new_count, still_open_count)),
        _judgment("state-snapshot-expert", "PASS", "Snapshots provide the baseline for history, current state, and verification."),
        _judgment("evidence-confidence-expert", "WARN" if low_confidence else "PASS", _evidence_summary(forecast)),
        _judgment("risk-visibility-expert", "WARN" if risk_level in {"medium", "high", "critical"} or new_count else "PASS", "Deferred-cost risks visible: {}".format(len(forecast.get("risk_visibility", [])))),
        _judgment("human-agent-decision-expert", "NEEDS_HUMAN" if risk_level in {"high", "critical"} or forecast.get("decision") == "FAIL" else "PASS", "Human approval is required for high, critical, or failing temporal risk."),
    ]


def minimum_safe_next_step(mode, decision, delta_ids):
    if delta_ids.get("new"):
        if mode == "verify":
            return "Stop and review the unpredicted findings before accepting this state as the new baseline."
        return "Revise or split the change before writing source; verify the new projected findings first."
    if delta_ids.get("still_open") and decision in {"WARN", "FAIL"}:
        return "Resolve or explicitly accept still-open findings before merging."
    if delta_ids.get("resolved"):
        return "Apply the change, then run verify against this run to prove the forecast landed."
    if decision == "UNAVAILABLE":
        return "Add a supported adapter or fixture before relying on this timeline."
    return "Proceed with normal review and keep the current snapshot as the next verification baseline."


def verification_points(mode, delta_ids):
    points = []
    if mode == "plan-change":
        points.append("After executing the plan, run verify against this run id.")
        if delta_ids.get("new"):
            points.append("Confirm that projected new findings did not reach the committed state.")
        if delta_ids.get("resolved"):
            points.append("Confirm that projected resolved findings disappeared from the next snapshot.")
    elif mode == "verify":
        points.append("Review unpredicted new findings before treating the change as safe.")
        points.append("Use this run as the new baseline only after still-open findings are accepted or fixed.")
    else:
        points.append("Use this run as the baseline for the next plan-change or verify command.")
    return points


def _ids(items):
    out = []
    for item in items:
        if isinstance(item, dict):
            ref = item.get("id")
        else:
            ref = item
        if ref:
            out.append(ref)
    return sorted(out)


def _forecast_confidence(findings):
    values = []
    for finding in findings:
        if isinstance(finding, dict) and finding.get("confidence") is not None:
            try:
                values.append(float(finding.get("confidence")))
            except (TypeError, ValueError):
                pass
    if not values:
        return 0.72
    return round(min(values), 4)


def _finding_objects(items, by_id):
    out = []
    for item in items:
        if isinstance(item, dict):
            out.append(item)
        elif item in by_id:
            out.append(by_id[item])
    return out


def _band(confidence):
    if confidence >= 0.85:
        return "confirmed"
    if confidence >= 0.60:
        return "probable"
    if confidence >= 0.30:
        return "concern"
    return "hypothesis"


def _judgment(expert, decision, summary):
    return {"expert": expert, "decision": decision, "summary": summary}


def _causal_summary(new_count, unpredicted):
    if unpredicted:
        return "Verification found unpredicted future findings: {}".format(unpredicted)
    if new_count:
        return "The plan projects new downstream findings: {}".format(new_count)
    return "No new causal risk was detected in this temporal slice."


def _scenario_summary(mode, new_count, still_open_count):
    if mode != "plan-change":
        return "Scenario rehearsal applies primarily to plan-change runs."
    return "Projected new findings: {}; still-open findings: {}.".format(new_count, still_open_count)


def _evidence_summary(forecast):
    return "Forecast confidence band is {} at confidence {}.".format(forecast.get("band"), forecast.get("confidence"))


def _load_prior_temporal_report(project_root, run_id):
    if not run_id:
        return None
    try:
        import json
        from pathlib import Path
        path = Path(project_root) / ".microcosm" / "reports" / run_id / "temporal-report.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None

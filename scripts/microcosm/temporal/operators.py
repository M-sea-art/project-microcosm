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
    "time-compression-architect",
    "minimum-path-expert",
    "structural-probe-expert",
    "deep-decision-expert",
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
    fastest_path = smallest_fastest_path(mode, decision, risk, delta_ids)
    return {
        "mode": mode,
        "decision": decision,
        "risk_level": (risk or {}).get("level", "low"),
        "finding_delta": delta_ids,
        "risk_visibility": visible_risks,
        "smallest_fastest_path": fastest_path,
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
    path = forecast.get("smallest_fastest_path") or {}
    return [
        _judgment("time-compression-architect", "PASS", "The run compresses slow implementation discovery into a structured decision point."),
        _judgment("minimum-path-expert", "WARN" if path.get("decision") not in {"FAST_TRACK", "APPLY_THEN_VERIFY"} else "PASS", _path_summary(path)),
        _judgment("structural-probe-expert", "PASS", "The decision starts from observed structure before execution."),
        _judgment("deep-decision-expert", "WARN" if low_confidence else "PASS", "The path decision uses confidence band {}.".format(forecast.get("band"))),
        _judgment("causal-chain-expert", "WARN" if new_count or unpredicted else "PASS", _causal_summary(new_count, unpredicted)),
        _judgment("scenario-rehearsal-expert", "WARN" if mode == "plan-change" and (new_count or still_open_count) else "PASS", _scenario_summary(mode, new_count, still_open_count)),
        _judgment("state-snapshot-expert", "PASS", "Snapshots provide the baseline for history, current state, and verification."),
        _judgment("evidence-confidence-expert", "WARN" if low_confidence else "PASS", _evidence_summary(forecast)),
        _judgment("risk-visibility-expert", "WARN" if risk_level in {"medium", "high", "critical"} or new_count else "PASS", "Deferred-cost risks visible: {}".format(len(forecast.get("risk_visibility", [])))),
        _judgment("human-agent-decision-expert", "NEEDS_HUMAN" if risk_level in {"high", "critical"} or forecast.get("decision") == "FAIL" else "PASS", "Human approval is required for high, critical, or failing temporal risk."),
    ]


def smallest_fastest_path(mode, decision, risk, delta_ids):
    risk_level = (risk or {}).get("level", "low")
    new = delta_ids.get("new", [])
    resolved = delta_ids.get("resolved", [])
    still_open = delta_ids.get("still_open", [])
    common_avoid = [
        "Do not start a broad rewrite before the structural finding is isolated.",
        "Do not run an open-ended execution flow when one plan-change plus one verify can prove the path.",
    ]
    if decision == "UNAVAILABLE":
        return _path(
            "NEEDS_STRUCTURE_PROBE",
            "No reliable fast path exists until the project exposes enough structure.",
            "The fastest route is not execution; it is one narrow structure probe that prevents guessing.",
            [
                "Enable a supported adapter or fixture for the target area.",
                "Run inspect again and use that snapshot as the decision baseline.",
            ],
            common_avoid + ["Do not guess the implementation path without observable structure."],
            [
                "Skip implementation work while active adapters are unavailable.",
                "Skip broad planning until the target area has observed nodes or edges.",
            ],
            [
                "A later inspect run has active adapters.",
                "The next report produces a current state with observable structure.",
            ],
        )
    if mode == "plan-change" and new:
        return _path(
            "SPLIT_OR_REVISE_BEFORE_BUILD",
            "The fastest real path is to revise the plan now because the current plan projects new findings.",
            "Changing the plan before coding avoids implementing a known bad future and then paying for rollback.",
            [
                "Keep the unchanged parts of the plan.",
                "Remove or split the action that creates projected findings: " + ", ".join(new),
                "Run plan-change again until projected new findings are empty.",
                "Apply only the clean slice, then verify against this run.",
            ],
            common_avoid + ["Do not implement the full plan and discover the violation after the fact."],
            [
                "Skip full implementation while projected_new_findings is not empty.",
                "Skip unrelated refactors; isolate only the action that creates the finding.",
            ],
            [
                "A follow-up plan-change has no projected new findings.",
                "A verify run proves the committed state did not inherit the projected findings.",
            ],
        )
    if mode == "plan-change" and resolved:
        return _path(
            "APPLY_THEN_VERIFY",
            "The fastest safe path is to apply the minimal planned change because it resolves existing findings without projecting new ones.",
            "The plan already proves value and does not forecast new structural cost.",
            [
                "Apply the planned change exactly as rehearsed.",
                "Run verify against this run id.",
                "Accept the change only if resolved findings disappear and no new findings appear.",
            ],
            common_avoid,
            [
                "Skip additional redesign unless verify produces new findings.",
                "Skip extra review loops when the proof is a direct resolved finding.",
            ],
            [
                "Verify reports the expected resolved findings.",
                "Verify reports no unpredicted new findings.",
            ],
        )
    if mode == "verify" and new:
        return _path(
            "STOP_AND_MINIMAL_FIX",
            "The fastest path is a narrow fix for the new observed findings before this state becomes baseline.",
            "Accepting a bad baseline compounds future work; a narrow fix now is cheaper than later cleanup.",
            [
                "Do not broaden scope.",
                "Fix only the subjects behind new findings: " + ", ".join(new),
                "Run verify again against the same baseline.",
            ],
            common_avoid + ["Do not accept this snapshot as baseline while new findings are open."],
            [
                "Skip baseline promotion while new findings are open.",
                "Skip broad cleanup until the new finding subject is fixed or accepted.",
            ],
            [
                "The next verify run has no new findings against the same baseline.",
                "The fixed subject no longer appears in unresolved findings.",
            ],
        )
    if still_open and decision in {"WARN", "FAIL"}:
        return _path(
            "MINIMAL_FIX_OR_ACCEPT",
            "The fastest path is to either fix or explicitly accept the still-open findings before adding more work.",
            "Adding new work on top of unresolved structural debt hides the shortest path.",
            [
                "Review still-open findings: " + ", ".join(still_open),
                "Choose one narrow fix or one explicit acceptance decision.",
                "Run verify or inspect after that single decision.",
            ],
            common_avoid + ["Do not stack new execution work on top of unresolved structure debt."],
            [
                "Skip new feature work until the still-open findings have a fix or acceptance decision.",
                "Skip multi-issue cleanup; handle one structural decision at a time.",
            ],
            [
                "The selected finding is either gone or explicitly accepted by policy/assertion.",
                "The next report shows fewer still-open findings or a documented acceptance.",
            ],
        )
    if risk_level in {"high", "critical"}:
        return _path(
            "HUMAN_DECISION_GATE",
            "The shortest feasible path requires a human decision because the compressed risk is high.",
            "A quick human approve/reject/split decision is cheaper than letting a high-risk path run automatically.",
            [
                "Review the risk section.",
                "Approve, reject, or split the path before execution.",
                "Run the smallest approved slice next.",
            ],
            common_avoid,
            [
                "Skip autonomous execution while risk is high or critical.",
                "Skip broad implementation until a human chooses approve, reject, or split.",
            ],
            [
                "The approval decision is recorded.",
                "The next run operates only on the approved slice.",
            ],
        )
    return _path(
        "FAST_TRACK",
        "No structural reason blocks the short path; proceed with the smallest intended change and verify once.",
        "No projected findings or high-risk signals justify a longer workflow.",
        [
            "Apply the smallest intended change.",
            "Run verify or inspect once after the change.",
            "Use the resulting snapshot as the next baseline.",
        ],
        common_avoid,
        [
            "Skip Microcosm escalation if the change remains small and findings stay empty.",
            "Skip extra review loops unless the post-change report produces findings.",
        ],
        [
            "Post-change inspect or verify reports PASS/WARN without new high-risk findings.",
            "The resulting snapshot is available for the next decision.",
        ],
    )


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


def _path(decision, summary, why, steps, avoid, skip_conditions, proof_needed):
    return {
        "decision": decision,
        "summary": summary,
        "why_this_is_fastest": why,
        "compressed_steps": [
            {"id": "path.step.{}".format(index), "action": step}
            for index, step in enumerate(steps, start=1)
        ],
        "avoid_cumbersome_flow": avoid,
        "skip_conditions": skip_conditions,
        "proof_needed_after_execution": proof_needed,
    }


def _path_summary(path):
    if not path:
        return "No minimum path decision was produced."
    return "{}: {}".format(path.get("decision"), path.get("summary"))


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

def planned_events(plan):
    events = []
    for index, action in enumerate((plan or {}).get("actions", []), start=1):
        subject_ref = _action_subject(action)
        events.append({
            "id": "event.plan-action.{}".format(index),
            "kind": "planned-change",
            "sequence": index,
            "action_kind": action.get("kind"),
            "subject_ref": subject_ref,
            "summary": _action_summary(action, subject_ref),
            "evidence_level": "E2",
            "confidence": 0.72,
        })
    return events


def observed_events(verify_diff):
    events = []
    geometry = (verify_diff or {}).get("geometry", {})
    finding_delta = (verify_diff or {}).get("findings", {})
    sequence = 1
    for kind, refs in (
        ("node-added", geometry.get("added_nodes", [])),
        ("node-deleted", geometry.get("deleted_nodes", [])),
        ("edge-added", geometry.get("added_edges", [])),
        ("edge-deleted", geometry.get("deleted_edges", [])),
        ("finding-resolved", finding_delta.get("resolved", [])),
        ("finding-new", finding_delta.get("new", [])),
        ("finding-still-open", finding_delta.get("still_open", [])),
    ):
        for ref in refs:
            events.append({
                "id": "event.verify.{}".format(sequence),
                "kind": kind,
                "sequence": sequence,
                "subject_ref": ref,
                "summary": "{}: {}".format(kind, ref),
                "evidence_level": "E3",
                "confidence": 0.9,
            })
            sequence += 1
    return events


def make_transition(transition_id, from_state, to_state, event_refs, geometry_delta, finding_delta, relation):
    return {
        "id": transition_id,
        "relation": relation,
        "from_state": from_state,
        "to_state": to_state,
        "event_refs": list(event_refs),
        "geometry_delta": geometry_delta or {},
        "finding_delta": finding_delta or {},
    }


def _action_subject(action):
    if not isinstance(action, dict):
        return "change-plan"
    if isinstance(action.get("edge"), dict):
        return action["edge"].get("id") or _edge_match_subject(action["edge"])
    if isinstance(action.get("node"), dict):
        return action["node"].get("id") or "planned-node"
    if action.get("id"):
        return action.get("id")
    if isinstance(action.get("match"), dict):
        return _edge_match_subject(action["match"])
    return action.get("kind") or "change-plan"


def _edge_match_subject(edge):
    return "{}-{}-{}".format(edge.get("from", "?"), edge.get("relation", "?"), edge.get("to", "?"))


def _action_summary(action, subject_ref):
    kind = action.get("kind") if isinstance(action, dict) else "unknown"
    if kind in {"add_edge", "remove_edge"}:
        edge = action.get("edge") or action.get("match") or {}
        return "{} {} -> {} ({})".format(kind, edge.get("from", "?"), edge.get("to", "?"), edge.get("relation", "?"))
    if kind in {"add_node", "remove_node"}:
        return "{} {}".format(kind, subject_ref)
    return "{} {}".format(kind or "unknown", subject_ref)

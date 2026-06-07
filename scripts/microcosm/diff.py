import json
from pathlib import Path
from .validate import stable_finding_id


def _id_set(coll):
    return {item.get("id") for item in coll or [] if item.get("id")}


def _normalize_finding_id(finding):
    if not isinstance(finding, dict):
        return finding
    if not (finding.get("category") and finding.get("subject_ref") is not None):
        return finding
    new_id = stable_finding_id(finding.get("category"), finding.get("subject_ref"), finding.get("expected"), finding.get("actual"))
    normalized = dict(finding)
    normalized["id"] = new_id
    return normalized


def geometry_diff(before, after):
    """Compute deterministic structural diff between two MIR snapshots.

    Inputs are dicts with `nodes` and `edges` lists. Returns node/edge add/delete
    and a fingerprint of nodes that were touched (added, deleted, or used by a
    changed edge).
    """
    before_nodes = _id_set(before.get("nodes"))
    after_nodes = _id_set(after.get("nodes"))
    before_edges = _id_set(before.get("edges"))
    after_edges = _id_set(after.get("edges"))
    added_nodes = sorted(after_nodes - before_nodes)
    deleted_nodes = sorted(before_nodes - after_nodes)
    added_edges = sorted(after_edges - before_edges)
    deleted_edges = sorted(before_edges - after_edges)
    touched_nodes = set()
    for edge_id in added_edges + deleted_edges:
        prefix = edge_id.split(".", 1)[-1]
        for piece in prefix.split("-"):
            if piece:
                touched_nodes.add(piece)
    return {
        "added_nodes": added_nodes,
        "deleted_nodes": deleted_nodes,
        "added_edges": added_edges,
        "deleted_edges": deleted_edges,
        "touched_node_tokens": sorted(touched_nodes),
    }


def findings_diff(before_findings, after_findings):
    """Split findings into resolved, new, and still-open sets."""
    before = {_normalize_finding_id(f).get("id") for f in before_findings or []}
    after = {_normalize_finding_id(f).get("id") for f in after_findings or []}
    resolved = sorted(before - after)
    new = sorted(after - before)
    still_open = sorted(before & after)
    return {"resolved": resolved, "new": new, "still_open": still_open}


def compare_snapshots(before_path, after):
    before = json.loads(Path(before_path).read_text(encoding="utf-8"))
    gdiff = geometry_diff(before, after)
    fdiff = findings_diff(before.get("findings", []), after.get("findings", []))
    return {
        "before_run": before.get("meta", {}).get("run_id"),
        "before_generated_at": before.get("meta", {}).get("generated_at"),
        "before_snapshot": str(before_path),
        "after_run": after.get("meta", {}).get("run_id"),
        "after_generated_at": after.get("meta", {}).get("generated_at"),
        "geometry": gdiff,
        "findings": fdiff,
    }

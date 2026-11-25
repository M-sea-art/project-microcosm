def summarize_state(state_id, role, mir):
    """Return a compact, deterministic state snapshot for temporal reports."""
    meta = mir.get("meta", {})
    findings = mir.get("findings", [])
    return {
        "id": state_id,
        "role": role,
        "run_id": meta.get("run_id"),
        "generated_at": meta.get("generated_at"),
        "node_count": len(mir.get("nodes", [])),
        "edge_count": len(mir.get("edges", [])),
        "observation_count": len(mir.get("observations", [])),
        "assertion_count": len(mir.get("assertions", [])),
        "policy_count": len(mir.get("policies", [])),
        "finding_count": len(findings),
        "finding_refs": sorted(
            f.get("id") for f in findings if isinstance(f, dict) and f.get("id")
        ),
    }

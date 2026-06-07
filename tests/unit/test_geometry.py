from microcosm.geometry.engine import run_invariants

def test_forbidden_edge():
    mir={"edges":[{"id":"edge.executor-memory","from":"agent.executor","to":"memory.long-term","relation":"writes","evidence_refs":["e1"]}]}
    findings=run_invariants(mir,[{"operator":"forbidden-edge","match":{"from":"agent.executor","to":"memory.long-term","relation":"writes"}}])
    assert findings and findings[0]["category"] == "authority-violation"

def test_single_writer():
    mir={"edges":[{"id":"e1","from":"svc.a","to":"store.x","relation":"writes","evidence_refs":["ev1"]},{"id":"e2","from":"svc.b","to":"store.x","relation":"writes","evidence_refs":["ev2"]}]}
    findings=run_invariants(mir,[{"operator":"single-writer","target":"store.x","allowed_writers":["svc.a"]}])
    assert findings and findings[0]["category"] == "multiple-writers"

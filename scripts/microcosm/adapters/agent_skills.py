from pathlib import Path

from microcosm.evidence import make_evidence
from microcosm.normalize import edge_id, node_id
from .base import Adapter, iter_project_files


class AgentSkillsAdapter(Adapter):
    name = "agent-skills"

    def available(self, project_root):
        return any(path.name in {"SKILL.md", "AGENTS.md"} for path in iter_project_files(project_root, {".md"}))

    def scan(self, project_root):
        root = Path(project_root).resolve()
        nodes = []
        edges = []
        observations = []
        evidence = []
        inferred = []

        for path in iter_project_files(root, {".md"}):
            if path.name not in {"SKILL.md", "AGENTS.md"}:
                continue
            rel = path.relative_to(root).as_posix()
            kind = "skill" if path.name == "SKILL.md" else "agent"
            name = path.parent.name if path.parent != root else root.name
            nid = node_id(kind, name)
            ev = make_evidence(self.name, rel, level="E2", confidence=0.86, kind="agent-manifest")
            evidence.append(ev)
            nodes.append({
                "id": nid,
                "kind": kind,
                "name": name,
                "attributes": {"manifest": rel, "format": path.name},
                "evidence_refs": [ev["id"]],
            })
            observations.append({
                "id": "observation." + nid,
                "layer": "configuration",
                "subject_ref": nid,
                "status": "observed",
                "evidence_refs": [ev["id"]],
            })
            eid = edge_id("project.root", "contains", nid)
            edges.append({
                "id": eid,
                "from": "project.root",
                "to": nid,
                "relation": "contains",
                "attributes": {"source": rel},
                "evidence_refs": [ev["id"]],
            })
            observations.append({
                "id": "observation." + eid,
                "layer": "configuration",
                "subject_ref": eid,
                "status": "observed",
                "evidence_refs": [ev["id"]],
            })
            inferred.append({
                "id": nid,
                "kind": kind,
                "name": name,
                "rule_id": "AGENT-MANIFEST-001",
                "confidence": 0.86,
                "reason": path.name + " declares an agent-facing entry point",
                "evidence_refs": [ev["id"]],
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "observations": observations,
            "evidence": evidence,
            "inferred": inferred,
            "proposed": [],
        }

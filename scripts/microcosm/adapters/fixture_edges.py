import json
from pathlib import Path
from .base import Adapter


class FixtureEdgesAdapter(Adapter):
    name = "fixture-edges"

    def available(self, project_root):
        return (Path(project_root) / "edges.microcosm.json").exists()

    def scan(self, project_root):
        path = Path(project_root) / "edges.microcosm.json"
        edges = json.loads(path.read_text(encoding="utf-8"))
        evidence = []
        observations = []
        for edge in edges:
            refs = edge.get("evidence_refs") or ["evidence.fixture." + edge["id"]]
            edge["evidence_refs"] = refs
            for ref in refs:
                evidence.append({
                    "id": ref,
                    "kind": "fixture-edge",
                    "level": "E3",
                    "source": {"path": "edges.microcosm.json"},
                    "collector": {"adapter": self.name, "version": "0.1.0"},
                    "confidence": 0.99
                })
            observations.append({
                "id": "observation." + edge["id"],
                "layer": "static",
                "subject_ref": edge["id"],
                "status": "observed",
                "evidence_refs": refs
            })
        return {"nodes": [], "edges": edges, "observations": observations, "evidence": evidence, "inferred": [], "proposed": []}

import re
from pathlib import Path
from microcosm.evidence import make_evidence
from microcosm.normalize import edge_id
from .base import Adapter, iter_project_files
IMPORT_RE = re.compile(r"(?:import\s+.*?from\s+|require\()[\"']([^\"']+)[\"']")
class NodeImportsAdapter(Adapter):
    name = "node-imports"
    def available(self, project_root):
        root = Path(project_root).resolve()
        return (root / "package.json").exists() or next(
            iter_project_files(root, {".js", ".ts", ".tsx"}), None
        ) is not None
    def scan(self, project_root):
        root = Path(project_root).resolve(); nodes=[]; edges=[]; observations=[]; evidence=[]
        for file in iter_project_files(root, {".js", ".ts", ".tsx"}):
            rel = file.relative_to(root).as_posix(); mod = "module." + rel.replace("/", ".")
            ev = make_evidence(self.name, rel, level="E3", confidence=0.90, kind="node-module"); evidence.append(ev)
            nodes.append({"id": mod, "kind": "module", "name": rel, "attributes": {"language": "javascript-typescript"}, "evidence_refs": [ev["id"]]})
            text = file.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                for m in IMPORT_RE.finditer(line):
                    dst = "module." + m.group(1); evid = make_evidence(self.name, rel, level="E3", line_start=i, confidence=0.90, kind="import"); evidence.append(evid)
                    eid = edge_id(mod, "imports", dst)
                    edges.append({"id": eid, "from": mod, "to": dst, "relation": "imports", "attributes": {}, "evidence_refs": [evid["id"]]})
                    observations.append({"id": "observation." + eid, "layer": "static", "subject_ref": eid, "status": "observed", "evidence_refs": [evid["id"]]})
        return {"nodes": nodes, "edges": edges, "observations": observations, "evidence": evidence, "inferred": [], "proposed": []}

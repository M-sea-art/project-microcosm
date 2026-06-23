import json
from pathlib import Path

from microcosm.evidence import make_evidence
from microcosm.normalize import edge_id, node_id
from .base import Adapter, iter_project_files


MCP_CONFIG_NAMES = {"mcp.json", ".mcp.json", "mcp.config.json"}


class McpConfigAdapter(Adapter):
    name = "mcp-config"

    def available(self, project_root):
        return any(path.name in MCP_CONFIG_NAMES for path in iter_project_files(project_root, {".json"}))

    def scan(self, project_root):
        root = Path(project_root).resolve()
        nodes = []
        edges = []
        observations = []
        evidence = []
        inferred = []

        for path in iter_project_files(root, {".json"}):
            if path.name not in MCP_CONFIG_NAMES:
                continue
            rel = path.relative_to(root).as_posix()
            ev = make_evidence(self.name, rel, level="E2", confidence=0.82, kind="mcp-config")
            evidence.append(ev)
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                inferred.append({
                    "id": node_id("mcp-server", path.stem + "-unparsed"),
                    "kind": "mcp-server",
                    "name": path.name,
                    "rule_id": "MCP-CONFIG-UNPARSED",
                    "confidence": 0.30,
                    "reason": "MCP config exists but could not be parsed as JSON",
                    "evidence_refs": [ev["id"]],
                })
                continue

            servers = payload.get("mcpServers") or payload.get("servers") or {}
            if isinstance(servers, list):
                servers = {str(index): item for index, item in enumerate(servers)}
            if not isinstance(servers, dict):
                servers = {}

            for server_name, server_config in sorted(servers.items()):
                nid = node_id("mcp-server", server_name)
                command = None
                if isinstance(server_config, dict):
                    command = server_config.get("command") or server_config.get("url")
                nodes.append({
                    "id": nid,
                    "kind": "mcp-server",
                    "name": str(server_name),
                    "attributes": {"config": rel, "command": command},
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

        return {
            "nodes": nodes,
            "edges": edges,
            "observations": observations,
            "evidence": evidence,
            "inferred": inferred,
            "proposed": [],
        }

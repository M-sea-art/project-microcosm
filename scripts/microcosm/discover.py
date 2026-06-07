from .adapters.generic_repo import GenericRepoAdapter
from .adapters.python_ast import PythonAstAdapter
from .adapters.node_imports import NodeImportsAdapter
from .adapters.fixture_edges import FixtureEdgesAdapter

ADAPTERS = [GenericRepoAdapter(), FixtureEdgesAdapter(), PythonAstAdapter(), NodeImportsAdapter()]


def active_adapters(project_root):
    return [adapter for adapter in ADAPTERS if adapter.available(project_root)]


def scan_project(project_root):
    merged = {"nodes": [], "edges": [], "observations": [], "evidence": [], "inferred": [], "proposed": [], "active_adapters": []}
    seen = {"nodes": set(), "edges": set(), "observations": set(), "evidence": set()}
    for adapter in active_adapters(project_root):
        merged["active_adapters"].append(adapter.name)
        data = adapter.scan(project_root)
        for key in ["nodes", "edges", "observations", "evidence"]:
            for item in data.get(key, []):
                item_id = item.get("id")
                if item_id and item_id in seen[key]:
                    continue
                if item_id:
                    seen[key].add(item_id)
                merged[key].append(item)
        merged["inferred"].extend(data.get("inferred", []))
        merged["proposed"].extend(data.get("proposed", []))
    return merged

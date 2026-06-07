import json
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from .config import load_assertions, load_policies
from .versioning import MICROCOSM_VERSION, SCHEMA_VERSION, GENERATOR_VERSION
from .discover import scan_project
from .reporting import write_reports


def new_run_id():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return "run-{}-{}".format(timestamp, uuid4().hex[:12])


def build_mir(project_root, run_id=None):
    run_id = run_id or new_run_id()
    scan = scan_project(project_root)
    mir = {
        "meta": {
            "microcosm_version": MICROCOSM_VERSION,
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator_version": GENERATOR_VERSION,
        },
        "project": {"id": "project." + Path(project_root).name, "name": Path(project_root).name, "root": str(project_root)},
        "nodes": scan["nodes"],
        "edges": scan["edges"],
        "assertions": load_assertions(project_root),
        "observations": scan["observations"],
        "policies": load_policies(project_root),
        "evidence": scan["evidence"],
        "findings": [],
    }
    return mir, scan


def bootstrap(project_root):
    mir, scan = build_mir(project_root)
    base = Path(project_root) / ".microcosm"
    for sub in ["meta", "config", "mir", "snapshots", "traces", "evidence"]:
        (base / sub).mkdir(parents=True, exist_ok=True)
    project_json = base / "meta" / "project.json"
    if not project_json.exists():
        project_json.write_text(json.dumps(mir["project"], indent=2, ensure_ascii=False), encoding="utf-8")
    project_yaml = "project:\n  id: {}\n  name: {}\naccepted_proposals: []\n".format(mir["project"]["id"], mir["project"]["name"])
    project_config = base / "config" / "project.yaml"
    if not project_config.exists():
        project_config.write_text(project_yaml, encoding="utf-8")
    invariants_yaml = "invariants:\n  - operator: no-cycle\n    relation: [imports, depends-on]\n"
    invariants_config = base / "config" / "invariants.yaml"
    if not invariants_config.exists():
        invariants_config.write_text(invariants_yaml, encoding="utf-8")
    if not (base / "config" / "assertions.json").exists():
        (base / "config" / "assertions.json").write_text('{"assertions": []}', encoding="utf-8")
    if not (base / "config" / "policies.json").exists():
        (base / "config" / "policies.json").write_text('{"policies": []}', encoding="utf-8")
    report_dir = write_reports(project_root, mir["meta"]["run_id"], mir, scan["active_adapters"], scan["inferred"], scan["proposed"])
    (base / "mir" / "bootstrap-inferred.json").write_text(json.dumps({"inferred": scan["inferred"], "proposed": scan["proposed"]}, indent=2, ensure_ascii=False), encoding="utf-8")
    return mir, scan, report_dir

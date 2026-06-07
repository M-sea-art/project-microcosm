import json
from pathlib import Path
from .bootstrap import build_mir
from .config import load_invariants
from .diff import compare_snapshots
from .geometry.engine import run_invariants
from .reporting import write_reports
from .versioning import MICROCOSM_VERSION, SCHEMA_VERSION, GENERATOR_VERSION


def resolve_baseline_snapshot(project_root, against):
    base = Path(project_root) / ".microcosm" / "snapshots"
    if not against:
        snapshots = sorted(base.glob("run-*.json"))
        if not snapshots:
            raise FileNotFoundError("No baseline snapshot found; run inspect first or pass --against <run-id>.")
        return snapshots[-1]
    candidate = base / (against + ".json")
    if not candidate.exists():
        raise FileNotFoundError("Baseline snapshot not found: " + str(candidate))
    baseline = json.loads(candidate.read_text(encoding="utf-8"))
    expected_version = baseline.get("meta", {}).get("microcosm_version")
    if expected_version and expected_version != MICROCOSM_VERSION:
        raise RuntimeError("Baseline microcosm_version mismatch: expected {} got {}".format(
            MICROCOSM_VERSION, expected_version))
    expected_schema = baseline.get("meta", {}).get("schema_version")
    if expected_schema and expected_schema != SCHEMA_VERSION:
        raise RuntimeError("Baseline schema_version mismatch: expected {} got {}".format(
            SCHEMA_VERSION, expected_schema))
    return candidate


def run_verify(project_root, against=None, report_unresolved=None):
    baseline_path = resolve_baseline_snapshot(project_root, against)
    mir, scan = build_mir(project_root)
    invariants = load_invariants(project_root)
    mir["findings"] = run_invariants(mir, invariants)
    diff = compare_snapshots(baseline_path, mir)
    report_dir = write_reports(
        project_root,
        mir["meta"]["run_id"],
        mir,
        scan["active_adapters"],
        scan["inferred"],
        scan["proposed"],
        unresolved=report_unresolved,
        verify_diff=diff,
    )
    return mir, scan, diff, report_dir

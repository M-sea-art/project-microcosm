import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))

import unittest

from microcosm.validate import (
    stable_finding_id, compute_band, validate_mir, write_validation_report,
)
from microcosm.reporting import compute_next_actions


class BandTests(unittest.TestCase):
    def test_band_thresholds(self):
        self.assertEqual(compute_band(0.95), "confirmed")
        self.assertEqual(compute_band(0.85), "confirmed")
        self.assertEqual(compute_band(0.70), "probable")
        self.assertEqual(compute_band(0.50), "concern")
        self.assertEqual(compute_band(0.10), "hypothesis")


class StableIdTests(unittest.TestCase):
    def test_is_deterministic(self):
        a = stable_finding_id("authority-violation", "edge.x", {"forbidden_edge": {"from": "a", "to": "b"}}, {"observed_edge": "edge.x"})
        b = stable_finding_id("authority-violation", "edge.x", {"forbidden_edge": {"from": "a", "to": "b"}}, {"observed_edge": "edge.x"})
        self.assertEqual(a, b)

    def test_ignores_extra_attributes(self):
        a = stable_finding_id("authority-violation", "edge.x", {"forbidden_edge": {"from": "a", "to": "b"}}, {"observed_edge": "edge.x"})
        b = stable_finding_id("authority-violation", "edge.x", {"forbidden_edge": {"from": "a", "to": "b"}}, {"observed_edge": "edge.x", "extra": "noise"})
        self.assertEqual(a, b)


class ValidateTests(unittest.TestCase):
    def test_detects_invalid_kind(self):
        mir = {
            "meta": {"microcosm_version": "0.1.0", "schema_version": "mir/v0.1", "run_id": "r", "generated_at": "t", "generator_version": "k"},
            "project": {},
            "nodes": [{"id": "n1", "kind": "alien-kind", "name": "x", "attributes": {}, "evidence_refs": ["e1"]}],
            "edges": [],
            "assertions": [], "observations": [], "policies": [],
            "evidence": [{"id": "e1", "kind": "src", "level": "E3", "source": {}, "collector": {"adapter": "x", "version": "0.1.0"}, "confidence": 1.0}],
            "findings": [],
        }
        ok, issues, delta, _ = validate_mir(mir)
        self.assertTrue(any(i.get("code") == "node-kind-invalid" for i in issues))
        self.assertTrue(any(f.get("category") == "schema-mismatch" for f in delta))

    def test_demotes_evidence_missing_finding(self):
        mir = {
            "meta": {"microcosm_version": "0.1.0", "schema_version": "mir/v0.1", "run_id": "r", "generated_at": "t", "generator_version": "k"},
            "project": {},
            "nodes": [], "edges": [], "assertions": [], "observations": [], "policies": [],
            "evidence": [],
            "findings": [{
                "id": "x", "category": "cyclic-dependency", "severity": "high", "band": "confirmed",
                "confidence": 0.99, "subject_ref": "edge.x", "expected": {}, "actual": {"cycle": ["a", "b", "a"]},
                "evidence_refs": [], "message": "no evidence",
            }],
        }
        ok, issues, delta, normalized = validate_mir(mir)
        self.assertTrue(any(i.get("code") == "evidence-required" for i in issues))
        f = normalized[0]
        self.assertEqual(f["band"], "hypothesis")
        self.assertEqual(f["severity"], "low")
        self.assertTrue(f["id"].startswith("finding.cyclic-dependency."))

    def test_detects_unresolved_subject_ref(self):
        mir = {
            "meta": {"microcosm_version": "0.1.0", "schema_version": "mir/v0.1", "run_id": "r", "generated_at": "t", "generator_version": "k"},
            "project": {},
            "nodes": [], "edges": [], "assertions": [], "observations": [], "policies": [],
            "evidence": [],
            "findings": [{
                "id": "x", "category": "cyclic-dependency", "severity": "high", "band": "confirmed",
                "confidence": 0.99, "subject_ref": "ghost", "expected": {}, "actual": {"cycle": ["a", "b"]},
                "evidence_refs": ["e1"], "message": "ghost",
            }],
        }
        ok, issues, delta, _ = validate_mir(mir)
        self.assertTrue(any(i.get("code") == "subject-ref-unresolved" and i.get("kind") == "finding" for i in issues))

    def test_write_validation_report(self):
        import json, tempfile, pathlib
        td = pathlib.Path(tempfile.mkdtemp())
        mir = {
            "meta": {"microcosm_version": "0.1.0", "schema_version": "mir/v0.1", "run_id": "r1", "generated_at": "t", "generator_version": "k"},
            "project": {}, "nodes": [], "edges": [], "assertions": [], "observations": [], "policies": [],
            "evidence": [], "findings": [],
        }
        ok, issues, delta, _ = validate_mir(mir)
        write_validation_report(str(td), "r1", ok, issues, delta)
        report = json.loads((td / ".microcosm" / "reports" / "r1" / "validation.json").read_text(encoding="utf-8"))
        self.assertEqual(report["run_id"], "r1")
        self.assertIn("issues", report)


class NextActionTests(unittest.TestCase):
    def test_routes_authority_violation_to_human_agent_decision_expert(self):
        actions = compute_next_actions([{
            "id": "finding.authority-violation.abc",
            "category": "authority-violation",
            "severity": "critical",
            "message": "forbidden write",
        }], [], "FAIL")
        self.assertEqual(actions[0]["priority"], "P0")
        self.assertEqual(actions[0]["owner_expert"], "human-agent-decision-expert")
        self.assertEqual(actions[0]["recommended_mode"], "plan-change")
        self.assertEqual(actions[0]["temporal_pressure"], "immediate")
        self.assertIn("unauthorized path", actions[0]["deferred_consequence"])
        self.assertTrue(actions[0]["requires_human_approval"])


if __name__ == "__main__":
    unittest.main()

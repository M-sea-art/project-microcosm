import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))

import unittest

from microcosm.temporal.operators import forecast_from_findings


class TemporalForecastTests(unittest.TestCase):
    def test_low_confidence_projection_stays_hypothesis(self):
        finding = {
            "id": "finding.unverified-inference.low",
            "category": "unverified-inference",
            "severity": "low",
            "band": "hypothesis",
            "confidence": 0.2,
            "subject_ref": "edge.future",
            "message": "weak future signal",
        }
        forecast = forecast_from_findings(
            "plan-change",
            "WARN",
            {"level": "low"},
            {"resolved": [], "new": [finding], "still_open": []},
            [finding],
        )
        self.assertEqual(forecast["band"], "hypothesis")
        self.assertEqual(forecast["confidence"], 0.2)
        self.assertEqual(forecast["smallest_fastest_path"]["decision"], "SPLIT_OR_REVISE_BEFORE_BUILD")
        self.assertIn("projected findings", forecast["minimum_safe_next_step"])


if __name__ == "__main__":
    unittest.main()

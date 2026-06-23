import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))

import unittest

from check_rule_copies import check_rule_copies


class RuleCopyTests(unittest.TestCase):
    def test_compact_rule_surfaces_do_not_drift(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        payload = check_rule_copies(root)
        self.assertTrue(payload["ok"], payload["issues"])


if __name__ == "__main__":
    unittest.main()

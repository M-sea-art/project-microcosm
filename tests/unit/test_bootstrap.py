import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))

from microcosm.bootstrap import bootstrap, new_run_id


class BootstrapTests(unittest.TestCase):
    def test_run_ids_are_unique_for_back_to_back_runs(self):
        self.assertNotEqual(new_run_id(), new_run_id())

    def test_bootstrap_preserves_existing_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_dir = root / ".microcosm" / "config"
            config_dir.mkdir(parents=True)
            project_config = config_dir / "project.yaml"
            invariants_config = config_dir / "invariants.yaml"
            project_config.write_text("project:\n  id: custom\n", encoding="utf-8")
            invariants_config.write_text("invariants: []\n", encoding="utf-8")

            bootstrap(root)

            self.assertEqual(project_config.read_text(encoding="utf-8"), "project:\n  id: custom\n")
            self.assertEqual(invariants_config.read_text(encoding="utf-8"), "invariants: []\n")

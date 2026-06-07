import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))

from microcosm.adapters.generic_repo import GenericRepoAdapter
from microcosm.adapters.python_ast import PythonAstAdapter


class AdapterExclusionTests(unittest.TestCase):
    def test_scanners_skip_generated_and_secret_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("import json\n", encoding="utf-8")
            (root / ".venv").mkdir()
            (root / ".venv" / "hidden.py").write_text("import secrets\n", encoding="utf-8")
            (root / ".ssh").mkdir()
            (root / ".ssh" / "SKILL.md").write_text("secret\n", encoding="utf-8")

            python_scan = PythonAstAdapter().scan(root)
            generic_scan = GenericRepoAdapter().scan(root)

            module_names = {node["name"] for node in python_scan["nodes"]}
            inferred_names = {item["name"] for item in generic_scan["inferred"]}
            self.assertEqual(module_names, {"src/main.py"})
            self.assertNotIn(".ssh", inferred_names)

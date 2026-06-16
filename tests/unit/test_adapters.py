import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))

from microcosm.adapters.generic_repo import GenericRepoAdapter
from microcosm.adapters.python_ast import PythonAstAdapter
from microcosm.adapters.agent_skills import AgentSkillsAdapter
from microcosm.adapters.mcp_config import McpConfigAdapter


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

    def test_agent_skills_adapter_observes_skill_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / "SKILL.md").write_text("---\nname: sample\n---\n", encoding="utf-8")

            scan = AgentSkillsAdapter().scan(root)

            self.assertIn("skill." + root.name.lower(), {node["id"] for node in scan["nodes"]})
            self.assertTrue(any(edge["relation"] == "contains" for edge in scan["edges"]))

    def test_mcp_config_adapter_observes_servers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / "mcp.json").write_text(
                '{"mcpServers":{"files":{"command":"python"}}}',
                encoding="utf-8",
            )

            scan = McpConfigAdapter().scan(root)

            self.assertIn("mcp-server.files", {node["id"] for node in scan["nodes"]})
            self.assertTrue(any(edge["to"] == "mcp-server.files" for edge in scan["edges"]))

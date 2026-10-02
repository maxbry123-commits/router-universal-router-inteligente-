import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts import in_scope, path, validate


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.chain = {
            "schema": "yaiwes.chain/v2", "request_id": "req-001",
            "agent": {"id": "grok", "framework": "openai-agents"},
            "input_block": "Fix the bug", "write_scope": ["src/component"],
            "tests": [["python", "-m", "unittest"]],
            "steps": [{"id": "read", "task": "Read code"}, {"id": "fix", "task": "Fix code"}],
            "edges": [["read", "fix"]],
        }

    def test_dag(self):
        self.assertEqual(validate(self.chain, "grok", "req-001"), ["read", "fix"])
        self.chain["edges"].append(["fix", "read"])
        with self.assertRaisesRegex(ValueError, "CYCLE"):
            validate(self.chain, "grok", "req-001")

    def test_scope_and_control_paths(self):
        for bad in ["../x", "/tmp/x", ".github/workflows", "ops/yaiwes/x",
                    "router inteligente universal/agents-yaiwes/x", "a//b", "src/.env"]:
            with self.subTest(path=bad), self.assertRaises(ValueError):
                path(bad)
        self.assertTrue(in_scope("src/component/file.py", ["src/component"]))
        self.assertFalse(in_scope("src/component-evil/file.py", ["src/component"]))

    def test_request_identity_and_edges(self):
        with self.assertRaisesRegex(ValueError, "INVALID_REQUEST"):
            validate(self.chain, "grok", "another")
        self.chain["edges"] = [["missing", "read"]]
        with self.assertRaisesRegex(ValueError, "INVALID_EDGES"):
            validate(self.chain, "grok", "req-001")


if __name__ == "__main__":
    unittest.main()

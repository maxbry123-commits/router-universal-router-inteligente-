import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
stub = types.ModuleType("agents")
stub.Agent = object
stub.Runner = object
stub.OpenAIChatCompletionsModel = object
stub.function_tool = lambda func: func
stub.set_tracing_disabled = lambda _: None
sys.modules.setdefault("agents", stub)
from supervisor import changes, snapshot, tests_in_workspace


class SupervisorTests(unittest.TestCase):
    def test_snapshot_detects_mutation_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "code.py").write_text("before")
            before = snapshot(root)
            (root / "code.py").write_text("after")
            self.assertEqual(changes(before, snapshot(root)), {"code.py"})
            (root / "linked.py").symlink_to(root / "code.py")
            with self.assertRaisesRegex(RuntimeError, "UNSAFE_WORKSPACE_ENTRY"):
                snapshot(root)

    def test_tests_cannot_write_outside_private_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            project = workspace / "project"
            project.mkdir(parents=True)
            outside = Path(directory) / "outside.txt"
            outside.write_text("unchanged")
            code = f"from pathlib import Path; Path({str(outside)!r}).write_text('bad')"
            tests = {"tests": [[sys.executable, "-c", code]]}
            records = tests_in_workspace(tests, project)
            self.assertNotEqual(records[0]["exit_code"], 0)
            self.assertEqual(outside.read_text(), "unchanged")

    def test_tests_write_into_workspace_is_detectable(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            project = workspace / "project"
            project.mkdir(parents=True)
            before = snapshot(project)
            tests = {"tests": [[sys.executable, "-c", "open('created.txt','w').write('ok')"]]}
            records = tests_in_workspace(tests, project)
            self.assertEqual(records[0]["exit_code"], 0, records[0]["output"])
            self.assertEqual(changes(before, snapshot(project)), {"created.txt"})


if __name__ == "__main__":
    unittest.main()

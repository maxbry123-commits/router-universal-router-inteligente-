import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class LandlockExecTests(unittest.TestCase):
    @unittest.skipUnless(platform.system() == "Linux" and platform.machine() in ("x86_64", "aarch64"), "Linux Landlock only")
    def test_sdk_can_write_workspace_but_not_checkout(self):
        script = Path(__file__).parents[1] / "landlock_exec.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            outside = root / "outside.txt"
            outside.write_text("original")
            code = (
                "from pathlib import Path; "
                "Path('inside.txt').write_text('ok'); "
                f"Path({str(outside)!r}).write_text('changed')"
            )
            proc = subprocess.run([sys.executable, str(script), str(workspace), "--",
                                   sys.executable, "-c", code], capture_output=True, text=True, timeout=15)
            self.assertEqual((workspace / "inside.txt").read_text(), "ok", proc.stderr)
            self.assertEqual(outside.read_text(), "original")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("PermissionError", proc.stderr)

    @unittest.skipUnless(platform.system() == "Linux" and platform.machine() in ("x86_64", "aarch64"), "Linux Landlock only")
    def test_truncate_is_denied_outside_workspace(self):
        script = Path(__file__).parents[1] / "landlock_exec.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            outside = root / "outside.txt"
            outside.write_text("original")
            code = f"import os; os.truncate({str(outside)!r}, 0)"
            proc = subprocess.run([sys.executable, str(script), str(workspace), "--",
                                   sys.executable, "-c", code], capture_output=True, text=True, timeout=15)
            self.assertEqual(outside.read_text(), "original")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("PermissionError", proc.stderr)


if __name__ == "__main__":
    unittest.main()

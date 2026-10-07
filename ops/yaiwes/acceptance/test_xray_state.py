"""Verify the forensics output against actual source bytes in the task branch."""

import hashlib
import json
from pathlib import Path
import subprocess
from unittest import TestCase


OUTPUT = Path("chat router/11-EVIDENCIA/delegacion-46-grok-xray/STATE.json")


class XRayStateTests(TestCase):
    def test_source_refs_are_real_and_hashes_match(self):
        state = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(state["schema"], "yaiwes.xray-state/v1")
        for field in ("observed", "expected", "present", "missing", "contradictions",
                      "not_verified", "source_refs", "artifact_sha256", "checked_at"):
            self.assertIn(field, state)
        self.assertIsInstance(state["source_refs"], list)
        self.assertGreater(len(state["source_refs"]), 0)
        self.assertIsInstance(state["artifact_sha256"], dict)
        for name in state["source_refs"]:
            self.assertIsInstance(name, str)
            self.assertFalse(name.startswith("/"))
            self.assertNotIn("..", name.split("/"))
            content = subprocess.run(["git", "show", "HEAD:" + name], capture_output=True,
                                     timeout=30, check=True).stdout
            self.assertEqual(hashlib.sha256(content).hexdigest(), state["artifact_sha256"][name])


if __name__ == "__main__":
    import unittest
    unittest.main()

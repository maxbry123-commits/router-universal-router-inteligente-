"""El boot del Space actual ya lanza Node y proxy: no duplicar el puerto 7870."""
import unittest
from unittest.mock import patch, Mock
from mvp import run


class TestBridgeManagedBySpace(unittest.TestCase):
    def test_hf_external_boot_does_not_launch_duplicate_node(self):
        with patch.object(run, "_bridge_externo", return_value=True), \
             patch.object(run.subprocess, "Popen") as popen:
            self.assertTrue(run._iniciar_bridge())
            popen.assert_not_called()

    def test_repo_only_boot_uses_existing_node_if_installed(self):
        proc = Mock()
        proc.poll.return_value = None
        before = run._BRIDGE
        try:
            run._BRIDGE = None
            with patch.object(run, "_bridge_externo", return_value=False), \
                 patch.object(run.shutil, "which", return_value="/usr/bin/node"), \
                 patch.object(run, "BRIDGE_DIR") as bridge, \
                 patch.object(run.subprocess, "Popen", return_value=proc) as popen:
                bridge.__truediv__.return_value.is_dir.return_value = True
                self.assertTrue(run._iniciar_bridge())
                popen.assert_called_once()
        finally:
            run._BRIDGE = before


if __name__ == "__main__":
    unittest.main()

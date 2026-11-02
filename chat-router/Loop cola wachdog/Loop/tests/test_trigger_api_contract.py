"""YAIWES DSL smoke: structural checks without external provider access."""
import sys
import unittest
from pathlib import Path

LOOP_ROOT = Path(__file__).resolve().parents[1]
if str(LOOP_ROOT) not in sys.path:
    sys.path.insert(0, str(LOOP_ROOT))

from nct_loop.trigger_contract import ContractError, validate_contract, validate_loop
from nct_loop.trigger_host import build_ports

class ContractSmoke(unittest.TestCase):
    def test_rechaza_json_malicioso(self):
        with self.assertRaises(ContractError):
            validate_contract({"schema": "yaiwes.trigger.v1", "id": "x"})

    def test_rechaza_loop_vacio(self):
        with self.assertRaises(ContractError):
            validate_loop([])

    def test_host_no_confia_en_browser(self):
        with self.assertRaises(ContractError):
            build_ports({"trusted_host": True, "authenticated": False})

    def test_rutas_relativas(self):
        from nct_loop.trigger_contract import _safe_path
        for p in ("../secret", "/etc/passwd", "a/../../b"):
            with self.subTest(path=p):
                with self.assertRaises(ContractError):
                    _safe_path(p)

    def test_existing_pluginhost_symlinks_resolve_inside_chat_router(self):
        chat_root = LOOP_ROOT.parents[1].resolve()
        app = chat_root / "chat" / "backend" / "mvp" / "app.py"
        self.assertEqual(app.resolve().parents[2], chat_root)
        repo_root = chat_root.parent
        self.assertTrue((repo_root / "router-mvp" / "mvp" / "app.py").is_file())
        for plug in ("nct_loop", "cola50", "watchdog48"):
            self.assertTrue((chat_root / "plugins" / plug / "plugin.py").is_file(),
                            "plugin no cableado: " + plug)
        self.assertTrue((chat_root / "plugins" / "puente_chat" / "constitucion" /
                         "CONSTITUCION-YAIWES.json").is_file())

    def test_cola_100_opt_in(self):
        from tempfile import TemporaryDirectory
        import importlib.util
        import uuid
        core = LOOP_ROOT.parent / "Cola" / "nct_addons" / "cola50" / "core.py"
        spec = importlib.util.spec_from_file_location("yaiwes_cit50_test_" + uuid.uuid4().hex, core)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tasks = [{"id": "T%03d" % i, "title": "Test", "type": "handoff",
                  "prompt": "test"} for i in range(100)]
        with TemporaryDirectory() as tmp:
            store = mod.QueueStore(Path(tmp) / "cola.db")
            q = store.create({"mode": "dsl", "title": "Test", "chat_id": "demo", "tasks": tasks})
            self.assertEqual(len(q["tasks"]), 100)
            with self.assertRaises(mod.QueueError):
                store.create({"mode": "sequential", "title": "Legacy", "chat_id": "demo", "tasks": tasks})

if __name__ == "__main__":
    unittest.main()

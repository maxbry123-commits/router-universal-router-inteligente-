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

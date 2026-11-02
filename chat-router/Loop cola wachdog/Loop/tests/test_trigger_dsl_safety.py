"""YAIWES DSL safety regressions: deadlines, exclusive claims, uncertain leases and cancel races.
Only existing QueueStore / HostPorts; no network, HF, model or secret calls.
"""
import importlib.util
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

LOOP = Path(__file__).resolve().parents[1]
COLA_CORE = LOOP.parent / "Cola" / "nct_addons" / "cola50" / "core.py"
if str(LOOP) not in sys.path:
    sys.path.insert(0, str(LOOP))

spec = importlib.util.spec_from_file_location("cola50_dsl_safety", COLA_CORE)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
from nct_loop.trigger_contract import ContractError
from nct_loop.trigger_host import build_ports


class QueueSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = core.QueueStore(self.root / "cola.db")

    def queue(self):
        q = self.store.create({"chat_id": "test", "title": "DSL",
            "mode": "dsl", "tasks": [
                {"id": "a", "title": "a", "type": "handoff"},
                {"id": "b", "title": "b", "type": "handoff"}]})
        return self.store.start(q["queue_id"], seconds=600)["queue_id"]

    def test_not_applicable_is_skipped_not_pass(self):
        qid = self.queue()
        result = self.store.skip_dsl_task(qid, "a", "NOT_APPLICABLE")
        self.assertTrue(result["skipped"])
        task = next(t for t in self.store.get(qid)["tasks"] if t["id"] == "a")
        self.assertEqual(task["status"], "skipped")
        self.assertIsNone(task["receipt_id"])
        self.assertTrue(any(x["event"] == "dsl.task.not_applicable" for x in self.store.events(qid)))

    def test_not_applicable_rejects_running_claim(self):
        qid = self.queue()
        self.store.claim_dsl_for(qid, "a")
        with self.assertRaises(core.QueueError):
            self.store.skip_dsl_task(qid, "b", "NOT_APPLICABLE")

    def test_segment_metadata_validation(self):
        from nct_loop.trigger_bridge import validate_loop_meta
        contracts = [{"id":"T01"},{"id":"T02"}]
        good = {"name":"A", "verify_on_end":True, "next_loop_id":"loop-02",
                "segments":[{"id":"phase1","name":"Arquitectura","trigger_ids":["T01"]},
                            {"id":"phase2","name":"Revision","trigger_ids":["T02"]}]}
        self.assertEqual(validate_loop_meta(good, loop_id="loop-01", contracts=contracts), good)
        with self.assertRaises(ContractError):
            validate_loop_meta({**good, "verify_on_end":"false"}, loop_id="loop-01", contracts=contracts)
        with self.assertRaises(ContractError):
            validate_loop_meta({**good, "next_loop_id":"loop-01"}, loop_id="loop-01", contracts=contracts)
        with self.assertRaises(ContractError):
            validate_loop_meta({**good, "segments":[{"id":"A","name":"A","trigger_ids":["T01"]},
                        {"id":"B","name":"B","trigger_ids":["T01"]}]}, loop_id="loop-01", contracts=contracts)
        with self.assertRaises(ContractError):
            validate_loop_meta({**good, "segments":[{"id":"A","name":"A","trigger_ids":["MISSING"]}]},
                               loop_id="loop-01", contracts=contracts)

    def test_not_applicable_and_success_can_close_loop(self):
        qid = self.queue()
        self.store.skip_dsl_task(qid,"a","NOT_APPLICABLE")
        self.assertTrue(self.store.claim_dsl_for(qid,"b")["claimed"])
        self.assertTrue(self.store.complete(qid,"b",{"verification":"PASS"}))
        self.assertEqual(self.store.get(qid)["status"],"completed")
        rows={row["id"]:row for row in self.store.get(qid)["tasks"]}
        self.assertEqual(rows["a"]["status"],"skipped")
        self.assertNotEqual(rows["a"]["status"],"succeeded")
        self.assertEqual(rows["b"]["status"],"succeeded")

    def test_success_and_not_applicable_can_close_loop(self):
        qid = self.queue()
        self.assertTrue(self.store.claim_dsl_for(qid,"a")["claimed"])
        self.assertTrue(self.store.complete(qid,"a",{"verification":"PASS"}))
        self.store.skip_dsl_task(qid,"b","NOT_APPLICABLE")
        self.assertEqual(self.store.get(qid)["status"],"completed")

    def test_one_writer_per_dsl_queue(self):
        qid = self.queue()
        self.assertTrue(self.store.claim_dsl_for(qid, "a")["claimed"])
        self.assertEqual("QUEUE_BUSY", self.store.claim_dsl_for(qid, "b")["error"])
        self.assertTrue(self.store.complete(qid, "a", {"verification": "PASS"}))
        self.assertTrue(self.store.claim_dsl_for(qid, "b")["claimed"])

    def test_deadline_prevents_new_model_call(self):
        qid = self.queue()
        with self.store.db() as con:
            con.execute("UPDATE queues SET deadline=? WHERE id=?", (time.time()-1, qid))
        self.assertEqual("QUEUE_EXPIRED", self.store.claim_dsl_for(qid, "a")["error"])
        self.assertEqual("expired", self.store.get(qid)["status"])

    def test_expired_running_lease_fail_closed(self):
        qid = self.queue()
        self.store.claim_dsl_for(qid, "a")
        with self.store.db() as con:
            con.execute("UPDATE tasks SET lease=? WHERE queue_id=? AND id=?",
                        (time.time()-1,qid,"a"))
        self.assertEqual("NEEDS_RECONCILIATION", self.store.claim_dsl_for(qid, "b")["error"])
        q = self.store.get(qid)
        self.assertEqual("failed", q["status"])
        self.assertEqual("needs_reconciliation", next(t for t in q["tasks"] if t["id"]=="a")["status"])

    def test_verify_exists_receipt_changes_with_file_contents(self):
        target = self.root / "tracked.txt"
        target.write_text("VERSION A", encoding="utf-8")
        control = types.SimpleNamespace(d={"proyectos":{"test":{"anclas":[]}},"agentes":{},"agentes_on":False},
                                        credencial=lambda *args,**kwargs:"fake")
        fake_mvp = types.ModuleType("mvp")
        fake_mvp.hf_store = types.ModuleType("hf_store")
        fake_plugins = types.ModuleType("plugins")
        fake_bridge = types.ModuleType("plugins.puente_chat")
        fake_bridge.plugin = types.SimpleNamespace(FICHAS={},RESPALDO={})
        fake_plugins.puente_chat = fake_bridge
        with patch.dict(sys.modules, {"mvp":fake_mvp,"plugins":fake_plugins,
                                      "plugins.puente_chat":fake_bridge}):
            ports = build_ports({"authenticated":True,"trusted_host":True,
                 "control":control,"banco":object(),"queue_store":self.store,
                 "watch_store":None,"root":self.root,"project_id":"test",
                 "loop_id":"x","sesion":"web-general"})
            first = ports.tool("verify_exists", {"path":"tracked.txt"}, {})
            target.write_text("VERSION B", encoding="utf-8")
            second = ports.tool("verify_exists", {"path":"tracked.txt"}, {})
        self.assertTrue(first["ok"] and second["ok"])
        self.assertNotEqual(first["evidence_ref"],second["evidence_ref"])

    def test_cancelled_task_never_reported_as_pass(self):
        qid = self.queue()
        self.store.claim_dsl_for(qid, "a")
        self.store.control(qid, "cancel")
        control = types.SimpleNamespace(d={"proyectos":{"test":{"anclas":[]}},"agentes":{},"agentes_on":False},
                                        credencial=lambda *args,**kwargs:"fake")
        fake_mvp = types.ModuleType("mvp")
        fake_mvp.hf_store = types.ModuleType("hf_store")
        fake_plugins = types.ModuleType("plugins")
        fake_bridge = types.ModuleType("plugins.puente_chat")
        fake_bridge.plugin = types.SimpleNamespace(FICHAS={},RESPALDO={})
        fake_plugins.puente_chat = fake_bridge
        with patch.dict(sys.modules, {"mvp":fake_mvp,"plugins":fake_plugins,
                                      "plugins.puente_chat":fake_bridge}):
            ports = build_ports({"authenticated":True,"trusted_host":True,
                 "control":control,"banco":object(),"queue_store":self.store,
                 "watch_store":None,"root":self.root,"project_id":"test",
                 "loop_id":"x","sesion":"web-general"})
            with self.assertRaises(ContractError) as raised:
                ports.queue_complete("cit:"+qid+":a", {"verification":"PASS"})
        self.assertEqual("QUEUE_COMPLETION_STATE_MISMATCH",raised.exception.code)
        self.assertEqual("cancelled",next(t for t in self.store.get(qid)["tasks"] if t["id"]=="a")["status"])


if __name__ == "__main__":
    unittest.main()

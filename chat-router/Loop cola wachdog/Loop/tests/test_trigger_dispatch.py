"""BE02: deterministic DSL dispatcher tests using mock model/queue; NOT remote E2E."""
from __future__ import annotations
import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from nct_loop.trigger_bridge import TriggerBridge


class TestDispatchReady(unittest.TestCase):
    def _run(self, kinds):
        contracts = [{"id": name, "enabled": True,
                      "depends_on": [] if index == 0 else [kinds[index-1]]}
                     for index, name in enumerate(kinds)]
        states = {name: "pending" for name in kinds}
        done = []
        def queue_status(_qid):
            status = "completed" if all(x == "succeeded" for x in states.values()) else "running"
            return {"status": status, "tasks": [
                {"id": name, "status": states[name],
                 "receipt_id": "r-" + name if states[name] == "succeeded" else None}
                for name in kinds]}
        async def previous(_project, _loop, c, _contracts):
            return {d: "PASS" for d in c["depends_on"] if states.get(d) == "succeeded"}
        async def run_one(**kwargs):
            name = kwargs["contract"]["id"]
            if any(states.get(dep) != "succeeded" for dep in kwargs["contract"]["depends_on"]):
                raise AssertionError("dependency bypass")
            states[name] = "succeeded"
            done.append(name)
            return {"ok": True, "status": "PASS"}
        ports = SimpleNamespace(queue_status=queue_status, queue_skip=None)
        bridge = TriggerBridge(ports)
        bridge._prior = previous
        bridge.engine.run_once = run_one
        outcome = asyncio.run(bridge.dispatch_ready(project="demo", loop="L1",
           state={"queue_id": "cit_mock", "contracts": contracts, "role_pairs": {}},
           server_context={"authenticated": True, "project_id": "demo"},
           max_steps=100))
        return outcome, done

    def test_three_dependent_contracts_in_order(self):
        output, done = self._run(["T01", "T02", "T03"])
        self.assertEqual(done, ["T01", "T02", "T03"])
        self.assertEqual(output["status"], "COMPLETED")
        self.assertEqual([x["receipt_id"] for x in output["processed"]],
                         ["r-T01", "r-T02", "r-T03"])

    def test_hundred_slots_finish_without_fake_limit(self):
        names = ["T%03d" % i for i in range(100)]
        output, done = self._run(names)
        self.assertEqual(len(done), 100)
        self.assertEqual(output["status"], "COMPLETED")

    def test_no_eligible_dependency_never_runs_model(self):
        ports = SimpleNamespace(queue_status=lambda q: {"status": "running",
            "tasks": [{"id":"A","status":"skipped"},{"id":"B","status":"pending"}]}, queue_skip=None)
        bridge = TriggerBridge(ports)
        async def prev(*args):
            return {}
        async def forbidden(**kwargs):
            raise AssertionError("called model with blocked dependency")
        bridge._prior = prev
        bridge.engine.run_once = forbidden
        output = asyncio.run(bridge.dispatch_ready(project="demo", loop="L1",
            state={"queue_id":"cit_mock", "contracts":[{"id":"A","enabled":False,"depends_on":[]},
                {"id":"B","enabled":True,"depends_on":["A"]}], "role_pairs":{}},
            server_context={"authenticated":True,"project_id":"demo"}))
        self.assertEqual(output["error"], "NO_ELIGIBLE_TRIGGER")
        self.assertEqual(output["pending"], ["B"])

    def test_paused_queue_does_not_execute(self):
        ports = SimpleNamespace(queue_status=lambda q: {"status":"paused","tasks":[]}, queue_skip=None)
        bridge = TriggerBridge(ports)
        output = asyncio.run(bridge.dispatch_ready(project="demo", loop="L1",
             state={"queue_id":"cit_mock","contracts":[],"role_pairs":{}},
             server_context={"authenticated":True,"project_id":"demo"}))
        self.assertEqual(output["status"], "PAUSED")
        self.assertFalse(output["ok"])



class TestCheckpointAfterClaim(unittest.TestCase):
    def test_claim_succeeded_but_start_checkpoint_failed_needs_reconciliation(self):
        from unittest.mock import AsyncMock, patch
        from nct_loop.trigger_engine import TriggerEngine
        from nct_loop.trigger_contract import ContractError
        claimed = []
        def claim(request):
            claimed.append(request["trigger_id"])
            return {"claimed": True, "receipt_ref": "cit:queue:T01"}
        ports = SimpleNamespace(load=lambda k: None,
            facts=lambda project, loop: {},
            queue_claim=claim, queue_complete=None, can_write=False)
        engine = TriggerEngine(ports)
        contract={"id":"T01","loop_id":"L01","enabled":True,
                  "depends_on":[],"attachments":[],
                  "source":{"source_anchor_ref":None},"role":"auditor","steps":[],
                  "execution":{}, "when":{"predicate":"always","args":{}}}
        async def never_saves(*args):
            raise ContractError("CHECKPOINT_NOT_DURABLE")
        with patch("nct_loop.trigger_engine.validate_contract", return_value=None), \
             patch("nct_loop.trigger_engine.check_condition", return_value=("PASS","matched")), \
             patch.object(engine,"_constitution", AsyncMock(return_value=("const",{}))), \
             patch.object(engine,"_save", side_effect=never_saves):
            result=asyncio.run(engine.run_once(project_id="project1",
                contract=contract, role_pairs={"auditor":{"model_id":"model",
                    "agent_id":"agent","available":True}},
                host_context={"authenticated":True,"project_id":"project1"}))
        self.assertEqual(claimed, ["T01"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"],"NEEDS_RECONCILIATION")
        self.assertEqual(result["error"],"CHECKPOINT_NOT_DURABLE")



class TestAutomaticLoopHandoff(unittest.TestCase):
    def test_requires_review_when_toggle_on(self):
        ports = SimpleNamespace(queue_status=lambda _: {"status":"completed","tasks":[]})
        bridge = TriggerBridge(ports)
        result = asyncio.run(bridge._handoff_verified(project="P01",loop="L1",
            state={"queue_id":"cit1","loop_meta":{"next_loop_id":"L2",
                   "verify_on_end":True}},server_context={"authenticated":True,"project_id":"P01"}))
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertFalse(result["dispatched"])

    def test_requires_actual_completed_queue(self):
        ports = SimpleNamespace(queue_status=lambda _:{"status":"running","tasks":[]})
        bridge = TriggerBridge(ports)
        result = asyncio.run(bridge._handoff_verified(project="P01",loop="L1",
            state={"queue_id":"cit1","loop_meta":{"next_loop_id":"L2",
                   "verify_on_end":False}},server_context={"authenticated":True,"project_id":"P01"}))
        self.assertEqual(result["status"],"QUEUE_NOT_COMPLETED")
        self.assertFalse(result["dispatched"])


class TestMechanicoLedger(unittest.TestCase):
    def test_real_checkpoint_yields_gap_not_pass(self):
        from nct_loop.repair import gap_events
        from nct_loop.trigger_contract import canonical,sha256
        c={"id":"T01","enabled":True}
        receipt={"error":"MODEL_TIMEOUT","contract_sha256":sha256(canonical(c))}
        rows={"queue_id":"Q1","tasks":[{"id":"T01","status":"failed"}]}
        found=gap_events("P1","L1",[c],{"T01":receipt},rows)
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["code"],"MODEL_TIMEOUT")

    def test_all_ten_unavailable_do_not_forge_evidence(self):
        from nct_loop.repair import research_sources
        def offline(url,espera=5):raise TimeoutError("offline")
        result=research_sources("MODEL_TIMEOUT",offline)
        self.assertEqual(len(result),10)
        self.assertTrue(all(row["status"]=="UNAVAILABLE" for row in result))


    def test_all_off_cannot_autojump_without_verified_work(self):
        ports=SimpleNamespace(queue_status=lambda _:{"status":"completed",
            "tasks":[{"id":"T1","status":"skipped"}]})
        bridge=TriggerBridge(ports)
        async def constitution():return ("sha",{})
        bridge.engine._constitution=constitution
        output=asyncio.run(bridge._handoff_verified(project="P1",loop="L1",
            state={"queue_id":"Q1","contracts":[{"id":"T1","enabled":False}],
                   "loop_meta":{"next_loop_id":"L2","verify_on_end":False}},
            server_context={"authenticated":True,"project_id":"P1"}))
        self.assertEqual(output["status"],"ALL_TRIGGERS_OFF_NO_HANDOFF")
        self.assertIs(output["dispatched"],False)

class TestHarnessResearchShape(unittest.TestCase):
    def test_mock_http_produces_normalizable_evidence(self):
        from nct_loop.repair import research_sources
        from nct_loop.gap_mechanic import normalize_research_hits
        class FakeResponse:
            status=200
            headers={"Content-Type":"text/html; charset=utf-8"}
            def __enter__(self):return self
            def __exit__(self,*a):return False
            def read(self,n):return b"<html><title>Verified test title</title><p>Mock issue report</p></html>"
        rows=research_sources("CIT50_FAIL",lambda *args,**kw:FakeResponse())
        self.assertEqual(len(rows),10)
        self.assertEqual(len(normalize_research_hits("gap_example",rows)),10)

if __name__ == "__main__":
    unittest.main()

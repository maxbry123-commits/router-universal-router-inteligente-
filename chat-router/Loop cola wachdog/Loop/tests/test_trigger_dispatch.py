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


if __name__ == "__main__":
    unittest.main()

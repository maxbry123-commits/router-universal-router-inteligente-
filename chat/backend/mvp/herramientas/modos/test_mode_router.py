import os
import asyncio, copy, json, unittest
import mode_router as mr
import validate_modes as vm
_CWD0 = os.getcwd(); os.chdir(os.path.dirname(os.path.abspath(__file__)))  # los datos (registro, contratos) viven junto al test

def setUpModule():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


def tearDownModule():
    os.chdir(_CWD0)


REG = mr.load_registry("modes_registry.json")
OBJ = {"goal": "Entregar modulo X", "done_when": ["tests en verde"], "constraints": ["aditivo"],
       "out_of_scope": ["migrar DB"], "deliverables": ["src/x.py"]}

class T(unittest.TestCase):
    def test_registry_pass(self):
        self.assertEqual(vm.validate_registry(REG), [])
        self.assertEqual(vm.validate_sources(vm.load("research_sources.json")), [])

    def test_button_beats_slash_and_auto(self):
        r = mr.resolve_mode(REG, "/plan hacer algo, investiga todo", {"mode_id": "m02_objetivo", "source": "button"})
        self.assertEqual((r.mode_id, r.source), ("m02_objetivo", "button_lock"))

    def test_slash_beats_auto(self):
        r = mr.resolve_mode(REG, "/objetivo arma el proyecto con agenda", None)
        self.assertEqual((r.mode_id, r.source, r.text), ("m02_objetivo", "slash_command", "arma el proyecto con agenda"))

    def test_auto_rules(self):
        self.assertEqual(mr.resolve_mode(REG, "planifica la arquitectura del chat").mode_id, "m01_plan")
        self.assertEqual(mr.resolve_mode(REG, "organiza la agenda y prioridades").mode_id, "m10_agenda")
        self.assertEqual(mr.resolve_mode(REG, "investiga metodos de rag").mode_id, "m03_investigacion")
        self.assertEqual(mr.resolve_mode(REG, "hola que tal").mode_id, "m05_respuesta_rapida")

    def test_auto_never_picks_autonomous(self):
        r = mr.resolve_mode(REG, "ejecuta todo el proyecto hasta terminar sin parar")
        self.assertFalse(next(m for m in REG["modes"] if m["id"] == r.mode_id)["autonomous_loop"])

    def test_unknown_mode_rejected(self):
        with self.assertRaises(mr.ModeError) as c:
            mr.resolve_mode(REG, "x", {"mode_id": "m99", "source": "button"})
        self.assertEqual(c.exception.code, "UNKNOWN_MODE")

    def test_explicit_mode_needs_button_source(self):
        with self.assertRaises(mr.ModeError) as c:
            mr.resolve_mode(REG, "x", {"mode_id": "m02_objetivo", "source": "auto"})
        self.assertEqual(c.exception.code, "BAD_SOURCE")

    def test_slash_auto_unlocks(self):
        r = mr.resolve_mode(REG, "/auto planifica la arquitectura")
        self.assertEqual(r.mode_id, "m01_plan")

    def test_unknown_slash_left_intact(self):
        r = mr.resolve_mode(REG, "/otrocomando algo")
        self.assertEqual(r.text, "/otrocomando algo")

    def test_ficha_fast_mode(self):
        f = mr.build_ficha(REG, "m05_respuesta_rapida")
        self.assertEqual(f["tools"], [])
        self.assertEqual(f["reasoning"]["execute"], "none")
        self.assertEqual(f["ui_thinking_toggle"], "mode_wins")

    def test_ficha_autonomous_has_objective_and_rules(self):
        f = mr.build_ficha(REG, "m02_objetivo", OBJ)
        self.assertIn("OBJETIVO", f["system_block"])
        self.assertIn("REGLAS DE AUTONOMIA", f["system_block"])
        self.assertIn("Entregar modulo X", f["system_block"])

    def test_bad_objective_rejected(self):
        bad = dict(OBJ); bad["done_when"] = []
        with self.assertRaises(mr.ModeError):
            mr.build_ficha(REG, "m02_objetivo", bad)

    def test_orchestrator_has_no_write_tools(self):
        for mid in ("m06_orquestador_pool", "m11_max_paralelo"):
            self.assertFalse({"edit_file", "bash"} & set(mr.build_ficha(REG, mid)["tools"]))

    def test_validator_negatives(self):
        bad = copy.deepcopy(REG)
        next(m for m in bad["modes"] if m["id"] == "m02_objetivo")["no_escalation"] = False
        next(m for m in bad["modes"] if m["id"] == "m11_max_paralelo")["parallel"]["max_running"] = 11
        next(m for m in bad["modes"] if m["id"] == "m09_mythos")["limits"]["max_cost_usd"] = 9999
        errs = vm.validate_registry(bad)
        self.assertTrue(any("no_escalation" in e for e in errs))
        self.assertTrue(any("max_running" in e for e in errs))
        self.assertTrue(any("tope duro" in e for e in errs))

    def test_immutable_violations(self):
        new = copy.deepcopy(REG)
        new["hard_limit_caps"]["max_cost_usd"] = 99999
        new["selector"]["gate"]["trigger_words"] = []
        v = mr.immutable_violations(REG, new)
        self.assertIn("hard_limit_caps", v); self.assertIn("selector.gate", v)
        self.assertEqual(mr.immutable_violations(REG, copy.deepcopy(REG)), [])

    def test_pool_cap_and_queue(self):
        events = []
        pool = mr.ParallelPool(10, on_event=lambda n, d: events.append(n))
        async def job():
            await asyncio.sleep(0.05); return "ok"
        res = asyncio.run(pool.run([mr.PoolTask(f"t{i}", job) for i in range(25)]))
        self.assertEqual(len(res), 25)
        self.assertTrue(all(v["status"] == "passed" for v in res.values()))
        self.assertEqual(pool.peak_running, 10)
        self.assertEqual(events.count("task_queued"), 15)

    def test_pool_retry_then_blocked(self):
        calls = {"n": 0}
        async def bad():
            calls["n"] += 1; raise RuntimeError("boom")
        async def slow():
            await asyncio.sleep(5)
        pool = mr.ParallelPool(10)
        res = asyncio.run(pool.run([mr.PoolTask("bad", bad, retries=2), mr.PoolTask("slow", slow, retries=0, timeout_s=0.1)]))
        self.assertEqual(res["bad"]["status"], "blocked_with_evidence"); self.assertEqual(calls["n"], 3)
        self.assertEqual(res["slow"]["error"], "timeout")

    def test_pool_hard_cap(self):
        with self.assertRaises(mr.ModeError):
            mr.ParallelPool(11)

    def test_priority_order(self):
        order = []
        async def mk(n):
            order.append(n)
        pool = mr.ParallelPool(1)
        asyncio.run(pool.run([mr.PoolTask("lo", lambda: mk("lo"), priority=90),
                              mr.PoolTask("hi", lambda: mk("hi"), priority=10),
                              mr.PoolTask("mid", lambda: mk("mid"), priority=50)]))
        self.assertEqual(order, ["hi", "mid", "lo"])

if __name__ == "__main__":
    unittest.main(verbosity=2)

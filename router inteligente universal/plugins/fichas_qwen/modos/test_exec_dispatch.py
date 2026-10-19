import os, tempfile, unittest
import exec_dispatch as ed
import loop_controller as lc
import test_additional as ta

GOB = "# GOBERNANZA\n" + "\n".join(f"- regla {i}" for i in range(50))
FILES = {"n01_a": "a.txt", "n02_b": "b.txt", "n03_f": "c.txt"}


def node(i="n01_a", kind="file_exists"):
    return {"id": i, "title": "t", "instruction": "Crea el archivo pedido", "acceptance": [{"id": "c", "kind": kind, "spec": {}, "required": True}]}


def fake_model(model, msgs):
    last = msgs[-1]["content"]
    if model == "dsv4pro":   return {"text": "Listo. Estoy a la espera de tus instrucciones.", "tool_calls": []}
    if model == "dsv4flash": return {"text": "Entendido. Estoy listo para ayudarte.", "tool_calls": []}
    if model == "glm52":     return {"text": "", "tool_calls": [{"name": "write_file", "args": {"task": last}}]} if "<tarea>" in last \
                                    else {"text": "Entendido.", "tool_calls": []}
    if model == "qwenD":     return {"text": "", "tool_calls": [{"name": "write_file"}]} if len(msgs) == 1 else {"text": "Entendido, esperando.", "tool_calls": []}
    raise RuntimeError("modelo desconocido")


def ok_tools(calls, nd): return [{"ok": True} for _ in calls]


class T(unittest.TestCase):
    def mk(self, models, **kw):
        return ed.ExecDispatcher(fake_model, kw.pop("run_tools", ok_tools), models,
                                 profile_path=kw.pop("profile", None), **kw)

    def test_clasifica_los_acuses_reales_del_batch(self):
        for t in ("Entendido. Estoy listo...", "Listo. Estoy a la espera...", "Estoy listo para ayudarte."):
            self.assertEqual(ed.classify({"text": t}, False), "ACK", t)
        self.assertEqual(ed.classify({"text": "x" * 500}, True), "HERRAMIENTA_NO_EJECUTADA")
        self.assertEqual(ed.classify({"text": "analisis largo " * 60}, False), "OK")
        self.assertEqual(ed.classify({"text": "ok", "tool_calls": [{"name": "t"}]}, True), "OK")
        self.assertEqual(ed.classify({}, True), "VACIO")

    def test_expects_tools_segun_checks(self):
        self.assertTrue(ed.expects_tools_for(node(kind="file_exists")))
        self.assertFalse(ed.expects_tools_for({"id": "x", "acceptance": [{"kind": "http_status"}]}))

    def test_fallback_entre_modelos_y_layouts_hasta_ejecutar(self):
        r = self.mk(["dsv4pro", "dsv4flash", "glm52"]).execute(node(), GOB, "Crea a.txt")
        self.assertTrue(r["ok"]); self.assertEqual((r["model"], r["layout"]), ("glm52", "B_tarea_etiquetada"))
        self.assertTrue(all(a["code"] == "ACK" for a in r["attempts"][:-1]))

    def test_todo_falla_es_blocked_con_evidencia_y_acotado(self):
        r = self.mk(["dsv4pro", "dsv4flash"], max_attempts=5).execute(node(), GOB, "Crea a.txt")
        self.assertFalse(r["ok"]); self.assertEqual(r["state"], "blocked_with_evidence"); self.assertEqual(len(r["attempts"]), 5)

    def test_herramienta_no_ejecutada_si_run_tools_no_devuelve_resultados(self):
        r = self.mk(["glm52"], run_tools=lambda c, n: []).execute(node(), GOB, "t")
        self.assertFalse(r["ok"]); self.assertIn("HERRAMIENTA_NO_EJECUTADA", [a["code"] for a in r["attempts"]])
        r = self.mk(["glm52"], run_tools=lambda c, n: 1 / 0).execute(node(), GOB, "t")
        self.assertFalse(r["ok"])

    def test_aprende_y_va_directo_a_la_combinacion_buena(self):
        p = os.path.join(tempfile.mkdtemp(), "state/layout_profile.json")
        d1 = self.mk(["dsv4pro", "dsv4flash", "glm52"], profile=p)
        self.assertGreater(len(d1.execute(node(), GOB, "t1")["attempts"]), 1)
        d2 = self.mk(["dsv4pro", "dsv4flash", "glm52"], profile=p)        # perfil persistido en disco
        r2 = d2.execute(node(), GOB, "t2")
        self.assertEqual(len(r2["attempts"]), 1); self.assertEqual((r2["model"], r2["layout"]), ("glm52", "B_tarea_etiquetada"))

    def test_cuarentena_manda_al_final_lo_que_falla_siempre(self):
        d = self.mk(["dsv4pro", "glm52"], quarantine_after=2)
        for _ in range(2): d.profile.record("dsv4pro", "A_system_user", False)
        order = d.profile.ordered(d.models, d.layouts, 2)
        self.assertEqual(order[-1], ("dsv4pro", "A_system_user"))

    def test_error_de_red_no_envenena_el_perfil(self):
        d = self.mk(["modelo_roto", "glm52"])
        r = d.execute(node(), GOB, "t")
        self.assertTrue(r["ok"]); self.assertNotIn("modelo_roto|A_system_user", d.profile.d)
        self.assertIn("MODEL_ERROR", [a["code"] for a in r["attempts"]])

    def test_costo_suma_todos_los_intentos(self):
        d = ed.ExecDispatcher(lambda m, msgs: {**fake_model(m, msgs), "cost_usd": 0.5}, ok_tools, ["dsv4pro", "glm52"])
        r = d.execute(node(), GOB, "t")
        self.assertEqual(r["cost_usd"], 0.5 * len(r["attempts"])); self.assertGreater(len(r["attempts"]), 1)

    def test_exclude_y_report(self):
        d = self.mk(["glm52", "qwenD"])
        r1 = d.execute(node(), GOB, "t")
        r2 = d.execute(node(), GOB, "t", exclude=[(r1["model"], r1["layout"])])
        self.assertNotEqual((r1["model"], r1["layout"]), (r2["model"], r2["layout"]))
        before = d.profile.score(*d.last["n01_a"]); d.report("n01_a", False)
        self.assertLess(d.profile.score(*d.last["n01_a"]), before)

    def test_integracion_con_loopcontroller(self):
        work = tempfile.mkdtemp()
        def tools(calls, nd):
            open(os.path.join(work, FILES[nd["id"]]), "w").close(); return [{"ok": True} for _ in calls]
        disp = ed.ExecDispatcher(fake_model, tools, ["dsv4pro", "glm52"], profile_path=os.path.join(work, "state/prof.json"))
        c = ta.contract([ta.node("n01_a", [], ta.fe("a.txt")), ta.node("n02_b", ["n01_a"], ta.fe("b.txt")),
                         ta.node("n03_f", ["n02_b"], ta.fe("c.txt"), typ="final")],
                        [{"from": "n01_a", "to": "n02_b"}, {"from": "n02_b", "to": "n03_f"}])
        for n in c["dag"]["nodes"]: n["instruction"] = f"Crea {FILES[n['id']]}"
        rep = lc.LoopController(c, disp.make_executor(GOB), work, on_event=disp.event_hook()).run()
        self.assertEqual(rep["state"], "DONE"); self.assertTrue(all(v["evidence"] for v in rep["nodes"].values()))
        self.assertEqual(disp.profile.ordered(disp.models, disp.layouts, 6)[0], ("glm52", "B_tarea_etiquetada"))   # aprendio


if __name__ == "__main__":
    unittest.main(verbosity=2)

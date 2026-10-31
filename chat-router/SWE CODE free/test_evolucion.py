"""Auto-evolucion: el agente registra cada arreglo, lo repetido se vuelve propuesta y nunca se toca lo protegido ni lo ajeno a SWE CODE."""
import json, os, tempfile, unittest
import evolucion


class TestEvolucion(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(); os.environ["SWE_EVOLUCION_DIR"] = self.dir

    def lec(self, codigo="SESSION_EXPIRED", accion="POST /refresh_session", resultado="PASS", **k):
        return evolucion.registrar({"codigo": codigo, "accion": accion, "resultado": resultado, "modelo": "web-qwen38max", "evidencia": "health ok", **k})

    def test_registrar_guarda_una_linea_con_fecha_y_exige_codigo_y_accion(self):
        self.lec()
        lineas = open(os.path.join(self.dir, "lecciones.jsonl")).read().splitlines()
        self.assertEqual(len(lineas), 1); self.assertIn("ts", json.loads(lineas[0]))
        with self.assertRaises(ValueError):
            evolucion.registrar({"codigo": "X"})

    def test_lo_repetido_tres_veces_con_exito_se_propone_como_paso_del_runbook(self):
        for _ in range(3): self.lec()
        self.lec(codigo="OTRO", accion="reiniciar")
        p = evolucion.proponer()
        self.assertEqual([x["codigo"] for x in p], ["SESSION_EXPIRED"])
        self.assertEqual(p[0]["tipo"], "promover_a_runbook"); self.assertEqual(p[0]["archivo"], "SWE CODE free/INSTRUCCIONES.md")

    def test_lo_que_falla_repetido_se_propone_cambiar_de_estrategia(self):
        for _ in range(3): self.lec(codigo="AGE_GATE", accion="click Continuar", resultado="FAIL")
        p = evolucion.proponer()
        self.assertEqual(p[0]["tipo"], "cambiar_estrategia")

    def test_nunca_propone_tocar_lo_protegido_ni_fuera_de_swe_code(self):
        self.assertTrue(evolucion.permitido("SWE CODE free/INSTRUCCIONES.md"))
        self.assertTrue(evolucion.permitido("SWE CODE/web-bridge/src/sites.js"))
        for ruta in ("chat/backend/mvp/app.py", "chat/frontend/shell.js", "../router-mvp/router/x.py", "SWE CODE/../chat/backend/a.py"):
            self.assertFalse(evolucion.permitido(ruta), ruta)

    def test_sin_variable_propia_lee_lo_que_registra_el_bridge(self):
        os.environ.pop("SWE_EVOLUCION_DIR", None); os.environ["BRIDGE_STATE_DIR"] = self.dir
        try:
            self.assertEqual(evolucion._dir(), os.path.join(self.dir, "evolucion"))
        finally:
            os.environ.pop("BRIDGE_STATE_DIR", None)

    def test_escribir_md_deja_lecciones_y_propuestas_legibles(self):
        for _ in range(3): self.lec()
        evolucion.escribir_md()
        self.assertIn("SESSION_EXPIRED", open(os.path.join(self.dir, "LECCIONES.md")).read())
        self.assertIn("promover_a_runbook", open(os.path.join(self.dir, "PROPUESTAS.md")).read())

    def test_registrar_valida_tipos_y_limpia_saltos_de_linea(self):
        for mal in ({"codigo": 5, "accion": "x"}, {"codigo": "X", "accion": ["a"]}, {"codigo": "  ", "accion": "x"}, {"codigo": "X", "accion": ""}, "texto", None):
            with self.assertRaises(ValueError, msg=repr(mal)):
                evolucion.registrar(mal)
        f = evolucion.registrar({"codigo": "A\nB\r\nC", "accion": "x\n- **falsa** linea", "resultado": "PASS\u2028", "evidencia": 7})
        self.assertEqual((f["codigo"], f["accion"], f["resultado"], f["evidencia"]), ("A B C", "x - **falsa** linea", "PASS", "7"))
        self.assertEqual(len(open(os.path.join(self.dir, "lecciones.jsonl")).read().splitlines()), 1)

    def test_lecciones_salta_lineas_corruptas_y_proponer_no_falla(self):
        for _ in range(3): self.lec()
        with open(os.path.join(self.dir, "lecciones.jsonl"), "a", encoding="utf-8") as f:
            f.write('{"ts": 1, "codigo": "TRUNC\n')                    # truncada
            f.write("basura sin json\n[1, 2]\n42\nnull\n")             # no-objetos
            f.write(json.dumps({"codigo": ["lista"], "accion": {"a": 1}}) + "\n")    # tipos raros (no hashables)
            f.write(json.dumps({"codigo": "SESSION_EXPIRED", "accion": "POST /refresh_session", "resultado": "PASS", "ts": "ayer"}) + "\n")
            f.write(json.dumps({"codigo": "Z", "accion": "z", "ts": 10 ** 30}) + "\n")
            f.write(b"\xff\xfe roto\n".decode("latin-1"))
        self.assertEqual(len(evolucion.lecciones()), 4)  # 3 buenas + 1 con ts raro (ts -> 0)
        p = evolucion.proponer()
        self.assertEqual([(x["codigo"], x["veces"]) for x in p], [("SESSION_EXPIRED", 4)])
        evolucion.escribir_md()

    def test_los_md_no_aceptan_lineas_inyectadas(self):
        with open(os.path.join(self.dir, "lecciones.jsonl"), "w", encoding="utf-8") as f:   # escrito a mano, sin pasar por registrar
            for _ in range(3):
                f.write(json.dumps({"ts": 1, "codigo": "C\n# INYECTADO", "accion": "a\n- **falsa**", "resultado": "PASS\n- otra"}) + "\n")
        evolucion.escribir_md()
        for nombre in ("LECCIONES.md", "PROPUESTAS.md"):
            lineas = open(os.path.join(self.dir, nombre)).read().splitlines()
            self.assertFalse([x for x in lineas if x.startswith("# INYECTADO") or x.startswith("- **falsa**") or x.startswith("- otra")], nombre)
        self.assertEqual(len([x for x in open(os.path.join(self.dir, "LECCIONES.md")).read().splitlines() if x.startswith("- ")]), 3)


if __name__ == "__main__":
    unittest.main()

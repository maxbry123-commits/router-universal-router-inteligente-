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


if __name__ == "__main__":
    unittest.main()

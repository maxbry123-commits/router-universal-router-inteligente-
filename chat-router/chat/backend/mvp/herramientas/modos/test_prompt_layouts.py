import unittest
import prompt_layouts as pl

GOB = "# GOBERNANZA\n" + "\n".join(f"- regla {i}" for i in range(300))
TAREA = "Crea el archivo hola.py que imprima hola"


def model_tag_only(msgs):          # obediente: solo ejecuta si la tarea viene etiquetada; si no, "entiende"
    last = msgs[-1]["content"]
    return {"text": "Hecho: hola.py creado con print('hola')", "tool_calls": []} if "<tarea>" in last \
        else {"text": "Entendido, esperando instrucciones.", "tool_calls": []}


class T(unittest.TestCase):
    def test_gobernanza_va_en_system_y_tarea_sola_en_user(self):
        m = pl.assemble("A_system_user", GOB, TAREA)
        self.assertEqual([x["role"] for x in m], ["system", "user"]); self.assertEqual(m[1]["content"], TAREA)
        self.assertNotIn("GOBERNANZA", m[1]["content"])

    def test_fallback_elige_layout_que_ejecuta(self):
        r = pl.run_with_fallback(model_tag_only, GOB, TAREA)
        self.assertTrue(r["ok"]); self.assertEqual(r["layout"], "B_tarea_etiquetada")
        self.assertEqual([a["ack"] for a in r["attempts"]], [True, False])

    def test_todo_acuse_es_blocked_con_evidencia(self):
        r = pl.run_with_fallback(lambda m: {"text": "Entendido."}, GOB, TAREA)
        self.assertFalse(r["ok"]); self.assertEqual(r["state"], "blocked_with_evidence"); self.assertEqual(len(r["attempts"]), 4)

    def test_detecta_el_caso_real(self):
        self.assertTrue(pl.is_ack_only("No se proporcionó bloque de tarea. Esperando instrucciones.")[0])
        self.assertTrue(pl.is_ack_only("")[0])

    def test_tool_calls_y_respuestas_largas_no_son_acuse(self):
        self.assertFalse(pl.is_ack_only("Entendido.", tool_calls=[{"name": "edit_file"}])[0])
        self.assertFalse(pl.is_ack_only("Entendido. " + "trabajo real " * 60)[0])

    def test_tarea_ausente_es_error_de_cableado(self):
        with self.assertRaises(pl.LayoutError):
            pl.assert_task_present([{"role": "system", "content": TAREA}, {"role": "user", "content": "otra cosa"}], TAREA)

    def test_gobernanza_compacta_y_layout_desconocido(self):
        self.assertLessEqual(len(pl.compact(GOB)), 1200)
        with self.assertRaises(pl.LayoutError):
            pl.assemble("Z", GOB, TAREA)


if __name__ == "__main__":
    unittest.main(verbosity=2)

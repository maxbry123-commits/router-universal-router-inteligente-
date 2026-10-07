"""Pruebas deterministas del piloto yaiwes.node-executor/xray-v2.

No usa red, Hugging Face ni GitHub Actions. Ejecutar:
python -m unittest tests.test_sentinela_xray_v2_pilot -v
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SENT = ROOT / "plugins" / "puente_chat" / "fichas" / "sentinela.py"
spec = importlib.util.spec_from_file_location("sentinela_pilot", SENT)
s = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(s)


def base_messages(raw="PASO 1 📌\n  conservar  espacios\nFIN"):
    return [
        {"role": "system", "content": "Sistema. Modelo seleccionado: qwen/qwen3.8-27b"},
        {"role": "user", "content": raw},
    ]


def answer(text):
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


CLOSED = (
    "🎯 MICRO RESUMEN\nTarea terminada.\n\n"
    "FLUJO: INPUT_BLOCK → RESEARCH → EXECUTE → VALIDATE → CLOSED\n\n"
    "CHECKLIST\n"
    "🎯 Objetivos: cumplidos\n"
    "⚠️ Pendientes: —\n"
    "🆘 Bloqueos: —\n"
    "✅ Cerrado/Terminado: sí\n"
    "[[YAIWES:CLOSED]]"
)


class SentinelPilotTests(unittest.TestCase):
    def test_1_verbatim_preserva_input_y_sha(self):
        raw = "A  B\n\n  C\tD\nñ🙂"
        msgs = base_messages(raw)
        checkpoints = []

        def paso(_):
            return answer(CLOSED), []

        out = s.ejecutar([("modelo", paso)], msgs, guardar_ck=lambda m: checkpoints.append(list(m)))
        self.assertTrue(out["completada"])
        self.assertEqual(out["input_sha256"], hashlib.sha256(raw.encode("utf-8")).hexdigest())
        wrapped = next(m["content"] for m in msgs if m.get("role") == "user" and s.BEGIN_MARK in m.get("content", ""))
        self.assertEqual(s._extract_raw(wrapped), raw)
        self.assertTrue(checkpoints)

    def test_2_parcial_reanuda_y_cierra(self):
        msgs = base_messages()
        calls = []

        def parcial(_):
            calls.append("parcial")
            return answer("He revisado el archivo; ahora voy a continuar."), [{"herramienta": "github_leer", "ok": True}]

        def final(_):
            calls.append("final")
            return answer(CLOSED), []

        out = s.ejecutar([("modelo", parcial), ("retoma", final)], msgs, guardar_ck=lambda m: None)
        self.assertTrue(out["completada"])
        self.assertEqual(calls, ["parcial", "final"])
        self.assertTrue(any(i.get("motor") == "RESUME_ENGINE" for i in out["items"]))
        visible = out["resultado"][0]["choices"][0]["message"]["content"]
        self.assertNotIn("[[YAIWES:CLOSED]]", visible)

    def test_3_tool_call_visible_no_cierra(self):
        msgs = base_messages()
        calls = []

        def fuga(_):
            calls.append("fuga")
            return answer("<tool_call><function=github_leer></function></tool_call>"), []

        def final(_):
            calls.append("final")
            return answer(CLOSED), []

        out = s.ejecutar([("modelo", fuga), ("retoma", final)], msgs, guardar_ck=lambda m: None)
        self.assertTrue(out["completada"])
        self.assertEqual(calls, ["fuga", "final"])
        rechazos = [i for i in out["items"] if i.get("motor") == "CLOSE_GATE" and i.get("estado") == "RECHAZADO"]
        self.assertTrue(any(i.get("motivo") == "TOOL_CALL_VISIBLE" for i in rechazos))

    def test_4_sin_cierre_termina_blocked_no_fake_pass(self):
        msgs = base_messages()
        count = {"n": 0}

        def nunca(_):
            count["n"] += 1
            return answer("Sigo trabajando pero no he terminado."), []

        out = s.ejecutar([("modelo", nunca), ("retoma", nunca), ("reserva", nunca)], msgs, guardar_ck=lambda m: None)
        self.assertFalse(out["completada"])
        self.assertEqual(out["estado"], "BLOCKED")
        self.assertEqual(count["n"], 3)
        self.assertEqual(out["resultado"][0]["error"], "TAREA_BLOCKED_FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main(verbosity=2)

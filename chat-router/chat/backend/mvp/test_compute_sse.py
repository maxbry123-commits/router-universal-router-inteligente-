"""Lectura incremental SSE de compute.py (Groq/NVIDIA): deltas, tool_calls por indice, finish_reason, usage, TTFT y tokens/s.
Sin red: se alimenta el acumulador con lineas SSE escritas a mano (datos ficticios)."""
import json
import os
import pathlib
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from mvp import compute


def d(**kw):
    return ("data: " + json.dumps(kw)).encode()


def chunk(delta=None, finish=None, **extra):
    return d(choices=[{"index": 0, "delta": delta or {}, "finish_reason": finish}], model="modelo-x", **extra)


class TestAcumuladorSSE(unittest.TestCase):
    def test_texto_incremental_y_callback_con_acumulado(self):
        vistos = []
        a = compute.AcumuladorSSE(al_texto=lambda total, frag: vistos.append((total, frag)))
        for linea in (chunk({"role": "assistant", "content": ""}), chunk({"content": "Ho"}), b"", chunk({"content": "la"}), chunk({}, "stop"), b"data: [DONE]"):
            terminado = a.linea(linea)
        self.assertTrue(terminado)
        self.assertEqual(vistos, [("Ho", "Ho"), ("Hola", "la")])
        r = a.resultado("groq/qwen/qwen3.8-27b")
        self.assertEqual((r["texto"], r["finish_reason"], r["modelo_solicitado"], r["modelo_respuesta"]), ("Hola", "stop", "groq/qwen/qwen3.8-27b", "modelo-x"))
        self.assertEqual(r["tool_calls"], [])
        self.assertEqual(r["mensaje_asistente"]["content"], "Hola")

    def test_ignora_comentarios_event_crlf_y_data_sin_espacio(self):
        a = compute.AcumuladorSSE()
        for linea in (b": keep-alive", b"event: message", b"data:" + json.dumps({"choices": [{"delta": {"content": "ok"}}]}).encode() + b"\r", b"\r", "data: [DONE]\r"):
            a.linea(linea)
        self.assertEqual(a.resultado("m")["texto"], "ok")

    def test_tool_calls_se_reconstruyen_por_indice_aunque_lleguen_mezclados(self):
        a = compute.AcumuladorSSE()
        f = lambda i, **fn: {"tool_calls": [{"index": i, **fn}]}
        a.linea(chunk(f(0, id="call_a", type="function", function={"name": "leer", "arguments": ""})))
        a.linea(chunk(f(1, id="call_b", type="function", function={"name": "escribir", "arguments": '{"ru'})))
        a.linea(chunk(f(0, function={"arguments": '{"x":'})))
        a.linea(chunk(f(1, function={"name": "", "arguments": 'ta":"a"}'})))  # name vacio posterior no sobrescribe
        a.linea(chunk(f(0, function={"arguments": ' 1}'})))
        a.linea(chunk({}, "tool_calls"))
        r = a.resultado("nvidia/m")
        self.assertEqual(r["finish_reason"], "tool_calls")
        self.assertEqual([(t["id"], t["type"], t["function"]["name"], t["function"]["arguments"]) for t in r["tool_calls"]],
                         [("call_a", "function", "leer", '{"x": 1}'), ("call_b", "function", "escribir", '{"ruta":"a"}')])
        self.assertEqual(json.loads(r["tool_calls"][0]["function"]["arguments"]), {"x": 1})
        self.assertEqual(r["mensaje_asistente"]["tool_calls"], r["tool_calls"])
        self.assertIsNone(r["mensaje_asistente"]["content"])
        self.assertEqual(r["texto"], "")

    def test_nombre_repetido_en_cada_fragmento_no_se_duplica(self):
        a = compute.AcumuladorSSE()
        for arg in ('{"a"', ':1}'):
            a.linea(chunk({"tool_calls": [{"index": 0, "id": "c1", "function": {"name": "leer", "arguments": arg}}]}))
        r = a.resultado("m")
        self.assertEqual((r["tool_calls"][0]["function"]["name"], r["tool_calls"][0]["function"]["arguments"]), ("leer", '{"a":1}'))

    def test_uso_en_el_ultimo_fragmento_sin_choices_y_en_x_groq(self):
        a = compute.AcumuladorSSE()
        a.linea(chunk({"content": "a"}, "stop"))
        a.linea(d(choices=[], usage={"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12}))
        self.assertEqual(a.resultado("m")["uso"], {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12})
        b = compute.AcumuladorSSE()
        b.linea(chunk({"content": "a"}, "stop", x_groq={"usage": {"completion_tokens": 3}}))
        self.assertEqual(b.resultado("m")["uso"], {"completion_tokens": 3})

    def test_razonamiento_se_guarda_aparte_y_no_va_al_texto_parcial(self):
        vistos = []
        a = compute.AcumuladorSSE(al_texto=lambda t, f: vistos.append(t))
        a.linea(chunk({"reasoning_content": "pienso"}))
        a.linea(chunk({"content": "resp"}))
        r = a.resultado("m")
        self.assertEqual((r["texto"], vistos, r["mensaje_asistente"]["reasoning_content"]), ("resp", ["resp"], "pienso"))

    def test_error_en_el_stream_lanza_con_codigo(self):
        a = compute.AcumuladorSSE()
        with self.assertRaisesRegex(RuntimeError, "HTTP 429"):
            a.linea(d(error={"message": "rate limit", "code": 429}))
        with self.assertRaisesRegex(RuntimeError, "rate"):
            compute.AcumuladorSSE().linea(d(error={"message": "rate limit"}))

    def test_linea_json_rota_se_ignora_y_se_cuenta(self):
        a = compute.AcumuladorSSE()
        a.linea(b'data: {"choices": [{"delta": {"content": "x')
        a.linea(chunk({"content": "ok"}))
        r = a.resultado("m")
        self.assertEqual((r["texto"], r["metricas"]["lineas_invalidas"]), ("ok", 1))

    def test_metricas_ttft_y_tokens_por_segundo_con_usage(self):
        reloj = iter([10.0, 10.5, 12.5])  # inicio, primer token, fin
        a = compute.AcumuladorSSE(reloj=lambda: next(reloj))
        a.linea(chunk({"content": "a"}))
        a.linea(chunk({"content": "b"}, "stop", usage={"completion_tokens": 40}))
        m = a.resultado("m")["metricas"]
        self.assertEqual((m["ttft_s"], m["duracion_s"], m["tokens"], m["tokens_por_s"], m["stream"], m["tokens_estimados"]), (0.5, 2.5, 40, 20.0, True, False))

    def test_sin_usage_tokens_por_s_se_estima_y_se_marca(self):
        reloj = iter([0.0, 1.0, 3.0])
        a = compute.AcumuladorSSE(reloj=lambda: next(reloj))
        for t in ("a", "b", "c", "d"):
            a.linea(chunk({"content": t}))
        m = a.resultado("m")["metricas"]
        self.assertEqual((m["tokens"], m["tokens_por_s"], m["tokens_estimados"]), (4, 2.0, True))

    def test_sin_datos_no_hay_ttft_ni_tokens_por_s(self):
        m = compute.AcumuladorSSE().resultado("m")["metricas"]
        self.assertIsNone(m["ttft_s"]); self.assertIsNone(m["tokens_por_s"])

    def test_bruto_reconstruido_tiene_la_forma_openai(self):
        a = compute.AcumuladorSSE()
        a.linea(chunk({"content": "hi"}, "length", usage={"completion_tokens": 1}))
        b = a.resultado("m")["bruto"]
        self.assertEqual((b["choices"][0]["message"]["content"], b["choices"][0]["finish_reason"], b["usage"], b["model"]), ("hi", "length", {"completion_tokens": 1}, "modelo-x"))


class TestNombresFragmentados(unittest.TestCase):
    """R3 (auditoria GPT): el nombre de la herramienta llega en trozos (github_ + leer) y NO debe reemplazarse por el ultimo trozo."""
    def _tc(self, a, i, **fn):
        a.linea(chunk({"tool_calls": [{"index": i, "id": "c%d" % i if fn.get("id") else None, "function": {k: v for k, v in fn.items() if k != "id"}}]}))

    def test_nombre_en_trozos_se_concatena(self):
        a = compute.AcumuladorSSE()
        a.linea(chunk({"tool_calls": [{"index": 0, "id": "c0", "function": {"name": "github_", "arguments": ""}}]}))
        a.linea(chunk({"tool_calls": [{"index": 0, "function": {"name": "leer", "arguments": '{"ruta"'}}]}))
        a.linea(chunk({"tool_calls": [{"index": 0, "function": {"arguments": ':"a"}'}}]}, "tool_calls"))
        t = a.resultado("m")["tool_calls"][0]["function"]
        self.assertEqual((t["name"], t["arguments"]), ("github_leer", '{"ruta":"a"}'))

    def test_nombre_acumulativo_o_repetido_no_se_duplica(self):
        for trozos, esperado in ((["git", "github", "github_leer"], "github_leer"), (["leer", "leer", "leer"], "leer"), (["github_leer", "", ""], "github_leer")):
            a = compute.AcumuladorSSE()
            for n in trozos:
                a.linea(chunk({"tool_calls": [{"index": 0, "id": "c0", "function": {"name": n, "arguments": ""}}]}))
            self.assertEqual(a.resultado("m")["tool_calls"][0]["function"]["name"], esperado, trozos)

    def test_dos_llamadas_fragmentadas_a_la_vez_no_se_mezclan(self):
        a = compute.AcumuladorSSE()
        for i, parte in ((0, "github_"), (1, "disco_"), (0, "leer"), (1, "escribir")):
            a.linea(chunk({"tool_calls": [{"index": i, "id": "c%d" % i, "function": {"name": parte}}]}))
        self.assertEqual([t["function"]["name"] for t in a.resultado("m")["tool_calls"]], ["github_leer", "disco_escribir"])

    def test_nombre_se_valida_contra_las_herramientas_declaradas(self):
        a = compute.AcumuladorSSE(herramientas=["github_leer", "disco_escribir"])
        a.linea(chunk({"tool_calls": [{"index": 0, "id": "c0", "function": {"name": "github_", "arguments": "{}"}}]}))
        a.linea(chunk({"tool_calls": [{"index": 1, "id": "c1", "function": {"name": "disco_escribir", "arguments": "{"}}]}))
        r = a.resultado("m")
        self.assertEqual(len(r["tool_calls"]), 2)  # no se pierde ninguna llamada pendiente: se marca, no se descarta
        inv = {x["id"]: x["motivo"] for x in r["tools_invalidas"]}
        self.assertEqual(inv, {"c0": "nombre_no_declarado", "c1": "argumentos_json_incompletos"})
        self.assertEqual(r["metricas"]["tools_invalidas"], 2)

    def test_sin_herramientas_declaradas_solo_se_valida_el_json(self):
        a = compute.AcumuladorSSE()
        a.linea(chunk({"tool_calls": [{"index": 0, "id": "c0", "function": {"name": "x", "arguments": '{"a":1}'}}]}))
        self.assertEqual(a.resultado("m")["tools_invalidas"], [])


class TestTimeoutConfigurable(unittest.TestCase):
    def test_prioridad_entorno_politica_defecto(self):
        with patch.dict(os.environ, {"RIU_EXTERNOS_TIMEOUT_S": ""}):
            self.assertEqual(compute.timeout_s(), 180.0)
            self.assertEqual(compute.timeout_s(45), 45.0)
            self.assertEqual(compute.timeout_s("basura"), 180.0)
            self.assertEqual(compute.timeout_s(-3), 180.0)
        with patch.dict(os.environ, {"RIU_EXTERNOS_TIMEOUT_S": "7.5"}):
            self.assertEqual(compute.timeout_s(45), 7.5)

    def test_el_cliente_qwen_no_cambia(self):  # Qwen sigue con urlopen sin tope propio (tests de test_compute.py)
        self.assertEqual(compute.REINTENTABLES, {429, 502, 503, 504})
        self.assertNotIn("stream", compute.OPCIONES)


if __name__ == "__main__":
    unittest.main()

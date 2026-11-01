"""Groq/NVIDIA en el Router MVP (ACELERADOR): catalogo PROVEEDORES_NUEVOS, parametros por modelo, conexiones persistentes,
reintentos con backoff+jitter+Retry-After, streaming SSE real, timeout configurable, disponibilidad real (GET /models) y
parciales hacia el chat. Servidores falsos en 127.0.0.1; claves ficticias; sin red real."""
import json
import os
import pathlib
import re
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from test_control import Base, CAB
from mvp import app as servicio, externos

RAIZ = pathlib.Path(__file__).resolve().parents[4]
ID_GROQ = "groq/qwen/qwen3.8-27b"
IDS_NVIDIA = ["nvidia/minimaxai/minimax-m3.1-flash", "nvidia/meta/muse-glimmer-30b", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/z-ai/glm-5.3"]
MSG = [{"role": "user", "content": "hola"}]


# ---------- servidor falso (compatible OpenAI) ----------
def ok(texto="ok", **mensaje):
    def f(h, cuerpo):
        doc = {"model": cuerpo["model"], "choices": [{"message": {"role": "assistant", "content": texto, **mensaje}, "finish_reason": "stop"}], "usage": {"completion_tokens": 4}}
        datos = json.dumps(doc).encode()
        h.send_response(200); h.send_header("Content-Type", "application/json"); h.send_header("Content-Length", str(len(datos))); h.end_headers(); h.wfile.write(datos)
    return f


def err(codigo, **cabeceras):
    def f(h, cuerpo):
        datos = b'{"error":{"message":"x"}}'
        h.send_response(codigo)
        for k, v in cabeceras.items():
            h.send_header(k.replace("_", "-"), v)
        h.send_header("Content-Length", str(len(datos))); h.end_headers(); h.wfile.write(datos)
    return f


def lento(segundos):
    def f(h, cuerpo):
        time.sleep(segundos)
        try: ok()(h, cuerpo)
        except OSError: pass
    return f


def sse(lineas, compuerta=None, tras=1):
    """Envia `tras` lineas, espera la compuerta (si hay) y envia el resto: prueba que el cliente lee de forma incremental."""
    def f(h, cuerpo):
        h.send_response(200); h.send_header("Content-Type", "text/event-stream"); h.send_header("Connection", "close"); h.end_headers()
        h.close_connection = True
        try:
            for i, linea in enumerate(lineas):
                if compuerta is not None and i == tras:
                    compuerta.wait(10)
                h.wfile.write(linea.encode() + b"\n\n"); h.wfile.flush()
        except OSError:
            pass
    return f


def delta(contenido=None, fin=None, **extra):
    d = {"content": contenido} if contenido is not None else {}
    return "data: " + json.dumps({"model": "m-real", "choices": [{"index": 0, "delta": {**d, **extra}, "finish_reason": fin}]})


class Servidor:
    def __init__(self, guion, modelos=None):
        self.guion, self.peticiones, self.conexiones, self.modelos = list(guion), [], 0, modelos or []
        s = self
        class H(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            def log_message(self, *a): pass
            def do_POST(self):
                cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                s.peticiones.append({"path": self.path, "auth": self.headers.get("Authorization"), "cuerpo": cuerpo})
                paso = s.guion.pop(0) if len(s.guion) > 1 else s.guion[0]
                paso(self, cuerpo)
            def do_GET(self):
                s.peticiones.append({"path": self.path, "auth": self.headers.get("Authorization"), "cuerpo": None})
                datos = json.dumps({"data": [{"id": m} for m in s.modelos]}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(datos))); self.end_headers(); self.wfile.write(datos)
        class S(ThreadingHTTPServer):
            daemon_threads = True
            def get_request(self_):
                r = super().get_request(); s.conexiones += 1; return r
        self.http = S(("127.0.0.1", 0), H)
        self.base = "http://127.0.0.1:%d/v1" % self.http.server_port
        threading.Thread(target=self.http.serve_forever, daemon=True).start()

    def cerrar(self):
        self.http.shutdown(); self.http.server_close()


class Entorno(unittest.TestCase):
    """Claves ficticias en el entorno, sin banco compartido y con reintentos sin dormir de verdad."""
    def setUp(self):
        limpio = {k: "" for k in os.environ if k.startswith(("GROQ_API_KEY", "NVIDIA_API_KEY"))}
        p = patch.dict(os.environ, {**limpio, "GROQ_API_KEY": "gsk-ficticia", "NVIDIA_API_KEY": "nv-ficticia", "RIU_BANCO_SWE": "/no/existe.bin",
                                    "RIU_EXTERNOS_TIMEOUT_S": "", "RIU_STREAM_EXTERNOS": ""})
        p.start(); self.addCleanup(p.stop)
        self.esperas = []
        for nombre, valor in (("_dormir", self.esperas.append), ("_azar", lambda: 0.0)):
            q = patch.object(externos, nombre, valor); q.start(); self.addCleanup(q.stop)
        externos.CACHE.clear(); externos._SWE.clear(); self.addCleanup(externos.CACHE.clear)
        externos.limpiar_enfriadas(); self.addCleanup(externos.limpiar_enfriadas)  # el cooldown de claves por 429 no se filtra entre pruebas
        self.srv = []
        self.addCleanup(lambda: [s.cerrar() for s in self.srv])

    def servidor(self, prov, *guion, **kw):
        s = Servidor(guion, **kw); self.srv.append(s)
        p = patch.dict(externos.PROVEEDORES[prov], {"base": s.base}); p.start(); self.addCleanup(p.stop)
        return s


class TestCatalogoYParametros(Entorno):
    def test_ids_y_parametros_del_director(self):
        n = externos.PROVEEDORES_NUEVOS
        self.assertEqual(list(n), [ID_GROQ] + IDS_NVIDIA)
        self.assertEqual(externos.PARAMETROS_MODELO[ID_GROQ], {"temperature": 1.0, "top_p": 0.95, "max_tokens": 2048, "reasoning_effort": "medium", "reasoning_format": "hidden"})
        for i in IDS_NVIDIA[:3]:
            self.assertEqual(externos.PARAMETROS_MODELO[i], {"temperature": 1.0, "top_p": 0.95, "max_tokens": 4096})
        self.assertEqual(externos.PARAMETROS_MODELO["nvidia/z-ai/glm-5.3"], {"temperature": 0.5, "top_p": 1.0, "max_tokens": 4096})
        self.assertEqual([n[i]["nombre"] for i in n], ["Qwen 3.8 27B", "MiniMax M3.1 Flash", "Muse Glimmer 30B", "Nemotron 3 Ultra 550B", "GLM 5.3"])
        for i, c in n.items():  # base y variable coinciden con el proveedor ya implementado; solo el NOMBRE de la variable, nunca su valor
            prov = externos.PROVEEDORES[c["proveedor"]]
            self.assertEqual((c["base_url"], c["env"], externos.proveedor(i)), (prov["base"], prov["var"], c["proveedor"]))

    def test_muse_glimmer_aparece_una_sola_vez(self):
        self.assertEqual(sum(1 for i in externos.PROVEEDORES_NUEVOS if "muse-glimmer" in i), 1)

    def test_sin_credenciales_en_el_codigo_ni_en_la_politica(self):
        pol = RAIZ / "router-mvp/fichas/fichas_qwen/fichas/politicas_modelo.json"
        for ruta in (pathlib.Path(externos.__file__), pol, pathlib.Path(externos.__file__).with_name("compute.py")):
            self.assertIsNone(re.search(r"gsk_[A-Za-z0-9]{10,}|nvapi-[A-Za-z0-9_\-]{10,}", ruta.read_text(encoding="utf-8")), ruta.name)

    def test_llamar_aplica_los_parametros_y_conserva_el_modelo_sin_prefijo(self):
        s = self.servidor("groq", ok("hola"))
        r = externos.llamar(MSG, ID_GROQ)
        c = s.peticiones[0]["cuerpo"]
        self.assertEqual((c["model"], c["temperature"], c["top_p"], c["max_tokens"], c["reasoning_effort"], c["reasoning_format"]), ("qwen/qwen3.8-27b", 1.0, 0.95, 2048, "medium", "hidden"))
        self.assertEqual((s.peticiones[0]["path"], s.peticiones[0]["auth"]), ("/v1/chat/completions", "Bearer gsk-ficticia"))
        self.assertNotIn("stream", c)
        self.assertEqual((r["texto"], r["modelo_solicitado"], r["finish_reason"], r["uso"]), ("hola", ID_GROQ, "stop", {"completion_tokens": 4}))

    def test_glm_usa_temperatura_05_y_no_envia_razonamiento(self):
        s = self.servidor("nvidia", ok())
        externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        c = s.peticiones[0]["cuerpo"]
        self.assertEqual((c["model"], c["temperature"], c["top_p"], c["max_tokens"]), ("z-ai/glm-5.3", 0.5, 1.0, 4096))
        self.assertNotIn("reasoning_effort", c)

    def test_los_parametros_explicitos_del_llamador_van_despues_de_los_del_modelo(self):
        """R7 (auditoria GPT, mas reciente que el payload.update literal del Director): defecto del modelo primero y despues los explicitos VALIDOS del llamador."""
        s = self.servidor("nvidia", ok())
        externos.llamar(MSG, "nvidia/meta/muse-glimmer-30b", opciones={"max_tokens": 10, "temperature": 0.2, "tool_choice": "auto"})
        c = s.peticiones[0]["cuerpo"]
        self.assertEqual((c["max_tokens"], c["temperature"], c["top_p"], c["tool_choice"]), (10, 0.2, 0.95, "auto"))  # top_p: no lo pidio el llamador, queda el del modelo

    def test_sin_opciones_manda_los_valores_por_defecto_del_modelo(self):
        s = self.servidor("nvidia", ok())
        externos.llamar(MSG, "nvidia/meta/muse-glimmer-30b")
        c = s.peticiones[0]["cuerpo"]
        self.assertEqual((c["max_tokens"], c["temperature"], c["top_p"]), (4096, 1.0, 0.95))

    def test_limite_real_de_groq_qwen38_16384_tokens_de_salida(self):
        """Fuente oficial: console.groq.com/docs/models y /docs/model/qwen/qwen3.8-27b -> MAX OUTPUT/COMPLETION TOKENS 16,384 (contexto 131,072)."""
        self.assertEqual(externos.LIMITES_MODELO[ID_GROQ]["max_tokens"], 16384)
        s = self.servidor("groq", ok())
        r = externos.llamar(MSG, ID_GROQ, opciones={"max_tokens": 99999})
        self.assertEqual(s.peticiones[0]["cuerpo"]["max_tokens"], 16384)
        self.assertEqual(r["metricas"]["parametros"]["recortados"], {"max_tokens": {"pedido": 99999, "aplicado": 16384}})  # el recorte NO es silencioso
        externos.llamar(MSG, ID_GROQ, opciones={"max_tokens": 16384})
        self.assertEqual(s.peticiones[1]["cuerpo"]["max_tokens"], 16384)

    def test_valores_invalidos_se_ignoran_y_se_avisa(self):
        s = self.servidor("groq", ok())
        r = externos.llamar(MSG, ID_GROQ, opciones={"temperature": "caliente", "max_tokens": -5, "top_p": 7, "reasoning_effort": "extremo"})
        c = s.peticiones[0]["cuerpo"]
        self.assertEqual((c["temperature"], c["max_tokens"], c["top_p"], c["reasoning_effort"]), (1.0, 2048, 0.95, "medium"))
        self.assertEqual(sorted(r["metricas"]["parametros"]["ignorados"]), ["max_tokens", "reasoning_effort", "temperature", "top_p"])

    def test_reasoning_explicito_valido_se_respeta_solo_donde_el_modelo_lo_admite(self):
        s = self.servidor("groq", ok())
        externos.llamar(MSG, ID_GROQ, opciones={"reasoning_effort": "high", "reasoning_format": "parsed"})
        c = s.peticiones[0]["cuerpo"]
        self.assertEqual((c["reasoning_effort"], c["reasoning_format"]), ("high", "parsed"))
        n = self.servidor("nvidia", ok())
        r = externos.llamar(MSG, "nvidia/z-ai/glm-5.3", opciones={"reasoning_effort": "high", "enable_thinking": True})
        self.assertNotIn("reasoning_effort", n.peticiones[0]["cuerpo"]); self.assertNotIn("enable_thinking", n.peticiones[0]["cuerpo"])
        self.assertIn("reasoning_effort", r["metricas"]["parametros"]["ignorados"])

    def test_modelo_ajeno_al_catalogo_sigue_funcionando_sin_parametros_extra(self):
        s = self.servidor("groq", ok())
        externos.llamar(MSG, "groq/llama-3.3-70b-versatile", opciones={"temperature": 0.2})
        c = s.peticiones[0]["cuerpo"]
        self.assertEqual((c["model"], c["temperature"]), ("llama-3.3-70b-versatile", 0.2)); self.assertNotIn("reasoning_format", c)


class TestConexionesYReintentos(Entorno):
    def test_conexion_persistente_se_reutiliza(self):
        s = self.servidor("nvidia", ok())
        for _ in range(3):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual((len(s.peticiones), s.conexiones), (3, 1))

    def test_retry_after_se_respeta(self):
        s = self.servidor("nvidia", err(429, Retry_After="2"), ok("listo"))
        self.assertEqual(externos.llamar(MSG, "nvidia/z-ai/glm-5.3")["texto"], "listo")
        self.assertEqual((self.esperas, len(s.peticiones)), ([2.0], 2))

    def test_retry_after_enorme_se_acota(self):
        self.servidor("nvidia", err(503, Retry_After="99999"), ok())
        externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual(self.esperas, [60.0])

    def test_retry_after_en_fecha_http(self):
        fecha = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time() + 5))
        self.servidor("nvidia", err(429, Retry_After=fecha), ok())
        externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual(len(self.esperas), 1); self.assertTrue(3.0 <= self.esperas[0] <= 6.0, self.esperas)

    def test_backoff_exponencial_con_jitter(self):
        self.servidor("nvidia", err(503), err(502), ok())
        with patch.object(externos, "_azar", lambda: 0.0):  # jitter minimo: la mitad
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual(self.esperas, [0.25, 0.5])
        self.esperas.clear()
        self.servidor("nvidia", err(503), err(502), ok())
        with patch.object(externos, "_azar", lambda: 1.0):  # jitter maximo: el valor completo base*2**n
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual(self.esperas, [0.5, 1.0])

    def test_reintentos_agotados_dejan_el_codigo_del_proveedor(self):
        s = self.servidor("nvidia", err(503))
        with self.assertRaisesRegex(RuntimeError, "HTTP 503"):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual((len(s.peticiones), len(self.esperas)), (3, 2))

    def test_error_no_transitorio_no_se_reintenta(self):
        s = self.servidor("nvidia", err(400))
        with self.assertRaisesRegex(RuntimeError, "HTTP 400"):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual((len(s.peticiones), self.esperas), (1, []))

    def test_429_con_otra_clave_disponible_rota_sin_esperar(self):
        s = self.servidor("groq", lambda h, c: (err(429, Retry_After="30") if h.headers["Authorization"] == "Bearer gsk-ficticia" else ok("de la 2"))(h, c))
        with patch.dict(os.environ, {"GROQ_API_KEY_2": "gsk-ficticia-2"}):
            r = externos.llamar(MSG, ID_GROQ)
        self.assertEqual((r["texto"], self.esperas, [p["auth"] for p in s.peticiones]), ("de la 2", [], ["Bearer gsk-ficticia", "Bearer gsk-ficticia-2"]))

    def test_401_rota_a_la_siguiente_clave(self):  # rotacion existente conservada
        s = self.servidor("groq", lambda h, c: (err(401) if h.headers["Authorization"] == "Bearer gsk-ficticia" else ok())(h, c))
        with patch.dict(os.environ, {"GROQ_API_KEY_2": "gsk-ficticia-2"}):
            self.assertEqual(externos.llamar(MSG, ID_GROQ)["texto"], "ok")
        self.assertEqual(len(s.peticiones), 2)

    def test_la_politica_manda_el_maximo_de_intentos(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = pathlib.Path(d) / "pol.json"
            ruta.write_text(json.dumps({"politicas_externos": {"nvidia/z-ai/glm-5.3": {"reintentos": {"max": 1}}}}))
            with patch.dict(os.environ, {"RIU_POLITICAS_MODELO": str(ruta)}):
                externos._POL.clear()
                s = self.servidor("nvidia", err(503))
                with self.assertRaisesRegex(RuntimeError, "HTTP 503"):
                    externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
                self.assertEqual(len(s.peticiones), 1)
        externos._POL.clear()

    def test_timeout_configurable_por_entorno(self):
        s = self.servidor("nvidia", lento(1.0))
        t0 = time.monotonic()
        with patch.dict(os.environ, {"RIU_EXTERNOS_TIMEOUT_S": "0.2"}), self.assertRaisesRegex(RuntimeError, "error de red.*tiempo"):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertLess(time.monotonic() - t0, 0.9); self.assertEqual(len(s.peticiones), 3)

    def test_sin_httpx_funciona_con_urllib(self):
        s = self.servidor("nvidia", ok("urllib"))
        with patch.object(externos, "_httpx", None):
            self.assertEqual(externos.llamar(MSG, "nvidia/z-ai/glm-5.3")["texto"], "urllib")
            self.esperas.clear(); s.guion[:] = [err(429, Retry_After="1"), ok("de nuevo")]
            self.assertEqual(externos.llamar(MSG, "nvidia/z-ai/glm-5.3")["texto"], "de nuevo"); self.assertEqual(self.esperas, [1.0])


class TestDisponibilidad(Entorno):
    def test_catalogo_real_get_models_y_modelo_ausente_no_se_cambia_en_silencio(self):
        s = self.servidor("nvidia", ok(), modelos=["z-ai/glm-5.3", "meta/llama-3.1-8b-instruct"])
        ids = externos.modelos("nvidia")
        self.assertEqual(ids, ["nvidia/meta/llama-3.1-8b-instruct", "nvidia/z-ai/glm-5.3"])
        self.assertEqual(s.peticiones[0]["path"], "/v1/models")
        self.assertIs(externos.disponible("nvidia/z-ai/glm-5.3"), True)
        self.assertIs(externos.disponible("nvidia/meta/muse-glimmer-30b"), False)
        with self.assertRaisesRegex(RuntimeError, r"NO DISPONIBLE.*muse-glimmer-30b.*no se cambi"):
            externos.llamar(MSG, "nvidia/meta/muse-glimmer-30b")
        self.assertEqual([p["path"] for p in s.peticiones], ["/v1/models"])  # ni una llamada de chat a ningun otro modelo

    def test_sin_catalogo_en_cache_se_intenta_y_el_404_se_explica(self):
        s = self.servidor("nvidia", err(404))
        self.assertIsNone(externos.disponible("nvidia/z-ai/glm-5.3"))
        with self.assertRaisesRegex(RuntimeError, r"HTTP 404.*z-ai/glm-5\.3.*no se cambi"):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertTrue(all(p["cuerpo"]["model"] == "z-ai/glm-5.3" for p in s.peticiones))

    def test_modelo_ajeno_al_catalogo_curado_no_se_bloquea_por_la_cache(self):
        self.servidor("nvidia", ok("x"))
        externos.CACHE["nvidia"] = (time.time(), ["nvidia/otro"])
        self.assertEqual(externos.llamar(MSG, "nvidia/meta/llama-3.1-8b-instruct")["texto"], "x")


class TestStreaming(Entorno):
    def test_el_texto_llega_a_medida_que_el_proveedor_lo_envia(self):
        compuerta, primero, vistos = threading.Event(), threading.Event(), []
        lineas = [delta("Hola "), delta("mundo"), delta(None, "stop"), 'data: {"choices": [], "usage": {"prompt_tokens": 3, "completion_tokens": 6}}', "data: [DONE]"]
        s = self.servidor("nvidia", sse(lineas, compuerta))
        def parcial(total, frag):
            vistos.append(total); primero.set()
        salida = {}
        h = threading.Thread(target=lambda: salida.update(externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=parcial)))
        h.start()
        self.assertTrue(primero.wait(5)); self.assertEqual(vistos, ["Hola "]); self.assertFalse(salida)  # aun no termino y ya hay texto
        compuerta.set(); h.join(5)
        self.assertEqual(vistos, ["Hola ", "Hola mundo"])
        self.assertEqual((salida["texto"], salida["finish_reason"], salida["uso"], salida["modelo_solicitado"], salida["modelo_respuesta"]),
                         ("Hola mundo", "stop", {"prompt_tokens": 3, "completion_tokens": 6}, "nvidia/z-ai/glm-5.3", "m-real"))
        c = s.peticiones[0]["cuerpo"]
        self.assertEqual((c["stream"], c["stream_options"], c["model"]), (True, {"include_usage": True}, "z-ai/glm-5.3"))
        m = salida["metricas"]
        self.assertTrue(m["stream"] and m["ttft_s"] is not None and m["tokens"] == 6)

    def test_tool_calls_por_indice_y_finish_reason_en_stream(self):
        tc = lambda **k: delta(None, None, tool_calls=[k])
        lineas = [tc(index=0, id="c1", type="function", function={"name": "leer", "arguments": ""}), tc(index=0, function={"arguments": '{"a":'}),
                  tc(index=0, function={"arguments": '1}'}), delta(None, "tool_calls"), "data: [DONE]"]
        self.servidor("nvidia", sse(lineas, tras=99))
        r = externos.llamar(MSG, "nvidia/z-ai/glm-5.3", opciones={"tools": [{"type": "function", "function": {"name": "leer"}}]}, al_parcial=lambda t, f: None)
        self.assertEqual((r["finish_reason"], r["texto"], [(t["id"], t["function"]["name"], t["function"]["arguments"]) for t in r["tool_calls"]]), ("tool_calls", "", [("c1", "leer", '{"a":1}')]))
        self.assertEqual(r["mensaje_asistente"]["tool_calls"], r["tool_calls"])

    def test_sin_callback_no_hay_stream(self):
        s = self.servidor("nvidia", ok())
        externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertNotIn("stream", s.peticiones[0]["cuerpo"])

    def test_el_streaming_se_apaga_por_entorno_y_por_politica(self):
        s = self.servidor("nvidia", ok("completo"))
        with patch.dict(os.environ, {"RIU_STREAM_EXTERNOS": "0"}):
            r = externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=lambda t, f: None)
        self.assertEqual((r["texto"], "stream" in s.peticiones[0]["cuerpo"]), ("completo", False))
        with tempfile.TemporaryDirectory() as d:
            ruta = pathlib.Path(d) / "pol.json"
            ruta.write_text(json.dumps({"politicas_externos": {"nvidia/z-ai/glm-5.3": {"streaming": {"activable": False}}}}))
            with patch.dict(os.environ, {"RIU_POLITICAS_MODELO": str(ruta)}):
                externos._POL.clear()
                externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=lambda t, f: None)
        externos._POL.clear()
        self.assertNotIn("stream", s.peticiones[1]["cuerpo"])

    def test_si_el_proveedor_rechaza_stream_se_repite_sin_stream_con_el_mismo_modelo(self):
        s = self.servidor("nvidia", err(400), ok("sin stream"))
        r = externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=lambda t, f: None)
        self.assertEqual(r["texto"], "sin stream")
        self.assertEqual([("stream" in p["cuerpo"], p["cuerpo"]["model"]) for p in s.peticiones], [(True, "z-ai/glm-5.3"), (False, "z-ai/glm-5.3")])

    def test_429_en_stream_respeta_retry_after(self):
        self.servidor("nvidia", err(429, Retry_After="3"), sse([delta("ok"), delta(None, "stop"), "data: [DONE]"], tras=99))
        r = externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=lambda t, f: None)
        self.assertEqual((r["texto"], self.esperas), ("ok", [3.0]))

    def test_corte_a_mitad_del_stream_no_se_reintenta_ni_duplica_texto(self):
        vistos = []
        s = self.servidor("nvidia", sse([delta("parte"), "data: [DONE]"][:1], tras=99))  # termina sin finish_reason ni [DONE]
        with self.assertRaisesRegex(RuntimeError, "error de red.*interrumpido"):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=lambda t, f: vistos.append(t))
        self.assertEqual((vistos, len(s.peticiones)), (["parte"], 1))

    def test_error_dentro_del_stream_se_propaga(self):
        s = self.servidor("nvidia", sse([delta("a"), 'data: {"error": {"message": "boom", "code": 500}}'], tras=99))
        with self.assertRaisesRegex(RuntimeError, "boom"):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=lambda t, f: None)
        self.assertEqual(len(s.peticiones), 1)

    def test_un_fallo_del_callback_no_rompe_la_respuesta(self):
        self.servidor("nvidia", sse([delta("a"), delta(None, "stop"), "data: [DONE]"], tras=99))
        def mal(t, f): raise ValueError("x")
        self.assertEqual(externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=mal)["texto"], "a")

    def test_sin_httpx_el_stream_tambien_funciona(self):
        self.servidor("nvidia", sse([delta("u"), delta("rllib"), delta(None, "stop"), "data: [DONE]"], tras=99))
        with patch.object(externos, "_httpx", None):
            self.assertEqual(externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=lambda t, f: None)["texto"], "urllib")

    def test_metricas_tambien_sin_stream(self):
        self.servidor("nvidia", ok("x"))
        m = externos.llamar(MSG, "nvidia/z-ai/glm-5.3")["metricas"]
        self.assertEqual((m["stream"], m["ttft_s"], m["tokens"]), (False, None, 4)); self.assertIsNotNone(m["duracion_s"])


class TestPoliticasYContexto(Entorno):
    def test_politicas_nvidia_groq_en_el_json_sin_tocar_las_de_qwen(self):
        d = json.loads((RAIZ / "router-mvp/fichas/fichas_qwen/fichas/politicas_modelo.json").read_text(encoding="utf-8"))
        self.assertEqual(list(d["politicas_modelo"]), ["ficha-qwen38flash", "ficha-qwen36flash", "ficha-dsv4pro", "ficha-dsv4pro0813", "ficha-dsv4flash", "ficha-glm52", "ficha-qwen38max"])
        ext = d["politicas_externos"]
        for i, cfg in externos.PROVEEDORES_NUEVOS.items():
            p = ext[i]
            for campo in ("streaming", "reintentos", "timeout_s", "parametros_compatibles", "contexto", "preservar"):
                self.assertIn(campo, p, i + "." + campo)
            self.assertEqual(set(p["parametros_compatibles"]) & {"temperature", "top_p", "max_tokens", "reasoning_effort", "reasoning_format"}, set(externos.PARAMETROS_MODELO[i]))
            self.assertTrue({"tool_calls", "finish_reason", "usage"} <= set(p["preservar"]))
            self.assertEqual(externos.politica(i)["reintentos"]["max"], p["reintentos"]["max"])

    def test_streaming_con_tools_se_puede_apagar_por_politica(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = pathlib.Path(d) / "pol.json"
            ruta.write_text(json.dumps({"politicas_externos": {"nvidia/z-ai/glm-5.3": {"streaming": {"con_tools": False}}}}))
            s = self.servidor("nvidia", ok())
            with patch.dict(os.environ, {"RIU_POLITICAS_MODELO": str(ruta)}):
                externos._POL.clear()
                externos.llamar(MSG, "nvidia/z-ai/glm-5.3", opciones={"tools": [{"type": "function", "function": {"name": "f"}}]}, al_parcial=lambda t, f: None)
            externos._POL.clear()
        self.assertNotIn("stream", s.peticiones[0]["cuerpo"])

    def test_parametros_incompatibles_segun_politica_se_quitan(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = pathlib.Path(d) / "pol.json"
            ruta.write_text(json.dumps({"politicas_externos": {ID_GROQ: {"parametros_compatibles": ["temperature", "max_tokens"]}}}))
            s = self.servidor("groq", ok())
            with patch.dict(os.environ, {"RIU_POLITICAS_MODELO": str(ruta)}):
                externos._POL.clear(); externos.llamar(MSG, ID_GROQ)
            externos._POL.clear()
        c = s.peticiones[0]["cuerpo"]
        self.assertEqual((c["temperature"], c["max_tokens"]), (1.0, 2048)); self.assertNotIn("reasoning_format", c); self.assertNotIn("top_p", c)

    def test_contexto_solo_recorta_resultados_viejos_de_herramientas_y_solo_sobre_el_tope(self):
        grande = "x" * 5000
        msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"},
                {"role": "assistant", "content": None, "tool_calls": [{"id": "1", "type": "function", "function": {"name": "f", "arguments": "{}"}}]},
                {"role": "tool", "tool_call_id": "1", "content": grande}, {"role": "assistant", "content": "r"}, {"role": "user", "content": "otra"}]
        pol = {"contexto": {"max_caracteres": 1000, "resultado_tool_max": 100, "recientes": 2}}
        out = externos._compactar(msgs, pol)
        self.assertLess(len(out[3]["content"]), 300); self.assertIn("recortado", out[3]["content"])
        self.assertEqual([m for i, m in enumerate(out) if i != 3], [m for i, m in enumerate(msgs) if i != 3])  # nada mas cambia
        self.assertEqual(msgs[3]["content"], grande)  # no muta el original
        self.assertEqual(externos._compactar(msgs, {"contexto": {"max_caracteres": 10**6, "resultado_tool_max": 100, "recientes": 2}}), msgs)
        reciente = msgs[:-1] + [{"role": "tool", "tool_call_id": "1", "content": grande}]
        self.assertEqual(externos._compactar(reciente, pol)[-1]["content"], grande)  # lo reciente se conserva


class TestAppParciales(Base):
    """El chat recibe el texto progresivo por el mecanismo existente: TRABAJOS[pid]['parcial'] (lo lee /resultado y api.js)."""
    def setUp(self):
        limpio = {k: "" for k in os.environ if k.startswith(("GROQ_API_KEY", "NVIDIA_API_KEY"))}
        p = patch.dict(os.environ, {**limpio, "NVIDIA_API_KEY": "nv-ficticia", "RIU_BANCO_SWE": "/no/existe.bin", "RIU_EXTERNOS_TIMEOUT_S": "", "RIU_STREAM_EXTERNOS": ""})
        p.start(); self.addCleanup(p.stop)  # antes que Base.setUp: su cleanup corre DESPUES del tearDown de Base y devuelve el entorno original
        super().setUp()
        externos.CACHE.clear(); self.addCleanup(externos.CACHE.clear)
        self.banco.datos.pop("NVIDIA_API_KEY", None)

    def _correr(self, ruta, cuerpo):
        compuerta, salida = threading.Event(), {}
        lineas = [delta("Hola "), delta("mundo"), delta(None, "stop"), "data: [DONE]"]
        srv = Servidor([sse(lineas, compuerta)])
        self.addCleanup(srv.cerrar)
        p = patch.dict(externos.PROVEEDORES["nvidia"], {"base": srv.base}); p.start(); self.addCleanup(p.stop)
        servicio.TRABAJOS["p-parcial"] = {"estado": "procesando", "proceso_id": "p-parcial"}
        self.addCleanup(servicio.TRABAJOS.pop, "p-parcial", None)
        h = threading.Thread(target=lambda: salida.update(r=self.client.post(ruta, headers=CAB, json=cuerpo)))
        h.start()
        for _ in range(100):
            if servicio.TRABAJOS["p-parcial"].get("parcial"): break
            time.sleep(0.05)
        antes = servicio.TRABAJOS["p-parcial"].get("parcial")
        compuerta.set(); h.join(10)
        return antes, salida["r"], srv

    def test_chat_directo_con_tarea_id_deja_el_parcial_antes_de_terminar(self):
        antes, r, srv = self._correr("/chat", {"modelo": "nvidia/z-ai/glm-5.3", "mensajes": MSG, "tarea_id": "p-parcial"})
        self.assertEqual(antes, "Hola ")
        self.assertEqual(r.status_code, 200, r.text); self.assertEqual((r.json()["texto"], r.json()["finish_reason"]), ("Hola mundo", "stop"))
        self.assertEqual(servicio.TRABAJOS["p-parcial"]["parcial"], "Hola mundo")
        self.assertTrue(r.json()["metricas"]["stream"]); self.assertIsNotNone(r.json()["metricas"]["ttft_s"])  # TTFT y tokens/s llegan al cliente del Router
        self.assertEqual(srv.peticiones[0]["cuerpo"]["model"], "z-ai/glm-5.3")

    def test_llm_de_la_ficha_tambien_entrega_parciales(self):
        antes, r, _ = self._correr("/plugins/fichas_qwen/call/llm", {"modelo": "nvidia/z-ai/glm-5.3", "messages": MSG, "tarea_id": "p-parcial"})
        self.assertEqual(antes, "Hola "); self.assertEqual(r.json()["result"]["texto"], "Hola mundo"); self.assertTrue(r.json()["result"]["metricas"]["stream"])

    def test_resultado_expone_el_parcial_con_el_mecanismo_existente(self):
        servicio.TRABAJOS["p-x"] = {"estado": "procesando", "proceso_id": "p-x", "parcial": "Hola "}
        self.addCleanup(servicio.TRABAJOS.pop, "p-x", None)
        r = self.client.post("/plugins/puente_chat/call/resultado", headers=CAB, json={"proceso_id": "p-x"})
        self.assertEqual(r.json()["result"]["parcial"], "Hola ")

    def test_el_long_poll_de_resultado_responde_apenas_hay_texto_nuevo(self):
        servicio.TRABAJOS["p-lp"] = {"estado": "procesando", "proceso_id": "p-lp"}
        self.addCleanup(servicio.TRABAJOS.pop, "p-lp", None)
        threading.Timer(0.5, lambda: servicio.TRABAJOS["p-lp"].update(parcial="Hola")).start()
        t0 = time.monotonic()
        r = self.client.post("/plugins/puente_chat/call/resultado", headers=CAB, json={"proceso_id": "p-lp", "espera": 8})
        self.assertLess(time.monotonic() - t0, 3)
        self.assertEqual((r.json()["result"]["estado"], r.json()["result"]["parcial"]), ("procesando", "Hola"))

    def test_sin_tarea_id_no_hay_stream_y_la_respuesta_es_la_misma(self):
        srv = Servidor([ok("entera")]); self.addCleanup(srv.cerrar)
        p = patch.dict(externos.PROVEEDORES["nvidia"], {"base": srv.base}); p.start(); self.addCleanup(p.stop)
        r = self.client.post("/chat", headers=CAB, json={"modelo": "nvidia/z-ai/glm-5.3", "mensajes": MSG})
        self.assertEqual((r.status_code, r.json()["texto"], "stream" in srv.peticiones[0]["cuerpo"]), (200, "entera", False))


if __name__ == "__main__":
    unittest.main()

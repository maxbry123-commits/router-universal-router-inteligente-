"""A5-proveedores sobre externos.py/compute.py: R8 (timeouts unificados), R9 (metricas con origen), 152 (tabla de errores), 153-155 (Retry-After, backoff, tope),
156-161 (modelo realmente usado visible), 184 (TTL del catalogo), 186 (contexto sin recortes silenciosos), 192 (observabilidad sin credenciales).
Servidores falsos en 127.0.0.1; claves ficticias; sin red real."""
import json
import logging
import os
import pathlib
import re
import unittest
from unittest.mock import patch
from mvp import compute, externos, harness_client
from test_externos_nuevos import Entorno, ID_GROQ, IDS_NVIDIA, MSG, err, ok, lento, sse, delta
import test_externos_nuevos as base

RAIZ = pathlib.Path(__file__).resolve().parents[4]
POLITICAS = RAIZ / "router-mvp/fichas/fichas_qwen/fichas/politicas_modelo.json"


class TestTimeoutsUnificados(Entorno):
    def test_tabla_unica_cubre_el_catalogo_y_coincide_con_la_politica_del_json(self):
        pol = json.loads(POLITICAS.read_text(encoding="utf-8"))["politicas_externos"]
        self.assertEqual(set(compute.TIMEOUTS_MODELO_S), set(externos.PROVEEDORES_NUEVOS))
        for mid, t in compute.TIMEOUTS_MODELO_S.items():
            self.assertEqual(pol[mid]["timeout_s"], t, mid)  # Groq 60 s en TODAS partes (antes 60 en el bridge y 90 en este JSON)
            self.assertEqual(externos.politica(mid)["timeout_s"], t, mid)
        self.assertEqual(compute.TIMEOUTS_MODELO_S[ID_GROQ], 60)

    def test_el_plazo_total_de_reintentos_cabe_en_el_timeout_del_harness(self):
        """Capas: peticion (modelo) < presupuesto de reintentos == TIMEOUT_LLM_S del cliente del Harness; ningun reintento puede empezar si ya no cabe."""
        self.assertEqual(compute.PRESUPUESTO_TOTAL_S, harness_client.TIMEOUT_LLM_S)
        self.assertEqual(externos.politica(ID_GROQ)["reintentos"]["presupuesto_s"], compute.PRESUPUESTO_TOTAL_S)
        for t in compute.TIMEOUTS_MODELO_S.values():
            self.assertLessEqual(t, compute.PRESUPUESTO_TOTAL_S)

    def test_la_tabla_documentada_incluye_todas_las_capas(self):
        capas = {c["capa"] for c in compute.TABLA_TIMEOUTS}
        self.assertTrue({"modelo", "bridge", "harness", "proxy"} <= capas)
        for c in compute.TABLA_TIMEOUTS:
            self.assertTrue(c["donde"] and c["variable"] and isinstance(c["segundos"], (int, float)) and c["segundos"] > 0, c)
        bridge = [c for c in compute.TABLA_TIMEOUTS if c["capa"] == "bridge"][0]
        self.assertEqual(bridge["segundos"], 100)  # BRIDGE_DEADLINE_MS por defecto (server.js); ningun tiempo por peticion del bridge lo supera (respaldo.js lo recorta)

    def test_el_presupuesto_corta_los_reintentos_cuando_ya_no_caben(self):
        s = self.servidor("nvidia", err(503))
        reloj = iter(range(0, 10000, 50))  # cada consulta del reloj avanza 50 s: tras el primer fallo ya han pasado 50 s
        pol = {**externos.politica("nvidia/z-ai/glm-5.3"), "reintentos": {**externos.POLITICA_DEFECTO["reintentos"], "max": 5, "presupuesto_s": 100}, "timeout_s": 90}
        with patch.object(externos, "politica", lambda m: pol), patch.object(externos, "_reloj", lambda: next(reloj)), self.assertRaisesRegex(RuntimeError, "no caben en el presupuesto"):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual(len(s.peticiones), 1)  # 50 s gastados + espera + 90 s de timeout > 100 s: no se reintenta
        self.assertEqual(self.esperas, [])


class TestMetricasConOrigen(unittest.TestCase):
    def _acu(self, lineas, reloj):
        a = compute.AcumuladorSSE(reloj=lambda r=iter(reloj): next(r))
        for l in lineas:
            a.linea(l)
        return a.resultado("m")["metricas"]

    def test_tokens_de_usage_son_del_proveedor(self):
        m = self._acu([base.delta("a"), base.delta("b", "stop").replace('"finish_reason": "stop"}]', '"finish_reason": "stop"}], "usage": {"completion_tokens": 40}')], [0.0, 0.5, 2.5])
        self.assertEqual((m["tokens"], m["origen_tokens"], m["tokens_estimados"], m["tokens_por_s"]), (40, "proveedor", False, 20.0))
        self.assertEqual((m["ttft_s"], m["duracion_s"]), (0.5, 2.5))

    def test_sin_usage_los_tokens_son_estimados_y_se_dice(self):
        m = self._acu([base.delta("a"), base.delta("b"), base.delta(None, "stop")], [0.0, 1.0, 3.0])
        self.assertEqual((m["origen_tokens"], m["tokens_estimados"], m["tokens"]), ("estimado", True, 2))

    def test_sin_datos_no_hay_origen(self):
        m = compute.AcumuladorSSE().resultado("m")["metricas"]
        self.assertIsNone(m["origen_tokens"])


class TestMetricasAmbosCaminos(Entorno):
    def test_camino_sin_stream_trae_duracion_tokens_del_proveedor_y_ttft_no_aplicable(self):
        self.servidor("nvidia", ok())
        m = externos.llamar(MSG, "nvidia/z-ai/glm-5.3")["metricas"]
        self.assertEqual((m["stream"], m["origen_tokens"], m["tokens"], m["ttft_s"]), (False, "proveedor", 4, None))
        self.assertGreater(m["duracion_s"], 0); self.assertEqual(m["ttft_origen"], "no_aplica_sin_stream")

    def test_camino_stream_trae_ttft_medido_y_el_mismo_conjunto_de_campos(self):
        self.servidor("nvidia", sse([delta("Hola"), delta(None, "stop"), "data: [DONE]"]))
        m = externos.llamar(MSG, "nvidia/z-ai/glm-5.3", al_parcial=lambda t, f: None)["metricas"]
        self.assertTrue(m["stream"] and m["ttft_s"] is not None and m["ttft_s"] >= 0)
        for campo in ("ttft_s", "duracion_s", "tokens", "tokens_por_s", "tokens_estimados", "origen_tokens"):
            self.assertIn(campo, m)

    def test_sin_usage_en_no_stream_no_se_inventan_tokens(self):
        def sin_uso(h, c):
            datos = json.dumps({"model": c["model"], "choices": [{"message": {"role": "assistant", "content": "x"}, "finish_reason": "stop"}]}).encode()
            h.send_response(200); h.send_header("Content-Type", "application/json"); h.send_header("Content-Length", str(len(datos))); h.end_headers(); h.wfile.write(datos)
        self.servidor("nvidia", sin_uso)
        m = externos.llamar(MSG, "nvidia/z-ai/glm-5.3")["metricas"]
        self.assertEqual((m["tokens"], m["origen_tokens"], m["tokens_por_s"]), (None, None, None))


class TestTablaDeErrores(Entorno):
    """152: cada familia de error tiene una politica distinta y queda clasificada en el error final."""
    def test_clasificacion(self):
        c = externos.clasificar_error
        self.assertEqual(c(429)["tipo"], "limite_temporal"); self.assertEqual(c(402)["tipo"], "credito_cuota")
        self.assertEqual(c(401)["tipo"], "credencial_permiso"); self.assertEqual(c(403)["tipo"], "credencial_permiso")
        self.assertEqual(c(408)["tipo"], "timeout_red"); self.assertEqual(c(None, red=True)["tipo"], "timeout_red")
        for k in (500, 502, 503, 504, 529):
            self.assertEqual(c(k)["tipo"], "servidor_temporal", k)
        for k in (400, 404, 422):
            self.assertEqual(c(k)["tipo"], "peticion_invalida", k)
        pol = {t: (c(k)["reintentar"], c(k)["rotar_clave"], c(k)["respeta_retry_after"], c(k)["enfriar_clave"]) for t, k in
               (("limite_temporal", 429), ("credito_cuota", 402), ("credencial_permiso", 401), ("servidor_temporal", 503), ("peticion_invalida", 400))}
        self.assertEqual(len(set(pol.values())), 5)  # politica distinta por tipo

    def test_error_final_lleva_tipo_y_codigo(self):
        self.servidor("nvidia", err(503))
        with self.assertRaises(externos.ErrorProveedor) as cm:
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual((cm.exception.tipo, cm.exception.codigo), ("servidor_temporal", 503)); self.assertIn("HTTP 503", str(cm.exception))
        self.servidor("nvidia", err(400))
        with self.assertRaises(externos.ErrorProveedor) as cm:
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual((cm.exception.tipo, cm.exception.reintentable), ("peticion_invalida", False))

    def test_402_rota_de_clave_sin_reintentar_la_misma(self):
        s = self.servidor("groq", lambda h, c: (err(402) if h.headers["Authorization"] == "Bearer gsk-ficticia" else ok("de la 2"))(h, c))
        with patch.dict(os.environ, {"GROQ_API_KEY_2": "gsk-ficticia-2"}):
            r = externos.llamar(MSG, ID_GROQ)
        self.assertEqual((r["texto"], self.esperas, len(s.peticiones)), ("de la 2", [], 2))
        s.guion[:] = [ok("otra vez")]; s.peticiones.clear()
        with patch.dict(os.environ, {"GROQ_API_KEY_2": "gsk-ficticia-2"}):
            externos.llamar(MSG, ID_GROQ)
        self.assertEqual([p["auth"] for p in s.peticiones], ["Bearer gsk-ficticia-2"])  # la clave sin credito ya no se prueba primero

    def test_402_en_la_unica_clave_se_clasifica_como_credito(self):
        self.servidor("groq", err(402))
        with self.assertRaises(RuntimeError) as cm:
            externos.llamar(MSG, ID_GROQ)
        self.assertEqual(getattr(cm.exception, "tipo", None), "credito_cuota"); self.assertIn("402", str(cm.exception))

    def test_timeout_es_timeout_red_y_5xx_agotado_no_es_infinito(self):
        s = self.servidor("nvidia", err(500))
        with self.assertRaises(externos.ErrorProveedor):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual(len(s.peticiones), 3)  # 155: tope de intentos de la politica


class TestCambioDeModeloVisible(Entorno):
    def test_el_resultado_siempre_dice_el_modelo_pedido_y_el_respondido(self):
        self.servidor("nvidia", ok())
        r = externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertEqual(r["modelo_solicitado"], "nvidia/z-ai/glm-5.3"); self.assertEqual(r["modelo_respuesta"], "z-ai/glm-5.3")  # lo que devuelve el proveedor, sin maquillar

    def test_404_nunca_sustituye_por_otro_modelo(self):
        s = self.servidor("nvidia", err(404))
        with self.assertRaisesRegex(RuntimeError, "no se cambió de modelo"):
            externos.llamar(MSG, "nvidia/z-ai/glm-5.3")
        self.assertTrue(all(p["cuerpo"]["model"] == "z-ai/glm-5.3" for p in s.peticiones))


class TestCatalogoTTL(Entorno):
    def test_el_catalogo_se_cachea_y_caduca_a_los_10_minutos(self):
        s = self.servidor("nvidia", ok(), modelos=["z-ai/glm-5.3"])
        reloj = [1000.0]
        with patch.object(externos.time, "time", lambda: reloj[0]):
            externos.modelos("nvidia"); externos.modelos("nvidia")
            self.assertEqual(len([p for p in s.peticiones if p["path"].endswith("/models")]), 1)
            reloj[0] += 599
            externos.modelos("nvidia"); self.assertEqual(len([p for p in s.peticiones if p["path"].endswith("/models")]), 1)
            reloj[0] += 2
            externos.modelos("nvidia"); self.assertEqual(len([p for p in s.peticiones if p["path"].endswith("/models")]), 2)

    def test_disponible_no_adivina_con_cache_vencida(self):
        externos.CACHE["nvidia"] = (1.0, ["nvidia/z-ai/glm-5.3"])
        self.assertIsNone(externos.disponible("nvidia/z-ai/glm-5.3"))


class TestContextoSinRecortesSilenciosos(Entorno):
    def test_si_se_compacta_la_respuesta_lo_avisa(self):
        grande = "x" * 5000
        msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"},
                {"role": "assistant", "content": None, "tool_calls": [{"id": "1", "type": "function", "function": {"name": "f", "arguments": "{}"}}]},
                {"role": "tool", "tool_call_id": "1", "content": grande}, {"role": "assistant", "content": "r"}, {"role": "user", "content": "otra"}]
        pol = {"contexto": {"max_caracteres": 1000, "resultado_tool_max": 100, "recientes": 2}}
        out, info = externos._compactar_info(msgs, pol)
        self.assertEqual(info["resultados_recortados"], 1); self.assertGreater(info["caracteres_antes"], info["caracteres_despues"])
        self.assertEqual(externos._compactar_info(msgs, {"contexto": {"max_caracteres": 10**6}})[1], None)
        with patch.object(externos, "politica", lambda m: {**externos.POLITICA_DEFECTO, "contexto": pol["contexto"]}):
            s = self.servidor("nvidia", ok())
            r = externos.llamar(msgs, "nvidia/z-ai/glm-5.3")
        self.assertEqual(r["metricas"]["contexto_compactado"]["resultados_recortados"], 1)  # visible en la respuesta, no solo en el log
        self.assertIn("recortado", json.dumps(s.peticiones[0]["cuerpo"]["messages"]))

    def test_sin_compactar_no_hay_aviso(self):
        self.servidor("nvidia", ok())
        self.assertNotIn("contexto_compactado", externos.llamar(MSG, "nvidia/z-ai/glm-5.3")["metricas"])


class TestObservabilidadSinCredenciales(Entorno):
    def test_ni_el_log_ni_los_errores_ni_las_metricas_llevan_la_clave(self):
        s = self.servidor("groq", err(503))
        with self.assertLogs(level=logging.DEBUG) as logs:
            logging.getLogger("mvp").info("arranque")
            with self.assertRaises(RuntimeError) as cm:
                externos.llamar(MSG, ID_GROQ)
            self.servidor("groq", ok())
            r = externos.llamar(MSG, ID_GROQ)
        volcado = "\n".join(logs.output) + str(cm.exception) + json.dumps(r["metricas"], default=str)
        self.assertNotIn("gsk-ficticia", volcado)

    def test_la_huella_del_cooldown_no_guarda_la_clave(self):
        externos._enfriar("groq", "gsk-ficticia", {}, 30)
        self.assertNotIn("gsk-ficticia", json.dumps([list(map(str, k)) for k in externos._ENFRIADAS]))


if __name__ == "__main__":
    unittest.main()

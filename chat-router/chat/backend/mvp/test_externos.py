"""Modelos de Groq y NVIDIA en el chat: «groq/<id>» y «nvidia/<id>» van a su API (compatible OpenAI) con su clave; antes el selector NVIDIA respondía con Qwen."""
import os, unittest
from unittest.mock import patch
from test_control import Base, CAB
from mvp import externos, modelos


class TestExternos(Base):
    def test_validar_acepta_prefijo_y_rechaza_proveedor_desconocido(self):
        self.assertEqual(modelos.validar("groq/llama-3.3-70b-versatile"), "groq/llama-3.3-70b-versatile")
        with self.assertRaises(ValueError):
            modelos.validar("otro/x")

    def test_chat_con_groq_llama_a_groq_con_su_clave_y_el_id_sin_prefijo(self):
        vistos = []
        def solicitar(url, payload, clave):
            vistos.append((url, payload["model"], clave))
            return {"model": payload["model"], "choices": [{"message": {"content": "Soy llama"}, "finish_reason": "stop"}]}
        self.banco.datos["GROQ_API_KEY"] = "gsk-ficticia"
        with patch("mvp.compute._solicitar", solicitar):
            r = self.client.post("/chat", headers=CAB, json={"modelo": "groq/llama-3.3-70b-versatile", "mensajes": [{"role": "user", "content": "hola"}]})
        self.assertEqual(r.status_code, 200, r.text); self.assertEqual(r.json()["texto"], "Soy llama")
        self.assertEqual(vistos, [("https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile", "gsk-ficticia")])

    def test_sin_clave_error_claro(self):
        with patch.dict(os.environ, {k: "" for k in os.environ if k.startswith(("GROQ_API_KEY", "NVIDIA_API_KEY"))}):
            r = self.client.post("/chat", headers=CAB, json={"modelo": "nvidia/meta/llama-3.1-8b-instruct", "mensajes": [{"role": "user", "content": "hola"}]})
        self.assertEqual(r.status_code, 503); self.assertIn("NVIDIA", r.json()["detail"])

    def test_lista_de_modelos_del_proveedor(self):
        self.banco.datos["GROQ_API_KEY"] = "gsk-ficticia"
        externos.CACHE.clear()
        with patch("mvp.externos._get", return_value={"data": [{"id": "llama-3.3-70b-versatile"}, {"id": "whisper-large-v3"}]}):
            r = self.client.get("/chat/providers/groq/models", headers=CAB)
        self.assertEqual(r.status_code, 200)
        self.assertEqual([m["model_id"] for m in r.json()["models"]], ["groq/llama-3.3-70b-versatile"])  # solo modelos de chat (sin whisper)
        prov = [p["id"] for p in self.client.get("/chat/providers", headers=CAB).json()["providers"]]
        self.assertIn("groq", prov)


    def test_pool_de_claves_salta_la_invalida(self):  # GROQ_API_KEY_1 inválida hoy (Director 2026-09-27): se usa la siguiente
        vistos = []
        def solicitar(url, payload, clave):
            vistos.append(clave)
            if clave == "gsk-mala":
                import urllib.error
                raise urllib.error.HTTPError(url, 401, "x", {}, None)
            return {"model": payload["model"], "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        with patch.dict(os.environ, {"GROQ_API_KEY": "", "GROQ_API_KEY_1": "gsk-mala", "GROQ_API_KEY_2": "gsk-buena"}), patch("mvp.compute._solicitar", solicitar):
            self.banco.datos.pop("GROQ_API_KEY", None)
            r = self.client.post("/chat", headers=CAB, json={"modelo": "groq/llama-3.3-70b-versatile", "mensajes": [{"role": "user", "content": "hola"}]})
        self.assertEqual(r.status_code, 200, r.text); self.assertEqual(vistos, ["gsk-mala", "gsk-buena"])

    def test_el_banco_guarda_las_claves_de_groq_y_nvidia_del_entorno(self):
        import tempfile
        from mvp import bank
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {"GROQ_API_KEY_3": "gsk-3", "NVIDIA_API_KEY_1": "nvapi-1"}):
            b = bank.abrir(d + "/b.bin", "clave"); b.bootstrap_desde_env()
            self.assertEqual((b.leer("GROQ_API_KEY_3"), b.leer("NVIDIA_API_KEY_1")), ("gsk-3", "nvapi-1"))

    def _swe(self, d, **claves):  # banco compartido temporal (como el del web-bridge) y entorno aislado de claves
        from mvp import bank
        b = bank.abrir(d + "/banco-swe.bin", "api-ficticia")
        for n, v in claves.items():
            b.guardar(n, v)
        externos._SWE.clear()
        return d + "/banco-swe.bin"

    def _entorno(self, ruta, acceso="api-ficticia"):
        limpio = {k: "" for k in os.environ if k.startswith(("GROQ_API_KEY", "NVIDIA_API_KEY"))}
        acc = {k: "" for k in ("RIU_API_KEY", "RIU_PUBLIC_CHAT_KEY", "RIU_MCP_KEY", "RIU_ROUTER_API_KEY")}
        return patch.dict(os.environ, {**limpio, **acc, "RIU_BANCO_SWE": ruta, **({"RIU_API_KEY": acceso} if acceso else {})})

    def test_banco_compartido_aporta_claves_al_final_sin_repetir(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ruta = self._swe(d, GROQ_API_KEY="gsk-swe", GROQ_API_KEY_1="gsk-env", NVIDIA_API_KEY="nv-swe")
            with self._entorno(ruta), patch.dict(os.environ, {"GROQ_API_KEY_1": "gsk-env"}):
                self.assertEqual(externos.claves("groq", None), ["gsk-env", "gsk-swe"])  # entorno antes que el compartido; sin repetir
                self.assertEqual(externos.claves("nvidia", None), ["nv-swe"])

    def test_chat_groq_usa_la_clave_del_banco_compartido(self):
        import tempfile
        vistos = []
        def solicitar(url, payload, clave):
            vistos.append(clave)
            return {"model": payload["model"], "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        self.banco.datos.pop("GROQ_API_KEY", None)
        with tempfile.TemporaryDirectory() as d:
            ruta = self._swe(d, GROQ_API_KEY="gsk-swe")
            with self._entorno(ruta), patch("mvp.compute._solicitar", solicitar):
                r = self.client.post("/chat", headers=CAB, json={"modelo": "groq/llama-3.3-70b-versatile", "mensajes": [{"role": "user", "content": "hola"}]})
        self.assertEqual(r.status_code, 200, r.text); self.assertEqual(vistos, ["gsk-swe"])

    def test_banco_compartido_ausente_o_clave_incorrecta_no_rompe(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ruta = self._swe(d, GROQ_API_KEY="gsk-swe")
            with self._entorno(d + "/no-existe.bin"):
                self.assertEqual(externos.claves("groq", None), [])
                self.assertFalse(os.path.exists(d + "/no-existe.bin"))  # solo lectura: no crea nada
            externos._SWE.clear()
            with self._entorno(ruta, acceso="otra-clave"):
                self.assertEqual(externos.claves("groq", None), [])
            externos._SWE.clear()
            with self._entorno(ruta, acceso=None):  # sin clave de acceso
                self.assertEqual(externos.claves("groq", None), [])
            open(d + "/corrupto.bin", "wb").write(b"basura")
            externos._SWE.clear()
            with self._entorno(d + "/corrupto.bin"):
                self.assertEqual(externos.claves("groq", None), [])

    def test_banco_compartido_se_cachea_por_mtime_y_tamano(self):
        import tempfile
        from mvp import bank
        with tempfile.TemporaryDirectory() as d:
            ruta = self._swe(d, GROQ_API_KEY="gsk-1")
            real = bank.abrir
            with self._entorno(ruta), patch("mvp.bank.abrir", side_effect=real) as ab:
                for _ in range(3):
                    self.assertEqual(externos.claves("groq", None), ["gsk-1"])
                self.assertEqual(ab.call_count, 1)  # no cambio: no se reabre
                b = real(ruta, "api-ficticia"); b.guardar("GROQ_API_KEY_1", "gsk-2")  # cambia el archivo
                self.assertEqual(externos.claves("groq", None), ["gsk-1", "gsk-2"])
                self.assertEqual(ab.call_count, 2)


if __name__ == "__main__":
    unittest.main()

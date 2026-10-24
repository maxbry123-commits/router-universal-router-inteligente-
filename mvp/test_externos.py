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


if __name__ == "__main__":
    unittest.main()

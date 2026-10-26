"""Respuestas ASR sincronas documentadas sin choices y compatibilidad multimodal."""
import json
import unittest
from unittest.mock import patch
from mvp import multimedia


class TestASR(unittest.TestCase):
    def llamar(self, doc):
        respuesta = ("application/json", json.dumps(doc).encode())
        with patch("mvp.multimedia._http", return_value=respuesta):
            return multimedia.asr("https://token-plan.test", "clave-ficticia", "https://audio.test/a.wav")

    def test_formatos_sin_choices(self):
        documentos = [
            {"output": {"text": " hola mundo "}},
            {"output": {"output": {"sentence": {"text": "hola mundo"}}}},
            {"output": {"text": "hola mundo", "output": {"sentence": {"text": "otro"}}}},
        ]
        for doc in documentos:
            with self.subTest(doc=doc):
                self.assertEqual(self.llamar(doc), "hola mundo")

    def test_compatibilidad_y_audio_sin_habla(self):
        doc = {"output": {"choices": [{"message": {"content": [{"text": "hola"}, {"text": " mundo"}]}}]}}
        self.assertEqual(self.llamar(doc), "hola mundo")
        self.assertEqual(self.llamar({"output": {"text": " "}}), "(sin texto reconocido)")

    def test_no_oculta_errores_ni_respuestas_malformadas(self):
        for doc, mensaje in [({}, "respuesta vacia"), ({"code": "InvalidParameter"}, "InvalidParameter"), ({"message": "Audio invalido"}, "Audio invalido")]:
            with self.subTest(doc=doc), self.assertRaisesRegex(RuntimeError, mensaje):
                self.llamar(doc)

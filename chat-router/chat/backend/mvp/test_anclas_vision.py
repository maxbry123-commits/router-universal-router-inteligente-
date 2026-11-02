"""Regresión: un ancla de foto debe llegar como data:image real, nunca desaparecer silenciosamente."""
import asyncio
import base64
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mvp import app as servicio


class TestAnclasVision(unittest.IsolatedAsyncioTestCase):
    async def test_imagen_almacenada_se_entrega_como_data_url(self):
        crudo = base64.b64encode(b"\\x89PNG\\r\\n\\x1a\\nfoto").decode()
        with patch.object(servicio.CONTROL, "ruta_de", return_value="chat_archivos/s1/foto.png"), patch.object(
                servicio, "almacen", new=AsyncMock(return_value={"valor": crudo})):
            _, imagenes = await servicio._contexto_anclado(["foto.png"], "s1")
            respuesta = await servicio.obtener_imagenes_ancladas({"sesion": "s1", "anclados": ["foto.png"]})
        self.assertEqual(imagenes[0]["url"], "data:image/png;base64," + crudo)
        self.assertEqual(respuesta["imagenes"], imagenes)

    async def test_foto_faltante_es_error_no_contexto_vacio(self):
        with patch.object(servicio.CONTROL, "ruta_de", return_value=None):
            with self.assertRaises(HTTPException) as e:
                await servicio._contexto_anclado(["foto.jpg"], "s1")
        self.assertEqual(e.exception.status_code, 422)
        self.assertIn("ANCLA_IMAGEN_NO_ENCONTRADA", e.exception.detail)

    async def test_mas_de_cuatro_fotos_no_se_omiten_silenciosamente(self):
        with self.assertRaises(HTTPException) as e:
            await servicio._contexto_anclado([f"foto{i}.png" for i in range(5)], "s1")
        self.assertIn("MAX_4", e.exception.detail)

    async def test_foto_corrupta_es_error_explicito(self):
        with patch.object(servicio.CONTROL, "ruta_de", return_value="foto"), patch.object(
                servicio, "almacen", new=AsyncMock(return_value={"valor": "NO_BASE64!!!"})):
            with self.assertRaises(HTTPException) as e:
                await servicio._contexto_anclado(["foto.png"], "s1")
        self.assertEqual(e.exception.status_code, 502)

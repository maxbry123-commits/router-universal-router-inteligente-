"""Prueba local de contratos del puente; memoria y GitHub sustituidos, sin red."""
import importlib.util
from pathlib import Path
import types
import unittest
from unittest.mock import patch
import base64


spec = importlib.util.spec_from_file_location('puente_acciones_test', str(Path(__file__).parent / 'plugin.py'))
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)


class Memoria:
    def __init__(self):
        self.datos = {}

    def save(self, scope, clave, valor):
        self.datos[(scope, clave)] = valor

    def search(self, scope, texto, limite):
        return [{'data': valor} for (sc, clave), valor in self.datos.items()
                if sc == scope and clave.startswith(texto)][:limite]


class Acciones(unittest.TestCase):
    def setUp(self):
        self.mem = Memoria()
        self.scope = lambda dueño, sesion: sesion
        self.memoria = patch.object(plugin, '_memoria', return_value=(self.mem, self.scope))
        self.memoria.start()
        self.addCleanup(self.memoria.stop)

    def test_archivo_sesion_ancla_xray_y_sandbox(self):
        archivo = base64.b64encode(b'# Raiz\nURL: https://ejemplo.invalid/guia').decode()
        subida = plugin.handle('subir', {'sesion': 'chat-uno', 'nombre': 'guia.md', 'datos_b64': archivo})
        self.assertEqual(subida['ok'], True)
        self.assertEqual(plugin.handle('archivos', {'sesion': 'chat-uno'})['archivos'], ['guia.md'])
        self.assertEqual(plugin.handle('archivos', {'sesion': 'chat-dos'})['archivos'], [])
        with patch.object(plugin, '_paso_llm', return_value='G1: leer archivo'):
            xray = plugin.handle('xray', {'sesion': 'chat-uno', 'nombre': 'guia.md'})
        self.assertTrue(xray['ok'])
        self.assertEqual(xray['urls'], ['https://ejemplo.invalid/guia'])
        self.assertEqual(plugin.handle('sandbox', {'sesion': 'chat-uno', 'texto': 'Sé preciso'})['encendido'], True)
        self.assertEqual(plugin.handle('sandbox', {'sesion': 'chat-uno'})['sandbox'], 'Sé preciso')
        self.assertEqual(plugin.handle('sandbox', {'sesion': 'chat-dos'})['sandbox'], '')

    def test_handoff_propio_sesion_y_handoff_proyecto(self):
        plugin.handle('handoff_texto', {'sesion': 'chat-uno', 'texto': 'Proyecto A'})
        self.assertEqual(plugin.handle('handoff_texto', {'sesion': 'chat-uno'})['texto'], 'Proyecto A')
        self.assertEqual(plugin.handle('handoff_texto', {'sesion': 'chat-dos'})['texto'], '')
        tree = {'tree': [
            {'path': 'chat router/01-PLAN/README.md', 'type': 'blob'},
            {'path': 'externo/a.py', 'type': 'blob'}]}
        gh = types.SimpleNamespace(_gh=lambda *args: (200, tree))
        with patch.object(plugin, '_herr', return_value=gh):
            handoff = plugin.handle('handoff', {'fuente': 'chat-router'})
        self.assertEqual(handoff['handoff']['archivos'], ['chat router/01-PLAN/README.md'])

    def test_auditor_clasifica_y_error_no_se_oculta(self):
        tree = {'tree': [
            {'path': 'chat router/chat frontend/api.js', 'type': 'blob'},
            {'path': 'router inteligente universal/plugins/puente_chat/plugin.py', 'type': 'blob'},
            {'path': 'chat router/captura.png', 'type': 'blob'}]}
        gh = types.SimpleNamespace(_gh=lambda *args: (200, tree))
        with patch.object(plugin, '_herr', return_value=gh):
            auditoria = plugin.handle('auditor_code', {})
        self.assertEqual(auditoria['total'], 2)
        with patch.object(plugin, '_herr', return_value=types.SimpleNamespace(
                _gh=lambda *args: (503, {'error': 'sin conexion'}))):
            self.assertEqual(plugin.handle('auditor_code', {})['error'], 'AUDITOR_GITHUB_FALLO')


if __name__ == '__main__':
    unittest.main()

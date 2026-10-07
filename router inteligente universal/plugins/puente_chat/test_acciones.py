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

    def test_mover_entre_repos_exige_readback_antes_de_borrar(self):
        borrados = []
        def bajar(repo, rama, ruta):
            if repo == 'origen':
                return b'contenido', 'sha-origen'
            return b'contenido', 'sha-destino'

        with patch.object(plugin, '_gh_lista', return_value=['src/a.txt']), \
             patch.object(plugin, '_gh_subir', return_value=True), \
             patch.object(plugin, '_gh_bajar', side_effect=bajar), \
             patch.object(plugin, '_gh_borrar', side_effect=lambda *args: borrados.append(args) or True):
            resultado = plugin.handle('mover_raiz', {
                'sesion': 'chat-uno', 'op': 'mover', 'origen': 'origen/src', 'destino': 'destino/dst'})
        self.assertEqual(resultado['estado'], 'completado')
        self.assertEqual(resultado['archivos'], 1)
        self.assertEqual(borrados, [('origen', 'main', 'src/a.txt', 'sha-origen')])
        registro = plugin.handle('descargas', {'sesion': 'chat-uno', 'op': 'ver', 'id': resultado['registro']})
        self.assertIn('SHA256:', registro['log'][0])

        borrados.clear()
        with patch.object(plugin, '_gh_lista', return_value=['src/a.txt']), \
             patch.object(plugin, '_gh_subir', return_value=True), \
             patch.object(plugin, '_gh_bajar', side_effect=[
                 (b'contenido', 'sha-origen'), (b'alterado', 'sha-destino')]), \
             patch.object(plugin, '_gh_borrar', side_effect=lambda *args: borrados.append(args) or True):
            fallo = plugin.handle('mover_raiz', {
                'sesion': 'chat-uno', 'op': 'mover', 'origen': 'origen/src', 'destino': 'destino/dst'})
        self.assertEqual(fallo['estado'], 'parcial')
        self.assertEqual(fallo['archivos'], 0)
        self.assertEqual(borrados, [])
        self.assertEqual(plugin.handle('mover_raiz', {
            'op': 'mover', 'origen': 'origen/src', 'destino': 'origen/src'})['error'], 'RUTAS_SOLAPADAS')


if __name__ == '__main__':
    unittest.main()

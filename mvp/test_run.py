"""Prueba el autopull con clones Git temporales; nunca toca GitHub."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from types import SimpleNamespace

import run


def git(*args):
    resultado = subprocess.run(["git", *map(str, args)], capture_output=True, text=True)
    if resultado.returncode:
        raise AssertionError(resultado.stderr)
    return resultado.stdout.strip()


class TestAutopull(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.origin = self.base / "origin.git"
        self.writer = self.base / "writer"
        self.worker = self.base / "worker"
        git("init", "--bare", "--initial-branch=main", self.origin)
        git("clone", self.origin, self.writer)
        git("-C", self.writer, "config", "user.name", "Test local")
        git("-C", self.writer, "config", "user.email", "test@example.invalid")
        (self.writer / "test.txt").write_text("primero\n")
        git("-C", self.writer, "add", "test.txt")
        git("-C", self.writer, "commit", "-m", "primero")
        git("-C", self.writer, "push", "-u", "origin", "main")
        git("clone", self.origin, self.worker)
        self.patcher = patch.object(run, "REPO", self.worker)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def test_sin_cambios_no_reinicia(self):
        antes = run._head()
        with patch.object(run.os, "execv") as reiniciar:
            self.assertFalse(run._actualizar())
            reiniciar.assert_not_called()
        self.assertEqual(run._head(), antes)

    def test_con_cambios_hace_pull_y_reinicia(self):
        antes = run._head()
        (self.writer / "test.txt").write_text("segundo\n")
        git("-C", self.writer, "commit", "-am", "segundo")
        git("-C", self.writer, "push", "origin", "main")
        nuevo = git("-C", self.writer, "rev-parse", "HEAD")
        with patch.object(run.os, "execv") as reiniciar:
            self.assertTrue(run._actualizar())
            reiniciar.assert_called_once_with(sys.executable, [sys.executable, *sys.argv])
        self.assertNotEqual(antes, nuevo)
        self.assertEqual(run._head(), nuevo)

    def test_cambio_solo_de_frontend_no_reinicia(self):
        (self.writer / "plugins" / "chat-router" / "frontend").mkdir(parents=True)
        (self.writer / "plugins" / "chat-router" / "frontend" / "x.js").write_text("1\n")
        git("-C", self.writer, "add", ".")
        git("-C", self.writer, "commit", "-m", "pantalla")
        git("-C", self.writer, "push", "origin", "main")
        nuevo = git("-C", self.writer, "rev-parse", "HEAD")
        with patch.object(run.os, "execv") as reiniciar:
            self.assertFalse(run._actualizar())
            reiniciar.assert_not_called()
        self.assertEqual(run._head(), nuevo)  # el código se actualiza igual, sin reiniciar

    def test_pull_fallido_no_reinicia(self):
        antes = run._head()
        git("-C", self.worker, "remote", "set-url", "origin", str(self.base / "inexistente.git"))
        with patch.object(run.os, "execv") as reiniciar:
            self.assertFalse(run._actualizar())
            reiniciar.assert_not_called()
        self.assertEqual(run._head(), antes)

    def test_mvp_autopull_0_desactiva_hilo(self):
        with patch.dict(os.environ, {"MVP_AUTOPULL": "0"}), patch.object(run.threading, "Thread") as hilo:
            self.assertFalse(run._iniciar_hilo())
            hilo.assert_not_called()

    def test_registra_commit_y_puerto(self):
        fake = Mock()
        with patch.dict(sys.modules, {"uvicorn": SimpleNamespace(run=fake)}), \
             patch.object(run, "_iniciar_hilo", return_value=False), \
             patch.object(run, "_head", return_value="abc123"), \
             patch("builtins.print") as escribir:
            run.main()
        escribir.assert_called_once_with("MVP commit: abc123", flush=True)
        fake.assert_called_once_with("mvp.app:app", host="0.0.0.0", port=7860)

    def test_ciclo_es_cada_60_segundos(self):
        with patch.object(run.time, "sleep") as dormir, \
             patch.object(run, "_actualizar", side_effect=RuntimeError("fin del test")):
            with self.assertRaisesRegex(RuntimeError, "fin del test"):
                run._vigilar()
        dormir.assert_called_once_with(60)


if __name__ == "__main__":
    unittest.main(verbosity=2)

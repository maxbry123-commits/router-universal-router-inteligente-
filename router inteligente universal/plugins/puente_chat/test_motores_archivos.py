"""Pruebas con ficheros temporales: ningún motor accede a GitHub ni a HF."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


MOTORES = Path(__file__).parent / 'fichas/motores_descarga'


class MotoresArchivos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.origen = self.raiz / 'origen'
        self.origen.mkdir()
        (self.origen / 'sub').mkdir()
        (self.origen / 'sub' / 'a.txt').write_bytes(b'A\n')
        (self.origen / 'b.txt').write_bytes(b'B\n')

    def ejecutar(self, fichero, **variables):
        env = {'PATH': os.environ.get('PATH', ''), 'PYTHONDONTWRITEBYTECODE': '1',
               **{k: str(v) for k, v in variables.items()}}
        p = subprocess.run([sys.executable, str(MOTORES / fichero)], cwd=self.raiz,
                           env=env, capture_output=True, text=True, timeout=10)
        return p, json.loads(p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr.strip().splitlines()[-1])

    def test_copia_mueve_y_readback_sha256(self):
        copia = self.raiz / 'copia'
        dest = self.raiz / 'movido'
        for fichero, salida, estado in [
                ('motor_3_copy_batches.py', copia, 'copia.json'),
                ('motor_4_move_batches.py', dest, 'movido.json')]:
            args = {'SOURCE_DIR': self.origen, 'DEST_DIR': salida, 'STATE_FILE': self.raiz / estado}
            p, resultado = self.ejecutar(fichero, **args)
            self.assertEqual((p.returncode, resultado['verdict']), (0, 'VERIFIED_CLOSED'))
            self.assertEqual(resultado['pending'], 0)
            for rel in ('sub/a.txt', 'b.txt'):
                self.assertEqual(hashlib.sha256((salida / rel).read_bytes()).hexdigest(),
                                 hashlib.sha256((copia / rel).read_bytes()).hexdigest())
            p, repetido = self.ejecutar(fichero, **args)
            self.assertEqual(repetido['verdict'], 'VERIFIED_CLOSED')
        self.assertFalse((self.origen / 'b.txt').exists())

    def test_rechaza_rutas_vacias_e_intercaladas(self):
        for fichero in ('motor_3_copy_batches.py', 'motor_4_move_batches.py'):
            _, falta = self.ejecutar(fichero)
            self.assertEqual(falta['verdict'], 'INPUT_GAP')
            _, overlap = self.ejecutar(fichero, SOURCE_DIR=self.origen, DEST_DIR=self.origen / 'sub')
            self.assertEqual(overlap['verdict'], 'INPUT_GAP')
            self.assertTrue((self.origen / 'sub' / 'a.txt').exists())

    def test_copia_y_mover_no_confunden_omision_o_cambio_con_exito(self):
        for fichero in ('motor_3_copy_batches.py', 'motor_4_move_batches.py'):
            with self.subTest(motor=fichero):
                src = self.raiz / ('src-' + fichero)
                dst = self.raiz / ('dst-' + fichero)
                src.mkdir()
                (src / 'a.txt').write_bytes(b'original')
                dst.mkdir()
                (dst / 'a.txt').write_bytes(b'colision')
                args = {'SOURCE_DIR': src, 'DEST_DIR': dst,
                        'STATE_FILE': self.raiz / ('estado-' + fichero + '.json'), 'COLLISION_POLICY': 'skip'}
                _, resultado = self.ejecutar(fichero, **args)
                self.assertEqual(resultado['verdict'], 'GAPS_PENDING')
                self.assertEqual(resultado['skipped'], 1)
                (dst / 'a.txt').unlink()
                (self.raiz / ('estado-' + fichero + '.json')).unlink()
                args['COLLISION_POLICY'] = 'fail'
                _, valido = self.ejecutar(fichero, **args)
                self.assertEqual(valido['verdict'], 'VERIFIED_CLOSED')
                (dst / 'a.txt').write_bytes(b'alterado')
                _, alterado = self.ejecutar(fichero, **args)
                self.assertEqual(alterado['verdict'], 'GAPS_PENDING')
                self.assertEqual(alterado['failed'], 1)

    def test_extrae_zip_y_rechaza_zip_slip(self):
        archivo = self.raiz / 'origen.zip'
        with zipfile.ZipFile(archivo, 'w') as z:
            z.writestr('sub/a.txt', b'A\n')
            z.writestr('b.txt', b'B\n')
        args = {'ARCHIVE_INPUT': archivo, 'DEST_DIR': self.raiz / 'extraido',
                'STATE_FILE': self.raiz / 'extraido.json'}
        _, falta = self.ejecutar('motor_1_extract_only.py')
        self.assertEqual(falta['verdict'], 'INPUT_GAP')
        _, resultado = self.ejecutar('motor_1_extract_only.py', **args)
        self.assertEqual(resultado['verdict'], 'VERIFIED_CLOSED')
        self.assertEqual(resultado['extracted_verified'], 2)
        self.assertEqual((self.raiz / 'extraido/sub/a.txt').read_bytes(), b'A\n')
        (self.raiz / 'extraido/sub/a.txt').write_bytes(b'alterado')
        _, alterado = self.ejecutar('motor_1_extract_only.py', **args)
        self.assertEqual(alterado['verdict'], 'GAPS_PENDING')
        self.assertEqual(alterado['failed'], 1)
        with zipfile.ZipFile(self.raiz / 'malicioso.zip', 'w') as z:
            z.writestr('../fuera.txt', b'malicioso')
        p = subprocess.run([sys.executable, str(MOTORES / 'motor_1_extract_only.py')],
                           cwd=self.raiz, env={'PATH': os.environ.get('PATH', ''),
                                               'ARCHIVE_INPUT': str(self.raiz / 'malicioso.zip'),
                                               'DEST_DIR': str(self.raiz / 'seguro'),
                                               'STATE_FILE': str(self.raiz / 'seguro.json')},
                           capture_output=True, text=True, timeout=10)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('UNSAFE_ZIP_PATH', p.stderr)
        self.assertFalse((self.raiz / 'fuera.txt').exists())

    def test_descarga_en_cola_sin_entrada_falla_cerrado(self):
        _, resultado = self.ejecutar('motor_2_queue_download_extract.py',
                                     QUEUE_FILE=self.raiz / 'no-existe.json',
                                     ENGINE_PATH=self.raiz / 'no-existe.py')
        self.assertEqual(resultado['verdict'], 'INPUT_GAP')


if __name__ == '__main__':
    unittest.main()

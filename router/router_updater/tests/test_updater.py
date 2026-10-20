"""PARCHE_UPDATER (offline, sin red): sincronizacion simulada, clasificacion, staging+rollback, swap de FICHAS, /version, HMAC, replay, autosync apagado.
Ejecutar:  python3 -I router/router_updater/tests/test_updater.py"""
import base64, hashlib, hmac, json, os, shutil, sys, tempfile, threading, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
import router.router_updater.plugin as U  # noqa: E402
import fichas.fichas_qwen.plugin as FQ  # noqa: E402

PREF = 'fichas'
FICHAS_REAL = RAIZ / 'fichas' / 'fichas_qwen' / 'fichas'
SECRETO = 'whsec-prueba-no-real'


def _gsha(b):
    return hashlib.sha1(b'blob %d\0' % len(b) + b).hexdigest()


class FakeGH:
    """Repo en memoria: commits {sha: {ruta: bytes}}. Cuenta las descargas de blobs."""
    def __init__(self):
        self.commits, self.head, self.blobs_pedidos, self.corromper, self.fallar = {}, '', [], set(), False

    def commit(self, tree):
        sha = hashlib.sha1(json.dumps(sorted((k, _gsha(v)) for k, v in tree.items())).encode()).hexdigest()
        self.commits[sha] = dict(tree)
        self.head = sha
        return sha

    def head_sha(self, rama):
        if self.fallar:
            raise RuntimeError('GITHUB_RED:URLError')
        return self.head

    def comparar(self, base, head):
        a, b = self.commits[base], self.commits[head]
        out = []
        for p, v in b.items():
            if p not in a:
                out.append({'path': p, 'estado': 'added', 'blob': _gsha(v), 'previo': ''})
            elif a[p] != v:
                out.append({'path': p, 'estado': 'modified', 'blob': _gsha(v), 'previo': ''})
        for p in a:
            if p not in b:
                out.append({'path': p, 'estado': 'removed', 'blob': '', 'previo': ''})
        return out, False

    def recorrer(self, directorio, ref):
        return {p: _gsha(v) for p, v in self.commits[ref].items() if p.startswith(directorio + '/')}

    def blob(self, sha):
        self.blobs_pedidos.append(sha)
        for t in self.commits.values():
            for v in t.values():
                if _gsha(v) == sha:
                    if sha in self.corromper:
                        raise RuntimeError('BLOB_INTEGRIDAD:' + sha[:12])
                    return v
        raise RuntimeError('BLOB_NO_ENCONTRADO')


def arbol_base():
    t = {PREF + '/fichas_qwen/fichas/' + f.name: f.read_bytes() for f in FICHAS_REAL.glob('*.json')}
    t[PREF + '/fichas_qwen/plugin.py'] = b'X = 1\n'
    t[PREF + '/otro/plugin.py'] = b'Y = 2\n'
    t[PREF + '/otro/LEEME.md'] = b'hola\n'
    return t


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='ru-')
        self._env = dict(os.environ)
        for k in list(os.environ):
            if k.startswith(('ROUTER_', 'GITHUB_', 'GH_')):
                del os.environ[k]
        os.environ['ROUTER_UPDATER_DIR'] = self.tmp
        os.environ['ROUTER_UPDATER_BRANCH'] = 'main'
        self.gh = FakeGH()
        self._fichas = FQ.FICHAS

    def tearDown(self):
        U.parar_autosync()
        FQ.FICHAS = self._fichas
        os.environ.clear(); os.environ.update(self._env)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sync(self, **k):
        return U.sincronizar(gh=self.gh, **k)

    def arranque(self, tree):
        """Primer despliegue + arranque del proceso DESDE ese release (asi el ACTIVE_SHA es real, no supuesto)."""
        h = self.gh.commit(tree)
        r = self.sync()
        assert r['estado'] == 'needs_restart', r  # sin base conocida no se puede afirmar que lo que corre sea esto
        U.__file__, orig = str(Path(self.tmp) / 'releases' / h / PREF / 'router_updater' / 'plugin.py'), U.__file__
        try:
            U.version()
        finally:
            U.__file__ = orig
        assert U.version()['active_sha'] == h and U.version()['update_state'] == 'ok', U.version()
        return h


class Clasificacion(Base):
    def test_clases(self):
        c = U.clasificar
        self.assertEqual(c(PREF + '/fichas_qwen/fichas/ficha2-dag-codigo.json'), 'reload')
        self.assertEqual(c(PREF + '/fichas_qwen/fichas/allowed_ops.json'), 'reload')
        self.assertEqual(c(PREF + '/fichas_qwen/fichas/nota.md'), 'reload')
        self.assertEqual(c(PREF + '/fichas_qwen/plugin.py'), 'restart')
        self.assertEqual(c('Dockerfile'), 'rebuild')
        self.assertEqual(c('x/requirements.txt'), 'rebuild')
        self.assertEqual(c(PREF + '/fichas_qwen/tests/test_x.py'), 'ninguno')
        self.assertEqual(c(PREF + '/otro/LEEME.md'), 'ninguno')


class Sincronizacion(Base):
    def test_primer_sync_y_version(self):
        h = self.gh.commit(arbol_base())
        r = self.sync()
        self.assertTrue(r['ok'], r)
        v = U.version()  # primer despliegue: nada garantiza que el proceso en marcha sea este SHA -> pide reinicio, ACTIVE vacio
        self.assertEqual((v['source'], v['desired_sha'], v['active_sha'], v['last_good_sha'], v['update_state']), ('github', h, '', h, 'needs_restart'))
        self.assertTrue((Path(self.tmp) / 'releases' / h / PREF / 'otro' / 'plugin.py').is_file())
        self.assertFalse((Path(self.tmp) / 'staging' / h).exists())
        self.assertEqual(json.loads((Path(self.tmp) / 'state.json').read_text())['LAST_GOOD_SHA'], h)
        self.assertEqual(U.handle('version')['last_good_sha'], h)
        self.assertEqual(os.path.realpath(Path(self.tmp) / 'current'), os.path.realpath(Path(self.tmp) / 'releases' / h))

    def test_segundo_sync_descarga_solo_lo_cambiado(self):
        t = arbol_base(); self.arranque(t)
        self.gh.blobs_pedidos.clear()
        ficha = PREF + '/fichas_qwen/fichas/ficha1-modelos.json'
        d = json.loads(t[ficha]); d['_nota'] = 'x'; t[ficha] = json.dumps(d).encode()
        h2 = self.gh.commit(t)
        r = self.sync()
        self.assertTrue(r['ok'] and r['cambio'], r)
        self.assertEqual(len(self.gh.blobs_pedidos), 1)
        self.assertEqual(U.version()['active_sha'], h2)
        rel = Path(self.tmp) / 'releases' / h2 / ficha
        self.assertEqual(json.loads(rel.read_text())['_nota'], 'x')
        self.assertEqual(r['estado'], 'ok')

    def test_sin_cambios_no_descarga(self):
        self.arranque(arbol_base()); self.gh.blobs_pedidos.clear()
        r = self.sync()
        self.assertFalse(r['cambio']); self.assertEqual(self.gh.blobs_pedidos, [])

    def test_recarga_en_memoria_de_FICHAS(self):
        t = arbol_base(); self.arranque(t)
        antes = FQ.FICHAS
        ficha = PREF + '/fichas_qwen/fichas/ficha1-modelos.json'
        d = json.loads(t[ficha]); d['_marca'] = 'NUEVA'; t[ficha] = json.dumps(d).encode()
        self.gh.commit(t); r = self.sync()
        self.assertEqual(r['estado'], 'ok')
        self.assertIsNot(FQ.FICHAS, antes)
        self.assertEqual(FQ.FICHAS['ficha1-modelos']['_marca'], 'NUEVA')
        self.assertNotIn('_marca', antes['ficha1-modelos'])

    def test_py_marca_requiere_reinicio_y_no_mueve_activo(self):
        t = arbol_base(); h1 = self.arranque(t)
        t[PREF + '/otro/plugin.py'] = b'Y = 3\n'
        h2 = self.gh.commit(t); r = self.sync()
        self.assertEqual(r['estado'], 'needs_restart'); self.assertTrue(r['requiere_reinicio'])
        v = U.version()
        self.assertEqual((v['active_sha'], v['last_good_sha'], v['desired_sha']), (h1, h2, h2))
        self.assertIn(PREF + '/otro/plugin.py', U.update_status()['requiere_reinicio'])

    def test_arranque_desde_release_confirma_activo(self):
        t = arbol_base(); self.arranque(t)
        t[PREF + '/otro/plugin.py'] = b'Y = 3\n'
        h2 = self.gh.commit(t); self.sync()
        orig = U.__file__
        try:
            U.__file__ = str(Path(self.tmp) / 'releases' / h2 / PREF / 'router_updater' / 'plugin.py')
            v = U.version()
        finally:
            U.__file__ = orig
        self.assertEqual((v['active_sha'], v['update_state']), (h2, 'ok'))

    def test_dockerfile_solo_se_reporta(self):
        t = arbol_base(); h1 = self.arranque(t); self.gh.blobs_pedidos.clear()
        t['Dockerfile'] = b'FROM x\n'
        t[PREF + '/requirements.txt'] = b'a==1\n'
        self.gh.commit(t); r = self.sync()
        self.assertEqual(r['estado'], 'needs_rebuild'); self.assertTrue(r['requiere_rebuild'])
        self.assertEqual(U.version()['active_sha'], h1)
        src = Path(U.__file__).read_text(encoding='utf-8')
        for prohibido in ('huggingface_hub', 'restart_space', 'create_commit', 'upload_file'):
            self.assertNotIn(prohibido, src)

    def test_json_malformado_rollback(self):
        t = arbol_base(); h1 = self.arranque(t)
        antes = FQ.FICHAS
        t[PREF + '/fichas_qwen/fichas/ficha2-dag-codigo.json'] = b'{ roto'
        h2 = self.gh.commit(t); r = self.sync()
        self.assertEqual(r['estado'], 'rolled_back'); self.assertFalse(r['ok'])
        v = U.version()
        self.assertEqual((v['active_sha'], v['last_good_sha'], v['desired_sha'], v['update_state']), (h1, h1, h2, 'rolled_back'))
        self.assertIn('JSON_INVALIDO', U.update_status()['last_error'])
        self.assertIs(FQ.FICHAS, antes)
        self.assertFalse((Path(self.tmp) / 'staging' / h2).exists())
        self.assertFalse((Path(self.tmp) / 'releases' / h2).exists())
        self.gh.blobs_pedidos.clear()
        self.assertEqual(self.sync()['estado'], 'rolled_back')  # mismo SHA malo: no se reintenta solo
        self.assertEqual(self.gh.blobs_pedidos, [])

    def test_py_con_sintaxis_mala_rollback(self):
        t = arbol_base(); h1 = self.arranque(t)
        t[PREF + '/otro/plugin.py'] = b'def (:\n'
        self.gh.commit(t); r = self.sync()
        self.assertEqual(r['estado'], 'rolled_back'); self.assertIn('PY_INVALIDO', U.update_status()['last_error'])
        self.assertEqual(U.version()['last_good_sha'], h1)

    def test_ficha_requerida_ausente_rollback(self):
        t = arbol_base(); h1 = self.arranque(t)
        t[PREF + '/fichas_qwen/fichas/ficha3-frontend.json'] = b'{"sin_ficha": 1}'
        self.gh.commit(t); r = self.sync()
        self.assertEqual(r['estado'], 'rolled_back'); self.assertIn('FICHAS_INVALIDAS', U.update_status()['last_error'])
        self.assertEqual(U.version()['active_sha'], h1)

    def test_rollback_se_recupera_con_commit_bueno(self):
        t = arbol_base(); self.arranque(t)
        t[PREF + '/otro/plugin.py'] = b'def (:\n'; self.gh.commit(t); self.sync()
        t[PREF + '/otro/plugin.py'] = b'Y = 9\n'; h3 = self.gh.commit(t)
        r = self.sync()
        self.assertTrue(r['ok'], r); self.assertEqual(U.version()['last_good_sha'], h3); self.assertEqual(U.update_status()['last_error'], '')

    def test_integridad_de_blob(self):
        t = arbol_base(); h1 = self.arranque(t)
        t[PREF + '/otro/LEEME.md'] = b'cambiado\n'; self.gh.corromper.add(_gsha(b'cambiado\n'))
        self.gh.commit(t); r = self.sync()
        self.assertEqual(r['estado'], 'rolled_back'); self.assertEqual(U.version()['active_sha'], h1)

    def test_ruta_fuera_de_prefijo_o_traversal_se_ignora(self):
        self.assertFalse(U._ruta_segura(PREF + '/../x', PREF))
        self.assertFalse(U._ruta_segura('/etc/passwd', PREF))
        self.assertFalse(U._ruta_segura('otro/plugin.py', PREF))
        self.assertTrue(U._ruta_segura(PREF + '/a/b.py', PREF))

    def test_github_caido_no_toca_el_activo(self):
        h1 = self.arranque(arbol_base())
        self.gh.fallar = True
        r = self.sync()
        self.assertEqual(r['estado'], 'error')
        v = U.version(); self.assertEqual((v['active_sha'], v['last_good_sha']), (h1, h1))

    def test_token_nunca_en_estado_ni_url(self):
        tok = 'ghp_' + 'A1b2C3d4' * 5
        os.environ['GITHUB_PERSONAL_ACCESS_TOKEN'] = tok
        self.gh.fallar = True
        self.gh.head_sha = lambda r: (_ for _ in ()).throw(RuntimeError('fallo con ' + tok))
        self.sync()
        self.assertNotIn(tok, (Path(self.tmp) / 'state.json').read_text())
        capt = []

        class R:
            status = 200
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return b'{"sha": "' + b'a' * 40 + b'"}'
        import urllib.request as ur
        orig = ur.urlopen
        ur.urlopen = lambda req, timeout=0: (capt.append(req), R())[1]
        try:
            self.assertEqual(U.GitHub('o/r').head_sha('main'), 'a' * 40)
        finally:
            ur.urlopen = orig
        self.assertNotIn(tok, capt[0].full_url)
        self.assertEqual(capt[0].get_header('Authorization'), 'Bearer ' + tok)
        self.assertTrue(capt[0].full_url.startswith('https://api.github.com/'))


class SwapFichas(Base):
    def test_swap_atomico_y_conserva_si_falla(self):
        d = Path(self.tmp) / 'f'; d.mkdir()
        for f in FICHAS_REAL.glob('*.json'):
            shutil.copy(f, d / f.name)
        antes = FQ.FICHAS
        d1 = json.loads((d / 'ficha1-modelos.json').read_text()); d1['_m'] = 1
        (d / 'ficha1-modelos.json').write_text(json.dumps(d1))
        r = FQ.recargar_fichas(d)
        self.assertTrue(r['ok'], r); self.assertEqual(FQ.FICHAS['ficha1-modelos']['_m'], 1)
        buena = FQ.FICHAS
        (d / 'ficha5-mvp.json').write_text('{ roto')
        r = FQ.recargar_fichas(d)
        self.assertFalse(r['ok']); self.assertIs(FQ.FICHAS, buena)
        (d / 'ficha5-mvp.json').write_text('[]')  # JSON valido pero no es ficha
        self.assertFalse(FQ.recargar_fichas(d)['ok']); self.assertIs(FQ.FICHAS, buena)
        FQ.FICHAS = antes

    def test_recarga_por_defecto_lee_el_disco_del_plugin(self):
        antes = FQ.FICHAS
        self.assertTrue(FQ.recargar_fichas()['ok'])
        self.assertEqual(set(FQ.FICHAS), set(antes))


class Webhook(Base):
    def _firmar(self, cuerpo, secreto=SECRETO):
        return 'sha256=' + hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()

    def _hdr(self, cuerpo, entrega='abcd1234-0001', evento='push', firma=None):
        return {'X-Hub-Signature-256': firma or self._firmar(cuerpo), 'X-GitHub-Delivery': entrega, 'X-GitHub-Event': evento}

    def _on(self):
        os.environ['ROUTER_WEBHOOK'] = '1'; os.environ['ROUTER_WEBHOOK_SECRET'] = SECRETO

    def test_apagado_por_defecto(self):
        b = b'{}'
        self.assertEqual(U.procesar_webhook(self._hdr(b), b)['codigo'], 404)
        os.environ['ROUTER_WEBHOOK'] = '1'  # sin secreto sigue apagado
        self.assertEqual(U.procesar_webhook(self._hdr(b), b)['codigo'], 404)

    def test_firma_valida_e_invalida(self):
        self._on()
        b = json.dumps({'ref': 'refs/heads/main'}).encode()
        self.assertTrue(U.verificar_firma(SECRETO, b, self._firmar(b)))
        self.assertFalse(U.verificar_firma(SECRETO, b, self._firmar(b, 'otro')))
        self.assertFalse(U.verificar_firma(SECRETO, b, ''))
        self.assertFalse(U.verificar_firma(SECRETO, b, self._firmar(b).replace('sha256=', 'sha1=')))
        self.assertEqual(U.procesar_webhook(self._hdr(b, firma='sha256=' + '0' * 64), b)['codigo'], 401)
        self.assertEqual(U.procesar_webhook({'X-GitHub-Delivery': 'abcd1234-9'}, b)['codigo'], 401)
        self.assertEqual(U.procesar_webhook(self._hdr(b, entrega=''), b)['codigo'], 400)
        self.assertEqual(U.leer_estado()['entregas'], [])  # una firma mala no consume delivery

    def test_replay(self):
        self._on()
        b = b'{"zen": "x"}'
        h = self._hdr(b, evento='ping')
        self.assertEqual(U.procesar_webhook(h, b)['estado'], 'pong')
        self.assertEqual(U.procesar_webhook(h, b)['estado'], 'replay_ignorado')

    def test_push_dispara_sync_y_otra_rama_no(self):
        self._on()
        h1 = self.gh.commit(arbol_base())
        b = json.dumps({'ref': 'refs/heads/otra'}).encode()
        self.assertEqual(U.procesar_webhook(self._hdr(b, 'dlv-00000001'), b, gh=self.gh, sincrono=True)['estado'], 'rama_ignorada')
        b = json.dumps({'ref': 'refs/heads/main'}).encode()
        r = U.procesar_webhook(self._hdr(b, 'dlv-00000002'), b, gh=self.gh, sincrono=True)
        self.assertEqual(r['codigo'], 200); self.assertEqual(U.version()['last_good_sha'], h1)

    def test_handle_webhook_sin_activar(self):
        b = b'{}'
        r = U.handle('webhook', {'headers': self._hdr(b), 'body_b64': base64.b64encode(b).decode()})
        self.assertEqual(r['codigo'], 404)


class Autosync(Base):
    def test_apagado_por_defecto(self):
        n0 = threading.active_count()
        self.assertFalse(U.iniciar_autosync()['activo'])
        self.assertTrue(U.handle('status')['ok'])
        self.assertFalse(U.handle('autosync_iniciar')['activo'])
        self.assertEqual(threading.active_count(), n0)
        self.assertFalse(U.update_status()['autosync']['activo'])
        self.assertFalse(U._cfg()['autosync']); self.assertFalse(U._cfg()['webhook'])

    def test_intervalo_minimo_30(self):
        os.environ['ROUTER_AUTOSYNC_S'] = '5'
        self.assertEqual(U._cfg()['intervalo'], 30)
        os.environ['ROUTER_AUTOSYNC_S'] = 'abc'
        self.assertGreaterEqual(U._cfg()['intervalo'], 30)
        os.environ['ROUTER_AUTOSYNC_S'] = '600'
        self.assertEqual(U._cfg()['intervalo'], 600)

    def test_activado_arranca_hilo_daemon(self):
        os.environ['ROUTER_AUTOSYNC'] = '1'
        h = self.gh.commit(arbol_base())
        r = U.iniciar_autosync(gh=self.gh)
        self.assertTrue(r['activo'])
        t = U._AUTOSYNC['hilo']; self.assertTrue(t.daemon)
        t.join(0)
        for _ in range(100):
            if U.leer_estado()['LAST_GOOD_SHA'] == h:
                break
            threading.Event().wait(0.05)
        self.assertEqual(U.leer_estado()['LAST_GOOD_SHA'], h)
        U.parar_autosync()


if __name__ == '__main__':
    unittest.main()

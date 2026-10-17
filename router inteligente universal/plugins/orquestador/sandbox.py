"""Sandbox de ejecucion de codigo por agente. Evaluacion con evidencia (2026-10-16):
1) Vercel Sandbox (microVM Firecracker, red deny-all): el mejor aislamiento, PERO la cuenta (plan Hobby) devuelve
   402 payment_required "Hobby plan usage limit exceeded" hasta 2026-11-01 -> queda cableado como opcion 'vercel' (VERCEL_TOKEN + VERCEL_SANDBOX_PROJECT).
2) HF Jobs (contenedor efimero aparte, cpu-basic): ya se usa en el Router (L4 de respaldo), mismo banco de tokens -> PROVEEDOR POR DEFECTO. Probado: 5050 en 6 s 456 ms, sin secretos en el entorno; ojo: la red sale abierta (HF Jobs no tiene politica de red).
   Arranque lento (decenas de s) a cambio de aislamiento real: otra maquina, sin los secretos del Space.
3) Local: bubblewrap (namespaces: sin red, FS de solo lectura salvo el sandbox) > unshare -rn > solo rlimits. Para pruebas o si HF falla.
El codigo NUNCA recibe secretos: entorno vacio (solo PATH/HOME)."""
from __future__ import annotations
import base64, json, os, resource, shutil, subprocess, time, urllib.request
from pathlib import Path

NS = os.getenv('RIU_HF_NS') or 'COMAND-CENTER-1'


def _tokens_hf():
    try:
        from integration.chat_mvp import providers
        return providers.env_keys('hf')
    except Exception:  # noqa: BLE001
        return [t for t in (os.getenv('HF_TOKEN'), os.getenv('HF_WRITE_TOKEN')) if t]


def proveedor():
    pref = (os.getenv('ORQ_SANDBOX') or '').lower()
    if pref == 'vercel' and os.getenv('VERCEL_TOKEN') and os.getenv('VERCEL_SANDBOX_PROJECT'):
        return 'vercel'
    if pref != 'local' and _tokens_hf():
        return 'hf-jobs'
    return 'local'


def _limites():
    resource.setrlimit(resource.RLIMIT_CPU, (20, 25))
    resource.setrlimit(resource.RLIMIT_AS, (768 << 20, 768 << 20))
    resource.setrlimit(resource.RLIMIT_FSIZE, (20 << 20, 20 << 20))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    os.setsid()


def _local(code, sb: Path, timeout):
    (sb / 'main.py').write_text(code, encoding='utf-8')
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/sandbox', 'PYTHONDONTWRITEBYTECODE': '1'}
    py = shutil.which('python3') or 'python3'
    cmds = []
    if shutil.which('bwrap'):
        cmds.append(('bwrap', 'namespaces: sin red, / solo lectura, solo /sandbox escribible',
                     ['bwrap', '--ro-bind', '/usr', '/usr', '--ro-bind', '/bin', '/bin', '--ro-bind-try', '/lib', '/lib', '--ro-bind-try', '/lib64', '/lib64',
                      '--ro-bind-try', '/etc/alternatives', '/etc/alternatives', '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
                      '--bind', str(sb), '/sandbox', '--chdir', '/sandbox', '--unshare-all', '--die-with-parent', '--clearenv',
                      '--setenv', 'PATH', env['PATH'], '--setenv', 'HOME', '/sandbox', py, '-I', 'main.py']))
    if shutil.which('unshare'):
        cmds.append(('unshare', 'sin red (user+net namespace), rlimits', ['unshare', '-rn', py, '-I', 'main.py']))
    cmds.append(('rlimits', 'solo rlimits y entorno vacio (aislamiento debil)', [py, '-I', 'main.py']))
    for nombre, aisl, cmd in cmds:
        t0 = time.time()
        try:
            r = subprocess.run(cmd, cwd=str(sb), env=env, capture_output=True, text=True, timeout=timeout, preexec_fn=_limites)
        except subprocess.TimeoutExpired:
            return {'proveedor': 'local-' + nombre, 'aislamiento': aisl, 'exit_code': 124, 'stdout': '', 'stderr': 'TIMEOUT %d s' % timeout, 'ms': int((time.time() - t0) * 1000)}
        if r.returncode in (1, 125, 126) and ('bwrap:' in r.stderr or 'unshare:' in r.stderr):
            continue  # el host no permite ese aislamiento: siguiente
        return {'proveedor': 'local-' + nombre, 'aislamiento': aisl, 'exit_code': r.returncode, 'stdout': r.stdout[-6000:], 'stderr': r.stderr[-3000:], 'ms': int((time.time() - t0) * 1000)}
    return {'proveedor': 'local', 'aislamiento': '-', 'exit_code': 1, 'stdout': '', 'stderr': 'SIN_SANDBOX', 'ms': 0}


def _hf(metodo, ruta, cuerpo=None, timeout=30):
    ultimo = (0, 'SIN_TOKEN_HF')
    for t in _tokens_hf():
        req = urllib.request.Request('https://huggingface.co' + ruta, data=json.dumps(cuerpo).encode() if cuerpo is not None else None, method=metodo,
                                     headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            ultimo = (e.code, e.read().decode('utf-8', 'replace')[:300])
        except Exception as e:  # noqa: BLE001
            ultimo = (0, type(e).__name__)
    return ultimo


def _hf_jobs(code, sb: Path, timeout):
    t0 = time.time()
    files = {}
    for f in (sb / 'archivos').glob('*'):
        if f.is_file() and f.stat().st_size < 200_000:
            files[f.name] = base64.b64encode(f.read_bytes()).decode()
    boot = ('import os,json,base64;os.makedirs("/sandbox/archivos",exist_ok=True);os.chdir("/sandbox")\n'
            '[open("archivos/"+k,"wb").write(base64.b64decode(v)) for k,v in json.loads(os.environ.pop("ORQ_FILES","{}")).items()]\n'
            'exec(compile(base64.b64decode(os.environ.pop("ORQ_CODE")).decode(),"main.py","exec"))')
    s, d = _hf('POST', '/api/jobs/' + NS, {'dockerImage': 'python:3.12-slim', 'command': ['python', '-c', boot], 'arguments': [],
                                          'environment': {'ORQ_CODE': base64.b64encode(code.encode()).decode(), 'ORQ_FILES': json.dumps(files)},
                                          'flavor': 'cpu-basic', 'timeoutSeconds': max(60, timeout + 60), 'labels': {'name': 'orq-sandbox'}})
    if s >= 400 or s == 0:
        r = _local(code, sb, timeout); r['nota'] = 'HF Jobs fallo (%s): se uso local' % s
        return r
    jid = json.loads(d)['id']
    stage = ''
    while time.time() - t0 < timeout + 240:
        time.sleep(3)
        s, d = _hf('GET', '/api/jobs/%s/%s' % (NS, jid))
        stage = ((json.loads(d) if s == 200 else {}).get('status') or {}).get('stage', '')
        if stage in ('COMPLETED', 'ERROR', 'CANCELED', 'DELETED'):
            break
    s, logs = _hf('GET', '/api/jobs/%s/%s/logs' % (NS, jid), timeout=30)
    out = []
    for ln in str(logs).splitlines():
        if ln.startswith('data:'):
            try:
                out.append(json.loads(ln[5:]).get('data', ''))
            except Exception:  # noqa: BLE001
                out.append(ln[5:])
    return {'proveedor': 'hf-jobs', 'aislamiento': 'contenedor efimero HF (otra maquina, sin secretos)', 'job_id': jid,
            'exit_code': 0 if stage == 'COMPLETED' else 1, 'stdout': '\n'.join(out)[-6000:], 'stderr': '' if stage == 'COMPLETED' else stage, 'ms': int((time.time() - t0) * 1000)}


def _vercel(code, sb: Path, timeout):
    t0 = time.time(); tok = os.getenv('VERCEL_TOKEN'); team = os.getenv('VERCEL_TEAM_ID') or ''
    q = ('?teamId=' + team) if team else ''
    def v(metodo, ruta, cuerpo=None):
        req = urllib.request.Request('https://api.vercel.com' + ruta + q, data=json.dumps(cuerpo).encode() if cuerpo is not None else None, method=metodo,
                                     headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout + 60) as r:
            return json.loads(r.read() or b'{}')
    try:
        sbx = v('POST', '/v1/sandboxes', {'projectId': os.getenv('VERCEL_SANDBOX_PROJECT'), 'runtime': 'python3.13', 'timeout': (timeout + 60) * 1000,
                                          'resources': {'vcpus': 1}, 'networkPolicy': {'mode': 'deny-all'}})
        sid = (sbx.get('sandbox') or sbx)['id']
        try:
            c = v('POST', '/v1/sandboxes/%s/cmd' % sid, {'command': 'python3', 'args': ['-c', 'import os,base64;exec(base64.b64decode(os.environ["ORQ_CODE"]).decode())'],
                                                          'env': {'ORQ_CODE': base64.b64encode(code.encode()).decode()}, 'wait': True})
            cmd = c.get('command') or c
            return {'proveedor': 'vercel', 'aislamiento': 'microVM Firecracker, red deny-all', 'exit_code': cmd.get('exitCode'), 'stdout': str(cmd.get('stdout') or '')[-6000:],
                    'stderr': str(cmd.get('stderr') or '')[-3000:], 'ms': int((time.time() - t0) * 1000)}
        finally:
            try:
                v('POST', '/v1/sandboxes/%s/stop' % sid)
            except Exception:  # noqa: BLE001
                pass
    except Exception as e:  # noqa: BLE001
        r = _local(code, sb, timeout); r['nota'] = 'Vercel Sandbox fallo (%s): se uso local' % type(e).__name__
        return r


def ejecutar(code, sb: Path, timeout=30):
    timeout = max(1, min(int(timeout), 300))
    p = proveedor()
    return _vercel(code, sb, timeout) if p == 'vercel' else _hf_jobs(code, sb, timeout) if p == 'hf-jobs' else _local(code, sb, timeout)

"""Enchufe PluginHost del LOOP NCT/CODA (nct_loop).
Trigger del chat: POST /plugins/nct_loop/call/ejecutar con el objetivo
(Yaiwes.md en markdown o mision completa) + el modelo ya elegido en el chat.
Sin sistemas paralelos: el modelo sale por plugins.puente_chat.plugin._chat
(el mismo cableado del chat), las ops Ricardo por referencia_ricardo/motor_cli
en workspace confinado, la cola es el QueueStore CIT-50 existente (claim ->
ejecutar -> complete con recibos) y la memoria son checkpoints en state/.
"""
from __future__ import annotations

import asyncio
import subprocess
import hashlib
import importlib.util
import json
import re
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))
_COLA_DIR = _DIR.parent / 'Cola'
_STATE = _DIR / 'state'
_STATE.mkdir(exist_ok=True)
_MEM = _STATE / 'memoria'
_MEM.mkdir(exist_ok=True)
_WS_ROOT = _STATE / 'workspaces'
_CONFIG = _DIR / 'config'
_MOTOR = _DIR / 'referencia_ricardo' / 'motor_cli.py'
_POLICY = _DIR / 'referencia_ricardo' / 'allowed_ops.json'
_OPS_RICARDO = ['inspect_workspace', 'create_directory', 'write_text', 'read_text',
                'verify_exists', 'verify_contains', 'finish']
_ACCIONES_ECC = {'run_approved_red_tests', 'run_approved_green_tests', 'run_test_suite',
                 'run_lint', 'check_diff_scope', 'run_security_checks', 'run_regression_suite',
                 'trace_click_path', 'check_accessibility', 'run_ui_e2e',
                 'run_api_contract_tests'}


# Carpeta ECC dentro del mismo repo (sin descargas): <repo>/chat-router/.../ECC
_ECC_DIR = (_DIR.parents[2] / 'chat-router' /
            'workflow-loop-code-yaiwes/skills/workflow-loop-yaiwes/ECC')
_CATALOGO_ECC = None
_CATALOGO_LOCK = threading.Lock()


def _catalogo_ecc() -> dict:
    """Compila los 311 motores desde el repo ECC a un registro de fases Python."""
    global _CATALOGO_ECC
    with _CATALOGO_LOCK:
        if _CATALOGO_ECC is None:
            if not _ECC_DIR.is_dir():
                raise RuntimeError('ECC fuente no presente en repo: ' + str(_ECC_DIR))
            from nct_loop.ecc_phase_compiler import compile_directory
            _CATALOGO_ECC = compile_directory(_ECC_DIR)
        return _CATALOGO_ECC


# Separacion de ciclos del motor: cada fase compilada se clasifica por su
# titulo de seccion en MAIN (procedimiento), VERIFY (comprobacion),
# RECOVERY (solo si falla), CONTINUOUS (re-disparo por eventos) y META
# (guia del documento; no corre como paso de ejecucion).
_CICLOS = (
    ('RECOVERY', re.compile(
        r'(recover|repair|fail|rollback|pitfall|escalat|incident|error|fault|degrad|revert|mitigat|diagnos|debug)',
        re.I)),
    ('CONTINUOUS', re.compile(
        r'(continuous|monitor|watchdog|watch|hook|trigger|schedule|observ|telemetry|alert|poll)',
        re.I)),
    ('VERIFY', re.compile(
        r'(verif|validat|check|test|audit|gate|review|eval|assert|lint|scan|quality|accept|receipt)',
        re.I)),
    ('META', re.compile(
        r'(when to|example|related|reference|see also|resource|overview|concept|principle|introduction|install|setup|config|glossar|faq|anti-?pattern|don.t|output format|quick reference|terminolog)',
        re.I)),
)


def _ciclo_de_fase(title: str) -> str:
    t = str(title or '')
    for ciclo, rx in _CICLOS:
        if rx.search(t):
            return ciclo
    return 'MAIN'


# Registro normalizado de motores (metodo de 8 macrociclos del audit):
# cada motor -> {motor_id, categoria, triggers, macrociclo C0..C7,
# required_tools, risk_level, evidence_requirements, sha256, ciclos}.
_MACROCICLOS = (
    ('C0_admision', re.compile(
        r'(guard|safety|gate-?guard|admission|permission|authoriz|policy|design-check|loop-design)',
        re.I)),
    ('C1_investigacion', re.compile(
        r'(scan|search|research|impact|analy|inspect|discover|explor|review-?code|audit|repo|debug|introspection)',
        re.I)),
    ('C2_decision', re.compile(
        r'(council|decision|deliberat|vote|consensus|arbitr)', re.I)),
    ('C3_planificacion', re.compile(
        r'(plan|dag|pipeline|rfc|decompos|orchestrat|architect|design|roadmap|spec)',
        re.I)),
    ('C4_preparacion', re.compile(
        r'(harness|parallel|schedul|resource|context|isolat|budget|setup|scaffold|bootstrap|provision)',
        re.I)),
    ('C5_ejecucion', re.compile(
        r'(tdd|code|coding|implement|fix|defect|feature|refactor|build|lang|python|typescript|react|rust|go-|sql|api-?connector|generator|writer)',
        re.I)),
    ('C6_verificacion', re.compile(
        r'(verif|valid|eval|test|review|security|santa|proof|lint|coverage|regression|benchmark|quality)',
        re.I)),
    ('C7_integracion', re.compile(
        r'(git|deliver|deploy|release|production|merge|integrat|publish|ship|rollout)',
        re.I)),
)

_RIESGO_ALTO = re.compile(
    r'(deploy|production|payment|financ|health|medical|secur|auth|credential|secret|infra|delete|destruct)',
    re.I)
_HERRAMIENTAS = re.compile(
    r'(docker|kubernetes|git|github|aws|gcp|azure|postgres|redis|kafka|terraform|ansible|jenkins|vercel|supabase|stripe)',
    re.I)


def _triggers_de(markdown_path: Path) -> list:
    """Disparadores: bullets de 'When to Use'/'When to Activate' del SKILL.md."""
    try:
        texto = markdown_path.read_text(encoding='utf-8', errors='replace')[:30000]
    except OSError:
        return []
    out = []
    lineas = texto.splitlines()
    cab = None
    rx_cab = re.compile(r'#{2,4}.*(when to (use|activat|apply)|cuando|triggers?)\s*$', re.I)
    for i, linea in enumerate(lineas):
        if rx_cab.search(linea.strip()):
            cab = i
            break
    if cab is None:
        return out
    for li in lineas[cab + 1:cab + 40]:
        li2 = li.strip()
        if li2.startswith('#'):
            break
        li2 = re.sub(r'^[-*\u2022\d.\)\s]+', '', li2).strip()
        if li2 and len(li2) <= 200:
            out.append(li2)
        if len(out) >= 12:
            break
    return out


_REG = None


def _registro_motores() -> dict:
    """Registro normalizado de los 311 motores (categoria, triggers, macrociclo...)."""
    global _REG
    if _REG is not None:
        return _REG
    cat = _catalogo_ecc()
    reg = {}
    skills_root = _ECC_DIR / 'skills'
    for sid, spec in cat.items():
        texto = sid + ' ' + ' '.join(p.get('title') or '' for p in spec.get('phases') or [])
        md = skills_root / sid / 'SKILL.md'
        triggers = _triggers_de(md)
        mejor = (0, 'C5_ejecucion')
        for nombre, rx in _MACROCICLOS:
            n = len(rx.findall(texto))
            if n > mejor[0]:
                mejor = (n, nombre)
        macro = mejor[1]
        riesgo = 'alto' if _RIESGO_ALTO.search(texto) else 'normal'
        tools = sorted(set(_HERRAMIENTAS.findall(texto)))
        ciclos = _fases_por_ciclo(spec)
        reg[sid] = {'motor_id': sid, 'categoria': macro,
                    'macrociclo': macro, 'triggers': triggers,
                    'required_tools': tools, 'risk_level': riesgo,
                    'source_sha256': spec.get('source_sha256'),
                    'fases': len(spec.get('phases') or []),
                    'ciclos': {k: len(v) for k, v in ciclos.items()}}
    _REG = reg
    return reg


def _fases_por_ciclo(spec: dict) -> dict:
    ciclos: dict = {'MAIN': [], 'VERIFY': [], 'RECOVERY': [], 'CONTINUOUS': [], 'META': []}
    for ph in spec.get('phases') or []:
        ciclos.setdefault(_ciclo_de_fase(ph.get('title')), []).append(ph)
    return ciclos


def _mod(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_cola_core = _mod('cola50_core_nct', _COLA_DIR / 'nct_addons' / 'cola50' / 'core.py')
_COLA_DB = _COLA_DIR / 'state' / 'cola50.db'
(_COLA_DIR / 'state').mkdir(exist_ok=True)
_COLA = None


def _cola():
    global _COLA
    if _COLA is None:
        _COLA = _cola_core.QueueStore(_COLA_DB)
    return _COLA


def _chat_modelo(modelo: str, prompt: str, sesion: str) -> dict:
    from plugins.puente_chat import plugin as _pc
    return _pc._chat({'model': modelo, 'messages': [{'role': 'user', 'content': prompt}],
                      'max_tokens': 4096, 'sesion': sesion})


def _texto_respuesta(r: dict) -> str:
    if not isinstance(r, dict):
        return ''
    return str(r.get('reply') or ((r.get('choices') or [{}])[0].get('message') or {}).get('content') or '')


def _json_de(texto: str):
    i = (texto or '').find('{')
    while i != -1:
        try:
            v, _ = json.JSONDecoder().raw_decode((texto or '')[i:])
            if isinstance(v, dict):
                return v
        except Exception:  # noqa: BLE001
            pass
        i = (texto or '').find('{', i + 1)
    return None


class _PuertoModelo:
    """block -> plugins.puente_chat._chat con el modelo elegido en el frontend."""

    def __init__(self, modelo: str, sesion: str):
        self.modelo, self.sesion = modelo, sesion

    async def invoke(self, block: str, payload: dict) -> dict:
        prompt = ('[LOOP %s] stage=%s task_id=%s\ncontexto=%s\nResponde SOLO JSON con '
                  '{"status":"READY|NEED_INPUT|BLOCKED","proposal":{"meta":{},"ops":[...]}} '
                  '(proposal solamente en stage IMPLEMENT).'
                  % (block, payload.get('stage'), payload.get('task_id'),
                     json.dumps(payload.get('context') or {}, ensure_ascii=False)[:4000]))
        r = await asyncio.to_thread(_chat_modelo, self.modelo, prompt, self.sesion)
        if isinstance(r, dict) and r.get('error'):
            raise RuntimeError('modelo: ' + str(r['error'])[:200])
        out = _json_de(_texto_respuesta(r))
        if not isinstance(out, dict):
            return {'status': 'BLOCKED', 'notes': 'respuesta del modelo sin JSON'}
        return out


_RECLAMADOS: dict = {}
_RECL_LOCK = threading.Lock()


class _PuertoCola:
    """submit_and_wait sobre el QueueStore CIT-50 existente: encola la unidad
    (tipo ricardo, sin aprobacion: ya viene gated por allowed_ops + ECC), la
    reclama y ejecuta perform; los recibos quedan en la cola (complete)."""

    async def submit_and_wait(self, task, perform) -> dict:
        q = _cola().create({'title': 'nct-' + task.id, 'chat_id': 'nct_loop',
                            'tasks': [{'id': task.id, 'title': task.goal[:150], 'type': 'handoff',
                                       'prompt': task.goal[:2000]}]})
        qid = q['queue_id']
        _cola().start(qid, seconds=900)
        # claim() es global y FIFO: con procesos en paralelo puede devolver la unidad de
        # otro. Lo reclamado se deja en _RECLAMADOS y cada dueno recoge solo lo suyo.
        for _ in range(400):
            with _RECL_LOCK:
                if qid not in _RECLAMADOS:
                    c = _cola().claim()
                    if c:
                        _RECLAMADOS[c[0].get('queue_id')] = c
                claimed = _RECLAMADOS.pop(qid, None)
            if claimed:
                break
            await asyncio.sleep(0.05)
        if not claimed:
            raise RuntimeError('cola CIT-50 no entrego la unidad %s' % task.id)
        try:
            out = await perform()
            _cola().complete(qid, task.id, {'resultado': out, 'verification': 'PASS'}, ok=True)
        except Exception as e:  # noqa: BLE001
            _cola().complete(qid, task.id, {'error': str(e)[:400], 'verification': 'FAIL'}, ok=False)
            raise
        return out


class _PuertoMemoria:
    """Checkpoint por mision en state/memoria/<mission>.json (persistencia local;
    el cableado al banco/memoria real queda cuando llegue su trazabilidad)."""

    def _ruta(self, key: str) -> Path:
        return _MEM / ('%s.json' % hashlib.sha256(key.encode()).hexdigest()[:40])

    async def load(self, key: str):
        f = self._ruta(key)
        return json.loads(f.read_text(encoding='utf-8')) if f.exists() else None

    async def checkpoint(self, key: str, value: dict) -> None:
        _MEM.mkdir(parents=True, exist_ok=True)
        self._ruta(key).write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding='utf-8')


class _PuertoECCAcciones:
    """executor.run_approved_action: verifica en el workspace las aceptaciones
    de la unidad (verify_exists/verify_contains por el mismo Motor confinado).
    Sin falso PASS: si no hay aceptaciones verificables, devuelve FAIL."""

    def __init__(self, ops_port, acceptance_por_unidad: dict):
        self.ops = ops_port
        self.acceptance = acceptance_por_unidad

    async def run_approved_action(self, req: dict) -> dict:
        rid = str(req.get('request_id') or '')
        tid = str(req.get('task_id') or '')
        if req.get('operation') not in _ACCIONES_ECC:
            return {'request_id': rid, 'status': 'FAIL', 'detail': 'op ECC no aprobada'}
        ops = [dict(o, id='ecc-%d' % i) for i, o in enumerate(self.acceptance.get(tid) or [])
               if isinstance(o, dict) and o.get('op') in ('verify_exists', 'verify_contains')]
        if not ops:
            return {'request_id': rid, 'status': 'FAIL',
                    'detail': 'unidad %s sin aceptaciones verificables' % tid}
        rep = await self.ops.execute({'meta': {'name': ('ecc' + rid[:20])[:48]}, 'ops': ops}, tid)
        receipt_id = hashlib.sha256((rid + rep['plan_sha256']).encode()).hexdigest()[:24]
        return {'request_id': rid, 'status': 'PASS' if rep['ok'] else 'FAIL',
                'receipt_id': receipt_id, 'errors': rep['errors']}


_PROC: dict = {}
MAX_PARALELO = 4
_POOL = ThreadPoolExecutor(max_workers=MAX_PARALELO, thread_name_prefix='nct_loop')
_GRUPOS: dict = {}
_CANCEL: set = set()


def _build_mission(p: dict) -> dict:
    m = p.get('mision')
    if isinstance(m, dict) and m.get('units'):
        return m
    objetivo = str(p.get('objetivo') or p.get('yaiwes_md') or p.get('objetivo_md') or '').strip()
    if not objetivo:
        raise ValueError('falta objetivo (markdown Yaiwes.md) o mision')
    ops = [o for o in (p.get('allowed_ops') or _OPS_RICARDO) if o in _OPS_RICARDO]
    return {'mission_id': str(p.get('mission_id') or 'nct-' + uuid.uuid4().hex[:12]),
            'goal': objetivo[:2000], 'profile': str(p.get('profile') or 'document'),
            'acceptance': p.get('acceptance') or [],
            'units': [{'id': 'T1', 'goal': objetivo[:8000], 'block': 'executor',
                       'depends_on': [], 'priority': 5, 'allowed_ops': ops,
                       'acceptance': p.get('acceptance') or [], 'scope': p.get('scope') or [],
                       'max_retries': int(p.get('max_retries') or 0)}]}


async def _correr(pid: str, p: dict) -> dict:
    from nct_loop.ecc_runtime import ECCCodeRuntime
    from nct_loop.engine_coda_fixed import NCTLoopCodaFixed
    from nct_loop.engine import NCTLoopEngine
    mission = _build_mission(p)
    modelo = str(p.get('modelo') or 'ficha-qwen38flash')
    sesion = str(p.get('sesion') or 'nct-loop')[:60]
    workdir = _WS_ROOT / pid
    from nct_loop.ricardo_adapter import RicardoOpsDemo, FileCheckerDemo
    ops_port = RicardoOpsDemo(workdir, _POLICY)
    acc_map = {u['id']: [a for a in (u.get('acceptance') or []) if isinstance(a, dict)]
               for u in mission['units']}
    approved = set()
    for u in mission['units']:
        approved.update(u.get('allowed_ops') or [])
    ecc = ECCCodeRuntime(_CONFIG / 'ecc_rules.json')
    cls = NCTLoopCodaFixed if str(p.get('motor') or 'coda') == 'coda' else NCTLoopEngine
    engine = cls(ecc=ecc,
                 model=_PuertoModelo(modelo, sesion),
                 queue=_PuertoCola(),
                 memory=_PuertoMemoria(),
                 tools=ops_port,
                 checker=FileCheckerDemo(workdir),
                 resources_file=_CONFIG / 'resources.json',
                 known_blocks={'planner', 'executor', 'verifier', 'auditor'},
                 approved_ops=approved,
                 max_calls=int(p.get('max_calls') or 60),
                 ecc_action_port=_PuertoECCAcciones(ops_port, acc_map),
                 approved_ecc_actions=_ACCIONES_ECC)
    resultado = await engine.run(mission)
    return resultado


# --- Motores code ECC (compilados desde el repo ECC)  ---------------------------
# Un handler por fase: el modelo del chat produce el artefacto de la fase
# (patron Ricardo: la LLM genera, el recibo verifica). Sin respuesta real ->
# la fase FALLA y el motor se detiene; nada se marca PASS sin evidencia.
def _handler_fase(modelo: str, sesion: str):
    def accion(request: dict) -> dict:
        prompt = (
            '[ECC MOTOR %(skill)s fase %(fase)s] Ejecuta esta etapa del procedimiento '
            'sobre la tarea %(tarea)s. Evento: %(evento)s. Contexto: %(ctx)s. '
            'Devuelve JSON {"status":"PASS","resultado":"<artefacto o decision real>"}.'
            % {'skill': request['skill_id'], 'fase': request['phase_id'],
               'tarea': request['task_id'], 'evento': request['event'],
               'ctx': json.dumps(request.get('context', {}), ensure_ascii=False)[:2000]})
        r = _chat_modelo(modelo, prompt, sesion)
        txt = _texto_respuesta(r)
        if not txt or (isinstance(r, dict) and r.get('error')):
            return {'status': 'FAIL', 'error': str((r or {}).get('error'))[:200]}
        data = _json_de(txt)
        if isinstance(data, dict) and str(data.get('status')).upper() in ('FAIL', 'BLOCKED'):
            return {'status': 'FAIL', 'error': str(data.get('error') or 'modelo declaro FAIL')[:200]}
        artefacto = str((data or {}).get('resultado') or txt)
        return {'status': 'PASS', 'resultado': artefacto[:8000],
                'evidence_sha256': hashlib.sha256(txt.encode()).hexdigest()}
    return accion


def _recibo_callback(request: dict, proposed: dict) -> dict:
    evid = str(proposed.get('evidence_sha256') or '')
    return {'request_id': request['request_id'], 'task_id': request['task_id'],
            'skill_id': request['skill_id'], 'phase_id': request['phase_id'],
            'status': 'PASS' if proposed.get('status') == 'PASS' and evid else 'FAIL',
            'receipt_id': hashlib.sha256(
                (request['request_id'] + evid).encode()).hexdigest()[:32],
            'evidence_source': 'approved_tool'}


async def _correr_ciclo(*, spec: dict, fases: list, skill_id: str, event: str,
                        task_id: str, context: dict, modelo: str, sesion: str) -> dict:
    """Un ciclo = sus fases en orden, cada una con handler + recibo verificado."""
    from nct_loop.ecc_compiled_executor import execute_compiled_motor
    if not fases:
        return {'ok': True, 'status': 'SKIPPED', 'executed': 0, 'receipts': []}
    handlers = {ph['action_id']: _handler_fase(modelo, sesion) for ph in fases}
    spec_parcial = dict(spec, phases=list(fases))
    catalogo = {'skills': {skill_id: spec_parcial}}
    res = await execute_compiled_motor(
        catalog=catalogo, skill_id=skill_id,
        source_sha256=spec['source_sha256'], event=event, task_id=task_id,
        context=context, approved_handlers=handlers,
        receipt_callback=_recibo_callback)
    return res


_MOTORES_CODE = _DIR / 'motores_code'


def _modulo_motor(motor_id: str):
    """Carga el motor code ejecutable (motores_code/ecc_<id>.py)."""
    ruta = _MOTORES_CODE / ('ecc_' + motor_id.replace('-', '_') + '.py')
    if not ruta.is_file():
        return None
    return _mod('eccskill_' + motor_id.replace('-', '_'), ruta)


async def _cerrar_ciclos(rep: dict, repetir) -> dict:
    """Todo motor termina con VERIFY y RECOVERY: si su fuente ECC no los trae, se
    aplican los universales (deterministas, sin modelo). VERIFY: cada recibo MAIN
    es PASS y tiene id. RECOVERY: un solo reintento acotado si MAIN fallo."""
    if not isinstance(rep, dict):
        return {'ok': False, 'status': 'FAIL', 'error': 'motor sin resultado'}
    if not rep.get('ok') and not rep.get('recovery'):
        rep['recovery'] = {'ciclo': 'RECOVERY', 'origen': 'universal', 'intentos': 1}
        segundo = await repetir()
        rep['recovery']['ok'] = bool(segundo.get('ok'))
        if segundo.get('ok'):
            rep = dict(segundo, recovery=rep['recovery'])
    if rep.get('ok') and not rep.get('verify'):
        recibos = (rep.get('main') or {}).get('receipts') or []
        ok = bool(recibos) and all(r.get('status') == 'PASS' and r.get('receipt_id') for r in recibos)
        rep['verify'] = {'ciclo': 'VERIFY', 'origen': 'universal', 'ok': ok,
                         'executed': len(recibos), 'receipts': []}
        if not ok:
            rep['ok'], rep['status'] = False, 'FAILED_VERIFY'
    return rep


_FASE_RX = re.compile(r'\[ECC (\S+) (s\d+)\]')
_TOPE_CUERPO, _TOPE_META = 3500, 2000
_CUERPOS: dict = {}


def _secciones(motor_id: str) -> dict:
    """phase_id -> (ciclo, cuerpo): el texto real de cada seccion del SKILL.md original."""
    if motor_id in _CUERPOS:
        return _CUERPOS[motor_id]
    out, spec = {}, _catalogo_ecc().get(motor_id) or {}
    md = _ECC_DIR / 'skills' / motor_id / 'SKILL.md'
    if md.is_file():
        lineas = md.read_text(encoding='utf-8', errors='replace').splitlines()
        # source_line no coincide con el archivo: cada seccion se ubica por su encabezado, en orden.
        titulos, pos, inicios = [f for f in spec.get('phases') or []], 0, []
        for ph in titulos:
            alvo = (ph.get('title') or '').strip().lower()
            hallado = next((i for i in range(pos, len(lineas))
                            if lineas[i].lstrip().startswith('#') and lineas[i].lstrip('# \t').strip().lower() == alvo), None)
            inicios.append(hallado)
            if hallado is not None:
                pos = hallado + 1
        for i, ph in enumerate(titulos):
            if inicios[i] is None:
                continue
            fin = next((inicios[j] for j in range(i + 1, len(titulos)) if inicios[j] is not None), len(lineas))
            out[ph['phase_id']] = (_ciclo_de_fase(ph.get('title')), '\n'.join(lineas[inicios[i]:fin]).strip())
    _CUERPOS[motor_id] = out
    return out


def _enriquecer(prompt: str) -> str:
    """A la fase se le entrega su seccion del motor y todo el contexto META del mismo motor."""
    m = _FASE_RX.search(prompt)
    sec = _secciones(m.group(1)) if m else {}
    if not m or m.group(2) not in sec:
        return prompt
    meta = '\n\n'.join(c for k, (ciclo, c) in sec.items() if ciclo == 'META' and k != m.group(2))[:_TOPE_META]
    return (prompt + '\n\n[CONTEXTO DEL MOTOR (guias)]\n' + meta +
            '\n\n[INSTRUCCIONES DE ESTA FASE]\n' + sec[m.group(2)][1][:_TOPE_CUERPO] +
            '\n\nResponde SOLO JSON: {"status":"PASS|FAIL|BLOCKED","evidencia":"lo verificable que hiciste","resultado":"..."}')


def _exigir_evidencia(r: dict) -> dict:
    """PASS solo si el modelo devuelve JSON con status PASS y evidencia; si no, FAIL (no se acepta cualquier texto)."""
    if not isinstance(r, dict) or r.get('error'):
        return r
    txt = r.get('reply') or r.get('texto') or ''
    try:
        d, _ = json.JSONDecoder().raw_decode(txt[txt.index('{'):])
    except ValueError:
        d = None
    if isinstance(d, dict) and str(d.get('status')).upper() in ('FAIL', 'BLOCKED'):
        return r
    if isinstance(d, dict) and str(d.get('status')).upper() == 'PASS' and str(d.get('evidencia') or '').strip():
        return r
    return {'reply': json.dumps({'status': 'FAIL', 'error': 'respuesta sin JSON con status PASS y evidencia'})}


async def _ejecutar_motor(motor_id: str, p: dict) -> dict:
    cat = _catalogo_ecc()
    spec = cat.get(motor_id)
    if not isinstance(spec, dict):
        return {'ok': False, 'status': 'MOTOR_NO_EXISTE', 'motor_id': motor_id,
                'disponibles': len(cat)}
    modelo = str(p.get('modelo') or 'ficha-qwen38flash')
    sesion = str(p.get('sesion') or ('motor-' + uuid.uuid4().hex[:8]))

    # Si existe el motor .py generado, el motor corre como codigo ejecutable.
    mod = _modulo_motor(motor_id)
    if mod is not None and hasattr(mod, 'run'):
        def model_fn(prompt: str) -> dict:
            return _exigir_evidencia(_chat_modelo(modelo, _enriquecer(prompt), sesion))
        task_id = str(p.get('task_id') or p.get('proceso_id') or 'tarea-' + uuid.uuid4().hex[:8])
        async def _una_vez():
            return await mod.run(dict(p.get('contexto') or p.get('context') or {}),
                                 task_id=task_id,
                                 event=str(p.get('event') or 'motor.run'),
                                 model_fn=model_fn, receipt_fn=None)
        return await _cerrar_ciclos(await _una_vez(), _una_vez)
    ciclos = _fases_por_ciclo(spec)
    modelo = str(p.get('modelo') or 'ficha-qwen38flash')
    sesion = str(p.get('sesion') or ('motor-' + uuid.uuid4().hex[:8]))
    task_id = str(p.get('task_id') or p.get('proceso_id') or 'tarea-' + uuid.uuid4().hex[:8])
    event = str(p.get('event') or 'motor.run')
    context = dict(p.get('contexto') or p.get('context') or {})
    context.setdefault('objetivo', p.get('objetivo'))

    resultado = {'motor_id': motor_id, 'task_id': task_id,
                 'ciclos': {k: len(v) for k, v in ciclos.items()},
                 'meta_omitidas': len(ciclos['META']),
                 'continuous_triggers': [ph['title'] for ph in ciclos['CONTINUOUS']],
                 'main': None, 'verify': None, 'recovery': None}

    # Ciclo MAIN
    main = await _correr_ciclo(spec=spec, fases=ciclos['MAIN'] or ciclos['VERIFY'], skill_id=motor_id,
                               event=event, task_id=task_id, context=context,
                               modelo=modelo, sesion=sesion)
    resultado['main'] = main
    if not main.get('ok'):
        # Ciclo RECOVERY solo cuando el principal falla
        if ciclos['RECOVERY']:
            resultado['recovery'] = await _correr_ciclo(
                spec=spec, fases=ciclos['RECOVERY'], skill_id=motor_id,
                event=event + '.recovery', task_id=task_id, context=context,
                modelo=modelo, sesion=sesion)
        resultado['ok'] = False
        resultado['status'] = 'FAILED_MAIN'
        return resultado

    # Ciclo VERIFY tras el principal (omitido si ya corrio como principal)
    if ciclos['VERIFY'] and ciclos['MAIN']:
        resultado['verify'] = await _correr_ciclo(
            spec=spec, fases=ciclos['VERIFY'], skill_id=motor_id,
            event=event + '.verify', task_id=task_id, context=context,
            modelo=modelo, sesion=sesion)
        if not resultado['verify'].get('ok'):
            if ciclos['RECOVERY']:
                resultado['recovery'] = await _correr_ciclo(
                    spec=spec, fases=ciclos['RECOVERY'], skill_id=motor_id,
                    event=event + '.recovery', task_id=task_id, context=context,
                    modelo=modelo, sesion=sesion)
            resultado['ok'] = False
            resultado['status'] = 'FAILED_VERIFY'
            return resultado

    resultado['ok'] = True
    resultado['status'] = 'PASS'
    return resultado


def _hilo(pid: str, p: dict) -> dict:
    try:
        return asyncio.run(_correr(pid, p))
    except Exception as e:  # noqa: BLE001
        return {'status': 'FAIL', 'error': '%s: %s' % (type(e).__name__, e)}


MOTORES_PARALELOS = 8


async def _motores_de_ciclo(ciclo: str, objetivo: str, p: dict, pid: str) -> dict:
    """Ejecuta TODOS los motores code del ciclo, sin seleccion. Varios a la vez
    (MOTORES_PARALELOS); cada uno corre MAIN -> VERIFY -> RECOVERY con recibos."""
    ids = sorted(s for s, v in _registro_motores().items() if v['macrociclo'].upper() == ciclo)
    sem = asyncio.Semaphore(MOTORES_PARALELOS)

    async def uno(sid):
        async with sem:
            if pid in _CANCEL:
                return sid, 'CANCELADO'
            r = await _ejecutar_motor(sid, {'modelo': p.get('modelo'), 'sesion': p.get('sesion'),
                                                  'task_id': ciclo + '-' + sid, 'objetivo': objetivo,
                                                  'event': 'gobernanza.' + ciclo})
            return sid, str(r.get('status'))

    hechos = await asyncio.gather(*(uno(x) for x in ids))
    fallos = sorted(sid for sid, st in hechos if st != 'PASS')
    return {'total': len(ids), 'pass': len(ids) - len(fallos), 'fallos': fallos}


async def _gobernar(pid: str, p: dict) -> dict:
    """OBJETIVO -> C0..C7 -> WATCHDOG (nct_loop/gobernanza.py) sobre el engine CODA.
    Los 311 motores code corren todos, cada uno en su ciclo."""
    from nct_loop.gobernanza import Gobernanza
    p = _resolver_mirror(dict(p))
    p['mission_id'] = str(p.get('mission_id') or 'nct-' + pid[-12:])
    activar = p.get('motores', True) is not False

    async def ejecutar(_mission):
        return await _correr(pid, dict(p))

    async def motores(ciclo, objetivo):
        return await _motores_de_ciclo(ciclo, objetivo, p, pid)

    from nct_loop.ricardo_adapter import RicardoOpsDemo
    gob = Gobernanza(
        ricardo=RicardoOpsDemo(_WS_ROOT / pid, _POLICY),
        ejecutar_mision=ejecutar,
        construir_mision=lambda q, _s: _build_mission(dict(q)),
        motores=motores if activar else None,
        cancelado=lambda: pid in _CANCEL,
        ops_permitidas=_OPS_RICARDO,
        checkpoint_dir=_WS_ROOT / pid,
        max_reparaciones=int(p.get('max_reparaciones') or 2))
    return await gob.run(p)


def _hilo_gob(pid: str, p: dict) -> dict:
    try:
        return asyncio.run(_gobernar(pid, p))
    except Exception as e:  # noqa: BLE001
        return {'status': 'FAIL', 'error': '%s: %s' % (type(e).__name__, e)}


_URL_GH = re.compile(r'^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
_MAX_MIRRORS = 10


def _espejo_base() -> dict:
    f = _CONFIG / 'agentes.json'
    if not f.is_file():
        raise ValueError('sin espejo: ejecutar GENERAR_MIRROR_AGENTES.py')
    return json.loads(f.read_text(encoding='utf-8'))


def _extras() -> dict:
    f = _STATE / 'mirrors_extra.json'
    return json.loads(f.read_text(encoding='utf-8')) if f.is_file() else {}


def _guardar_extras(d: dict) -> None:
    _STATE.mkdir(exist_ok=True)
    tmp = _STATE / 'mirrors_extra.tmp'
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    tmp.replace(_STATE / 'mirrors_extra.json')


def _espejo() -> dict:
    """Espejo generado + los espejos que se agregaron en caliente (fuente_agregar)."""
    doc, extra = _espejo_base(), _extras()
    for a in doc['agentes']:
        a['mirrors'] = list(a.get('mirrors') or []) + list(extra.get(a['id'], []))
    return doc


def _fuente(action: str, p: dict) -> dict:
    ids = {a['id'] for a in _espejo_base()['agentes']}
    aid = str(p.get('agente') or '')
    if action == 'fuente_listar':
        doc = _espejo()
        lista = [a for a in doc['agentes'] if not aid or a['id'] == aid]
        return {'ok': True, 'agentes': len(lista), 'mirrors': sum(len(a['mirrors']) for a in lista),
                'detalle': {a['id']: a['mirrors'] for a in lista if a['mirrors']}}
    if aid not in ids:
        return {'error': 'AGENTE_NO_EXISTE', 'agente': aid}
    extra = _extras()
    if action == 'fuente_agregar':
        url = str(p.get('url') or '')
        if not _URL_GH.match(url):
            return {'error': 'url debe ser https://github.com/<dueno>/<repo>'}
        actuales = next(a for a in _espejo()['agentes'] if a['id'] == aid)['mirrors']
        if len(actuales) >= _MAX_MIRRORS:
            return {'error': 'maximo %d espejos por agente' % _MAX_MIRRORS}
        if any(m.get('url') == url for m in actuales):
            return {'error': 'ESPEJO_REPETIDO', 'url': url}
        m = {'id': 'extra-' + uuid.uuid4().hex[:6], 'tipo': str(p.get('tipo') or 'extra')[:12],
             'url': url, 'rama': str(p.get('rama') or 'HEAD')[:60], 'sha': ''}
        extra.setdefault(aid, []).append(m)
        _guardar_extras(extra)
        return {'ok': True, 'agente': aid, 'mirror': m, 'total': len(actuales) + 1}
    if action == 'fuente_quitar':
        mid = str(p.get('mirror_id') or '')
        antes = len(extra.get(aid, []))
        extra[aid] = [m for m in extra.get(aid, []) if m.get('id') != mid]
        if len(extra[aid]) == antes:
            return {'error': 'solo se quitan espejos agregados (extra-...)', 'mirror_id': mid}
        _guardar_extras(extra)
        return {'ok': True, 'agente': aid, 'quitado': mid}
    return {'error': 'ACCION_DESCONOCIDA'}


def _sha_remoto(url: str, rama: str) -> str:
    r = subprocess.run(['git', 'ls-remote', url, rama or 'HEAD'], capture_output=True, text=True, timeout=30, check=False)
    return r.stdout.split()[0] if r.returncode == 0 and r.stdout.strip() else ''


def _fuente_sync(p: dict) -> dict:
    """Refresca el sha de cada espejo remoto con git ls-remote (sin clonar). Los de
    config/ se informan; los agregados en caliente se actualizan en state/."""
    aid, extra, vistos = str(p.get('agente') or ''), _extras(), []
    for a in _espejo()['agentes']:
        if aid and a['id'] != aid:
            continue
        for m in a['mirrors']:
            if not _URL_GH.match(str(m.get('url') or '')):
                continue
            try:
                sha = _sha_remoto(m['url'], m.get('rama', 'HEAD'))
            except (OSError, subprocess.SubprocessError) as e:
                sha = ''
                m['error'] = type(e).__name__
            vistos.append({'agente': a['id'], 'mirror': m['id'], 'sha': sha, 'cambio': bool(m.get('sha')) and sha != m.get('sha')})
            for e in extra.get(a['id'], []):
                if e.get('id') == m['id'] and sha:
                    e['sha'] = sha
    _guardar_extras(extra)
    return {'ok': True, 'revisados': len(vistos), 'espejos': vistos}


# --- Mirrors = instancias de agente (hermes-01..10, openclaw-01..10, ...) con su modelo ---------------
_TIPOS_MIRROR = {'hermes': 'hermes-agent', 'openclaw': 'openclaw', 'claudecode': 'claude-code', 'codex': None}
_MAX_POR_TIPO = 10


def _cfg_mirror(sesion: str) -> tuple:
    f = _STATE / 'mirror_cfg.json'
    todo = json.loads(f.read_text(encoding='utf-8')) if f.is_file() else {}
    cfg = todo.setdefault(sesion, {})
    cfg.setdefault('modelo', {})
    cfg.setdefault('extra', [])
    return todo, cfg


def _guardar_cfg_mirror(todo: dict) -> None:
    _STATE.mkdir(exist_ok=True)
    tmp = _STATE / 'mirror_cfg.tmp'
    tmp.write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding='utf-8')
    tmp.replace(_STATE / 'mirror_cfg.json')


def _llamables() -> list:
    return [{'id': a['id'], 'grupo': a['id'].split('-')[0].split('.')[0].upper(), 'nombre': a['id']}
            for a in _espejo_base()['agentes'] if a['tipo'] == 'modelo' and a['estado'] == 'llamable']


def _slots(extra: list) -> list:
    base = [{'id': '%s-%02d' % (t, i), 'tipo': t, 'nombre': '%s %02d' % (t.title(), i)}
            for t in _TIPOS_MIRROR for i in range(1, _MAX_POR_TIPO + 1)]
    return base + [dict(x) for x in extra]


def _mirror_inst(action: str, p: dict) -> dict:
    sesion = str(p.get('sesion') or 'general')[:60]
    todo, cfg = _cfg_mirror(sesion)
    slots = _slots(cfg.get('extra') or [])
    ids = {x['id'] for x in slots}
    if action == 'mirror_listar':
        reg = {a['id']: a for a in _espejo()['agentes']}
        for x in slots:
            x['modelo'] = cfg['modelo'].get(x['id'])
            fuente = reg.get(_TIPOS_MIRROR.get(x['tipo']) or x['tipo'])
            x['fuentes'] = [m['url'] for m in (fuente or {}).get('mirrors', []) if m.get('url')]
        return {'ok': True, 'agentes': slots, 'modelos': _llamables(), 'sesion': sesion}
    if action == 'mirror_configurar':
        aid, mod = str(p.get('agente') or '')[:60], str(p.get('modelo') or '')[:120]
        if not aid:
            return {'error': 'GAP_MIRROR_AGENTE_VACIO'}
        if aid not in ids:
            return {'error': 'MIRROR_NO_EXISTE', 'agente': aid}
        if mod and mod not in {m['id'] for m in _llamables()}:
            return {'error': 'MODELO_NO_LLAMABLE', 'modelo': mod}
        if mod:
            cfg['modelo'][aid] = mod
        else:
            cfg['modelo'].pop(aid, None)
        _guardar_cfg_mirror(todo)
        return {'ok': True, 'agente': aid, 'modelo': mod or None}
    if action == 'mirror_agregar':
        tipo, nombre = str(p.get('tipo') or 'custom')[:30], str(p.get('nombre') or '')[:60]
        if not nombre:
            return {'error': 'GAP_MIRROR_NOMBRE_VACIO'}
        if tipo != 'custom' and tipo not in _TIPOS_MIRROR and tipo not in {a['id'] for a in _espejo_base()['agentes']}:
            return {'error': 'TIPO_NO_EXISTE', 'tipo': tipo}
        if sum(1 for x in slots if x['tipo'] == tipo) >= _MAX_POR_TIPO:
            return {'error': 'GAP_MIRROR_MAX', 'tipo': tipo, 'max': _MAX_POR_TIPO}
        nid = '%s-%02d' % (tipo, 1 + sum(1 for x in slots if x['tipo'] == tipo))
        while nid in ids:
            nid += 'x'
        cfg.setdefault('extra', []).append({'id': nid, 'tipo': tipo, 'nombre': nombre})
        _guardar_cfg_mirror(todo)
        return {'ok': True, 'id': nid}
    if action == 'mirror_quitar':
        aid = str(p.get('agente') or '')[:60]
        if aid not in {x['id'] for x in cfg.get('extra') or []}:
            return {'error': 'solo se quitan los mirrors agregados', 'agente': aid}
        cfg['extra'] = [x for x in cfg['extra'] if x['id'] != aid]
        cfg['modelo'].pop(aid, None)
        _guardar_cfg_mirror(todo)
        return {'ok': True, 'agente': aid}
    return {'error': 'ACCION_DESCONOCIDA'}


def _resolver_mirror(p: dict) -> dict:
    """Si el pedido trae `agente` (un mirror, p. ej. hermes-03), su modelo configurado manda."""
    aid = str(p.get('agente') or '')
    if aid:
        _t, cfg = _cfg_mirror(str(p.get('sesion') or 'general')[:60])
        if cfg['modelo'].get(aid):
            p['modelo'] = cfg['modelo'][aid]
    return p


def handle(action: str, payload: "dict | None" = None) -> dict:
    p = payload or {}
    if action in ('status', 'health'):
        return {'ok': True, 'service': 'nct_loop', 'motores': ['coda', 'original', 'gobernanza'],
                'procesos': len(_PROC)}
    if action in ('gobernar', 'ejecutar'):  # ejecutar es un alias: un solo camino, con los 311 motores
        if not str(p.get('objetivo') or p.get('yaiwes_md') or p.get('objetivo_md') or '').strip():
            return {'error': 'falta objetivo (markdown Yaiwes.md)'}
        pid = 'gob-' + uuid.uuid4().hex[:12]
        _PROC[pid] = _POOL.submit(_hilo_gob, pid, dict(p))
        return {'estado': 'procesando', 'proceso_id': pid, 'ciclos': list(__import__('nct_loop.gobernanza', fromlist=['CICLOS']).CICLOS)}
    if action in ('mirror_listar', 'mirror_configurar', 'mirror_agregar', 'mirror_quitar'):
        try:
            return _mirror_inst(action, p)
        except ValueError as e:
            return {'error': str(e)}
    if action in ('fuente_listar', 'fuente_agregar', 'fuente_quitar'):
        try:
            return _fuente(action, p)
        except ValueError as e:
            return {'error': str(e)}
    if action == 'fuente_sync':
        try:
            return _fuente_sync(p)
        except ValueError as e:
            return {'error': str(e)}
    if action == 'agentes':
        try:
            doc = _espejo()
        except ValueError as e:
            return {'error': str(e)}
        tipo = str(p.get('tipo') or '')
        lista = [a for a in doc['agentes'] if not tipo or a['tipo'] == tipo]
        return {'ok': True, 'total': len(lista), 'agentes': lista}
    if action == 'paralelo':
        objetivos = p.get('objetivos')
        if not isinstance(objetivos, list) or not 1 <= len(objetivos) <= MAX_PARALELO:
            return {'error': 'objetivos: lista de 1 a %d' % MAX_PARALELO}
        gid, procesos = 'par-' + uuid.uuid4().hex[:10], []
        for i, o in enumerate(objetivos):
            q = dict(o) if isinstance(o, dict) else {'objetivo': str(o)}
            if not str(q.get('objetivo') or q.get('yaiwes_md') or '').strip():
                return {'error': 'objetivo %d vacio' % i}
            q.setdefault('modelo', p.get('modelo'))
            q.setdefault('agente', p.get('agente'))
            q.setdefault('sesion', '%s-%d' % (gid, i))
            pid = 'gob-' + uuid.uuid4().hex[:12]
            _PROC[pid] = _POOL.submit(_hilo_gob, pid, q)
            procesos.append(pid)
        _GRUPOS[gid] = procesos
        return {'estado': 'procesando', 'grupo_id': gid, 'procesos': procesos, 'maximo': MAX_PARALELO}
    if action == 'estado_paralelo':
        gid = str(p.get('grupo_id') or '')
        if gid not in _GRUPOS:
            return {'error': 'GRUPO_NO_EXISTE'}
        est = [dict(handle('estado', {'proceso_id': x}), proceso_id=x) for x in _GRUPOS[gid]]
        hechos = all(e.get('estado') != 'procesando' for e in est)
        return {'grupo_id': gid, 'estado': 'completado' if hechos else 'procesando', 'procesos': est}
    if action == 'estado':
        pid = str(p.get('proceso_id') or '')
        fut = _PROC.get(pid)
        if fut is None:
            return {'error': 'PROCESO_NO_EXISTE'}
        if pid in _CANCEL:
            return {'estado': 'cancelado', 'proceso_id': pid}
        if not fut.done():
            return {'estado': 'procesando', 'proceso_id': pid}
        if fut.cancelled():
            return {'estado': 'cancelado', 'proceso_id': pid}
        return {'estado': 'completado', 'proceso_id': pid, 'resultado': fut.result()}
    if action == 'motores':
        try:
            cat = _catalogo_ecc()
        except Exception as e:  # noqa: BLE001
            return {'error': str(e)}
        return {'ok': True, 'total': len(cat),
                'motores': {k: {'fases': len(v.get('phases') or []),
                                'ciclos': {c: len(f) for c, f in _fases_por_ciclo(v).items()}}
                            for k, v in cat.items()}}
    if action == 'motores_registro':
        reg = _registro_motores()
        return {'ok': True, 'total': len(reg), 'motores': reg}
    if action == 'motor_fases':
        mid = str(p.get('motor_id') or '')
        spec = _catalogo_ecc().get(mid)
        if not isinstance(spec, dict):
            return {'error': 'MOTOR_NO_EXISTE', 'motor_id': mid}
        ciclos = _fases_por_ciclo(spec)
        return {'ok': True, 'motor_id': mid,
                'ciclos': {c: [{'phase_id': ph['phase_id'], 'title': ph['title']}
                              for ph in f] for c, f in ciclos.items()}}
    if action == 'motor_ejecutar':
        mid = str(p.get('motor_id') or '')
        if not _catalogo_ecc().get(mid):
            return {'error': 'MOTOR_NO_EXISTE', 'motor_id': mid,
                    'disponibles': len(_catalogo_ecc())}
        pid = 'mot-' + uuid.uuid4().hex[:12]
        def _run():
            try:
                return asyncio.run(_ejecutar_motor(mid, dict(p)))
            except Exception as e:  # noqa: BLE001
                return {'ok': False, 'status': 'FAIL',
                        'error': '%s: %s' % (type(e).__name__, e)}
        _PROC[pid] = _POOL.submit(_run)
        return {'estado': 'procesando', 'proceso_id': pid, 'motor_id': mid}
    if action == 'cancelar':
        pid = str(p.get('proceso_id') or '')
        _CANCEL.add(pid)
        fut = _PROC.get(pid)
        if fut is not None:
            fut.cancel()
        return {'estado': 'cancelado', 'proceso_id': pid}
    return {'error': 'ACCION_DESCONOCIDA', 'allowed': ACCIONES}


ACCIONES = ['status', 'health', 'ejecutar', 'gobernar', 'estado', 'cancelar',
            'motores', 'motor_fases', 'motor_ejecutar', 'motores_registro', 'agentes', 'fuente_listar', 'fuente_agregar', 'fuente_quitar', 'fuente_sync',
            'paralelo', 'estado_paralelo']

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
    """Compila los 311 SKILL.md del repo a un registro de fases Python."""
    global _CATALOGO_ECC
    with _CATALOGO_LOCK:
        if _CATALOGO_ECC is None:
            if not _ECC_DIR.is_dir():
                raise RuntimeError('ECC skills no presentes en repo: ' + str(_ECC_DIR))
            from nct_loop.ecc_phase_compiler import compile_directory
            _CATALOGO_ECC = compile_directory(_ECC_DIR)
        return _CATALOGO_ECC


# Separacion de ciclos del skills: cada fase compilada se clasifica por su
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


# Registro normalizado de skills (metodo de 8 macrociclos del audit):
# cada skill -> {skill_id, categoria, triggers, macrociclo C0..C7,
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


def _registro_ecc() -> dict:
    """Registro normalizado de las 311 skills (categoria, triggers, macrociclo...)."""
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
        reg[sid] = {'skill_id': sid, 'categoria': macro,
                    'macrociclo': macro, 'triggers': triggers,
                    'required_tools': tools, 'risk_level': riesgo,
                    'source_sha256': spec.get('source_sha256'),
                    'fases': len(spec.get('phases') or []),
                    'ciclos': {k: len(v) for k, v in ciclos.items()}}
    _REG = reg
    return reg


_ES_EN = {
    'seguridad': 'security', 'codigo': 'code', 'revisar': 'review', 'revisión': 'review',
    'arreglar': 'fix', 'corregir': 'fix', 'error': 'bug defect', 'bug': 'defect bug',
    'pruebas': 'test', 'prueba': 'test', 'desplegar': 'deploy', 'produccion': 'production',
    'producción': 'production', 'diseñar': 'design', 'diseño': 'design',
    'arquitectura': 'architecture', 'crear': 'create build', 'documentar': 'docs',
    'documento': 'document', 'memoria': 'memory', 'cola': 'queue', 'tarea': 'task',
    'verificar': 'verify', 'verificación': 'verify', 'auditar': 'audit',
    'auditoria': 'audit', 'auditoría': 'audit', 'planear': 'plan', 'ejecutar': 'run',
    'analizar': 'analyze', 'investigar': 'research', 'integrar': 'integrate',
    'entregar': 'deliver', 'monitor': 'watch', 'vigilar': 'monitor watchdog',
}


def _palabras_objetivo(objetivo: str) -> set:
    base = set(re.findall(r'[a-zA-Záéíóúñ][a-zA-Z0-9áéíóúñ_+-]{2,}', str(objetivo).lower()))
    extra = set()
    for w in base:
        if w in _ES_EN:
            extra.update(_ES_EN[w].split())
    return base | extra


def _seleccionar_skills(objetivo: str, top: int = 8) -> list:
    """Seleccion contextual: puntua skills por triggers/keywords del objetivo."""
    reg = _registro_ecc()
    palabras = _palabras_objetivo(objetivo)
    scored = []
    for sid, info in reg.items():
        puntos = 0
        for tr in info['triggers']:
            tw = set(re.findall(r'[a-zA-Z][a-zA-Z0-9_+-]{2,}', tr.lower()))
            puntos += len(palabras & tw)
        sid_parts = set(re.split(r'[-_]', sid))
        puntos += 3 * len(palabras & sid_parts)
        if not puntos:
            # fallback: description frontmatter (guardada en triggers vacios)
            puntos = 0
        if puntos:
            scored.append((puntos, sid))
    scored.sort(reverse=True)
    return [{'skill_id': sid, 'score': p, 'macrociclo': reg[sid]['macrociclo']}
            for p, sid in scored[:top]]


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
        if p.get('skills') and not p.get('auto_skills'):
            for u in m['units']:
                u.setdefault('skills', list(p['skills'])[:int(p.get('top_skills') or 3)])
        if p.get('auto_skills'):
            for u in m['units']:
                if not u.get('skills'):
                    u['skills'] = [x['skill_id'] for x in
                                   _seleccionar_skills(u.get('goal') or '',
                                                       int(p.get('top_skills') or 3))]
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
                       'skills': [x['skill_id'] for x in
                                  _seleccionar_skills(objetivo, int(p.get('top_skills') or 3))]
                               if p.get('auto_skills') else (p.get('skills') or []),
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
    # WorkUnit no acepta la clave 'skills': se retira y se conserva por id.
    skills_por_unidad = {u['id']: list(u.pop('skills', []) or [])
                         for u in mission['units']}
    resultado = await engine.run(mission)

    # Activacion por contexto: skills declaradas en cada unidad corren como
    # motores compilados (MAIN->VERIFY->RECOVERY) con recibos por fase.
    corridas = []
    total = 0
    for uid, sids in skills_por_unidad.items():
        for sid in sids[:5]:
            if total >= 12:
                break
            total += 1
            u = next((x for x in mission['units'] if x['id'] == uid), {})
            rep = await _ejecutar_skill_motor(sid, {
                'modelo': modelo, 'sesion': sesion, 'task_id': uid,
                'objetivo': u.get('goal'), 'event': 'unit.skill'})
            corridas.append({'unit_id': uid, 'skill_id': sid,
                             'status': rep.get('status'),
                             'ciclos': rep.get('ciclos'),
                             'recibos': sum(len((rep.get(k) or {}).get('receipts', []))
                                          for k in ('main', 'verify', 'recovery'))})
    if corridas:
        resultado['skills_ejecutadas'] = corridas
    return resultado


# --- Skills ECC compilados a motores ejecutables ---------------------------
# Un handler por fase: el modelo del chat produce el artefacto de la fase
# (patron Ricardo: la LLM genera, el recibo verifica). Sin respuesta real ->
# la fase FALLA y el skill se detiene; nada se marca PASS sin evidencia.
def _handler_fase(modelo: str, sesion: str):
    def accion(request: dict) -> dict:
        prompt = (
            '[ECC SKILL %(skill)s fase %(fase)s] Ejecuta esta etapa del procedimiento '
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
    from nct_loop.ecc_compiled_executor import execute_compiled_skill
    if not fases:
        return {'ok': True, 'status': 'SKIPPED', 'executed': 0, 'receipts': []}
    handlers = {ph['action_id']: _handler_fase(modelo, sesion) for ph in fases}
    spec_parcial = dict(spec, phases=list(fases))
    catalogo = {'skills': {skill_id: spec_parcial}}
    res = await execute_compiled_skill(
        catalog=catalogo, skill_id=skill_id,
        source_sha256=spec['source_sha256'], event=event, task_id=task_id,
        context=context, approved_handlers=handlers,
        receipt_callback=_recibo_callback)
    return res


_PY_SKILLS = _DIR / 'python_skills'


def _modulo_skill(skill_id: str):
    """Carga el motor .py ejecutable del skill (python_skills/ecc_<id>.py)."""
    ruta = _PY_SKILLS / ('ecc_' + skill_id.replace('-', '_') + '.py')
    if not ruta.is_file():
        return None
    return _mod('eccskill_' + skill_id.replace('-', '_'), ruta)


async def _cerrar_ciclos(rep: dict, repetir) -> dict:
    """Todo skill termina con VERIFY y RECOVERY: si su SKILL.md no los trae, se
    aplican los universales (deterministas, sin modelo). VERIFY: cada recibo MAIN
    es PASS y tiene id. RECOVERY: un solo reintento acotado si MAIN fallo."""
    if not isinstance(rep, dict):
        return {'ok': False, 'status': 'FAIL', 'error': 'skill sin resultado'}
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


async def _ejecutar_skill_motor(skill_id: str, p: dict) -> dict:
    cat = _catalogo_ecc()
    spec = cat.get(skill_id)
    if not isinstance(spec, dict):
        return {'ok': False, 'status': 'SKILL_NO_EXISTE', 'skill_id': skill_id,
                'disponibles': len(cat)}
    modelo = str(p.get('modelo') or 'ficha-qwen38flash')
    sesion = str(p.get('sesion') or ('skill-' + uuid.uuid4().hex[:8]))

    # Si existe el motor .py generado, el skill corre como codigo ejecutable.
    mod = _modulo_skill(skill_id)
    if mod is not None and hasattr(mod, 'run'):
        def model_fn(prompt: str) -> dict:
            return _chat_modelo(modelo, prompt, sesion)
        task_id = str(p.get('task_id') or p.get('proceso_id') or 'tarea-' + uuid.uuid4().hex[:8])
        async def _una_vez():
            return await mod.run(dict(p.get('contexto') or p.get('context') or {}),
                                 task_id=task_id,
                                 event=str(p.get('event') or 'skill.run'),
                                 model_fn=model_fn, receipt_fn=None)
        return await _cerrar_ciclos(await _una_vez(), _una_vez)
    ciclos = _fases_por_ciclo(spec)
    modelo = str(p.get('modelo') or 'ficha-qwen38flash')
    sesion = str(p.get('sesion') or ('skill-' + uuid.uuid4().hex[:8]))
    task_id = str(p.get('task_id') or p.get('proceso_id') or 'tarea-' + uuid.uuid4().hex[:8])
    event = str(p.get('event') or 'skill.run')
    context = dict(p.get('contexto') or p.get('context') or {})
    context.setdefault('objetivo', p.get('objetivo'))

    resultado = {'skill_id': skill_id, 'task_id': task_id,
                 'ciclos': {k: len(v) for k, v in ciclos.items()},
                 'meta_omitidas': len(ciclos['META']),
                 'continuous_triggers': [ph['title'] for ph in ciclos['CONTINUOUS']],
                 'main': None, 'verify': None, 'recovery': None}

    # Ciclo MAIN
    main = await _correr_ciclo(spec=spec, fases=ciclos['MAIN'] or ciclos['VERIFY'], skill_id=skill_id,
                               event=event, task_id=task_id, context=context,
                               modelo=modelo, sesion=sesion)
    resultado['main'] = main
    if not main.get('ok'):
        # Ciclo RECOVERY solo cuando el principal falla
        if ciclos['RECOVERY']:
            resultado['recovery'] = await _correr_ciclo(
                spec=spec, fases=ciclos['RECOVERY'], skill_id=skill_id,
                event=event + '.recovery', task_id=task_id, context=context,
                modelo=modelo, sesion=sesion)
        resultado['ok'] = False
        resultado['status'] = 'FAILED_MAIN'
        return resultado

    # Ciclo VERIFY tras el principal (omitido si ya corrio como principal)
    if ciclos['VERIFY'] and ciclos['MAIN']:
        resultado['verify'] = await _correr_ciclo(
            spec=spec, fases=ciclos['VERIFY'], skill_id=skill_id,
            event=event + '.verify', task_id=task_id, context=context,
            modelo=modelo, sesion=sesion)
        if not resultado['verify'].get('ok'):
            if ciclos['RECOVERY']:
                resultado['recovery'] = await _correr_ciclo(
                    spec=spec, fases=ciclos['RECOVERY'], skill_id=skill_id,
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


async def _gobernar(pid: str, p: dict) -> dict:
    """OBJETIVO -> C0..C7 -> WATCHDOG (nct_loop/gobernanza.py) sobre el engine CODA."""
    from nct_loop.gobernanza import Gobernanza
    p = dict(p)
    p['mission_id'] = str(p.get('mission_id') or 'nct-' + pid[-12:])
    p['top_skills'] = int(p.get('top_skills') or 3)

    elegidos = {'skills': []}

    def construir(q, skills):
        elegidos['skills'] = list(skills)  # lo que C1 selecciono llega a la ejecucion
        return _build_mission(dict(q, auto_skills=False, skills=skills))

    async def ejecutar(_mission):
        return await _correr(pid, dict(p, auto_skills=False, skills=elegidos['skills']))

    async def skill(sid, tid, obj):
        return await _ejecutar_skill_motor(sid, {'modelo': p.get('modelo'), 'sesion': p.get('sesion'),
                                                 'task_id': tid, 'objetivo': obj, 'event': 'gobernanza.verify'})

    from nct_loop.ricardo_adapter import RicardoOpsDemo
    gob = Gobernanza(
        ricardo=RicardoOpsDemo(_WS_ROOT / pid, _POLICY),
        ejecutar_mision=ejecutar,
        construir_mision=construir,
        seleccionar_skills=_seleccionar_skills,
        correr_skill=skill,
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
    """Espejo generado + los espejos que se agregaron en caliente (mirror_agregar)."""
    doc, extra = _espejo_base(), _extras()
    for a in doc['agentes']:
        a['mirrors'] = list(a.get('mirrors') or []) + list(extra.get(a['id'], []))
    return doc


def _mirror(action: str, p: dict) -> dict:
    ids = {a['id'] for a in _espejo_base()['agentes']}
    aid = str(p.get('agente') or '')
    if action == 'mirror_listar':
        doc = _espejo()
        lista = [a for a in doc['agentes'] if not aid or a['id'] == aid]
        return {'ok': True, 'agentes': len(lista), 'mirrors': sum(len(a['mirrors']) for a in lista),
                'detalle': {a['id']: a['mirrors'] for a in lista if a['mirrors']}}
    if aid not in ids:
        return {'error': 'AGENTE_NO_EXISTE', 'agente': aid}
    extra = _extras()
    if action == 'mirror_agregar':
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
    if action == 'mirror_quitar':
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


def _mirror_sync(p: dict) -> dict:
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


def handle(action: str, payload: "dict | None" = None) -> dict:
    p = payload or {}
    if action in ('status', 'health'):
        return {'ok': True, 'service': 'nct_loop', 'motores': ['coda', 'original', 'gobernanza'],
                'procesos': len(_PROC)}
    if action == 'ejecutar':
        try:
            _build_mission(p)  # validar antes de lanzar
        except ValueError as e:
            return {'error': str(e)}
        pid = 'nct-' + uuid.uuid4().hex[:12]
        _PROC[pid] = _POOL.submit(_hilo, pid, dict(p))
        return {'estado': 'procesando', 'proceso_id': pid}
    if action == 'gobernar':
        if not str(p.get('objetivo') or p.get('yaiwes_md') or p.get('objetivo_md') or '').strip():
            return {'error': 'falta objetivo (markdown Yaiwes.md)'}
        pid = 'gob-' + uuid.uuid4().hex[:12]
        _PROC[pid] = _POOL.submit(_hilo_gob, pid, dict(p))
        return {'estado': 'procesando', 'proceso_id': pid, 'ciclos': list(__import__('nct_loop.gobernanza', fromlist=['CICLOS']).CICLOS)}
    if action in ('mirror_listar', 'mirror_agregar', 'mirror_quitar'):
        try:
            return _mirror(action, p)
        except ValueError as e:
            return {'error': str(e)}
    if action == 'mirror_sync':
        try:
            return _mirror_sync(p)
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
    if action == 'skills':
        try:
            cat = _catalogo_ecc()
        except Exception as e:  # noqa: BLE001
            return {'error': str(e)}
        return {'ok': True, 'compiladas': len(cat),
                'skills': {k: {'fases': len(v.get('phases') or []),
                               'ciclos': {c: len(f) for c, f in _fases_por_ciclo(v).items()}}
                           for k, v in cat.items()}}
    if action == 'skills_registro':
        reg = _registro_ecc()
        return {'ok': True, 'total': len(reg), 'skills': reg}
    if action == 'skills_seleccionar':
        objetivo = str(p.get('objetivo') or p.get('goal') or '')
        if not objetivo:
            return {'error': 'objetivo requerido'}
        sel = _seleccionar_skills(objetivo, int(p.get('top') or 8))
        macros = sorted({x['macrociclo'] for x in sel})
        return {'ok': True, 'seleccionadas': sel, 'macrociclos': macros}
    if action == 'skill_fases':
        sid = str(p.get('skill_id') or '')
        spec = _catalogo_ecc().get(sid)
        if not isinstance(spec, dict):
            return {'error': 'SKILL_NO_EXISTE', 'skill_id': sid}
        ciclos = _fases_por_ciclo(spec)
        return {'ok': True, 'skill_id': sid,
                'ciclos': {c: [{'phase_id': ph['phase_id'], 'title': ph['title']}
                              for ph in f] for c, f in ciclos.items()}}
    if action == 'skill_ejecutar':
        sid = str(p.get('skill_id') or '')
        if not _catalogo_ecc().get(sid):
            return {'error': 'SKILL_NO_EXISTE', 'skill_id': sid,
                    'disponibles': len(_catalogo_ecc())}
        pid = 'skl-' + uuid.uuid4().hex[:12]
        def _run():
            try:
                return asyncio.run(_ejecutar_skill_motor(sid, dict(p)))
            except Exception as e:  # noqa: BLE001
                return {'ok': False, 'status': 'FAIL',
                        'error': '%s: %s' % (type(e).__name__, e)}
        _PROC[pid] = _POOL.submit(_run)
        return {'estado': 'procesando', 'proceso_id': pid, 'skill_id': sid}
    if action == 'cancelar':
        pid = str(p.get('proceso_id') or '')
        _CANCEL.add(pid)
        fut = _PROC.get(pid)
        if fut is not None:
            fut.cancel()
        return {'estado': 'cancelado', 'proceso_id': pid}
    return {'error': 'ACCION_DESCONOCIDA', 'allowed': ACCIONES}


ACCIONES = ['status', 'health', 'ejecutar', 'gobernar', 'estado', 'cancelar',
            'skills', 'skill_fases', 'skill_ejecutar',
            'skills_registro', 'skills_seleccionar', 'agentes', 'mirror_listar', 'mirror_agregar', 'mirror_quitar', 'mirror_sync',
            'paralelo', 'estado_paralelo']

"""Motor de gobernanza: OBJETIVO -> C0..C7 -> WATCHDOG, como codigo Python.

Cinco motores con una responsabilidad cada uno. No hay prompts ni JSON que
decidan el flujo: el orden de ciclos y el microciclo estan aqui, y cada paso
deja un recibo. El engine (NCTLoopEngine/CODA) sigue siendo quien ejecuta la
unidad; este modulo lo gobierna y lo verifica por fuera.
"""
from __future__ import annotations
import json, time
from pathlib import Path
from .contracts import stable_hash
from .classifier import classify, choose_route

CICLOS = ('C0_ADMISION', 'C1_INVESTIGACION', 'C2_DECISION', 'C3_PLANIFICACION',
          'C4_PREPARACION', 'C5_EJECUCION', 'C6_VERIFICACION', 'C7_INTEGRACION')

MOTORES = {
    'M1_GOBERNANZA': ('C0_ADMISION', 'C4_PREPARACION'),
    'M2_PLANIFICACION': ('C1_INVESTIGACION', 'C2_DECISION', 'C3_PLANIFICACION'),
    'M3_EJECUCION': ('C5_EJECUCION',),
    'M4_VERIFICACION': ('C6_VERIFICACION',),
    'M5_OPERACIONES': ('C7_INTEGRACION',),
}

# Microciclo por unidad. 'etapa' = etapa del engine que lo cubre; 'motor' = quien
# lo cubre cuando no es una etapa del engine.
MICROCICLO = (
    ('INSPECCIONAR', 'etapa', 'INSPECT'),
    ('INVESTIGAR', 'etapa', 'RESEARCH'),
    ('PLANIFICAR', 'etapa', 'PLAN'),
    ('CREAR_PRUEBA', 'etapa', 'TEST_RED'),
    ('EJECUTAR_RED', 'etapa', 'TEST_RED'),
    ('IMPLEMENTAR', 'etapa', 'IMPLEMENT'),
    ('EJECUTAR_GREEN', 'etapa', 'TEST_GREEN'),
    ('REFACTORIZAR', 'etapa', 'REVIEW'),
    ('PRUEBAS_REGRESION', 'skill', 'ai-regression-testing'),
    ('VERIFICADOR_INDEPENDIENTE', 'motor', 'M4_VERIFICACION'),
    ('REPARACION_ACOTADA', 'motor', 'M3_EJECUCION'),
    ('CHECKPOINT', 'motor', 'M5_OPERACIONES'),
)

SKILLS_REGRESION = ('ai-regression-testing', 'verification-loop', 'module-regression')


class Gobernanza:
    """Puertos inyectados (todos opcionales salvo ejecutar_mision):

    ejecutar_mision(mission) -> awaitable dict   engine.run
    construir_mision(p, skills) -> dict          misión con units/DAG
    seleccionar_skills(objetivo, top) -> list    registro ECC
    correr_skill(skill_id, task_id, objetivo) -> awaitable dict
    council(contexto) -> awaitable dict          solo si C2 lo pide
    cancelado() -> bool                          Sheriff/Guardian: bloqueo externo
    ricardo                                      ejecutor Ricardo (Motor confinado) usado en C0..C7
    """

    def __init__(self, *, ejecutar_mision, construir_mision, seleccionar_skills=None,
                 correr_skill=None, council=None, cancelado=None,
                 ops_permitidas=None, checkpoint_dir=None, max_reparaciones=2, ricardo=None):
        self.ricardo = ricardo  # RicardoOpsDemo / ejecutor Motor: participa en cada ciclo
        self.ejecutar_mision = ejecutar_mision
        self.construir_mision = construir_mision
        self.seleccionar_skills = seleccionar_skills or (lambda o, n: [])
        self.correr_skill = correr_skill
        self.council = council
        self.cancelado = cancelado or (lambda: False)
        self.ops_permitidas = set(ops_permitidas or [])
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
        self.max_reparaciones = max(0, int(max_reparaciones))
        self.ciclos = []
        self._t0 = time.monotonic()

    # ---- helpers -------------------------------------------------------
    def _cerrar(self, ciclo, ok, **datos):
        motor = next(m for m, cs in MOTORES.items() if ciclo in cs)
        rec = {'ciclo': ciclo, 'motor': motor, 'ok': bool(ok),
               't': round(time.monotonic() - self._t0, 4), **datos}
        rec['recibo'] = stable_hash([ciclo, motor, bool(ok), datos])[:16]
        self.ciclos.append(rec)
        return rec

    def _salida(self, status, p, **extra):
        ultimo = self.ciclos[-1]['ciclo'] if self.ciclos else None
        return {'status': status, 'objetivo': str(p.get('objetivo') or '')[:200],
                'ciclo_alcanzado': ultimo, 'ciclos': self.ciclos,
                'watchdog': self._watchdog(), **extra}

    def _watchdog(self):
        """Supervision separada: solo lee los recibos, nunca decide."""
        fallos = [c['ciclo'] for c in self.ciclos if not c['ok']]
        return {'ciclos_vistos': len(self.ciclos), 'ciclos_totales': len(CICLOS),
                'fallos': fallos, 'duracion_s': round(time.monotonic() - self._t0, 4),
                'orden_valido': [c['ciclo'] for c in self.ciclos] == list(CICLOS[:len(self.ciclos)]),
                'estado': 'OK' if not fallos else 'ALERTA'}

    def _checkpoint(self, mission_id, datos):
        if not self.checkpoint_dir:
            return None
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        f = self.checkpoint_dir / ('gobernanza_%s.json' % mission_id)
        f.write_text(json.dumps(datos, ensure_ascii=False, indent=1, default=str), encoding='utf8')
        return str(f)

    async def _ricardo_inspeccionar(self):
        """C1: inspect_workspace por el Motor Ricardo (lectura real del workspace)."""
        if self.ricardo is None:
            return None
        try:
            rep = await self.ricardo.execute({'meta': {'name': 'gob-c1'},
                                              'ops': [{'id': 'i1', 'op': 'inspect_workspace'}]}, 'GOB')
            return {'ok': bool(rep.get('ok')), 'origen': rep.get('report_origin'),
                    'ejecutadas': rep.get('executed_count')}
        except Exception as e:  # noqa: BLE001
            return {'ok': False, 'error': '%s: %s' % (type(e).__name__, e)}

    def _ricardo_dag(self, units):
        """C3: el DAG de unidades pasa por Motor.order de Ricardo (ids unicos, deps, ciclos)."""
        if self.ricardo is None:
            return None
        from referencia_ricardo.motor_cli import Motor, MotorError
        try:
            m = Motor(self.ricardo.root, self.ricardo.policy)
            nodos = [{'id': u['id'], 'op': 'finish', 'depends_on': list(u.get('depends_on') or [])} for u in units]
            m.max_ops = max(m.max_ops, len(nodos))
            return {'ok': True, 'orden': [x['id'] for x in m.order(nodos)]}
        except MotorError as e:
            return {'ok': False, 'error': str(e)}

    # ---- ejecucion -----------------------------------------------------
    async def run(self, p: dict) -> dict:
        objetivo = str(p.get('objetivo') or p.get('yaiwes_md') or p.get('objetivo_md') or '').strip()

        # C0 ADMISION (M1): objetivo decidible, no bloqueado, permisos dentro de politica.
        pedidas = set(p.get('allowed_ops') or [])
        fuera = sorted(pedidas - self.ops_permitidas) if self.ops_permitidas and pedidas else []
        motivo = ('objetivo_vacio' if len(objetivo) < 8 else
                  'bloqueado_por_guardian' if self.cancelado() else
                  'ops_fuera_de_politica' if fuera else None)
        self._cerrar('C0_ADMISION', motivo is None, motivo=motivo, ops_fuera=fuera,
                     ricardo={'catalogo_allowed_ops': sorted(self.ops_permitidas)})
        if motivo:
            return self._salida('RECHAZADO', p, motivo=motivo)

        # C1 INVESTIGACION (M2): skills y macrociclos que aplican al objetivo.
        skills = list(self.seleccionar_skills(objetivo, int(p.get('top_skills') or 8)) or [])
        ids = [s['skill_id'] if isinstance(s, dict) else str(s) for s in skills]
        inspeccion = await self._ricardo_inspeccionar()
        self._cerrar('C1_INVESTIGACION', True, skills=ids, ricardo=inspeccion,
                     macrociclos=sorted({s.get('macrociclo') for s in skills
                                         if isinstance(s, dict) and s.get('macrociclo')}))

        # C2 DECISION (M2): Council solo si hay ambiguedad (sin skills o objetivo complejo).
        clas = classify(objetivo, [])
        ruta = choose_route(clas)
        pide_council = (not ids) or clas['intent'] == 'compleja'
        decision = {'ruta': ruta['route'], 'council': 'NO_REQUERIDO'}
        if pide_council:
            if self.council is None:
                decision['council'] = 'REQUERIDO_NO_CONECTADO'
            else:
                r = await self.council({'objetivo': objetivo, 'ruta': ruta, 'skills': ids})
                decision['council'] = 'CONSULTADO'
                decision['veredicto'] = r.get('veredicto') if isinstance(r, dict) else None
        decision['ricardo'] = {'tipado': 'pendiente_C4'}
        self._cerrar('C2_DECISION', True, **decision)

        # C3 PLANIFICACION (M2): DAG de unidades, sin ciclos ni dependencias rotas.
        mission = self.construir_mision(p, ids)
        units = mission.get('units') or []
        orden, err = _orden_topologico(units)
        dag = self._ricardo_dag(units) if not err else None
        if dag is not None and not dag['ok']:
            err = 'dag_rechazado_por_ricardo: ' + dag['error']
        self._cerrar('C3_PLANIFICACION', not err, error=err, unidades=orden, ricardo=dag)
        if err:
            return self._salida('BLOQUEADO', p, motivo=err)

        # C4 PREPARACION (M1): contexto y permisos por unidad; nada sin allowed_ops.
        permisos = {u['id']: sorted(u.get('allowed_ops') or []) for u in units}
        sin = [k for k, v in permisos.items() if not v]
        fuera_cat = sorted({o for v in permisos.values() for o in v} - self.ops_permitidas) if self.ops_permitidas else []
        self._cerrar('C4_PREPARACION', not sin and not fuera_cat, permisos=permisos, unidades_sin_permiso=sin,
                     ricardo={'ops_fuera_de_catalogo': fuera_cat})
        if fuera_cat:
            return self._salida('BLOQUEADO', p, motivo='ops_fuera_de_catalogo_ricardo')
        if sin:
            return self._salida('BLOQUEADO', p, motivo='unidades_sin_permiso')

        # C5 EJECUCION (M3): microciclo por unidad con reparacion acotada.
        resultado, intentos = {}, 0
        while True:
            intentos += 1
            resultado = await self.ejecutar_mision(mission)
            if resultado.get('status') in ('DONE_VERIFICADO', 'ALREADY_COMPLETED') \
               or intentos > self.max_reparaciones or self.cancelado():
                break
        micro = _microciclo(resultado, units)
        self._cerrar('C5_EJECUCION', resultado.get('status') in ('DONE_VERIFICADO', 'ALREADY_COMPLETED'),
                     ricardo={'recibos_motor': sum(1 for r in resultado.get('receipts') or []
                                                  if (r.get('evidence') or {}).get('report_origin') == 'MOTOR_CLI_LOCAL_REAL')},
                     intentos=intentos, estado_engine=resultado.get('status'),
                     error=resultado.get('error'), microciclo=micro)

        # C6 VERIFICACION (M4): independiente del ejecutor. Usa el checker del engine
        # (tres capas + gate de evidencia) y corre skills de regresion como motores.
        triple = (resultado.get('triple_gate') or {})
        evidencia_ok = bool(triple.get('ok')) or resultado.get('status') == 'ALREADY_COMPLETED'
        regresion = []
        if self.correr_skill and evidencia_ok:
            disponibles = [s for s in SKILLS_REGRESION if s in ids] or []
            for sid in disponibles[:2]:
                r = await self.correr_skill(sid, units[0]['id'], objetivo)
                regresion.append({'skill_id': sid, 'status': (r or {}).get('status')})
        regresion_ok = all(x['status'] == 'PASS' for x in regresion)
        self._cerrar('C6_VERIFICACION', evidencia_ok and regresion_ok,
                     evidencia=evidencia_ok, regresion=regresion,
                     ricardo={'tres_capas_por_unidad': [x.get('ok') for x in triple.get('per_task') or []]})

        # C7 INTEGRACION (M5): checkpoint y cierre. DONE solo con C6 en PASS.
        todo_ok = all(c['ok'] for c in self.ciclos)
        ruta_cp = self._checkpoint(mission.get('mission_id', 'sin-id'),
                                   {'ciclos': self.ciclos, 'status_engine': resultado.get('status'),
                                    'mission_sha': stable_hash(mission)})
        self._cerrar('C7_INTEGRACION', todo_ok, checkpoint=ruta_cp,
                     ricardo={'ciclos_con_ricardo': [c['ciclo'] for c in self.ciclos if c.get('ricardo') is not None]})
        return self._salida('DONE_VERIFICADO' if todo_ok else 'FALLO_VERIFICACION', p,
                            mission_id=mission.get('mission_id'), engine=resultado.get('status'),
                            recibos=len(resultado.get('receipts') or []))


def _orden_topologico(units):
    ids = [u.get('id') for u in units]
    if not units or len(set(ids)) != len(ids):
        return [], 'dag_vacio_o_ids_repetidos'
    deps = {u['id']: set(u.get('depends_on') or []) for u in units}
    if any(d - set(ids) for d in deps.values()):
        return [], 'dependencia_inexistente'
    orden, listos = [], {k for k, v in deps.items() if not v}
    while listos:
        n = sorted(listos)[0]
        listos.discard(n)
        orden.append(n)
        for k, v in deps.items():
            if n in v:
                v.discard(n)
                if not v and k not in orden:
                    listos.add(k)
    return orden, (None if len(orden) == len(ids) else 'dag_con_ciclo')


def _microciclo(resultado, units):
    """Cobertura real del microciclo leida del trace del engine (no declarada)."""
    vistas = {}
    for ev in resultado.get('trace') or []:
        if ev.get('event') == 'phase.4.model':
            vistas.setdefault(ev.get('task_id'), set()).add(ev.get('stage'))
    recibos = {r.get('task_id') for r in resultado.get('receipts') or []}
    out = []
    for u in units:
        st = vistas.get(u['id'], set())
        pasos = {}
        for nombre, tipo, ref in MICROCICLO:
            pasos[nombre] = (ref in st) if tipo == 'etapa' else tipo
        out.append({'unidad': u['id'], 'etapas_engine': sorted(st),
                    'recibo': u['id'] in recibos, 'pasos': pasos})
    return out

# DSL G17 — MOTOR DE OBJETIVOS EN BUCLE (LOOP hasta cumplir) + MODO POR VUELTA
# Una llamada al modelo por tarea por vuelta, sin salir al chat, hasta verificar el objetivo
# o alcanzar un limite. Usa el Harness existente via llamar(modo, prompt). DSL G19: el buzon
# del proceso se lee al INICIO de cada vuelta (instruccion/tarea/prioridad/pausa/cancelar).
import json
import re
import time

ESTADOS = ('pendiente', 'sigue', 'hecho', 'bloqueada')

_ESTADOS: dict = {}  # proceso_id -> ultimo estado guardado (visor/estado_objetivo)


def _bloques_verbatim(texto, max_chars=8500):
    # DSL A03: particion preservando el INPUT integro (concatenado = original; ni un caracter fuera)
    t = str(texto or '')
    if len(t) <= max_chars:
        return [t]
    partes, i, n = [], 0, len(t)
    while i < n:
        j = min(i + max_chars, n)
        if j < n:
            c = max(t.rfind('\n\n', i, j), t.rfind('\n', i, j), t.rfind(' ', i, j))
            if c > i:
                j = c
        partes.append(t[i:j])
        i = j
    return [b for b in partes if b]


def _normalizar_tarea(x, i, modo):
    # DSL A03: los dict conservan sus campos (input_bloque + shas); solo el TEXTO de un escalar se corta
    if isinstance(x, dict):
        t = dict(x)
        t.setdefault('texto', 'bloque verbatim')
        t.setdefault('id', 'T%d' % (i + 1))
        t.setdefault('estado', 'pendiente')
        t.setdefault('intentos', 0)
        t.setdefault('modo', modo)
        return t
    return {'id': 'T%d' % (i + 1), 'texto': str(x)[:500], 'estado': 'pendiente', 'intentos': 0, 'modo': modo}


def _json_de(texto):
    m = re.search(r'\{.*\}', texto or '', re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return None


def _prompt_vuelta(obj, t, resumen, instrucciones=None):
    ins = ''
    if instrucciones:
        ins = ('\n\nINSTRUCCIONES NUEVAS DEL DIRECTOR (obligatorias):\n'
               + '\n'.join('- ' + str(x)[:500] for x in instrucciones))
    if t.get('input_bloque') is not None:  # DSL A03: bloque verbatim + sha que referencia el objetivo literal
        tarea_txt = ('<tarea_verbatim sha256="%s" objetivo_sha256="%s">\n%s\n</tarea_verbatim>'
                     % (str(t.get('sha_input') or '')[:12], str(t.get('sha_objetivo') or '')[:12], str(t['input_bloque'])))
    else:
        tarea_txt = str(t.get('texto') or '')
    return ('OBJETIVO DEL DIRECTOR:\n' + obj['objetivo'] + '\n\n'
            'TAREA ACTUAL (' + t['id'] + '): ' + tarea_txt + '\n\n'
            'HECHO HASTA AHORA (resumen):\n' + (resumen or '(nada aún)') + ins + '\n\n'
            'Haz SOLO esta tarea ahora, usando herramientas si hacen falta. No pidas confirmación.\n'
            'Responde AL FINAL con este JSON exacto: {"tarea":"' + t['id'] + '","estado":"hecho|sigue|bloqueado",'
            '"resultado":"...","evidencia":"...","nuevas_tareas":[],"nota_siguiente":"..."}')


def _prompt_plan(obj, lim):
    return ('OBJETIVO DEL DIRECTOR:\n' + obj['objetivo'] + '\n\nDivide el objetivo en tareas pequeñas y ejecutables, '
            'una instrucción por tarea, en orden, máximo ' + str(lim['max_tareas']) + '. '
            'Responde SOLO JSON: {"tareas":["...","..."]}')


def _prompt_verif(obj, tareas):
    hechas = '\n'.join('- %s %s: %s' % (t['id'], t['estado'], (t.get('evidencia') or '')[:200]) for t in tareas)
    return ('OBJETIVO:\n' + obj['objetivo'] + '\n\nESTADO DE TAREAS:\n' + hechas + '\n\n'
            'Verifica con herramientas de lectura si el objetivo COMPLETO está cumplido. '
            'Responde SOLO JSON: {"cumplido":true|false,"faltantes":["tarea que falta",...],"evidencia":"..."}')


def estado_de(proceso_id):
    # para estado_objetivo / buzon_enviar: la ultima foto del motor por proceso
    return dict(_ESTADOS.get(proceso_id) or {})


def correr_objetivo(obj, llamar, guardar, progreso, estado=None, buzon=None):
    """llamar(modo, prompt) -> {'texto': str, 'herramientas_ok': int}  (usa el Harness existente)
       guardar(estado) -> checkpoint (objective_store/SQLite por proceso_id) ; progreso(txt) -> visor, NO chat
       buzon(proceso_id) -> [mensajes no aplicados] + aplicar(id, vuelta)  (DSL G19)"""
    pid = str(obj.get('proceso_id') or '')
    lim = dict({'max_vueltas': 20, 'max_tareas': 50, 'max_minutos': 240, 'max_intentos_por_tarea': 3,
                'max_vueltas_sin_progreso': 5, 'pausa_entre_vueltas_s': 2}, **(obj.get('limites') or {}))
    st = estado or {'tareas': [], 'vuelta': 0, 'resumen': [], 't0': time.time(), 'sin_progreso': 0,
                    'instrucciones_director': [], 'reanudaciones': 0}
    if not st['tareas']:
        base = obj.get('tareas')
        if not base:
            import hashlib as _h3
            obj_txt = str(obj.get('objetivo') or '')
            if len(obj_txt) > 8500:  # DSL A03: entrada grande -> particion verbatim con sha; NUNCA se resume ni trunca
                bloques = _bloques_verbatim(obj_txt)
                if len(bloques) > lim['max_tareas']:
                    return {'estado': 'LIMITE', 'gap': 'GAP_INPUT_EXCEDE_COLA', 'tareas': [], 'vueltas': 0}
                base = [{'id': 'T%d' % (k + 1), 'texto': 'Entregar bloque %d/%d del objetivo verbatim' % (k + 1, len(bloques)),
                         'input_bloque': b, 'sha_input': _h3.sha256(b.encode('utf-8')).hexdigest(),
                         'sha_objetivo': _h3.sha256(obj_txt.encode('utf-8')).hexdigest()} for k, b in enumerate(bloques)]
            else:
                r = llamar('planificador', _prompt_plan(obj, lim))
                base = ((_json_de(r['texto']) or {}).get('tareas') or [obj_txt])
        st['tareas'] = [_normalizar_tarea(x, i, obj.get('modo_por_defecto', 'code')) for i, x in enumerate(base[:lim['max_tareas']])]
        guardar(st)
    if pid:
        _ESTADOS[pid] = dict(st)

    def _leer_buzon():
        if not pid or buzon is None:
            return []
        try:
            return buzon(pid)
        except Exception:  # noqa: BLE001
            return []

    while True:
        # --- DSL G19: al INICIO de cada vuelta el motor lee el buzon antes de elegir tarea ---
        for m in _leer_buzon():
            tipo, txt = m.get('tipo'), str(m.get('texto') or '')
            if tipo == 'instruccion':
                st['instrucciones_director'].append(txt)
            elif tipo == 'tarea':
                if len(st['tareas']) < lim['max_tareas']:
                    st['tareas'].append({'id': 'T%d' % (len(st['tareas']) + 1), 'texto': txt[:500],
                                         'estado': 'pendiente', 'intentos': 0, 'modo': obj.get('modo_por_defecto', 'code')})
            elif tipo == 'prioridad':
                hit = next((t for t in st['tareas'] if txt[:80] in t['texto'] or txt == t['id']), None)
                if hit:
                    st['tareas'].remove(hit); st['tareas'].insert(0, hit)
                elif txt and len(st['tareas']) < lim['max_tareas']:
                    st['tareas'].insert(0, {'id': 'T%d' % (len(st['tareas']) + 1), 'texto': txt[:500],
                                            'estado': 'pendiente', 'intentos': 0, 'modo': obj.get('modo_por_defecto', 'code')})
            elif tipo == 'pausa':
                guardar(st)
                progreso('PAUSADO por el Director (buzon)')
                while True:  # espera sin gastar modelo hasta continuar/cancelar
                    time.sleep(5)
                    for m2 in _leer_buzon():
                        if m2.get('tipo') == 'cancelar':
                            return {'estado': 'CANCELADO', 'tareas': st['tareas'], 'vueltas': st['vuelta']}
                        if m2.get('tipo') == 'continuar':
                            break
                    else:
                        continue
                    break
            elif tipo == 'cancelar':
                guardar(st)
                return {'estado': 'CANCELADO', 'tareas': st['tareas'], 'vueltas': st['vuelta'],
                        'reporte': '%d tareas hechas, %d pendientes' % (
                            sum(1 for t in st['tareas'] if t['estado'] == 'hecho'),
                            sum(1 for t in st['tareas'] if t['estado'] in ('pendiente', 'sigue')))}
            if m.get('id') is not None and buzon is not None:
                try:
                    buzon(pid, aplicar=(m['id'], st['vuelta']))
                except Exception:  # noqa: BLE001
                    pass
        # --- fin buzon ---

        # DSL A05: los limites se evaluan ANTES de cada verificacion (nunca verificar en bucle infinito)
        if (st['vuelta'] >= lim['max_vueltas'] or time.time() - st['t0'] > lim['max_minutos'] * 60
                or st['sin_progreso'] >= lim['max_vueltas_sin_progreso']):
            guardar(st)
            return {'estado': 'LIMITE', 'tareas': st['tareas'], 'vueltas': st['vuelta']}
        pend = [t for t in st['tareas'] if t['estado'] in ('pendiente', 'sigue')]
        if not pend:
            v_r = llamar('auditor', _prompt_verif(obj, st['tareas']))
            v = _json_de(v_r['texto']) or {}
            todas_hecho = all(t.get('estado') == 'hecho' for t in st['tareas'])
            # DSL A05: CUMPLIDO exige veredicto + todas hechas + evidencia real de herramienta; un texto NO basta
            if v.get('cumplido') and todas_hecho and int(v_r.get('herramientas_ok') or 0) > 0:
                return {'estado': 'CUMPLIDO', 'tareas': st['tareas'], 'evidencia': v.get('evidencia'), 'vueltas': st['vuelta']}
            nuevas = [f for f in (v.get('faltantes') or []) if f]
            if not nuevas:
                if len(st['tareas']) >= lim['max_tareas']:  # DSL A05: cola llena + falta -> GAP, no verificacion infinita
                    return {'estado': 'LIMITE', 'gap': 'GAP_MAX_TAREAS', 'tareas': st['tareas'], 'vueltas': st['vuelta']}
                return {'estado': 'CERRADO_SIN_VERIFICAR', 'tareas': st['tareas'], 'vueltas': st['vuelta']}
            for f in nuevas[: max(0, lim['max_tareas'] - len(st['tareas']))]:
                st['tareas'].append({'id': 'T%d' % (len(st['tareas']) + 1), 'texto': f[:500], 'estado': 'pendiente',
                                     'intentos': 0, 'modo': obj.get('modo_por_defecto', 'code')})
            continue
        t = pend[0]
        st['vuelta'] += 1
        progreso('vuelta %d/%d · %s · %s' % (st['vuelta'], lim['max_vueltas'], t['id'], t['texto'][:80]))
        r = llamar(t.get('modo') or 'code',
                   _prompt_vuelta(obj, t, '\n'.join(st['resumen'][-10:]), st.get('instrucciones_director')))
        j = _json_de(r.get('texto') or '') or {}  # >>> PARCHE_ORDENES <<< ORDEN 07-B: un informe narrativo no es 'hecho'
        if not j:
            j = {'tarea': t['id'], 'estado': 'sigue', 'resultado': 'Falta resultado JSON verificable', 'evidencia': '',
                 'nuevas_tareas': [], 'nota_siguiente': 'Revisar evidencia real del DAG'}
        modo_actual = t.get('modo') or 'code'
        ok_ev = (int(r.get('mutaciones_ok') or 0) > 0 if modo_actual == 'code'
                 else int(r.get('herramientas_ok') or 0) > 0 or modo_actual in ('rapido', 'planificador'))
        if j.get('estado') == 'hecho' and ok_ev:
            t['estado'], t['evidencia'] = 'hecho', str(j.get('evidencia') or '')[:500]
            st['sin_progreso'] = 0
        else:
            t['intentos'] += 1
            t['estado'] = 'bloqueada' if (j.get('estado') == 'bloqueado' or t['intentos'] >= lim['max_intentos_por_tarea']) else 'sigue'
            st['sin_progreso'] += 1
        conocidos = {x['texto'] for x in st['tareas']}
        for n in (j.get('nuevas_tareas') or [])[:5]:
            if n and n not in conocidos and len(st['tareas']) < lim['max_tareas']:
                st['tareas'].append({'id': 'T%d' % (len(st['tareas']) + 1), 'texto': str(n)[:500],
                                     'estado': 'pendiente', 'intentos': 0, 'modo': obj.get('modo_por_defecto', 'code')})
        st['resumen'].append('%s %s: %s' % (t['id'], t['estado'], str(j.get('resultado') or '')[:200]))
        guardar(st)
        if pid:
            _ESTADOS[pid] = dict(st)
        time.sleep(lim['pausa_entre_vueltas_s'])

"""Plugin puente_chat (Director 2026-10-04): papel del harness para la UI del chat, dentro del Router (su computo, puerta fija).

Llamada: POST <puerta>/plugins/puente_chat/call/<accion> con el token del chat (Bearer). Respuesta del host: {"status": "ok", "result": ...}.
Acciones: status | modelos | chat {model, messages, max_tokens, sesion, respaldo_url?} | estado {job, url} | apagar {job}.
Modelos NV/GROQ: llamada directa al proveedor con las claves del banco; rota claves del MISMO modelo; tope total 90 s (GLM 96 s).
Modelos HF: enciende un L4 (almacenamiento conectado como disco). Seguridades: (1) se apaga solo 30 s tras terminar la salida; (2) 5 min sin pedidos; (3) tope duro de HF de 20 min; (4) barrendero del Router cancela L4 viejos; (5) un solo L4 a la vez; remoto: apagar / apagar_todo.
Memoria: antes de responder busca contexto en /memoria (scope chat:<sesion>); despues guarda pregunta y respuesta.
"""
from __future__ import annotations

import importlib.util
import json
import re
from contextvars import ContextVar
_DEADLINE = ContextVar("riu_chat_deadline", default=None)
import time
import urllib.error
import urllib.request
from typing import Any

NS = "COMAND-CENTER-1"
DUENO = "chat-ui"
ETIQUETA_L4 = "router-respaldo-l4"
TOPE_TOTAL_S = 90
MAX_PASOS = 6
_CACHE_H = {}
from pathlib import Path
_CONFIG_DIR = Path(__file__).resolve().parent / "fichas"
_catalog = [json.loads(f.read_text()) for f in sorted(_CONFIG_DIR.glob("modelo-*.json"))]
FICHAS = {f["id"]:(f["nombre"],f["proveedor"],f["modelo"],f["timeout_s"]) for f in _catalog if f["tipo"]=="api"}
RESPALDO = {f["id"]:(f["nombre"],f["archivo"]) for f in _catalog if f["tipo"]=="hf"}
ARRANQUE = ('/app/llama-server --host 0.0.0.0 --port 8080 -m "/modelos/$ARCHIVO" --alias "$ALIAS" -ngl 999 -fa on -np 1 -b 128 -c 16384 '
            '--temp 0 --top-k 20 --top-p 0.95 --no-mmproj --reasoning-budget 0 --spec-type draft-mtp --spec-draft-n-max 2 --jinja > /tmp/l.log 2>&1 &\n'
            'P=$!\nwhile kill -0 $P 2>/dev/null; do\n  sleep 5\n  I=$(( $(date +%s) - $(stat -c %Y /tmp/l.log) ))\n'
            '  if grep -q print_timing /tmp/l.log && [ $I -ge 30 ]; then echo APAGADO_FIN_DE_SALIDA; kill $P; exit 0; fi\n'
            '  if [ $I -ge 300 ]; then echo APAGADO_5_MIN_SIN_USO; kill $P; exit 0; fi\ndone\n')


def _http(metodo: str, url: str, token: str, cuerpo: Any = None, espera: float = 60) -> tuple[int, Any]:
    deadline = _DEADLINE.get()
    if deadline is not None:
        espera = min(espera, deadline - time.monotonic())
        if espera <= 0: return 0, {'error': 'TIEMPO_TOTAL_AGOTADO'}
    req = urllib.request.Request(url, data=json.dumps(cuerpo).encode() if cuerpo is not None else None, method=metodo,
                                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json", "User-Agent": "riu-chat-mvp", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=espera) as r:
            texto = r.read().decode()
            return r.status, (json.loads(texto) if texto else {})
    except urllib.error.HTTPError as e:
        texto = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(texto)
        except ValueError:
            return e.code, {"error": texto[:200]}
    except (TimeoutError, urllib.error.URLError):
        return 0, {'error': 'PROVEEDOR_TIMEOUT_O_RED'}


def _tokens_hf() -> list[str]:
    from integration.chat_mvp import providers, vault_hook
    vistos: list[str] = []
    for t in [*vault_hook.provider_keys("huggingface"), *providers.env_keys("hf")]:
        if t and t not in vistos:
            vistos.append(t)
    return vistos


def _hf(metodo: str, ruta: str, cuerpo: Any = None) -> tuple[int, Any]:
    ultimo: tuple[int, Any] = (0, {"error": "SIN_TOKEN_HF_EN_EL_BANCO"})
    for t in _tokens_hf():
        ultimo = _http(metodo, "https://huggingface.co" + ruta, t, cuerpo)
        if ultimo[0] < 400:
            return ultimo
    return ultimo


def _memoria():
    from integration.chat_mvp.memory_runtime import memory, scope_for
    from integration.chat_mvp.router import get_store
    return memory(get_store()), scope_for


def _contexto(sesion: str, pregunta: str) -> str:
    try:
        mem, scope_for = _memoria()
        res = mem.search(scope_for(DUENO, "chat:" + sesion), "", 6)  # ultimos turnos de esta conversacion
        filas = res if isinstance(res, list) else next((v for v in (res or {}).values() if isinstance(v, list)), [])
        trozos = []
        for f in reversed(filas):
            d = f.get("data", f) if isinstance(f, dict) else f
            if isinstance(d, dict) and "pregunta" in d:
                trozos.append("Usuario: " + str(d["pregunta"])[:500] + "\nAsistente: " + str(d.get("respuesta", ""))[:500])
        return "\n".join(trozos)
    except Exception:  # noqa: BLE001 - la memoria nunca bloquea el chat
        return ""


def _guardar(sesion: str, modelo: str, pregunta: str, respuesta: str) -> bool:
    try:
        mem, scope_for = _memoria()
        mem.save(scope_for(DUENO, "chat:" + sesion), "turno-%d" % int(time.time() * 1000),
                 {"modelo": modelo, "pregunta": pregunta[:4000], "respuesta": respuesta[:8000]})
        return True
    except Exception:  # noqa: BLE001
        return False


def _api(proveedor: str, modelo: str, mensajes: list, max_tokens: int, tope: int) -> dict[str, Any]:
    from integration.chat_mvp import providers
    claves = providers.env_keys(proveedor)
    if not claves:
        return {"error": "SIN_CLAVES_" + proveedor.upper()}
    fin = time.monotonic() + tope
    providers.ATTEMPT_DEADLINE.set(fin)
    ultimo = ""
    for clave in claves:  # mismo modelo, otra clave; nunca otro modelo
        if time.monotonic() >= fin:
            break
        try:
            return providers.chat(proveedor, clave, modelo, mensajes, max_tokens)
        except Exception as exc:  # noqa: BLE001
            ultimo = str(exc)[:200]
    return {"error": "SIN_RESPUESTA_EN_%dS" % tope if time.monotonic() >= fin else "TODAS_LAS_CLAVES_FALLARON", "detalle": ultimo}


MAX_VIDA_L4_S = 1200  # seguridad 3: tope duro de HF (20 min), se aplica FUERA del contenedor
FINALIZADOS = ("COMPLETED", "CANCELED", "ERROR", "DELETED")


def _edad_s(creado: str) -> float:
    from datetime import datetime, timezone
    try:
        t = datetime.fromisoformat(str(creado).replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - t).total_seconds()
    except ValueError:
        return 0.0


def _l4_vivos() -> list[dict[str, Any]]:
    s, lista = _hf("GET", "/api/jobs/" + NS)
    if s >= 400 or not isinstance(lista, list):
        return []
    return [j for j in lista if (j.get("labels") or {}).get("name") == ETIQUETA_L4
            and (j.get("status") or {}).get("stage") not in FINALIZADOS]


def _cancelar(job_id: str) -> bool:
    s, _ = _hf("POST", "/api/jobs/%s/%s/cancel" % (NS, job_id))
    return s < 400


def _apagar_todo() -> dict[str, Any]:
    """Apagado remoto de emergencia: cancela TODOS los L4 de respaldo."""
    return {"apagados": sum(1 for j in _l4_vivos() if _cancelar(j["id"]))}


def _barrer() -> int:
    """Seguridad 4 (barrendero del Router): cualquier L4 mas viejo que su vida maxima se cancela."""
    return sum(1 for j in _l4_vivos() if _edad_s(j.get("createdAt", "")) > MAX_VIDA_L4_S and _cancelar(j["id"]))


def _encender(model: str) -> dict[str, Any]:
    _apagar_todo()  # seguridad 5: un solo L4 a la vez
    _, archivo = RESPALDO[model]
    s, j = _hf("POST", "/api/jobs/" + NS, {
        "dockerImage": "ghcr.io/ggml-org/llama.cpp:server-cuda", "command": ["bash", "-c", ARRANQUE], "arguments": [],
        "environment": {"ARCHIVO": archivo, "ALIAS": model}, "flavor": "l4x1", "timeoutSeconds": MAX_VIDA_L4_S, "labels": {"name": ETIQUETA_L4},
        "volumes": [{"type": "bucket", "source": NS + "/yaiwes-memoria-storage", "mountPath": "/modelos", "readOnly": True,
                     "path": "router-respaldo/modelos"}],
        "expose": {"ports": [8080], "portsPublic": []}})
    if s >= 400:
        return {"error": "NO_SE_PUDO_ENCENDER", "detalle": str(j)[:300]}
    return {"estado": "encendiendo", "job_id": j["id"], "url": "https://" + j["id"] + "--8080.hf.jobs", "model": model}


def _herr():
    if 'h' not in _CACHE_H:
        import importlib.util
        import os
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'herramientas.py')
        spec = importlib.util.spec_from_file_location('puente_herramientas', ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _CACHE_H['h'] = mod
    return _CACHE_H['h']


_BUENA = {}


def _sentinela():
    # mini-agente determinista dentro de las fichas: envuelve a la LLM en un bucle
    p = _CONFIG_DIR / 'sentinela.py'
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location('riu_sentinela', str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod  # proveedor -> indice de la ultima clave que respondio bien


def _recortar(mensajes, limite=20000):
    # Mantiene el envio por debajo del tope de la API: acorta salidas de
    # herramientas y luego suelta los turnos mas viejos (sin romper pares
    # assistant(tool_calls) -> tool).
    ms = [dict(m) for m in mensajes]
    for m in ms:
        if m.get('role') == 'tool' and len(m.get('content') or '') > 1200:
            m['content'] = m['content'][:1200] + ' ...[recortado]'
    def tam():
        return sum(len(str(m.get('content') or '')) + len(json.dumps(m.get('tool_calls') or '')) for m in ms)
    while len(ms) > 3 and tam() > limite:
        for i, m in enumerate(ms):
            if m.get('role') == 'system':
                continue
            ms.pop(i)
            if m.get('tool_calls'):
                while i < len(ms) and ms[i].get('role') == 'tool':
                    ms.pop(i)
            break
        else:
            break
    return ms


def _llamar_api(proveedor, modelo, mensajes, max_tokens, tope, tools):
    from integration.chat_mvp import providers
    claves = providers.env_keys(proveedor)
    base = providers.base_url(proveedor)
    if not claves or not base:
        return 0, {'error': 'SIN_CLAVES_' + proveedor.upper()}
    fin = time.monotonic() + tope
    ultimo = (0, {'error': 'SIN_RESPUESTA'})
    buena = _BUENA.get(proveedor)  # la ultima clave que respondio va primero
    orden = ([buena] if isinstance(buena, int) and 0 <= buena < len(claves) else []) + [i for i in range(len(claves)) if i != buena]
    muertas = set()
    for _vuelta in range(2):  # dos vueltas: si el servicio dice ocupado, otra pasada completa
        for i in orden:
            if i in muertas:
                continue
            clave = claves[i]
            resta = fin - time.monotonic()
            if resta < 2:
                return ultimo
            if proveedor == 'groq':
                resta = min(resta, 45)  # una clave lenta no se come el tiempo de las demas
            cuerpo = {'model': modelo, 'messages': _recortar(mensajes), 'max_tokens': max_tokens}
            if modelo == 'z-ai/glm-5.3':
                cuerpo['reasoning_effort'] = 'low'
                cuerpo['chat_template_kwargs'] = {'clear_thinking': True}
            if modelo in ('moonshotai/kimi-k3', 'nvidia/nemotron-3-super-120b-a12b'):
                cuerpo['chat_template_kwargs'] = {'clear_thinking': True}
            if tools:
                cuerpo['tools'] = tools
                cuerpo['tool_choice'] = 'auto'
            ultimo = _http('POST', base + '/chat/completions', clave, cuerpo, resta)
            if ultimo[0] < 400 and isinstance(ultimo[1], dict) and ultimo[1].get('choices'):
                c = str((ultimo[1]['choices'][0].get('message') or {}).get('content') or '')
                if not any(x in c.lower() for x in ('server is busy', 'try again later', 'service unavailable')):
                    _BUENA[proveedor] = i
                    return ultimo
                ultimo = (503, {'error': 'SERVICIO_OCUPADO'})
                time.sleep(2)  # el servicio dice ocupado: siguiente clave
                continue
            if ultimo[0] in (401, 403, 429):
                muertas.add(i)  # clave sin acceso o sin cuota: no insistir en la segunda vuelta
                continue
            if ultimo[0] == 400:
                detalle = json.dumps(ultimo[1])
                if 'too large' not in detalle and 'tier' not in detalle:
                    return ultimo  # 400 de formato: no lo arregla otra clave; los de cuota/tier si
        time.sleep(3)
    return ultimo


def _llamar_l4(url, modelo, mensajes, max_tokens, tools):
    ultimo = (0, {'error': 'SIN_TOKEN_HF_EN_EL_BANCO'})
    for t in _tokens_hf():
        cuerpo = {'model': modelo, 'messages': mensajes, 'max_tokens': max_tokens}
        if tools:
            cuerpo['tools'] = tools
            cuerpo['tool_choice'] = 'auto'
        ultimo = _http('POST', url + '/v1/chat/completions', t, cuerpo, 110)
        if ultimo[0] < 400 or ultimo[0] == 400:
            return ultimo
    return ultimo


def _calls_texto(content):
    # Algunos modelos escriben la llamada como <tool_call>... en el texto en vez de tool_calls: la ejecutamos igual.
    calls = []
    for bloque in re.findall(r'<tool_call>(.*?)</tool_call>', content or '', re.S):
        b = bloque.strip()
        m = re.match(r'<function=(\w+)>(.*?)</function>', b, re.S)
        if m:
            args = {k: v.strip() for k, v in re.findall(r'<parameter=(\w+)>(.*?)</parameter>', m.group(2), re.S)}
            calls.append((m.group(1), args))
            continue
        try:
            d = json.loads(b)
            calls.append((d.get('name', ''), d.get('arguments') or {}))
        except Exception:  # noqa: BLE001
            pass
    return calls


def _limpiar_texto(c):
    # quita bloques <tool_call> cerrados y tambien el resto si quedo truncado sin cierre
    c = re.sub(r'<tool_call>.*?</tool_call>', '', c or '', flags=re.S)
    c = re.sub(r'<tool_call>.*', '', c, flags=re.S)
    return c.strip()


def _bucle(llamar, mensajes):
    h = _herr()
    usadas = []
    vistos = {}   # dedup: misma herramienta + mismos args = mismo resultado
    rotas = set()  # herramientas que ya fallaron por token/desconocidas
    fin = _DEADLINE.get() or (time.monotonic() + TOPE_TOTAL_S)
    con_tools = True
    pasos = 0
    final_hecho = False
    while True:
        if time.monotonic() >= fin:
            if final_hecho:
                return {'error':'TIEMPO_TOTAL_AGOTADO'}, usadas
            final_hecho = True  # una ultima llamada sin herramientas para contestar con lo que haya
            con_tools = False
            fin = time.monotonic() + 45
            mensajes.append({'role': 'user', 'content': 'Se acabo el tiempo. Responde ya, sin usar mas herramientas, con lo que tengas.'})
            continue
        s, d = llamar(mensajes, h.TOOLS if con_tools else None)
        if s == 400 and con_tools and not usadas:
            con_tools = False  # este modelo no admite herramientas: responde sin ellas
            continue
        if s >= 400 or s == 0 or not isinstance(d, dict) or not d.get('choices'):
            return {'error': 'MODELO_NO_RESPONDE', 'detalle': str(d)[:300]}, usadas
        msg = d['choices'][0].get('message') or {}
        calls = msg.get('tool_calls') or []
        if not calls and con_tools:
            calls = [{'id': 'texto%d' % i, 'type': 'function', 'function': {'name': n, 'arguments': json.dumps(a)}}
                     for i, (n, a) in enumerate(_calls_texto(msg.get('content')))]
            if calls:
                msg['content'] = _limpiar_texto(msg.get('content'))
        if not calls or not con_tools:
            if (not (msg.get('content') or '').strip()) and msg.get('reasoning_content') and not final_hecho and time.monotonic() < fin:
                mensajes.append({'role': 'assistant', 'content': ''})
                mensajes.append({'role': 'user', 'content': 'Deja de razonar y da ya la respuesta final, o usa una herramienta si la necesitas.'})
                pasos += 1
                continue
            return d, usadas
        mensajes.append({'role': 'assistant', 'content': msg.get('content') or '', 'tool_calls': calls})
        for c in calls:
            f = c.get('function') or {}
            try:
                args = json.loads(f.get('arguments') or '{}')
            except ValueError:
                args = {}
            nom = f.get('name', '')
            sello = (nom, json.dumps(args, sort_keys=True, default=str))
            if sello in vistos:
                res = vistos[sello]  # misma llamada repetida: no gasta otra peticion
            elif nom in rotas:
                res = 'ERROR: herramienta no disponible en este momento, no la uses mas y responde con lo que tengas'
            else:
                res = h.ejecutar(nom, args)
                vistos[sello] = res
                if 'no hay token' in res or 'herramienta desconocida' in res:
                    rotas.add(nom)
            usadas.append({'herramienta': nom, 'ok': not res.startswith(('ERROR', 'HTTP 4', 'HTTP 5', 'HTTP 0'))})
            mensajes.append({'role': 'tool', 'tool_call_id': c.get('id', ''), 'content': res[:3000]})
        pasos += 1
        if pasos >= MAX_PASOS or time.monotonic() >= fin:
            con_tools = False  # tiempo o pasos agotados: pedir la respuesta final sin herramientas


_CHECKPOINTS = {}


def _ck_guardar(sesion, mensajes):
    _CHECKPOINTS[sesion] = mensajes
    try:  # lo mismo en la memoria persistente: sobrevive al cambio de job
        mem, scope_for = _memoria()
        mem.save(scope_for(DUENO, 'chat:' + sesion), 'checkpoint', {'mensajes': mensajes[-40:]})
    except Exception:  # noqa: BLE001
        pass


def _ck_cargar(sesion):
    if sesion in _CHECKPOINTS:
        return _CHECKPOINTS.pop(sesion)
    try:
        mem, scope_for = _memoria()
        res = mem.search(scope_for(DUENO, 'chat:' + sesion), 'checkpoint', 5)
        filas = res if isinstance(res, list) else next((v for v in (res or {}).values() if isinstance(v, list)), [])
        hallado = None
        for f in filas:
            d = f.get('data', f) if isinstance(f, dict) else f
            if isinstance(d, dict) and isinstance(d.get('mensajes'), list):
                hallado = d['mensajes']
        return hallado
    except Exception:  # noqa: BLE001
        return None


def _chat(p):
    model = str(p.get('model') or '')
    mensajes = list(p.get('messages') or [])
    max_tokens = int(p.get('max_tokens') or 2048)
    sesion = str(p.get('sesion') or 'general')[:60]
    pregunta = next((str(m.get('content', '')) for m in reversed(mensajes) if m.get('role') == 'user'), '')
    if model not in FICHAS and model not in RESPALDO:
        return {'error': 'MODELO_DESCONOCIDO', 'validos': [*FICHAS, *RESPALDO]}
    if model in RESPALDO and not p.get('respaldo_url'):
        return _encender(model)
    presupuesto = 96 if model == 'nv-glm-5-3' else TOPE_TOTAL_S
    _DEADLINE.set(time.monotonic() + presupuesto)
    ctx = _contexto(sesion, pregunta) if pregunta else ''
    sistema = _herr().SISTEMA + ' Modelo seleccionado: ' + (FICHAS[model][2] if model in FICHAS else RESPALDO[model][0])
    if ctx:
        sistema += ' Contexto guardado de esta conversacion: ' + ctx
    if re.search(r'(?i)(contin[uú]a?s?|sigue|retoma|seguid|seguir)', pregunta):
        guardado = _ck_cargar(sesion)
        if guardado:
            mensajes = guardado
            mensajes.append({'role': 'user', 'content': pregunta + ' (retoma el trabajo donde quedo, sin empezar de cero)'})
    mensajes = [{'role': 'system', 'content': sistema}, *mensajes]
    if model in FICHAS:
        _, proveedor, modelo, tope = FICHAS[model]

        def llamar(ms, tl):
            return _llamar_api(proveedor, modelo, ms, max_tokens, tope, tl)
        presupuesto = min(250, max(TOPE_TOTAL_S, int(tope * 2.4)))
        _DEADLINE.set(time.monotonic() + presupuesto)
    else:
        url = str(p['respaldo_url'])
        if not url.startswith('https://') or not url.endswith('--8080.hf.jobs'):
            return {'error': 'RESPALDO_URL_INVALIDA'}

        def llamar(ms, tl):
            return _llamar_l4(url, model, ms, max_tokens, tl)
    # el sentinela de las fichas envuelve a la LLM: bucle hasta terminar la tarea
    ultimo = {'model': model}

    def paso_modelo(ms):
        _DEADLINE.set(time.monotonic() + presupuesto)
        return _bucle(llamar, ms)

    def paso_retoma(ms):
        ms.append({'role': 'user', 'content': 'Se corto la llamada. Continua el trabajo donde quedo y termina.'})
        _DEADLINE.set(time.monotonic() + presupuesto)
        return _bucle(llamar, ms)

    plan = [('modelo:' + model, paso_modelo), ('retoma', paso_retoma)]
    if model in FICHAS:
        # reserva entre proveedores: la tarea pasa a otro modelo con lo ya hecho
        prov0 = FICHAS[model][1]
        alternos = [m for m in FICHAS if m != model and FICHAS[m][1] != prov0] + [m for m in FICHAS if m != model and FICHAS[m][1] == prov0]
        for alt in alternos[:2]:
            _, prov_a, modelo_a, tope_a = FICHAS[alt]

            def paso_alt(ms, _a=alt, _p=prov_a, _m=modelo_a, _t=tope_a):
                hechas = ', '.join(sorted({tc.get('function', {}).get('name', '') for m2 in ms if m2.get('role') == 'assistant' for tc in (m2.get('tool_calls') or [])})) or 'ninguna'
                ms.append({'role': 'user', 'content': 'El modelo anterior dejo de responder. Continua TU el trabajo donde quedo (ya se usaron estas herramientas: %s) y da la respuesta final.' % hechas})
                _DEADLINE.set(time.monotonic() + min(200, max(TOPE_TOTAL_S, int(_t * 2.4))))
                ultimo['model'] = _a
                return _bucle(lambda m2, tl: _llamar_api(_p, _m, m2, max_tokens, _t, tl), ms)

            plan.append(('reserva:' + alt, paso_alt))

    sen = _sentinela()
    if sen:
        def _ck_in():
            ck = _ck_cargar(sesion)
            return ([{'role': 'system', 'content': sistema}] + list(ck)) if ck else None
        cl = sen.ejecutar(plan, mensajes,
                          guardar_ck=lambda ms: _ck_guardar(sesion, _recortar(ms[1:])),
                          cargar_ck=_ck_in)
        d, usadas = cl['resultado']
        checklist = cl['items']
        model = ultimo['model']
    else:
        d, usadas = _bucle(llamar, mensajes)
        checklist = []
    if 'error' in d:
        if len(mensajes) > 3:  # habia trabajo a medias: guardarlo para 'continua'
            _ck_guardar(sesion, _recortar(mensajes[1:]))
        return d
    texto = _limpiar_texto(d['choices'][0].get('message', {}).get('content'))
    if not texto.strip() and (d['choices'][0].get('message') or {}).get('reasoning_content'):
        texto = str(d['choices'][0]['message']['reasoning_content'])[-1500:]
    if not texto.strip() and usadas:
        s2, d2 = llamar(mensajes + [{'role': 'user', 'content': 'Dime en espanol el resultado de lo que hiciste.'}], None)
        if s2 < 400 and isinstance(d2, dict) and d2.get('choices'):
            d = d2
            texto = d['choices'][0].get('message', {}).get('content') or ''
    if not texto.strip() and usadas:
        ultimo_tool = next((m.get('content') for m in reversed(mensajes) if m.get('role') == 'tool' and m.get('content')), '')
        texto = 'La herramienta devolvio esto:\n\n' + ultimo_tool[:2000]
    if texto.strip() and not (d['choices'][0].get('message', {}).get('content') or '').strip():
        d['choices'][0]['message']['content'] = texto
    salida = {'model': model, 'choices': d['choices'], 'usage': d.get('usage'), 'herramientas': usadas}
    if checklist:
        salida['checklist'] = checklist  # salida del sentinela: lista de verificacion
    salida['memoria_guardada'] = _guardar(sesion, model, pregunta, texto)
    return salida


def _estado(p: dict[str, Any]) -> dict[str, Any]:
    try:
        _barrer()
    except Exception:  # noqa: BLE001
        pass
    s, j = _hf("GET", "/api/jobs/%s/%s" % (NS, p.get("job")))
    etapa = (j.get("status") or {}).get("stage", "DESCONOCIDA") if isinstance(j, dict) else "DESCONOCIDA"
    listo = False
    url = str(p.get("url") or "")
    if etapa == "RUNNING" and url.endswith("--8080.hf.jobs"):
        for t in _tokens_hf():
            code, _ = _http("GET", url + "/health", t, None, 10)
            if code == 200:
                listo = True
                break
    return {"etapa": etapa, "listo": listo}


def _apagar(p: dict[str, Any]) -> dict[str, Any]:
    job = str(p.get("job") or "")
    s, j = _hf("GET", "/api/jobs/%s/%s" % (NS, job))
    etiqueta = ((j.get("labels") or {}).get("name") if isinstance(j, dict) else None)
    if etiqueta != ETIQUETA_L4:
        return {"error": "SOLO_SE_APAGAN_JOBS_DEL_L4_DE_RESPALDO", "job_id": job}
    s, _ = _hf("POST", "/api/jobs/%s/%s/cancel" % (NS, job))
    return {"job_id": job, "apagado": s < 400}


def handle(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action == "status":
        try:
            vivos = len(_l4_vivos())
        except Exception:  # noqa: BLE001
            vivos = -1
        return {"ok": True, "modelos": len(FICHAS) + len(RESPALDO), "l4_vivos": vivos}
    if action == "modelos":
        return {"modelos": [{"id": k, "nombre": v[0], "respaldo": False} for k, v in FICHAS.items()]
                + [{"id": k, "nombre": v[0], "respaldo": True} for k, v in RESPALDO.items()]}
    if action == "chat":
        return _chat(payload)
    if action == "estado":
        return _estado(payload)
    if action == "apagar":
        return _apagar(payload)
    if action == 'herramientas_estado':
        h = _herr()
        return {'github': bool(h._token_gh()), 'hf': bool(h._token_hf())}
    if action == "apagar_todo":
        return _apagar_todo()
    return {"error": "ACCION_DESCONOCIDA"}

# Long model calls are polled through HTTP, so browser requests do not expire at the HF ingress.
import concurrent.futures as _cf
import threading as _threading
import secrets as _secrets
_ASYNC_POOL = _cf.ThreadPoolExecutor(max_workers=16, thread_name_prefix='riu-chat')
_ASYNC_LOCK = _threading.Lock()
_ASYNC_REQUESTS = {}
_original_handle = handle
def handle(action, payload):
    if action == 'chat_async':
        with _ASYNC_LOCK:
            now=time.time()
            for key, (future, created) in list(_ASYNC_REQUESTS.items()):
                if now-created>900 and future.done(): del _ASYNC_REQUESTS[key]
            if sum(not f.done() for f,_ in _ASYNC_REQUESTS.values())>=16:
                return {'error':'CHAT_OCUPADO_REINTENTA'}
            key=_secrets.token_urlsafe(24)
            future=_ASYNC_POOL.submit(_chat,dict(payload))
            _ASYNC_REQUESTS[key]=(future,now)
        return {'estado':'procesando','proceso_id':key}
    if action == 'resultado':
        key=str(payload.get('proceso_id') or '')
        with _ASYNC_LOCK: item=_ASYNC_REQUESTS.get(key)
        if not item: return {'error':'PROCESO_NO_EXISTE'}
        future,_=item
        if not future.done():return {'estado':'procesando','proceso_id':key}
        try:return future.result()
        except Exception as exc:return {'error':'CHAT_FAILED','detalle':type(exc).__name__}
    return _original_handle(action,payload)

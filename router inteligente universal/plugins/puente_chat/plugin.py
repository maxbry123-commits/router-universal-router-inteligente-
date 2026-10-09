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
import urllib.parse
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
FICHAS = {f["id"]:(f["nombre"],f.get("proveedor","pipeline"),f.get("modelo","pipeline"),f["timeout_s"]) for f in _catalog if f["tipo"] in ("api","consil","motor","xray","auditor")}
ESPECIALES = {f["id"]: f["tipo"] for f in _catalog if f["tipo"] in ("consil","motor","xray","auditor")}
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
                 {"modelo": modelo, "pregunta": pregunta[:1_000_000], "respuesta": respuesta[:1_000_000]})
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


def _recortar(mensajes, limite=1_000_000):
    # Mantiene el envio por debajo del tope de la API: acorta salidas de
    # herramientas y luego suelta los turnos mas viejos (sin romper pares
    # assistant(tool_calls) -> tool).
    ms = [dict(m) for m in mensajes]
    for m in ms:
        if m.get('role') == 'tool' and len(m.get('content') or '') > 1_000_000:
            m['content'] = m['content'][:1_000_000] + ' ...[recortado]'
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
            if modelo in ('moonshotai/kimi-k3', 'nvidia/nemotron-3-super-120b-a12b', 'meta/muse-glimmer-30b', 'nvidia/nemotron-3-ultra-550b-a55b'):
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
            mensajes.append({'role': 'tool', 'tool_call_id': c.get('id', ''), 'content': res[:1_000_000]})
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


import os as _os
import subprocess as _sub
import base64 as _b64

_SYS_PIPE = 'Eres un paso de una cadena determinista (consil). Responde solo lo pedido, en espanol y conciso.'


def _paso_llm(prov, modelo, msgs, tope=120, mt=1200):
    # una llamada de la cadena: misma rotacion de claves y deteccion de ocupado que el chat
    _DEADLINE.set(time.monotonic() + tope + 30)
    s, d = _llamar_api(prov, modelo, msgs, mt, tope, None)
    if s < 400 and isinstance(d, dict) and d.get('choices'):
        m = d['choices'][0].get('message') or {}
        return _limpiar_texto(m.get('content')) or str(m.get('reasoning_content') or '')[-1500:]
    return ''


def _motores_buscar(query):
    # paso 0 del consil: motores de busqueda canonicos del repo (web + github + hf)
    base = str(_CONFIG_DIR / 'motores_busqueda')
    h = _herr()
    runs = [('motor_1_web_domains.py', {'SOURCES_FILE': base + '/sources.json', 'MAX_RESULTS_PER_SOURCE': '2'}),
            ('motor_2_github_search.py', {'GITHUB_TOKEN': h._token_gh() or ''}),
            ('motor_3_huggingface_search.py', {'HF_TOKEN': h._token_hf() or ''})]
    salida = []
    for nom, extra in runs:
        try:
            e = dict(_os.environ, QUERY=query, **extra)
            r = _sub.run(['python3', base + '/' + nom], env=e, capture_output=True, text=True, timeout=45)
            salida.append(nom + ':\n' + (r.stdout or r.stderr or '')[:2200])
        except Exception as x:  # noqa: BLE001
            salida.append(nom + ': ERROR ' + str(x)[:120])
    return '\n'.join(salida)


def _consil(pregunta):
    usadas = ['paso0:motores_busqueda']
    ctx = _motores_buscar(pregunta)
    g12 = _paso_llm('nvidia', 'nvidia/nemotron-3-ultra-550b-a55b',
        [{'role': 'system', 'content': _SYS_PIPE},
         {'role': 'user', 'content': 'Propone exactamente 12 goals de entrada para esta tarea.\nTarea: %s\nInvestigacion:\n%s' % (pregunta, ctx[:6000])}], 150)
    usadas.append('paso1:ultra-550b-12-goals')
    rondas = []
    for ronda in range(1, 4):
        prop = _paso_llm('groq', 'qwen/qwen3.8-27b',
            [{'role': 'system', 'content': _SYS_PIPE},
             {'role': 'user', 'content': 'Ronda %d/3. Propone soluciones concretas para los goals %d-%d.\nGoals:\n%s\nTarea: %s' % (ronda, ronda * 4 - 3, ronda * 4, g12[:4000], pregunta)}], 120)
        ref = _paso_llm('nvidia', 'meta/muse-glimmer-30b',
            [{'role': 'system', 'content': _SYS_PIPE},
             {'role': 'user', 'content': 'Refuta estas propuestas y propone mejores soluciones.\nPropuestas:\n%s' % prop[:4000]}], 120)
        dec = _paso_llm('nvidia', 'moonshotai/kimi-k3',
            [{'role': 'system', 'content': _SYS_PIPE},
             {'role': 'user', 'content': 'Decide la mejor solucion final de esta ronda entre propuestas y refutaciones.\nPropuestas:\n%s\nRefutaciones:\n%s' % (prop[:3000], ref[:3000])}], 150)
        rondas.append(dec or prop or ref)
        usadas.append('paso2:consil-ronda%d' % ronda)
    plan = '\n'.join(rondas)
    out = _paso_llm('nvidia', 'nvidia/nemotron-3-super-120b-a12b',
        [{'role': 'system', 'content': _SYS_PIPE},
         {'role': 'user', 'content': 'Ejecuta la tarea siguiendo el plan decidido.\nTarea: %s\nPlan:\n%s' % (pregunta, plan[:6000])}], 150, 1600)
    usadas.append('paso3:nemotron-super-ejecuta')
    fin = _paso_llm('nvidia', 'moonshotai/kimi-k3',
        [{'role': 'system', 'content': _SYS_PIPE},
         {'role': 'user', 'content': 'Revisa, refactoriza y mejora este resultado con 12 goals de salida (calidad, claridad, completitud). Entrega la respuesta final mejorada.\nResultado:\n%s' % out[:6000]}], 150, 1600)
    usadas.append('paso4:kimi-12-goals-salida')
    return (fin or out or plan or g12 or 'CONSIL_SIN_RESPUESTA'), usadas


_MOTORES_DESC = {
    'descargar_extraer': ('motor_2_queue_download_extract.py', 'descarga componentes y extrae zip en cola'),
    'extraer_zip': ('motor_1_extract_only.py', 'extrae un zip local'),
    'copiar': ('motor_3_copy_batches.py', 'copia archivos en lotes verificados SOURCE_DIR->DEST_DIR'),
    'mover': ('motor_4_move_batches.py', 'mueve archivos en lotes SOURCE_DIR->DEST_DIR'),
    'descarga_hf': ('hf_download_extract_engine.py', 'descarga desde Hugging Face y extrae'),
}


def _embed_rank(query, items):
    # nemotron-3-embed-1b ancla la tarea al motor que mejor encaja
    from integration.chat_mvp import providers
    claves = providers.env_keys('nvidia')
    if not claves:
        return 0
    import math
    cuerpo = {'model': 'nvidia/nemotron-3-embed-1b', 'input': [query] + items, 'truncate': 'NONE'}
    s, d = _http('POST', providers.base_url('nvidia') + '/embeddings', claves[0], cuerpo, 30)
    try:
        vecs = [x['embedding'] for x in d['data']]
        q = vecs[0]
        nq = math.sqrt(sum(a * a for a in q)) or 1
        best, bi = -2, 0
        for i, v in enumerate(vecs[1:]):
            sc = sum(a * b for a, b in zip(q, v)) / (nq * (math.sqrt(sum(b * b for b in v)) or 1))
            if sc > best:
                best, bi = sc, i
        return bi
    except Exception:  # noqa: BLE001
        return 0


def _motor_descarga(pregunta):
    usadas = ['embed:nemotron-3-embed-1b']
    nombres = list(_MOTORES_DESC)
    elegido = nombres[_embed_rank(pregunta, [n + ' ' + d for n, (f, d) in _MOTORES_DESC.items()])]
    fichero, desc = _MOTORES_DESC[elegido]
    plan_txt = _paso_llm('nvidia', 'meta/muse-glimmer-30b',
        [{'role': 'system', 'content': _SYS_PIPE},
         {'role': 'user', 'content': 'Eres el director del motor de fichas "%s" (%s). Solo puedes usar los motores de descarga/extraccion/copiar/mover del repo. Tarea: %s. Devuelve SOLO JSON {"env": {variables del motor}, "explicacion": "..."}' % (fichero, desc, pregunta)}], 120)
    usadas.append('muse-glimmer:plan')
    env_extra, expl = {}, plan_txt
    try:
        dd = json.loads(plan_txt[plan_txt.index('{'):plan_txt.rindex('}') + 1])
        env_extra = {k: str(v) for k, v in (dd.get('env') or {}).items()}
        expl = dd.get('explicacion') or plan_txt
    except Exception:  # noqa: BLE001
        pass
    base = str(_CONFIG_DIR / 'motores_descarga')
    try:
        e = dict(_os.environ, **env_extra)
        r = _sub.run(['python3', base + '/' + fichero], env=e, capture_output=True, text=True, timeout=90)
        salida_motor = (r.stdout or '') + (r.stderr or '')
        usadas.append('motor:' + fichero)
    except Exception as x:  # noqa: BLE001
        salida_motor = 'MOTOR_ERROR ' + str(x)[:200]
    fin = _paso_llm('nvidia', 'meta/muse-glimmer-30b',
        [{'role': 'system', 'content': _SYS_PIPE},
         {'role': 'user', 'content': 'Resume el resultado del motor para el usuario en 3 lineas.\nPlan: %s\nSalida del motor:\n%s' % (expl, salida_motor[:3000])}], 120)
    return (fin or expl or salida_motor[:1500] or 'MOTOR_SIN_RESPUESTA'), usadas


_REPO_DIR = 'router-universal-router-inteligente-'
_URL_RE = re.compile(r'https?://\S+')
_CODE_EXT = {'.py', '.js', '.mjs', '.ts', '.tsx', '.jsx', '.html', '.css', '.json',
             '.yaml', '.yml', '.sh', '.md', '.go', '.rs', '.java', '.c', '.cpp',
             '.h', '.sql', '.toml', '.ini', '.cfg', '.vue', '.php', '.rb', '.ipynb'}


def _mem_dato(sesion, clave):
    # un registro de la memoria del harness (scope chat:<sesion>); nunca lanza
    try:
        mem, scope_for = _memoria()
        res = mem.search(scope_for(DUENO, 'chat:' + sesion), clave, 1)
        filas = res if isinstance(res, list) else next((v for v in (res or {}).values() if isinstance(v, list)), [])
        dd = (filas[0].get('data') if filas and isinstance(filas[0], dict) else None) or {}
        return dd if isinstance(dd, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _archivo_memoria(sesion, nombre):
    try:
        dd = _mem_dato(sesion, 'archivo:' + str(nombre)[:120])
        if dd.get('datos_b64'):
            return _b64.b64decode(dd['datos_b64']).decode('utf-8', 'replace')
    except Exception:  # noqa: BLE001
        pass
    return ''


def _xray(sesion, nombre, texto=''):
    # motor de auditoria forense x-ray: resumen compacto + urls + estructura raiz +
    # mapa mental + microflujo horizontal + goals de la IA en ids G1..G12
    nombre = str(nombre or '')[:120]
    if not texto and nombre:
        texto = _archivo_memoria(sesion, nombre)
    if not texto:
        return {'error': 'XRAY_SIN_ARCHIVO', 'detalle': 'ancla o sube un archivo primero'}
    base_t = texto[:20000]
    urls = sorted({u.rstrip('.,;:)]}"\'') for u in _URL_RE.findall(base_t)})[:30]
    lineas = base_t.count('\n') + 1
    ext = nombre.rsplit('.', 1)[-1].lower() if '.' in nombre else 'texto'
    cabeza, funcs = [], []
    for ln in base_t.splitlines():
        s = ln.strip()
        if s.startswith('#'):
            cabeza.append(s.lstrip('#').strip()[:64])
        elif re.match(r'(def |class |function |export |const |async )', s):
            funcs.append(s[:64])
    guia = (cabeza or funcs)[:10]
    mapa = '\n'.join('  - ' + g for g in guia) or '  - (sin estructura detectada)'
    microflujo = ' -> '.join('P%d:%s' % (i + 1, g[:20]) for i, g in enumerate(guia[:6])) \
        or 'P1:leer -> P2:extraer -> P3:clasificar -> P4:goals'
    goals = _paso_llm('nvidia', 'nvidia/nemotron-3-super-120b-a12b',
        [{'role': 'system', 'content': _SYS_PIPE},
         {'role': 'user', 'content': 'Auditoria forense X-RAY de este archivo. Entrega compacto: 1) resumen de 2 lineas 2) tipo de code/documento y funcion 3) 12 goals que la IA debe ejecutar con este archivo, ids G1..G12.\nArchivo %s:\n%s' % (nombre or 'entrada', base_t[:6000])}], 120, 1400)
    return {'ok': True, 'nombre': nombre or 'entrada', 'urls': urls,
            'estructura': 'lineas=%d tipo=%s titulos=%d simbolos=%d' % (lineas, ext, len(cabeza), len(funcs)),
            'mapa_mental': mapa, 'microflujo': microflujo, 'resumen_goals': goals or '',
            'checklist': [{'item': 'xray:extraer-urls', 'estado': 'COMPLETADO'},
                          {'item': 'xray:estructura-raiz', 'estado': 'COMPLETADO'},
                          {'item': 'xray:mapa-mental', 'estado': 'COMPLETADO'},
                          {'item': 'xray:microflujo', 'estado': 'COMPLETADO'},
                          {'item': 'xray:goals-ia', 'estado': 'COMPLETADO' if goals else 'PENDIENTE'}]}


def _xray_texto_out(r):
    return ('X-RAY %s\n%s\nURLs: %s\nMAPA:\n%s\nFLUJO: %s\n%s'
            % (r.get('nombre'), r.get('estructura'), ', '.join(r.get('urls') or [])[:400] or '-',
               r.get('mapa_mental'), r.get('microflujo'), r.get('resumen_goals') or ''))


def _auditor_code(pregunta=''):
    # motor auditor de code del repo: ubica y clasifica los archivos de code del proyecto
    h = _herr()
    s, d = h._gh('GET', '/repos/maxbry123-commits/%s/git/trees/main?recursive=1' % _REPO_DIR)
    if s >= 400 or not isinstance(d, dict):
        return {'error': 'AUDITOR_GITHUB_FALLO', 'detalle': str(d)[:200]}
    por_dir = {}
    for t in d.get('tree') or []:
        pth = str(t.get('path') or '')
        if t.get('type') != 'blob' or _os.path.splitext(pth)[1].lower() not in _CODE_EXT:
            continue
        por_dir.setdefault(pth.split('/')[0], []).append(pth)
    lineas = ['%s/ (%d): %s' % (k, len(v), ', '.join(x.rsplit('/', 1)[-1] for x in v[:8]))
              for k, v in sorted(por_dir.items(), key=lambda kv: -len(kv[1]))]
    return {'ok': True, 'total': sum(len(v) for v in por_dir.values()), 'carpetas': lineas,
            'checklist': [{'item': 'auditor:git-tree', 'estado': 'COMPLETADO'},
                          {'item': 'auditor:clasificar-code', 'estado': 'COMPLETADO'}]}


def _handoff(fuente):
    # selector de ancla: handoff JSON anclable al input (proyecto, skill maestro, preview)
    h = _herr()
    if fuente == 'preview':
        return {'handoff': {'fuente': 'preview-vercel-nuevo',
                            'url': 'https://riu-jev-bridge-git-devin-179117-1f446d-maxbry123-8833s-projects.vercel.app/chat/ui/nuevo/panel-chat.html',
                            'usa_para': 'frontend de prueba: replicar funciones y diseno'}}
    if fuente == 'skill':
        s, d = h._gh('GET', '/repos/maxbry123-commits/%s/contents/chat%%20router/01-PLAN/%%F0%%9F%%98%%84SKILL.md?ref=main' % _REPO_DIR)
        extracto = ''
        if s < 400:
            try:
                extracto = _b64.b64decode((d or {}).get('content') or '').decode('utf-8', 'replace')[:3500]
            except Exception:  # noqa: BLE001
                pass
        return {'handoff': {'fuente': 'chat router/01-PLAN/SKILL.md', 'skill': 'fromted-yaiwes-frontend-factory',
                            'usa_para': 'arquitectura, diseno y verificacion de la UI', 'extracto': extracto}}
    s, d = h._gh('GET', '/repos/maxbry123-commits/%s/git/trees/main?recursive=1' % _REPO_DIR)
    archivos = [str(t.get('path')) for t in (d or {}).get('tree') or []
                if str(t.get('path') or '').startswith('chat router/') and t.get('type') == 'blob'][:160]
    return {'handoff': {'fuente': 'chat router/', 'proyecto': 'workflow Loops code Yaiwes', 'rama': 'main',
                        'archivos': archivos, 'usa_para': 'trabajar sobre el proyecto del chat'}}


def _gh_enlace(enlace):
    # enlace github (tree/blob/repo) o 'repo/ruta' -> (repo, rama, ruta); owner siempre maxbry123-commits
    enlace = str(enlace or '').strip()
    m = re.match(r'https?://github\.com/[^/]+/([^/#?]+)/(?:tree|blob)/([^/#?]+)/?(.+)?', enlace)
    if m:
        return m.group(1), str(m.group(2) or 'main'), str(m.group(3) or '').strip('/')
    m = re.match(r'https?://github\.com/[^/]+/([^/#?]+)', enlace)
    if m:
        return m.group(1), 'main', ''
    partes = enlace.strip('/').split('/')
    return partes[0], 'main', '/'.join(partes[1:]) if len(partes) > 1 else ''


def _gh_lista(repo, rama, ruta, prof=0):
    # archivos (blob) bajo ruta, recursivo
    if prof > 10:
        return []
    s, d = _herr()._gh('GET', '/repos/maxbry123-commits/%s/contents/%s?ref=%s' % (
        urllib.parse.quote(repo, safe=''), urllib.parse.quote(ruta, safe='/'), urllib.parse.quote(rama, safe='')))
    if s != 200:
        return []
    if isinstance(d, list):
        out = []
        for it in d:
            if it.get('type') == 'dir':
                out += _gh_lista(repo, rama, str(it.get('path') or ''), prof + 1)
            elif it.get('type') == 'file':
                out.append(str(it.get('path')))
        return out
    if isinstance(d, dict) and d.get('path') and d.get('type') != 'dir':
        return [str(d.get('path'))]
    return []


def _gh_bajar(repo, rama, ruta):
    s, d = _herr()._gh('GET', '/repos/maxbry123-commits/%s/contents/%s?ref=%s' % (
        urllib.parse.quote(repo, safe=''), urllib.parse.quote(ruta, safe='/'), urllib.parse.quote(rama, safe='')))
    if s == 200 and isinstance(d, dict) and d.get('content'):
        try:
            return _b64.b64decode(d['content']), str(d.get('sha') or '')
        except Exception:  # noqa: BLE001
            pass
    return None, ''


def _gh_subir(repo, rama, ruta, datos, mensaje):
    base = '/repos/maxbry123-commits/%s/contents/%s' % (urllib.parse.quote(repo, safe=''), urllib.parse.quote(ruta, safe='/'))
    s0, d0 = _herr()._gh('GET', base + '?ref=' + urllib.parse.quote(rama, safe=''))
    cuerpo = {'message': mensaje, 'content': _b64.b64encode(datos).decode('ascii'), 'branch': rama}
    if s0 == 200 and isinstance(d0, dict) and d0.get('sha'):
        cuerpo['sha'] = d0['sha']
    s, _ = _herr()._gh('PUT', base, cuerpo)
    return s in (200, 201)


def _gh_borrar(repo, rama, ruta, sha):
    base = '/repos/maxbry123-commits/%s/contents/%s' % (urllib.parse.quote(repo, safe=''), urllib.parse.quote(ruta, safe='/'))
    s, _ = _herr()._gh('DELETE', base, {'message': 'mover raiz (motor de descarga)', 'sha': sha, 'branch': rama})
    return s == 200


def _desc_registrar(sesion, reg):
    # stated JSON + bitacora permanente de descargas en la memoria del harness
    try:
        mem, scope_for = _memoria()
        sc = scope_for(DUENO, 'chat:' + sesion)
        mem.save(sc, 'descarga:' + reg['id'], reg)
        prev = _mem_dato(sesion, 'descargas_hist').get('lista') or []
        prev = [x for x in prev if x.get('id') != reg.get('id')]
        prev.append({'id': reg.get('id'), 'op': reg.get('op'), 'origen': str(reg.get('origen'))[:150],
                     'destino': str(reg.get('destino'))[:150], 'estado': reg.get('estado'),
                     'archivos': reg.get('ok') or len(reg.get('log') or []), 'ts': reg.get('ts')})
        mem.save(sc, 'descargas_hist', {'lista': prev[-50:]})
    except Exception:  # noqa: BLE001
        pass


def _mover_raiz(payload):
    # motor de descarga/extraccion/copiar/mover entre repos del owner, via API de GitHub
    import secrets as _sec
    sesion = str(payload.get('sesion') or 'general')[:60]
    op = 'mover' if str(payload.get('op') or 'copiar').lower().startswith('m') else 'copiar'
    repo_o, rama_o, ruta_o = _gh_enlace(payload.get('origen'))
    repo_d, rama_d, ruta_d = _gh_enlace(payload.get('destino'))
    if not repo_o or not repo_d:
        return {'error': 'ENLACE_FALTA', 'detalle': 'Falta el enlace de origen o de destino'}
    if not ruta_o and not payload.get('archivo'):
        return {'error': 'RAIZ_VACIA', 'detalle': 'El enlace de origen debe apuntar a una raiz/archivo, no al repo entero'}
    reg = {'id': 'desc-' + _sec.token_hex(5), 'op': op, 'origen': str(payload.get('origen'))[:200],
           'destino': str(payload.get('destino'))[:200], 'estado': 'procesando', 'log': [], 'ts': int(time.time())}
    _desc_registrar(sesion, reg)
    archivos = _gh_lista(repo_o, rama_o, ruta_o)
    if not archivos:
        reg['estado'] = 'error'; reg['log'].append('sin archivos en origen'); _desc_registrar(sesion, reg)
        return {'error': 'ORIGEN_VACIO', 'detalle': 'No hay archivos en el enlace de origen', 'registro': reg['id']}
    ok, fallos = 0, []
    for f in archivos:
        rel = f[len(ruta_o):].lstrip('/') if ruta_o and f.startswith(ruta_o) else f.split('/')[-1]
        rel = rel or f.split('/')[-1]
        datos, sha = _gh_bajar(repo_o, rama_o, f)
        if datos is None:
            fallos.append(f)
            continue
        destino = (ruta_d + '/' + rel).strip('/') if ruta_d else rel
        if not _gh_subir(repo_d, rama_d, destino, datos, 'motor %s: %s' % (op, rel[:60])):
            fallos.append(f)
            continue
        ok += 1
        if op == 'mover' and sha:
            _gh_borrar(repo_o, rama_o, f, sha)
        reg['log'].append('%s -> %s' % (f, destino))
    reg['estado'] = 'completado' if not fallos else 'parcial'
    reg['ok'] = ok
    reg['fallos'] = fallos[:20]
    _desc_registrar(sesion, reg)
    return {'registro': reg['id'], 'estado': reg['estado'], 'archivos': ok, 'fallos': fallos[:20], 'op': op}


def _descargas(payload):
    # auditoria/seguimiento: lista la bitacora o el stated JSON de una descarga
    sesion = str(payload.get('sesion') or 'general')[:60]
    if str(payload.get('op') or 'lista') == 'ver':
        dd = _mem_dato(sesion, 'descarga:' + str(payload.get('id') or '')[:40])
        return dd if dd else {'error': 'DESCARGA_NO_EXISTE'}
    return {'lista': _mem_dato(sesion, 'descargas_hist').get('lista') or []}


def _especial(tipo, model, sesion, pregunta, p=None):
    if tipo == 'consil':
        texto, usadas = _consil(pregunta)
    elif tipo == 'xray':
        nombres = [str(n) for n in ((p or {}).get('anclados') or []) if not str(n).startswith(('handoff:', 'enlace:'))]
        r = _xray(sesion, nombres[0] if nombres else '', pregunta if not nombres else '')
        texto = _xray_texto_out(r) if r.get('ok') else ('X-RAY ERROR: ' + str(r.get('detalle') or r.get('error')))
        usadas = [c['item'] for c in r.get('checklist') or []] or ['xray']
    elif tipo == 'auditor':
        r = _auditor_code()
        texto = ('Auditor de code del repo — %d archivos:\n%s' % (r.get('total', 0), '\n'.join(r.get('carpetas') or [])))
        usadas = [c['item'] for c in r.get('checklist') or []] or ['auditor']
    else:
        texto, usadas = _motor_descarga(pregunta)
    return {'model': model,
            'choices': [{'message': {'role': 'assistant', 'content': texto}}],
            'herramientas': [{'herramienta': u, 'ok': True} for u in usadas],
            'checklist': [{'item': u, 'estado': 'COMPLETADO'} for u in usadas],
            'memoria_guardada': _guardar(sesion, model, pregunta, texto)}


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
    anclados = p.get('anclados') or []
    if anclados:  # archivos, handoffs y enlaces anclados por el usuario desde la ventana del chat
        try:
            mem, scope_for = _memoria()
            trozos = []
            for nom in anclados[:8]:
                nom = str(nom)[:300]
                if nom.startswith('handoff:'):  # handoff encendido en el selector de ancla
                    try:
                        trozos.append('HANDOFF ' + json.dumps(_handoff(nom[8:]).get('handoff') or {}, ensure_ascii=False)[:1500])
                    except Exception:  # noqa: BLE001
                        pass
                elif nom.startswith('enlace:'):  # enlace/handoff pegado por el usuario
                    trozos.append('ENLACE_ANCLADO: ' + nom[7:])
                else:
                    res = mem.search(scope_for(DUENO, 'chat:' + sesion), 'archivo:' + nom[:120], 1)
                    filas = res if isinstance(res, list) else next((v for v in (res or {}).values() if isinstance(v, list)), [])
                    dd = (filas[0].get('data') if filas and isinstance(filas[0], dict) else None) or {}
                    if dd.get('datos_b64'):
                        trozos.append('ARCHIVO %s:\n%s' % (nom, _b64.b64decode(dd['datos_b64']).decode('utf-8', 'replace')[:3000]))
            if trozos:
                sistema += ' Anclados por el usuario: ' + ' | '.join(trozos)
        except Exception:  # noqa: BLE001
            pass
    try:
        sd = _mem_dato(sesion, 'sandbox')
        if sd.get('texto'):
            sistema += ' SANDBOX del usuario (system prompt de code; sigue estas instrucciones): ' + str(sd['texto'])[:3000]
        hp = _mem_dato(sesion, 'handoff_propio')
        if hp.get('texto'):
            sistema += ' HANDOFF del usuario (donde trabajar; sigue este handoff): ' + str(hp['texto'])[:6000]
    except Exception:  # noqa: BLE001
        pass
    if re.search(r'(?i)(contin[uú]a?s?|sigue|retoma|seguid|seguir)', pregunta):
        guardado = _ck_cargar(sesion)
        if guardado:
            mensajes = guardado
            mensajes.append({'role': 'user', 'content': pregunta + ' (retoma el trabajo donde quedo, sin empezar de cero)'})
    if model in ESPECIALES:  # ficha pipeline (consil / motor / xray / auditor): no es una sola api
        return _especial(ESPECIALES[model], model, sesion, pregunta, p)
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
    # siempre queda el texto limpio: si era solo una llamada a herramienta, sale vacio
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
    if action == "subir":  # archivo adjunto del chat -> sistema de almacenamiento/memoria
        try:
            nombre = str(payload.get('nombre') or 'archivo')[:120]
            datos = str(payload.get('datos_b64') or '')
            if len(datos) > 4_000_000:
                return {'error': 'ARCHIVO_MUY_GRANDE'}
            mem, scope_for = _memoria()
            mem.save(scope_for(DUENO, 'chat:' + str(payload.get('sesion') or 'general')[:60]),
                     'archivo:' + nombre, {'nombre': nombre, 'tipo': str(payload.get('tipo') or '')[:80], 'datos_b64': datos})
            return {'ok': True, 'nombre': nombre}
        except Exception as x:  # noqa: BLE001
            return {'error': 'SUBIR_FALLO', 'detalle': str(x)[:200]}
    if action == "archivos":  # ventana del chat: lista lo subido para seleccionar y anclar
        try:
            mem, scope_for = _memoria()
            res = mem.search(scope_for(DUENO, 'chat:' + str(payload.get('sesion') or 'general')[:60]), 'archivo:', 50)
            filas = res if isinstance(res, list) else next((v for v in (res or {}).values() if isinstance(v, list)), [])
            nombres = sorted({str((f.get('data', f) if isinstance(f, dict) else f).get('nombre')) for f in filas
                              if isinstance((f.get('data', f) if isinstance(f, dict) else f), dict) and (f.get('data', f) if isinstance(f, dict) else f).get('nombre')})
            return {'archivos': nombres}
        except Exception:  # noqa: BLE001
            return {'archivos': []}
    if action == 'xray':  # motor de auditoria forense x-ray del archivo anclado
        return _xray(str(payload.get('sesion') or 'general')[:60],
                     str(payload.get('nombre') or ''), str(payload.get('texto') or ''))
    if action == 'auditor_code':  # motor auditor de code: ubica los archivos de code del repo
        return _auditor_code(str(payload.get('filtro') or ''))
    if action == 'handoff':  # selector de ancla: handoff JSON para anclar al input
        return _handoff(str(payload.get('fuente') or 'chat-router'))
    if action == 'handoff_texto':  # mi handoff: texto del usuario guardado/editable por sesion
        try:
            mem, scope_for = _memoria()
            sc = scope_for(DUENO, 'chat:' + str(payload.get('sesion') or 'general')[:60])
            if 'texto' in payload:
                mem.save(sc, 'handoff_propio', {'texto': str(payload.get('texto') or '')[:8000]})
                return {'ok': True, 'encendido': bool(str(payload.get('texto') or '').strip())}
            dd = _mem_dato(str(payload.get('sesion') or 'general')[:60], 'handoff_propio')
            return {'texto': str(dd.get('texto') or ''), 'encendido': bool(dd.get('texto'))}
        except Exception as x:  # noqa: BLE001
            return {'error': 'HANDOFF_TEXTO_FALLO', 'detalle': str(x)[:200]}
    if action == 'sandbox':  # ventana sandbox: system prompt de code anclado a esta sesion
        try:
            mem, scope_for = _memoria()
            sc = scope_for(DUENO, 'chat:' + str(payload.get('sesion') or 'general')[:60])
            if 'texto' in payload:
                mem.save(sc, 'sandbox', {'texto': str(payload.get('texto') or '')[:4000]})
                return {'ok': True, 'encendido': bool(str(payload.get('texto') or '').strip())}
            dd = _mem_dato(str(payload.get('sesion') or 'general')[:60], 'sandbox')
            return {'sandbox': str(dd.get('texto') or '')}
        except Exception as x:  # noqa: BLE001
            return {'error': 'SANDBOX_FALLO', 'detalle': str(x)[:200]}
    if action == 'mover_raiz':  # motor: copiar/mover una raiz entre repos por enlace
        try:
            return _mover_raiz(payload)
        except Exception as x:  # noqa: BLE001
            return {'error': 'MOVER_FALLO', 'detalle': str(x)[:200]}
    if action == 'descargas':  # motor: auditoria, seguimiento y bitacora de descargas
        try:
            return _descargas(payload)
        except Exception as x:  # noqa: BLE001
            return {'error': 'DESCARGAS_FALLO', 'detalle': str(x)[:200]}
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

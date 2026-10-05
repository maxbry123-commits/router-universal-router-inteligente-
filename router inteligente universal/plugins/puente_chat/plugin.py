"""Plugin puente_chat (Director 2026-10-04): papel del harness para la UI del chat, dentro del Router (su computo, puerta fija).

Llamada: POST <puerta>/plugins/puente_chat/call/<accion> con el token del chat (Bearer). Respuesta del host: {"status": "ok", "result": ...}.
Acciones: status | modelos | chat {model, messages, max_tokens, sesion, respaldo_url?} | estado {job, url} | apagar {job}.
Modelos NV/GROQ: llamada directa al proveedor con las claves del banco; rota claves del MISMO modelo; tope total 90 s (GLM 96 s).
Modelos HF: enciende un L4 (almacenamiento conectado como disco); se apaga solo al terminar la salida, a los 5 min o con 'apagar'.
Memoria: antes de responder busca contexto en /memoria (scope chat:<sesion>); despues guarda pregunta y respuesta.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

NS = "COMAND-CENTER-1"
DUENO = "chat-ui"
ETIQUETA_L4 = "router-respaldo-l4"
FICHAS = {
    "nv-kimi-k3": ("NV Kimi K3", "nvidia", "moonshotai/kimi-k3", 90),
    "nv-glm-5-3": ("NV GLM 5.3", "nvidia", "z-ai/glm-5.3", 96),
    "nv-nemotron-super": ("NV Nemotron 3 Super", "nvidia", "nvidia/nemotron-3-super-120b-a12b", 90),
    "nv-nemotron-lightning": ("NV Nemotron 3.5 Lightning", "nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b", 90),
    "groq-qwen-3-8": ("GROQ Qwen 3.8", "groq", "qwen/qwen3.8-27b", 90),
}
RESPALDO = {
    "hf-1-qwen-3-8": ("HF 1 Qwen 3.8 (27B)", "Qwen3.8-27B-UD-Q3_K_XL.gguf"),
    "hf-2-qwen-3-6": ("HF 2 Qwen 3.6 (35B)", "Qwen3.6-35B-A3B-UD-Q3_K_XL.gguf"),
}
ARRANQUE = ('/app/llama-server --host 0.0.0.0 --port 8080 -m "/modelos/$ARCHIVO" --alias "$ALIAS" -ngl 999 -fa on -np 1 -b 128 -c 16384 '
            '--temp 0 --top-k 20 --top-p 0.95 --no-mmproj --reasoning-budget 0 --spec-type draft-mtp --spec-draft-n-max 2 --jinja > /tmp/l.log 2>&1 &\n'
            'P=$!\nwhile kill -0 $P 2>/dev/null; do\n  sleep 5\n  I=$(( $(date +%s) - $(stat -c %Y /tmp/l.log) ))\n'
            '  if grep -q print_timing /tmp/l.log && [ $I -ge 30 ]; then echo APAGADO_FIN_DE_SALIDA; kill $P; exit 0; fi\n'
            '  if [ $I -ge 300 ]; then echo APAGADO_5_MIN_SIN_USO; kill $P; exit 0; fi\ndone\n')


def _http(metodo: str, url: str, token: str, cuerpo: Any = None, espera: float = 60) -> tuple[int, Any]:
    req = urllib.request.Request(url, data=json.dumps(cuerpo).encode() if cuerpo is not None else None, method=metodo,
                                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
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


def _encender(model: str) -> dict[str, Any]:
    _, archivo = RESPALDO[model]
    s, j = _hf("POST", "/api/jobs/" + NS, {
        "dockerImage": "ghcr.io/ggml-org/llama.cpp:server-cuda", "command": ["bash", "-c", ARRANQUE], "arguments": [],
        "environment": {"ARCHIVO": archivo, "ALIAS": model}, "flavor": "l4x1", "timeoutSeconds": 7200, "labels": {"name": ETIQUETA_L4},
        "volumes": [{"type": "bucket", "source": NS + "/yaiwes-memoria-storage", "mountPath": "/modelos", "readOnly": True,
                     "path": "router-respaldo/modelos"}],
        "expose": {"ports": [8080], "portsPublic": []}})
    if s >= 400:
        return {"error": "NO_SE_PUDO_ENCENDER", "detalle": str(j)[:300]}
    return {"estado": "encendiendo", "job_id": j["id"], "url": "https://" + j["id"] + "--8080.hf.jobs", "model": model}


def _chat(p: dict[str, Any]) -> dict[str, Any]:
    model = str(p.get("model") or "")
    mensajes = list(p.get("messages") or [])
    max_tokens = int(p.get("max_tokens") or 2048)
    sesion = str(p.get("sesion") or "general")[:60]
    pregunta = next((str(m.get("content", "")) for m in reversed(mensajes) if m.get("role") == "user"), "")
    if model not in FICHAS and model not in RESPALDO:
        return {"error": "MODELO_DESCONOCIDO", "validos": [*FICHAS, *RESPALDO]}
    if model in RESPALDO and not p.get("respaldo_url"):
        return _encender(model)
    ctx = _contexto(sesion, pregunta) if pregunta else ""
    if ctx:
        mensajes = [{"role": "system", "content": "Contexto guardado de esta conversacion:\n" + ctx}, *mensajes]
    if model in FICHAS:
        _, proveedor, modelo, tope = FICHAS[model]
        r = _api(proveedor, modelo, mensajes, max_tokens, tope)
        if "error" in r:
            return r
        texto = r["message"].get("content") or ""
        salida = {"model": model, "choices": [{"index": 0, "message": r["message"], "finish_reason": r.get("finish_reason")}], "usage": r.get("usage")}
    else:
        url = str(p["respaldo_url"])
        if not url.startswith("https://") or not url.endswith("--8080.hf.jobs"):
            return {"error": "RESPALDO_URL_INVALIDA"}
        ultimo: tuple[int, Any] = (0, {})
        for t in _tokens_hf():
            ultimo = _http("POST", url + "/v1/chat/completions", t, {"model": model, "messages": mensajes, "max_tokens": max_tokens}, 110)
            if ultimo[0] < 400:
                break
        if ultimo[0] >= 400 or not isinstance(ultimo[1], dict) or "choices" not in ultimo[1]:
            return {"error": "RESPALDO_NO_RESPONDE", "detalle": str(ultimo[1])[:300]}
        salida = ultimo[1]
        texto = salida["choices"][0]["message"].get("content") or ""
    salida["memoria_guardada"] = _guardar(sesion, model, pregunta, texto)
    return salida


def _estado(p: dict[str, Any]) -> dict[str, Any]:
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
        return {"ok": True, "modelos": len(FICHAS) + len(RESPALDO)}
    if action == "modelos":
        return {"modelos": [{"id": k, "nombre": v[0], "respaldo": False} for k, v in FICHAS.items()]
                + [{"id": k, "nombre": v[0], "respaldo": True} for k, v in RESPALDO.items()]}
    if action == "chat":
        return _chat(payload)
    if action == "estado":
        return _estado(payload)
    if action == "apagar":
        return _apagar(payload)
    return {"error": "ACCION_DESCONOCIDA"}

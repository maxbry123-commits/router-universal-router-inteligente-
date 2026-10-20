"""Las 7 herramientas. Cada una devuelve dict {ok, ...}; ok=False es fallo real (nunca PASS).
Todo va por HTTP: GitHub REST y Router /plugins/<id>/call/<accion>. Sin imports de plugins."""
from __future__ import annotations
import base64
import re
import time
import urllib.parse

from . import config, transport

API = "https://api.github.com"
RE_ID = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
RE_REPO = re.compile(r"^[A-Za-z0-9_.\-]{1,100}$")
# get_keys del banco y similares nunca se exponen por el MCP.
ACCIONES_BLOQUEADAS = {("banco", "get_keys")}
PLUGINS_BLOQUEADOS = {"banco"}


def _fallo(codigo: str, detalle="") -> dict:
    return {"ok": False, "error": codigo, "detalle": config.redactar(str(detalle))[:500]}


# ---------- GitHub (HTTP directo a la API REST) ----------
def _gh(metodo, ruta, cuerpo=None):
    pat = config.github_pat()
    if not pat:
        return None, _fallo("FALTA_GITHUB_PAT", "definir RIU_GITHUB_PAT (banco del Router)")
    h = {"Authorization": "Bearer " + pat, "Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "riu-mcp"}
    try:
        st, d = transport.enviar(metodo, API + ruta, h, cuerpo)
    except OSError as e:
        return None, _fallo("RED", e)
    return (st, d), None


def _ruta_contenidos(repo, ruta):
    q = urllib.parse.quote(ruta.strip("/"), safe="/")
    return "/repos/%s/%s/contents/%s" % (config.OWNER, repo, q)


def _valida_repo_ruta(repo, ruta):
    if not isinstance(repo, str) or not RE_REPO.match(repo):
        return _fallo("REPO_INVALIDO")
    if ".." in (ruta or "").split("/"):
        return _fallo("RUTA_INVALIDA")
    return None


def github_leer(a: dict) -> dict:
    repo, ruta, rama = a.get("repo"), a.get("ruta") or "", a.get("rama") or "main"
    e = _valida_repo_ruta(repo, ruta)
    if e:
        return e
    r, err = _gh("GET", _ruta_contenidos(repo, ruta) + "?ref=" + urllib.parse.quote(rama, safe=""))
    if err:
        return err
    st, d = r
    if st >= 400:
        return _fallo("GITHUB_%s" % st, d)
    if isinstance(d, list):
        return {"ok": True, "tipo": "dir", "entradas": [{"nombre": x.get("name"), "tipo": x.get("type"), "tam": x.get("size")} for x in d]}
    try:
        txt = base64.b64decode(d.get("content") or "").decode("utf-8", "replace")
    except Exception as x:  # noqa: BLE001
        return _fallo("DECODIFICAR", x)
    lin = a.get("lineas")
    if lin:
        try:
            p = str(lin).split("-", 1)
            ini = max(1, int(p[0])) - 1
            fin = int(p[1]) if len(p) > 1 and p[1].strip() else None
            txt = "\n".join(txt.split("\n")[ini:fin])
        except ValueError:
            return _fallo("LINEAS_INVALIDO", 'usa "200-400"')
    return {"ok": True, "tipo": "file", "sha": d.get("sha"), "rama": rama, "contenido": txt}


def github_escribir(a: dict) -> dict:
    """PUT + readback: exito solo si el commit existe y el contenido leido de vuelta coincide byte a byte."""
    if not config.escritura_activa():
        return _fallo("ESCRITURA_DESACTIVADA")
    repo, ruta, cont = a.get("repo"), a.get("ruta") or "", a.get("contenido")
    rama, msg = a.get("rama"), a.get("mensaje") or "mcp riu: update"
    e = _valida_repo_ruta(repo, ruta)
    if e:
        return e
    if not ruta or not isinstance(cont, str):
        return _fallo("ARGUMENTOS", "ruta y contenido (texto) obligatorios")
    if rama not in config.ramas_permitidas():
        return _fallo("RAMA_NO_PERMITIDA", "permitidas: " + ", ".join(config.ramas_permitidas()))
    base = _ruta_contenidos(repo, ruta)
    r, err = _gh("GET", base + "?ref=" + urllib.parse.quote(rama, safe=""))
    if err:
        return err
    sha = r[1].get("sha") if r[0] == 200 and isinstance(r[1], dict) else None
    if r[0] not in (200, 404):
        return _fallo("GITHUB_%s" % r[0], r[1])
    cuerpo = {"message": msg, "branch": rama, "content": base64.b64encode(cont.encode("utf-8")).decode("ascii")}
    if sha:
        cuerpo["sha"] = sha
    r, err = _gh("PUT", base, cuerpo)
    if err:
        return err
    st, d = r
    if st not in (200, 201):
        return _fallo("GITHUB_%s" % st, d)
    csha = ((d or {}).get("commit") or {}).get("sha")
    if not csha:
        return _fallo("SIN_COMMIT_SHA", "GitHub no devolvio sha de commit")
    rb, err = _gh("GET", base + "?ref=" + urllib.parse.quote(csha, safe=""))
    if err:
        return {**err, "commit": csha, "readback_ok": False}
    ok = False
    if rb[0] == 200 and isinstance(rb[1], dict):
        try:
            ok = base64.b64decode(rb[1].get("content") or "").decode("utf-8") == cont
        except Exception:  # noqa: BLE001
            ok = False
    if not ok:
        return {"ok": False, "error": "READBACK_NO_COINCIDE", "commit": csha, "readback_ok": False}
    return {"ok": True, "commit": csha, "rama": rama, "ruta": ruta, "readback_ok": True}


# ---------- Router / Harness (HTTP) ----------
def _router(metodo, ruta, cuerpo=None):
    h = {"Accept": "application/json"}
    k = config.llave_chat()
    if k:
        h["X-API-Key"] = k
        h["Authorization"] = "Bearer " + k  # el Router documenta ambas formas; se envian las dos
    try:
        st, d = transport.enviar(metodo, config.router_base() + ruta, h, cuerpo, 60)
    except OSError as e:
        return None, _fallo("RED", e)
    return (st, d), None


def _call(plugin, accion, payload):
    """POST /plugins/<id>/call/<accion>; el host responde {status:'ok', result:...}."""
    if not RE_ID.match(plugin or "") or not RE_ID.match(accion or ""):
        return _fallo("ID_INVALIDO")
    r, err = _router("POST", "/plugins/%s/call/%s" % (plugin, accion), payload or {})
    if err:
        return err
    st, d = r
    if st >= 400:
        return _fallo("ROUTER_%s" % st, d)
    if not isinstance(d, dict) or d.get("status") != "ok":
        return _fallo("PLUGIN_NO_OK", d)
    return {"ok": True, "resultado": d.get("result")}


def router_estado(a: dict) -> dict:
    salud, err = _router("GET", "/health")
    out = {"salud_http": None if err else salud[0]}
    if err:
        return {**err, "partes": out}
    chat = _call("puente_chat", "status", {})
    ok = salud[0] == 200 and chat.get("ok", False)
    return {"ok": ok, "salud_http": salud[0], "salud": salud[1] if salud[0] == 200 else None,
            "puente_chat": chat.get("resultado") if chat.get("ok") else chat}


def plugin_llamar(a: dict) -> dict:
    p, ac = a.get("plugin"), a.get("accion")
    if p in PLUGINS_BLOQUEADOS or (p, ac) in ACCIONES_BLOQUEADAS:
        return _fallo("BLOQUEADO", "plugin/accion no expuesto por MCP")
    return _call(p, ac, a.get("payload") or {})


def chat_enviar(a: dict) -> dict:
    msgs = a.get("messages") or ([{"role": "user", "content": a["mensaje"]}] if a.get("mensaje") else None)
    if not a.get("model") or not msgs:
        return _fallo("ARGUMENTOS", "model y (messages o mensaje) obligatorios")
    r = _call("puente_chat", "chat_async", {"model": a["model"], "messages": msgs,
                                            "max_tokens": int(a.get("max_tokens") or 512),
                                            "sesion": a.get("sesion") or "mcp"})
    if not r["ok"]:
        return r
    res = r["resultado"] if isinstance(r["resultado"], dict) else {}
    pid = res.get("proceso_id")
    if not pid:
        return {"ok": False, "error": "SIN_PROCESO_ID", "resultado": res}
    return {"ok": True, "proceso_id": pid, "estado": res.get("estado")}


def ver_proceso(a: dict) -> dict:
    pid = a.get("proceso_id")
    if not pid:
        return _fallo("ARGUMENTOS", "proceso_id obligatorio")
    r = _call("puente_chat", "resultado", {"proceso_id": pid})
    if not r["ok"]:
        return r
    res = r["resultado"] if isinstance(r["resultado"], dict) else {}
    try:
        contenido = res["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        contenido = None
    if contenido:
        return {"ok": True, "terminado": True, "contenido": contenido, "resultado": res}
    return {"ok": True, "terminado": False, "estado": res.get("estado"), "resultado": res}


def probar_modelo(a: dict, dormir=time.sleep) -> dict:
    """PASS solo con contenido real. Timeout o error = FALLO/PENDIENTE, nunca PASS."""
    model = a.get("model")
    env_ = chat_enviar({"model": model, "mensaje": a.get("prompt") or "Responde solo: OK", "max_tokens": 64, "sesion": "mcp-prueba"})
    if not env_["ok"]:
        return {"veredicto": "FALLO", **env_}
    n = max(1, min(int(a.get("intentos") or 20), 60))
    seg = max(0.0, float(a.get("espera_s") if a.get("espera_s") is not None else 3))
    for _ in range(n):
        v = ver_proceso({"proceso_id": env_["proceso_id"]})
        if not v["ok"]:
            return {"veredicto": "FALLO", **v}
        if v["terminado"]:
            return {"ok": True, "veredicto": "PASS", "proceso_id": env_["proceso_id"], "contenido": v["contenido"][:500]}
        dormir(seg)
    return {"ok": False, "veredicto": "PENDIENTE", "error": "SIN_RESPUESTA_A_TIEMPO", "proceso_id": env_["proceso_id"]}


_S = lambda **p: {"type": "object", "properties": p, "required": [k for k, v in p.items() if v.pop("_req", False)]}  # noqa: E731
_T = lambda d=None, req=False: ({"type": "string", "description": d or ""} | ({"_req": True} if req else {}))  # noqa: E731

TOOLS = {
    "github_leer": (github_leer, "lectura", "Lee archivo/lista carpeta de un repo de maxbry123-commits. Salida: contenido+sha.",
                    _S(repo=_T(req=True), ruta=_T(), rama=_T(), lineas=_T('ej "200-400"'))),
    "github_escribir": (github_escribir, "escritura", "Commit en rama permitida (feat/modos-router, reorganizacion). Exito solo con commit sha + readback.",
                        _S(repo=_T(req=True), ruta=_T(req=True), contenido=_T(req=True), mensaje=_T(), rama=_T(req=True))),
    "router_estado": (router_estado, "lectura", "GET /health y puente_chat/status del Router.", _S()),
    "plugin_llamar": (plugin_llamar, "ejecucion", "POST /plugins/<plugin>/call/<accion>. banco bloqueado.",
                      {"type": "object", "properties": {"plugin": _T(req=False), "accion": _T(), "payload": {"type": "object"}}, "required": ["plugin", "accion"]}),
    "chat_enviar": (chat_enviar, "ejecucion", "Envia chat_async al puente_chat; devuelve proceso_id.",
                    {"type": "object", "properties": {"model": _T(), "mensaje": _T(), "messages": {"type": "array"}, "sesion": _T(), "max_tokens": {"type": "integer"}}, "required": ["model"]}),
    "probar_modelo": (probar_modelo, "ejecucion", "Prueba un modelo extremo a extremo; PASS solo con respuesta real.",
                      {"type": "object", "properties": {"model": _T(), "prompt": _T(), "intentos": {"type": "integer"}, "espera_s": {"type": "number"}}, "required": ["model"]}),
    "ver_proceso": (ver_proceso, "lectura", "Consulta un proceso_id (resultado del chat).", _S(proceso_id=_T(req=True))),
}

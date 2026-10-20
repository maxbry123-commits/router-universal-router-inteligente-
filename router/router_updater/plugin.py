"""router_updater (PARCHE_UPDATER): el Router se actualiza desde GitHub sin regenerar router-bundle.tar.gz a mano.

Solo biblioteca estandar. GitHub es de SOLO LECTURA (API contents/compare/blobs). Nunca se escribe sobre el codigo activo:
cada SHA se prepara en <DIR>/staging/<sha>/, se valida y solo entonces pasa a <DIR>/releases/<sha>/ (puntero atomico <DIR>/current).
Clasificacion de cambios:  reload (json/fichas/allowed_ops: recarga en memoria) | restart (.py de plugin: requiere reinicio de
proceso) | rebuild (Dockerfile/requirements: solo se REPORTA; este modulo no toca el Space ni lo reinicia).
Estado persistente (JSON atomico): DESIRED_SHA, ACTIVE_SHA, LAST_GOOD_SHA, UPDATE_STATE, LAST_ERROR.
Autosync y webhook: APAGADOS por defecto (ROUTER_AUTOSYNC=1 / ROUTER_WEBHOOK=1 + ROUTER_WEBHOOK_SECRET).
Acciones del plugin host: status, version, update_status, sync_now, webhook, autosync_iniciar, autosync_parar.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

REPO_DEFECTO = "maxbry123-commits/router-universal-router-inteligente-"
RAMA_DEFECTO = "main"
PREFIJO_DEFECTO = "fichas"  # subarbol que se sincroniza en caliente (fichas/fichas_qwen/...); plugins/ y router/ requieren redeploy
DIR_DEFECTO = "/data/router_updater"
AUTOSYNC_MIN_S = 30
MAX_ARCHIVO = 20 * 1024 * 1024
MAX_TOTAL = 200 * 1024 * 1024
MAX_WEBHOOK_BYTES = 5 * 1024 * 1024
MAX_ENTREGAS = 200
RETENER_RELEASES = 3
API = "https://api.github.com"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RAMA_RE = re.compile(r"^[A-Za-z0-9._/-]{1,100}$")
REPO_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}/[A-Za-z0-9._-]{1,100}$")

_LOCK = threading.RLock()
_SYNC_LOCK = threading.Lock()
_AUTOSYNC: dict[str, Any] = {"hilo": None, "stop": None}
_PARCHE_UPDATER = True  # marcador vivo


# ----------------------------------------------------------------------------------------------------------- configuracion
def _cfg() -> dict[str, Any]:
    e = os.environ
    repo = e.get("ROUTER_UPDATER_REPO", REPO_DEFECTO)
    rama = e.get("ROUTER_UPDATER_BRANCH", RAMA_DEFECTO)
    if not REPO_RE.match(repo):
        raise ValueError("ROUTER_UPDATER_REPO invalido")
    if not RAMA_RE.match(rama) or ".." in rama:
        raise ValueError("ROUTER_UPDATER_BRANCH invalido")
    prefijo = e.get("ROUTER_UPDATER_PREFIX", PREFIJO_DEFECTO).strip("/")
    try:
        intervalo = max(AUTOSYNC_MIN_S, int(e.get("ROUTER_AUTOSYNC_S", "120")))
    except ValueError:
        intervalo = 120
    return {"repo": repo, "rama": rama, "prefijo": prefijo, "dir": Path(e.get("ROUTER_UPDATER_DIR", DIR_DEFECTO)),
            "autosync": e.get("ROUTER_AUTOSYNC", "") == "1", "intervalo": intervalo,
            "webhook": e.get("ROUTER_WEBHOOK", "") == "1", "import_check": e.get("ROUTER_UPDATER_IMPORT_CHECK", "") == "1"}


def _token() -> str:
    # solo lectura, del banco/entorno del Router; nunca se imprime ni se guarda en estado/log
    for k in ("ROUTER_UPDATER_GH_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN", "GITHUB_TOKEN"):
        v = os.environ.get(k, "").strip()
        if v:
            return v
    return ""


def _limpiar(msg: Any) -> str:
    t = _token()
    s = str(msg)
    if t:
        s = s.replace(t, "***")
    return re.sub(r"(?i)(bearer|token)\s+[A-Za-z0-9_\-\.]{12,}", r"\1 ***", s)[:500]


# ----------------------------------------------------------------------------------------------------------- estado persistente
def _estado_vacio() -> dict[str, Any]:
    return {"DESIRED_SHA": "", "ACTIVE_SHA": "", "LAST_GOOD_SHA": "", "UPDATE_STATE": "idle", "LAST_ERROR": "",
            "FAILED_SHA": "", "pendiente_reinicio": [], "pendiente_rebuild": [], "manifiesto": {}, "entregas": [],
            "ultimo_chequeo": 0, "ultimo_plan": {}}


def _ruta_estado(c: dict[str, Any]) -> Path:
    return c["dir"] / "state.json"


def leer_estado(c: dict[str, Any] | None = None) -> dict[str, Any]:
    c = c or _cfg()
    est = _estado_vacio()
    try:
        d = json.loads(_ruta_estado(c).read_text(encoding="utf-8"))
        if isinstance(d, dict):
            est.update({k: d[k] for k in est if k in d})
    except (OSError, ValueError):
        pass
    return est


def _escribir_atomico(ruta: Path, data: bytes) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(ruta.parent), prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, ruta)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def guardar_estado(est: dict[str, Any], c: dict[str, Any] | None = None) -> None:
    c = c or _cfg()
    _escribir_atomico(_ruta_estado(c), json.dumps(est, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8"))


def _detectar_activo(c: dict[str, Any], est: dict[str, Any]) -> None:
    # si este proceso corre desde <DIR>/releases/<sha>/, ese sha es el ACTIVO (lo fija el arranque, no la sincronizacion)
    try:
        rel = (c["dir"] / "releases").resolve()
        me = Path(__file__).resolve()
        if rel in me.parents:
            sha = me.relative_to(rel).parts[0]
            if SHA_RE.match(sha) and est.get("ACTIVE_SHA") != sha:
                est["ACTIVE_SHA"] = sha
                if est.get("LAST_GOOD_SHA") == sha:
                    est["pendiente_reinicio"], est["pendiente_rebuild"] = [], []
                    est["UPDATE_STATE"] = "ok"
                guardar_estado(est, c)
    except Exception:  # noqa: BLE001
        pass


# ----------------------------------------------------------------------------------------------------------- GitHub (solo lectura)
class GitHub:
    """Cliente de solo lectura. `http(ruta) -> (status, objeto_json)` es inyectable para pruebas (sin red)."""

    def __init__(self, repo: str, http: Callable[[str], tuple[int, Any]] | None = None):
        self.repo = repo
        self._http = http or self._http_real

    def _http_real(self, ruta: str) -> tuple[int, Any]:
        if not ruta.startswith("/repos/"):
            raise ValueError("ruta no permitida")
        h = {"Accept": "application/vnd.github+json", "User-Agent": "riu-router-updater", "X-GitHub-Api-Version": "2022-11-28"}
        t = _token()
        if t:
            h["Authorization"] = "Bearer " + t  # solo cabecera; nunca en URL ni en log
        req = urllib.request.Request(API + ruta, headers=h, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (host fijo https)
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, {"message": _limpiar(e.reason)}
        except Exception as e:  # noqa: BLE001
            raise RuntimeError("GITHUB_RED:" + _limpiar(type(e).__name__)) from None

    def _get(self, ruta: str) -> Any:
        st, d = self._http(ruta)
        if st != 200:
            raise RuntimeError("GITHUB_HTTP_%s:%s" % (st, _limpiar((d or {}).get("message", "") if isinstance(d, dict) else "")))
        return d

    def _q(self, s: str) -> str:
        return urllib.parse.quote(s, safe="/")

    def head_sha(self, rama: str) -> str:
        d = self._get("/repos/%s/commits/%s" % (self.repo, self._q(rama)))
        sha = str(d.get("sha") or "") if isinstance(d, dict) else ""
        if not SHA_RE.match(sha):
            raise RuntimeError("GITHUB_SHA_INVALIDO")
        return sha

    def comparar(self, base: str, head: str) -> tuple[list[dict[str, str]], bool]:
        """-> (cambios[{path,estado,blob,previo}], truncado). La API devuelve como mucho 300 archivos por pagina; >=300 = posible truncado."""
        cambios: list[dict[str, str]] = []
        pag = 1
        while pag <= 10:
            d = self._get("/repos/%s/compare/%s...%s?per_page=100&page=%d" % (self.repo, base, head, pag))
            fs = d.get("files") or [] if isinstance(d, dict) else []
            for f in fs:
                cambios.append({"path": str(f.get("filename") or ""), "estado": str(f.get("status") or ""),
                                "blob": str(f.get("sha") or ""), "previo": str(f.get("previous_filename") or "")})
            if len(fs) < 100:
                break
            pag += 1
        return cambios, (len(cambios) >= 300 or pag > 10)

    def recorrer(self, directorio: str, ref: str) -> dict[str, str]:
        """{ruta: blob_sha} de todo el arbol bajo `directorio` en `ref`, por la API contents (recursivo)."""
        out: dict[str, str] = {}
        pila = [directorio]
        while pila:
            d = pila.pop()
            lst = self._get("/repos/%s/contents/%s?ref=%s" % (self.repo, self._q(d), ref))
            if isinstance(lst, dict):
                lst = [lst]
            for it in lst:
                t, p = it.get("type"), str(it.get("path") or "")
                if t == "dir":
                    pila.append(p)
                elif t in ("file", "symlink") and it.get("sha"):
                    out[p] = str(it["sha"])
        return out

    def blob(self, sha: str) -> bytes:
        if not SHA_RE.match(sha):
            raise RuntimeError("BLOB_SHA_INVALIDO")
        d = self._get("/repos/%s/git/blobs/%s" % (self.repo, sha))
        if not isinstance(d, dict) or d.get("encoding") != "base64":
            raise RuntimeError("BLOB_FORMATO")
        data = base64.b64decode(str(d.get("content") or ""))
        if hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() != sha:  # noqa: S324 (integridad git, no seguridad)
            raise RuntimeError("BLOB_INTEGRIDAD:" + sha[:12])
        return data


# ----------------------------------------------------------------------------------------------------------- clasificacion
def clasificar(path: str) -> str:
    """-> 'reload' | 'restart' | 'rebuild' | 'ninguno' para una ruta del repo."""
    p = path.replace("\\", "/")
    nombre = p.rsplit("/", 1)[-1]
    if nombre.startswith("Dockerfile") or re.match(r"^requirements[\w.-]*\.txt$", nombre) or nombre in ("pyproject.toml", "setup.py", "setup.cfg", "boot.sh", "packages.txt"):
        return "rebuild"
    partes = p.split("/")
    if "tests" in partes or nombre.startswith("test_"):
        return "ninguno"  # los tests no son codigo en ejecucion
    if nombre.endswith(".py"):
        return "restart"
    if nombre.endswith(".json") or ("fichas_qwen" in partes and "fichas" in partes[partes.index("fichas_qwen") + 1:-1]):  # el prefijo "fichas" ya contiene la palabra: solo cuenta fichas_qwen/fichas/
        return "reload"
    return "ninguno"


def clasificar_cambios(cambios: list[dict[str, str]]) -> dict[str, list[str]]:
    plan: dict[str, list[str]] = {"reload": [], "restart": [], "rebuild": [], "ninguno": []}
    for c in cambios:
        for p in {c.get("path", ""), c.get("previo", "")} - {""}:
            plan[clasificar(p)].append(p)
    return plan


def _ruta_segura(path: str, prefijo: str) -> bool:
    if not path or path.startswith("/") or "\\" in path or "\0" in path:
        return False
    partes = path.split("/")
    if any(x in ("", ".", "..") for x in partes):
        return False
    return path == prefijo or path.startswith(prefijo + "/")


# ----------------------------------------------------------------------------------------------------------- staging + validacion
def _copiar_arbol(origen: Path, destino: Path) -> None:
    def cp(s: str, d: str) -> None:
        try:
            os.link(s, d)  # los releases son inmutables: el enlace duro evita copiar cientos de MB
        except OSError:
            shutil.copy2(s, d)
    shutil.copytree(origen, destino, copy_function=cp)


def validar_staging(raiz: Path, cambios_rel: list[str], c: dict[str, Any]) -> list[str]:
    """Lista de errores (vacia = valido). JSON parsea, .py compila (compile, sin escribir .pyc) y, si ROUTER_UPDATER_IMPORT_CHECK=1, importa en subproceso."""
    errores: list[str] = []
    for rel in cambios_rel:
        f = raiz / rel
        if not f.is_file():
            continue
        if rel.endswith(".json"):
            try:
                json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                errores.append("JSON_INVALIDO:%s:%s" % (rel, type(e).__name__))
        elif rel.endswith(".py"):
            try:
                compile(f.read_bytes(), str(f), "exec", dont_inherit=True)  # equivale a py_compile sin escribir .pyc
            except Exception as e:  # noqa: BLE001
                errores.append("PY_INVALIDO:%s:%s" % (rel, _limpiar(str(e).splitlines()[-1] if str(e) else type(e).__name__)))
    fdir = raiz / c["prefijo"] / "fichas_qwen" / "fichas"
    if not errores and fdir.is_dir():
        try:
            mod = sys.modules.get("fichas.fichas_qwen.plugin")
            if mod is not None and hasattr(mod, "cargar_fichas_validadas"):
                mod.cargar_fichas_validadas(fdir)
        except Exception as e:  # noqa: BLE001
            errores.append("FICHAS_INVALIDAS:" + _limpiar(e))
    if not errores and c.get("import_check"):
        for rel in cambios_rel:
            if rel.endswith("/plugin.py") and (raiz / rel).is_file():
                base = raiz / c["prefijo"]
                try:
                    modn = "fichas." + str((raiz / rel).relative_to(base).with_suffix("")).replace("/", ".")
                    r = subprocess.run([sys.executable, "-I", "-c", "import importlib,sys;sys.path.insert(0,sys.argv[1]);importlib.import_module(sys.argv[2])", str(base.parent), modn],  # noqa: S603
                                       capture_output=True, timeout=60, env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}, cwd=str(raiz))
                    if r.returncode != 0:
                        errores.append("IMPORT_FALLA:%s" % modn)
                except Exception as e:  # noqa: BLE001
                    errores.append("IMPORT_ERROR:" + _limpiar(type(e).__name__))
    return errores


def _poda(c: dict[str, Any], conservar: set[str]) -> None:
    rel = c["dir"] / "releases"
    if not rel.is_dir():
        return
    todos = sorted((d for d in rel.iterdir() if d.is_dir()), key=lambda d: d.stat().st_mtime, reverse=True)
    for d in todos[RETENER_RELEASES:]:
        if d.name not in conservar:
            shutil.rmtree(d, ignore_errors=True)


def _apuntar_current(c: dict[str, Any], sha: str) -> None:
    tmp = c["dir"] / (".current-%d" % os.getpid())
    try:
        if tmp.is_symlink() or tmp.exists():
            tmp.unlink()
        os.symlink(c["dir"] / "releases" / sha, tmp)
        os.replace(tmp, c["dir"] / "current")
    except OSError:
        _escribir_atomico(c["dir"] / "current.txt", sha.encode())  # sin symlinks (FS exotico): puntero en texto


def _aplicar_recarga(c: dict[str, Any], sha: str) -> dict[str, Any]:
    """Recarga en memoria de lo que sea 'reload': FICHAS de fichas_qwen (swap atomico). No importa nada nuevo."""
    mod = sys.modules.get("fichas.fichas_qwen.plugin")
    if mod is None or not hasattr(mod, "recargar_fichas"):
        return {"ok": True, "fichas": "modulo_no_cargado"}
    d = c["dir"] / "releases" / sha / c["prefijo"] / "fichas_qwen" / "fichas"
    if not d.is_dir():
        return {"ok": True, "fichas": "sin_directorio"}
    return mod.recargar_fichas(d)


# ----------------------------------------------------------------------------------------------------------- sincronizacion
def sincronizar(forzar: bool = False, gh: GitHub | None = None, c: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compara ACTIVE/LAST_GOOD con el HEAD de la rama; descarga solo lo cambiado a staging/<sha>; valida; activa o hace rollback."""
    c = c or _cfg()
    if not _SYNC_LOCK.acquire(blocking=False):
        return {"ok": False, "estado": "busy"}
    try:
        gh = gh or GitHub(c["repo"])
        with _LOCK:
            est = leer_estado(c)
        _detectar_activo(c, est)
        try:
            head = gh.head_sha(c["rama"])
        except Exception as e:  # noqa: BLE001
            return _fallo_suave(c, est, "CHEQUEO:" + _limpiar(e))
        est["DESIRED_SHA"], est["ultimo_chequeo"] = head, int(time.time())
        if head == est["LAST_GOOD_SHA"] and not forzar:
            est["UPDATE_STATE"] = est["UPDATE_STATE"] if est["pendiente_reinicio"] or est["pendiente_rebuild"] else "ok"
            guardar_estado(est, c)
            return {"ok": True, "cambio": False, "head": head, "estado": est["UPDATE_STATE"]}
        if head == est["FAILED_SHA"] and not forzar:
            guardar_estado(est, c)
            return {"ok": False, "cambio": False, "head": head, "estado": "rolled_back", "error": est["LAST_ERROR"]}
        est["UPDATE_STATE"] = "staging"
        guardar_estado(est, c)
        stg = c["dir"] / "staging" / head
        try:
            return _preparar_y_activar(c, est, gh, head, stg)
        except Exception as e:  # noqa: BLE001
            shutil.rmtree(stg, ignore_errors=True)
            return _rollback(c, est, head, "SYNC:" + _limpiar(e))
    finally:
        _SYNC_LOCK.release()


def _fallo_suave(c: dict[str, Any], est: dict[str, Any], msg: str) -> dict[str, Any]:
    # no se pudo ni consultar GitHub: no es un rollback, el activo sigue intacto
    est["LAST_ERROR"] = msg
    est["UPDATE_STATE"] = "error"
    est["ultimo_chequeo"] = int(time.time())
    guardar_estado(est, c)
    return {"ok": False, "estado": "error", "error": msg}


def _rollback(c: dict[str, Any], est: dict[str, Any], head: str, msg: str) -> dict[str, Any]:
    est["LAST_ERROR"], est["FAILED_SHA"], est["UPDATE_STATE"] = msg, head, "rolled_back"  # ACTIVE y LAST_GOOD no se tocan
    guardar_estado(est, c)
    return {"ok": False, "cambio": False, "head": head, "estado": "rolled_back", "error": msg, "conserva": est["LAST_GOOD_SHA"]}


def _preparar_y_activar(c: dict[str, Any], est: dict[str, Any], gh: GitHub, head: str, stg: Path) -> dict[str, Any]:
    prefijo = c["prefijo"]
    base = est["LAST_GOOD_SHA"]
    base_dir = c["dir"] / "releases" / base if base else None
    manifiesto: dict[str, str] = dict(est["manifiesto"]) if (base_dir and base_dir.is_dir()) else {}
    cambios: list[dict[str, str]] = []
    if base_dir and base_dir.is_dir():
        cambios, trunc = gh.comparar(base, head)
        if trunc:
            cambios = []  # demasiados archivos: se recorre el arbol y se compara contra el manifiesto
            base_dir = base_dir if manifiesto else None
            remoto = gh.recorrer(prefijo, head)
            for p, b in remoto.items():
                if manifiesto.get(p) != b:
                    cambios.append({"path": p, "estado": "modified", "blob": b, "previo": ""})
            for p in manifiesto:
                if p not in remoto:
                    cambios.append({"path": p, "estado": "removed", "blob": "", "previo": ""})
    else:
        base_dir = None
        manifiesto = {}
        for p, b in gh.recorrer(prefijo, head).items():
            cambios.append({"path": p, "estado": "added", "blob": b, "previo": ""})
    plan = clasificar_cambios(cambios)
    # solo rutas bajo el prefijo se materializan; las de rebuild fuera del prefijo solo se reportan
    utiles = [x for x in cambios if _ruta_segura(x["path"], prefijo) or _ruta_segura(x.get("previo", ""), prefijo)]
    shutil.rmtree(stg, ignore_errors=True)
    if base_dir and base_dir.is_dir():
        _copiar_arbol(base_dir, stg)
    else:
        stg.mkdir(parents=True)
    total = 0
    tocados: list[str] = []
    nuevo_man = dict(manifiesto)
    for x in utiles:
        for viejo in {x.get("previo", "")} | ({x["path"]} if x["estado"] == "removed" else set()):
            if viejo and _ruta_segura(viejo, prefijo):
                (stg / viejo).unlink(missing_ok=True)
                nuevo_man.pop(viejo, None)
        if x["estado"] == "removed":
            continue
        p = x["path"]
        if not _ruta_segura(p, prefijo):
            continue
        data = gh.blob(x["blob"])
        total += len(data)
        if len(data) > MAX_ARCHIVO or total > MAX_TOTAL:
            raise RuntimeError("TAMANO_EXCEDIDO:" + p)
        destino = stg / p
        if destino.exists():
            destino.unlink()  # nunca escribir sobre un enlace duro compartido con el release anterior
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(data)
        nuevo_man[p] = x["blob"]
        tocados.append(p)
    est["UPDATE_STATE"] = "validating"
    guardar_estado(est, c)
    errores = validar_staging(stg, tocados, c)
    if errores:
        shutil.rmtree(stg, ignore_errors=True)
        return _rollback(c, est, head, "VALIDACION:" + "; ".join(errores)[:400])
    # promover: staging -> releases/<sha> (rename atomico) y puntero current
    rel = c["dir"] / "releases" / head
    rel.parent.mkdir(parents=True, exist_ok=True)
    if rel.exists():
        shutil.rmtree(rel)
    os.replace(stg, rel)
    _apuntar_current(c, head)
    est.update({"LAST_GOOD_SHA": head, "manifiesto": nuevo_man, "FAILED_SHA": "", "LAST_ERROR": "",
                "ultimo_plan": {k: sorted(set(v))[:50] for k, v in plan.items() if k != "ninguno"}})
    est["pendiente_reinicio"] = sorted(set(est["pendiente_reinicio"]) | set(plan["restart"]))[:100]
    est["pendiente_rebuild"] = sorted(set(est["pendiente_rebuild"]) | set(plan["rebuild"]))[:100]
    if est["pendiente_rebuild"]:
        est["UPDATE_STATE"] = "needs_rebuild"  # solo se reporta: este modulo no hace commits al Space ni lo reinicia
    elif est["pendiente_reinicio"]:
        est["UPDATE_STATE"] = "needs_restart"
    else:
        antes = est["ACTIVE_SHA"]
        r = _aplicar_recarga(c, head)
        if r.get("ok") is False:  # el swap fallo: se vuelve al LAST_GOOD anterior
            est["LAST_GOOD_SHA"] = antes if (c["dir"] / "releases" / antes).is_dir() else ""
            if est["LAST_GOOD_SHA"]:
                _apuntar_current(c, est["LAST_GOOD_SHA"])
            shutil.rmtree(rel, ignore_errors=True)
            return _rollback(c, est, head, "RECARGA:" + str(r.get("error"))[:300])
        est["ACTIVE_SHA"], est["UPDATE_STATE"] = head, "ok"
    guardar_estado(est, c)
    _poda(c, {est["ACTIVE_SHA"], est["LAST_GOOD_SHA"], head})
    return {"ok": True, "cambio": True, "head": head, "estado": est["UPDATE_STATE"], "plan": est["ultimo_plan"],
            "requiere_reinicio": bool(est["pendiente_reinicio"]), "requiere_rebuild": bool(est["pendiente_rebuild"]),
            "archivos": len(tocados)}


# ----------------------------------------------------------------------------------------------------------- estado publico
def version(c: dict[str, Any] | None = None) -> dict[str, Any]:
    c = c or _cfg()
    est = leer_estado(c)
    _detectar_activo(c, est)
    return {"source": "github", "repo": c["repo"], "branch": c["rama"], "desired_sha": est["DESIRED_SHA"], "active_sha": est["ACTIVE_SHA"],
            "last_good_sha": est["LAST_GOOD_SHA"], "update_state": est["UPDATE_STATE"]}


def update_status(c: dict[str, Any] | None = None) -> dict[str, Any]:
    c = c or _cfg()
    est = leer_estado(c)
    v = version(c)
    return {**v, "last_error": est["LAST_ERROR"], "failed_sha": est["FAILED_SHA"], "requiere_reinicio": est["pendiente_reinicio"],
            "requiere_rebuild": est["pendiente_rebuild"], "ultimo_plan": est["ultimo_plan"], "ultimo_chequeo": est["ultimo_chequeo"],
            "autosync": {"activo": bool(_AUTOSYNC["hilo"] and _AUTOSYNC["hilo"].is_alive()), "habilitado": c["autosync"], "intervalo_s": c["intervalo"]},
            "webhook_habilitado": bool(c["webhook"] and os.environ.get("ROUTER_WEBHOOK_SECRET"))}


# ----------------------------------------------------------------------------------------------------------- autosync (apagado por defecto)
def iniciar_autosync(gh: GitHub | None = None, forzar_env: bool = False) -> dict[str, Any]:
    c = _cfg()
    if not c["autosync"] and not forzar_env:
        return {"ok": False, "activo": False, "motivo": "ROUTER_AUTOSYNC!=1 (apagado por defecto)"}
    with _LOCK:
        h = _AUTOSYNC["hilo"]
        if h and h.is_alive():
            return {"ok": True, "activo": True, "ya": True}
        stop = threading.Event()

        def bucle() -> None:
            while not stop.is_set():
                try:
                    sincronizar(gh=gh)
                except Exception:  # noqa: BLE001
                    pass
                stop.wait(_cfg()["intervalo"])

        t = threading.Thread(target=bucle, name="router_updater_autosync", daemon=True)
        _AUTOSYNC.update({"hilo": t, "stop": stop})
        t.start()
    return {"ok": True, "activo": True, "intervalo_s": c["intervalo"]}


def parar_autosync() -> dict[str, Any]:
    with _LOCK:
        if _AUTOSYNC["stop"]:
            _AUTOSYNC["stop"].set()
        _AUTOSYNC.update({"hilo": None, "stop": None})
    return {"ok": True, "activo": False}


# ----------------------------------------------------------------------------------------------------------- webhook (apagado por defecto)
def verificar_firma(secreto: str, cuerpo: bytes, cabecera: str) -> bool:
    if not secreto or not cabecera or not cabecera.startswith("sha256="):
        return False
    esperado = "sha256=" + hmac.new(secreto.encode("utf-8"), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, cabecera)


def procesar_webhook(cabeceras: dict[str, str], cuerpo: bytes, gh: GitHub | None = None, sincrono: bool = False) -> dict[str, Any]:
    """-> {codigo: http, ...}. Nunca imprime ni devuelve el secreto."""
    c = _cfg()
    secreto = os.environ.get("ROUTER_WEBHOOK_SECRET", "")
    if not (c["webhook"] and secreto):
        return {"codigo": 404, "error": "webhook_desactivado"}
    if len(cuerpo) > MAX_WEBHOOK_BYTES:
        return {"codigo": 413, "error": "cuerpo_demasiado_grande"}
    h = {k.lower(): v for k, v in cabeceras.items()}
    if not verificar_firma(secreto, cuerpo, h.get("x-hub-signature-256", "")):
        return {"codigo": 401, "error": "firma_invalida"}
    entrega = h.get("x-github-delivery", "")
    if not re.match(r"^[A-Za-z0-9-]{8,64}$", entrega):
        return {"codigo": 400, "error": "falta_x_github_delivery"}
    with _LOCK:
        est = leer_estado(c)
        if entrega in {e[0] for e in est["entregas"]}:
            return {"codigo": 200, "estado": "replay_ignorado", "delivery": entrega}
        est["entregas"] = (est["entregas"] + [[entrega, int(time.time())]])[-MAX_ENTREGAS:]
        guardar_estado(est, c)
    evento = h.get("x-github-event", "")
    if evento == "ping":
        return {"codigo": 200, "estado": "pong"}
    if evento != "push":
        return {"codigo": 202, "estado": "evento_ignorado", "evento": evento[:30]}
    try:
        ref = str(json.loads(cuerpo.decode("utf-8")).get("ref") or "")
    except Exception:  # noqa: BLE001
        return {"codigo": 400, "error": "json_invalido"}
    if ref != "refs/heads/" + c["rama"]:
        return {"codigo": 202, "estado": "rama_ignorada"}
    if sincrono:
        return {"codigo": 200, "estado": "sincronizado", "resultado": sincronizar(gh=gh)}
    threading.Thread(target=lambda: sincronizar(gh=gh), name="router_updater_webhook", daemon=True).start()
    return {"codigo": 202, "estado": "sync_encolado"}


# ----------------------------------------------------------------------------------------------------------- HTTP (montaje opcional)
def crear_router(auth_dependency: Any) -> Any:
    """APIRouter con GET /version, GET /update-status, POST /sync-now (misma auth que el Router) y POST /webhook/github (HMAC).
    Se monta una sola vez: app.include_router(crear_router(_auth)). fastapi se importa aqui, no al cargar el modulo."""
    from fastapi import APIRouter, Depends, Request  # noqa: PLC0415
    from fastapi.responses import JSONResponse  # noqa: PLC0415
    r = APIRouter()

    @r.get("/version")
    def _v(_o: Any = Depends(auth_dependency)) -> dict[str, Any]:
        return version()

    @r.get("/update-status")
    def _u(_o: Any = Depends(auth_dependency)) -> dict[str, Any]:
        return update_status()

    @r.post("/sync-now")
    def _s(forzar: bool = False, _o: Any = Depends(auth_dependency)) -> dict[str, Any]:
        return sincronizar(forzar=forzar)

    @r.post("/webhook/github")
    async def _w(req: Request) -> Any:
        out = procesar_webhook(dict(req.headers), await req.body())
        return JSONResponse(out, status_code=int(out.pop("codigo", 200)))

    return r


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    p = payload or {}
    if action == "status":
        r = update_status()
        if _cfg()["autosync"]:
            iniciar_autosync()  # idempotente; solo si ROUTER_AUTOSYNC=1
        return {"ok": True, **r}
    if action == "version":
        return version()
    if action == "update_status":
        return update_status()
    if action == "sync_now":
        return sincronizar(forzar=bool(p.get("forzar")))
    if action == "webhook":
        try:
            cuerpo = base64.b64decode(str(p.get("body_b64") or ""))
        except Exception:  # noqa: BLE001
            return {"codigo": 400, "error": "body_b64_invalido"}
        return procesar_webhook(dict(p.get("headers") or {}), cuerpo)
    if action == "autosync_iniciar":
        return iniciar_autosync()
    if action == "autosync_parar":
        return parar_autosync()
    return {"error": "accion_desconocida"}

"""Plugin Host core (no FastAPI): registry of plugins/<id>/ficha.json plus the mandatory call() wrapper (the "harness").

What: every plugins/<id>/ficha.json is read and validated; a bad one marks only that plugin `invalid`. call() is the only way the Router
should invoke a plugin: it never raises and never takes the Router down; on any failure it returns {"status": "degraded", "reason": ...}
(or {"status": "off"} when the plugin is switched off). Entry points ("module:function") are imported with importlib ONLY when the module
starts with an allowed prefix (integration. / plugins.); nothing is exec'd or eval'd. The on/off switch is kept in a small JSON file.
Why: the Director's rule is ONE Router with plugins hanging under it (the chat is just the first plugin), and a broken plugin must never stop it.
Not wired (see plugins/README-ROJO.md): declarative failover, per-level budget, L1-L4 evidence, hot-swap, sandbox, signature/tribunal.
"""
from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import math
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

APP_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_PREFIXES = ("integration.", "plugins.")
SCHEMA_V1 = "plugin_host/v1"
STATE_SCHEMA = "plugin_host_state/v1"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
ENTRY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+:[A-Za-z][A-Za-z0-9_]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
CATEGORIES = ("pipeline", "transversal", "acelerador")
MAX_FICHA_BYTES = 256 * 1024
DEFAULT_TIMEOUT_S = 5.0
MAX_TIMEOUT_S = 120.0
MAX_INFLIGHT = 8  # calls per plugin that may be running at once; a timed-out call cannot be killed, so this bounds leaked threads
PLACEHOLDER_ERROR = "placeholder: sin codigo montado (no se ha revisado ni importado nada)"


def entrypoint_error(entry: Any) -> str | None:
    """Why `entry` ("package.module:function") is refused, or None when it is allowed. Pure string check: nothing is imported."""
    if not isinstance(entry, str) or ":" not in entry:
        return "entrypoint mal formado (se espera 'paquete.modulo:funcion')"
    if not entry.split(":", 1)[0].startswith(ALLOWED_PREFIXES):
        return "entrypoint fuera de la lista permitida (solo modulos " + " / ".join(p + "*" for p in ALLOWED_PREFIXES) + ")"
    if not ENTRY_RE.match(entry):
        return "entrypoint mal formado (se espera 'paquete.modulo:funcion')"
    return None


def resolve_entrypoint(entry: str) -> Callable[..., Any]:
    """Import the allowed module with importlib and return its function; raises ValueError for a refused entry point."""
    why = entrypoint_error(entry)
    if why:
        raise ValueError(why)
    module, name = entry.split(":", 1)
    fn = getattr(importlib.import_module(module), name)
    if not callable(fn):
        raise TypeError(f"{entry} no es invocable")
    return fn


_repo_validator: list[Any] = []  # [validar or None], filled on first use


def repo_validator() -> Callable[[dict], Any] | None:
    """validar() of the repo's own enchufe/validator_v2.py (Fables' ficha contract), loaded once by file path; None if it cannot be loaded."""
    if not _repo_validator:
        found = None
        name = "_riu_enchufe_validator_v2"
        try:
            spec = importlib.util.spec_from_file_location(name, APP_ROOT / "enchufe" / "validator_v2.py")
            module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            sys.modules[name] = module  # dataclasses in that file look their module up in sys.modules
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            found = module.validar
        except Exception:
            sys.modules.pop(name, None)
        _repo_validator.append(found)
    return _repo_validator[0]


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def check_v1(ficha: Any, folder_id: str) -> list[str]:
    """Small required-fields check for `plugin_host/v1` (always run, stdlib only). Returns error codes; an empty list means the ficha is usable."""
    if not isinstance(ficha, dict):
        return ["H01_ficha_no_es_objeto"]
    errors: list[str] = []
    ph = ficha.get("plugin_host")
    if not isinstance(ph, dict) or ph.get("schema") != SCHEMA_V1:
        return ["H02_falta_bloque_plugin_host_con_schema_" + SCHEMA_V1]
    if not ID_RE.match(folder_id) or ph.get("id") != folder_id:
        errors.append("H03_id_debe_ser_el_nombre_de_la_carpeta")
    if not isinstance(ph.get("enabled_default"), bool):
        errors.append("H04_enabled_default_bool")
    if not (isinstance(ficha.get("version"), str) and SEMVER_RE.match(ficha["version"])):
        errors.append("H05_version_semver")
    if ficha.get("categoria") not in CATEGORIES:
        errors.append("H06_categoria")
    if not isinstance(ph.get("nota_roja", ""), str):
        errors.append("H07_nota_roja_texto")
    ej = ficha.get("ejecucion")
    if not isinstance(ej, dict):
        return errors + ["H08_ejecucion_objeto"]
    if ph.get("placeholder") is True:
        if ej.get("entry_point") != "":
            errors.append("H09_placeholder_sin_entrypoint")
    else:
        why = entrypoint_error(ej.get("entry_point"))
        if why:
            errors.append("H09_entrypoint: " + why)
    actions = ej.get("allowed_actions")
    if not (isinstance(actions, list) and all(isinstance(a, str) and a for a in actions)):
        errors.append("H10_allowed_actions_lista_de_texto")
    elif ph.get("health_action") is not None and ph.get("health_action") not in actions:
        errors.append("H11_health_action_debe_estar_en_allowed_actions")
    return errors


class Plugin:
    """One registry entry. status: invalid (ficha rejected) > off (switched off) > degraded (last call failed / placeholder) > ready."""

    def __init__(self, plugin_id: str) -> None:
        self.id = plugin_id
        self.version: str | None = None
        self.category: str | None = None
        self.entrypoint: str | None = None
        self.enabled = False
        self.errors: list[str] = []
        self.last_error: str | None = None
        self.last_call_ms: int | None = None
        self.actions: tuple[str, ...] = ()
        self.health_action: str | None = None
        self.timeout_s = DEFAULT_TIMEOUT_S
        self.placeholder = False
        self.note: str | None = None

    @property
    def status(self) -> str:
        if self.errors:
            return "invalid"
        if not self.enabled:
            return "off"
        return "degraded" if (self.last_error or self.placeholder) else "ready"

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"id": self.id, "version": self.version, "category": self.category, "entrypoint": self.entrypoint, "enabled": self.enabled,
                               "status": self.status, "last_error": self.last_error, "last_call_ms": self.last_call_ms}
        if self.errors:
            out["errors"] = list(self.errors)
        if self.note:
            out["nota_roja"] = self.note
        return out


def _reply(status: str, plugin_id: str, action: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, "plugin": plugin_id, "action": action, **extra}


def default_state_path() -> Path:
    """RIU_PLUGINS_STATE, else plugins_state.json in the Router data dir (same default as the chat store: RIU_DATA_DIR, /data, ./riu_data)."""
    env = os.getenv("RIU_PLUGINS_STATE")
    if env:
        return Path(env)
    return Path(os.getenv("RIU_DATA_DIR") or (Path("/data") if os.access("/data", os.W_OK) else Path.cwd() / "riu_data")) / "plugins_state.json"


class PluginHost:
    """Registry + harness. The constructor never raises: a folder or file that cannot be read only leaves fewer plugins."""

    def __init__(self, plugins_dir: Path | str | None = None, state_path: Path | str | None = None, *, use_repo_validator: bool = True) -> None:
        self.plugins_dir = Path(plugins_dir or os.getenv("RIU_PLUGINS_DIR") or APP_ROOT / "plugins")
        self.state_path = Path(state_path) if state_path else default_state_path()
        self.validator = repo_validator() if use_repo_validator else None
        self.load_error: str | None = None
        self._plugins: dict[str, Plugin] = {}
        self._overrides: dict[str, bool] = {}
        self._inflight: dict[str, int] = {}
        self._persisted: bool | None = None  # None = no switch has been changed since start
        self._state_error: str | None = None
        self._lock = threading.RLock()  # short in-memory sections only (the gate reads it on every chat request)
        self._io_lock = threading.Lock()  # serialises state-file writes
        try:
            self.reload()
        except Exception as exc:  # never take the Router down for the host
            self.load_error = f"{type(exc).__name__}: {str(exc)[:200]}"

    @property
    def validator_name(self) -> str:
        return "enchufe/validator_v2 + plugin_host/v1" if self.validator else "plugin_host/v1 solo (validador del repo no disponible)"

    # ---- registry -------------------------------------------------------------------------------------------------
    def reload(self) -> None:
        """(Re)read the switch file and every plugins/<id>/ficha.json. Runtime counters (last_call_ms, last_error) restart."""
        overrides = self._read_state()
        self.load_error = None
        found: dict[str, Plugin] = {}
        try:
            folders = sorted(p for p in self.plugins_dir.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))
        except OSError as exc:
            self.load_error = f"no se pudo leer la carpeta de plugins ({type(exc).__name__})"
            folders = []
        for folder in folders:
            found[folder.name] = self._load_one(folder, overrides)
        with self._lock:
            self._overrides = overrides
            self._plugins = found

    def _read_state(self) -> dict[str, bool]:
        self._state_error = None
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            enabled = raw.get("enabled") if isinstance(raw, dict) else None
            if isinstance(enabled, dict):
                return {k: v for k, v in enabled.items() if isinstance(k, str) and isinstance(v, bool)}
            self._state_error = "archivo de estado con formato inesperado (se ignora)"
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            self._state_error = f"archivo de estado ilegible ({type(exc).__name__}); se ignora"
        return {}

    def _load_one(self, folder: Path, overrides: dict[str, bool]) -> Plugin:
        p = Plugin(folder.name)
        ficha: Any = None
        path = folder / "ficha.json"
        try:
            if path.stat().st_size > MAX_FICHA_BYTES:
                p.errors = ["H00_ficha_demasiado_grande"]
            else:
                ficha = json.loads(path.read_text(encoding="utf-8"))
                p.errors = check_v1(ficha, folder.name)
        except FileNotFoundError:
            p.errors = ["H00_sin_ficha_json"]
        except (OSError, ValueError) as exc:
            p.errors = [f"H00_ficha_ilegible: {type(exc).__name__}"]
        if not p.errors and self.validator is not None:
            try:
                verdict = self.validator(ficha)
                p.errors = [str(e) for e in verdict.errores] if not verdict.valido else []
            except Exception as exc:
                p.errors = [f"H99_el_validador_fallo: {type(exc).__name__}"]
        if isinstance(ficha, dict):  # best effort for display, also when invalid
            ph = ficha.get("plugin_host") if isinstance(ficha.get("plugin_host"), dict) else {}
            ej = ficha.get("ejecucion") if isinstance(ficha.get("ejecucion"), dict) else {}
            lim = ficha.get("seguridad", {}).get("limites", {}) if isinstance(ficha.get("seguridad"), dict) else {}
            p.version, p.category = _str_or_none(ficha.get("version")), _str_or_none(ficha.get("categoria"))
            p.entrypoint = _str_or_none(ej.get("entry_point")) or None
            p.note = _str_or_none(ph.get("nota_roja")) or None
            p.placeholder = ph.get("placeholder") is True
            p.health_action = _str_or_none(ph.get("health_action"))
            if isinstance(ej.get("allowed_actions"), list):
                p.actions = tuple(a for a in ej["allowed_actions"] if isinstance(a, str))
            ms = lim.get("timeout_ms") if isinstance(lim, dict) else None
            if isinstance(ms, (int, float)) and not isinstance(ms, bool) and math.isfinite(ms) and ms > 0:
                p.timeout_s = min(ms / 1000.0, MAX_TIMEOUT_S)
            p.enabled = overrides.get(p.id, ph.get("enabled_default") is True)
        else:
            p.enabled = overrides.get(p.id, False)
        if p.errors:
            p.last_error = "; ".join(p.errors)[:500]
        elif p.placeholder:
            p.last_error = PLACEHOLDER_ERROR
        return p

    def list_plugins(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._plugins[k].to_dict() for k in sorted(self._plugins)]

    def get(self, plugin_id: str) -> dict[str, Any] | None:
        with self._lock:
            p = self._plugins.get(plugin_id)
            return p.to_dict() if p else None

    def gate_open(self, plugin_id: str) -> bool:
        """False only when the plugin exists, has a valid ficha and is switched off. Unknown or invalid plugins leave the gate open (fail-open)."""
        with self._lock:
            p = self._plugins.get(plugin_id)
            return p is None or p.status != "off"

    # ---- on/off switch ----------------------------------------------------------------------------------------------
    def state_info(self) -> dict[str, Any]:
        """persisted: True/False = whether the last switch change reached the file (False: it lives in memory only); None = nothing changed yet."""
        return {"persisted": self._persisted, "error": self._state_error}

    def set_enabled(self, plugin_id: str, enabled: bool) -> dict[str, Any] | None:
        """Switch a plugin on/off and try to save it. Returns the plugin record, or None if the id is unknown. Saving failures never raise."""
        with self._io_lock:
            with self._lock:
                p = self._plugins.get(plugin_id)
                if p is None:
                    return None
                p.enabled = bool(enabled)
                self._overrides[plugin_id] = p.enabled
                text = json.dumps({"schema": STATE_SCHEMA, "enabled": self._overrides}, sort_keys=True, indent=2)
            try:
                self.state_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.state_path.with_name(self.state_path.name + ".tmp")
                tmp.write_text(text, encoding="utf-8")
                os.replace(tmp, self.state_path)
                self._persisted, self._state_error = True, None
            except (OSError, ValueError) as exc:
                self._persisted = False
                self._state_error = f"no se pudo guardar el estado ({type(exc).__name__}); el interruptor vive solo en memoria"
        return self.get(plugin_id)

    # ---- the harness ------------------------------------------------------------------------------------------------
    def call(self, plugin_id: str, action: str, payload: dict[str, Any] | None = None, timeout_s: float | None = None) -> dict[str, Any]:
        """Run `action` of a plugin: its entry point is called as fn(action, payload_dict) in a daemon thread and waited for at most `timeout_s`
        (default: the ficha's seguridad.limites.timeout_ms, else 5 s; never more than 120 s). Never raises. Returns {"status": "ok", "result": ...,
        "ms": n}, {"status": "degraded", "reason": ...} (failure, timeout, invalid ficha, refused entry point or action) or {"status": "off", ...}."""
        try:
            return self._call(plugin_id, action, payload, timeout_s)
        except Exception as exc:  # the harness itself must not raise either
            return _reply("degraded", str(plugin_id), str(action), reason=f"fallo interno del host: {type(exc).__name__}")

    def _call(self, plugin_id: str, action: str, payload: dict[str, Any] | None, timeout_s: float | None) -> dict[str, Any]:
        with self._lock:
            p = self._plugins.get(plugin_id)
            if p is None:
                return _reply("degraded", plugin_id, action, reason="plugin desconocido")
            if p.errors:
                return _reply("degraded", plugin_id, action, reason="ficha invalida: " + "; ".join(p.errors)[:300])
            if not p.enabled:
                return _reply("off", plugin_id, action, reason="plugin apagado")
            if p.placeholder:
                return _reply("degraded", plugin_id, action, reason=PLACEHOLDER_ERROR)
            if action not in p.actions:
                return _reply("degraded", plugin_id, action, reason="accion no permitida por la ficha")
            entry = p.entrypoint or ""
            if payload is not None and not isinstance(payload, dict):
                return _reply("degraded", plugin_id, action, reason="payload debe ser un objeto JSON o None")
            limit = p.timeout_s
            if isinstance(timeout_s, (int, float)) and not isinstance(timeout_s, bool) and math.isfinite(timeout_s) and timeout_s > 0:
                limit = timeout_s
            limit = min(limit, MAX_TIMEOUT_S)
            why = entrypoint_error(entry)  # already checked at load time; checked again right before the import
            if why:
                return _reply("degraded", plugin_id, action, reason=why)
            if self._inflight.get(plugin_id, 0) >= MAX_INFLIGHT:
                return _reply("degraded", plugin_id, action, reason=f"ya hay {MAX_INFLIGHT} llamadas en curso (posiblemente colgadas)")
            self._inflight[plugin_id] = self._inflight.get(plugin_id, 0) + 1
        box: dict[str, Any] = {}
        done = threading.Event()

        def run() -> None:
            try:
                res = resolve_entrypoint(entry)(action, dict(payload) if payload else {})
                if inspect.iscoroutine(res):
                    res.close()
                    raise TypeError("entrypoint async no soportado (debe ser una funcion normal)")
                box["ok"] = res
            except BaseException as exc:  # only this worker thread is affected
                box["err"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            finally:
                with self._lock:
                    self._inflight[plugin_id] = max(0, self._inflight.get(plugin_id, 1) - 1)
                done.set()

        t0 = time.perf_counter()
        try:
            threading.Thread(target=run, daemon=True, name=f"plugin-{plugin_id}").start()
        except Exception as exc:
            with self._lock:
                self._inflight[plugin_id] = max(0, self._inflight.get(plugin_id, 1) - 1)
            return _reply("degraded", plugin_id, action, reason=f"no se pudo lanzar la llamada: {type(exc).__name__}")
        finished = done.wait(limit)
        ms = int((time.perf_counter() - t0) * 1000)
        if finished and "ok" in box:
            error = None
        else:
            error = box.get("err") if finished else f"timeout: sin respuesta en {limit:g} s"
        with self._lock:
            p.last_call_ms, p.last_error = ms, error
        if error is not None:
            return _reply("degraded", plugin_id, action, reason=error, ms=ms)
        return _reply("ok", plugin_id, action, result=box["ok"], ms=ms)

    def health(self, plugin_id: str) -> dict[str, Any] | None:
        """Result of the plugin's `health_action` (from its ficha) through call(); None when the plugin has none or is unknown."""
        with self._lock:
            p = self._plugins.get(plugin_id)
            action = p.health_action if p else None
        if not action:
            return None
        out = self.call(plugin_id, action)
        return {"status": out["status"], "ms": out.get("ms"), "reason": out.get("reason")}


_host: PluginHost | None = None
_host_lock = threading.Lock()


def get_host() -> PluginHost:
    """The process-wide host, created on first use."""
    global _host
    with _host_lock:
        if _host is None:
            _host = PluginHost()
        return _host


def set_host(host: PluginHost | None) -> None:
    """Replace (or clear) the process-wide host; used by tests."""
    global _host
    with _host_lock:
        _host = host

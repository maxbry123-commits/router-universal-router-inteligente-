"""agent_state.py — Estado ON/OFF, historial y memoria persistente POR AGENTE.

FIX (MINIMAX 2F) — el selector de agentes del chat no tenia interruptor: el
registro declaraba `status` pero NADIE lo consumia, no existia memoria por
agente y el historial del chat vivia solo en el navegador (se perdia al
recargar). Este modulo es la UNICA fuente de verdad del estado de cada agente.

Diseno (fail-closed, sin dependencias externas):
  · Nada de SQLite: se usa el sistema de ficheros, porque el Space no
    garantiza el modulo `sqlite3` y el almacenamiento debe funcionar igual.
  · Un directorio por agente: `state/agents/<agente>/`
      - `state.json`   -> {"enabled": bool, "updated_at": ISO}
      - `history.jsonl`-> un turno por linea (append-only, como la bitacora)
      - `memory.json`  -> pares clave/valor (memoria persistente del agente)
  · `AGENT_STATE_DIR` permite cambiar la raiz (tests, Spaces).
  · Si una escritura falla, se devuelve el error real: nunca un OK falso.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_STATE_SUBDIR = Path("state") / "agents"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def state_root() -> Path:
    env = os.getenv("AGENT_STATE_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return (_repo_root() / DEFAULT_STATE_SUBDIR).resolve()


def agent_dir(agent_name: str) -> Path:
    safe = "".join(ch for ch in agent_name if ch.isalnum() or ch in ("-", "_", "."))
    if not safe:
        raise ValueError(f"nombre de agente invalido: {agent_name!r}")
    return state_root() / safe


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"estado ilegible {path}: {exc}") from exc


def _write_json(path: Path, payload: Any) -> Dict[str, Any]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except OSError as exc:
        raise RuntimeError(f"no se pudo escribir {path}: {exc}") from exc
    return payload


# --------------------------------------------------------------------------
# ON / OFF
# --------------------------------------------------------------------------
def default_enabled(agent_name: str, registry: Optional[Dict[str, Any]] = None) -> bool:
    """Valor por defecto: el del registro central (`enabled`), si no, True."""
    if registry is None:
        try:
            from router_llm_hf.agent_router import load_registry
            registry = load_registry()
        except Exception:
            registry = {}
    agent = (registry.get("agents") or {}).get(agent_name) or {}
    if "enabled" in agent:
        return bool(agent.get("enabled"))
    return str(agent.get("status", "active")).lower() == "active"


def is_enabled(agent_name: str, registry: Optional[Dict[str, Any]] = None) -> bool:
    """Estado real del agente: el interruptor si existe, el registro si no."""
    path = agent_dir(agent_name) / "state.json"
    data = _read_json(path, None)
    if isinstance(data, dict) and "enabled" in data:
        return bool(data.get("enabled"))
    return default_enabled(agent_name, registry)


def set_enabled(agent_name: str, enabled: bool, reason: str = "") -> Dict[str, Any]:
    """Enciende o apaga un agente. Devuelve el estado real ya escrito."""
    payload = {
        "enabled": bool(enabled),
        "updated_at": _now(),
        "reason": reason or "",
        "agent": agent_name,
    }
    _write_json(agent_dir(agent_name) / "state.json", payload)
    return payload


def toggle(agent_name: str, enabled: Optional[bool] = None) -> Dict[str, Any]:
    """Alterna el interruptor si `enabled` es None; si no, lo fija."""
    target = (not is_enabled(agent_name)) if enabled is None else bool(enabled)
    return set_enabled(agent_name, target)


def list_state(registry: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
    """Estado de TODOS los agentes del registro (con interruptor y contadores)."""
    if registry is None:
        try:
            from router_llm_hf.agent_router import load_registry
            registry = load_registry()
        except Exception:
            registry = {}
    out: Dict[str, Dict[str, Any]] = {}
    for name, cfg in (registry.get("agents") or {}).items():
        out[name] = {
            "enabled": is_enabled(name, registry),
            "default_enabled": bool(cfg.get("enabled", str(cfg.get("status", "active")).lower() == "active")),
            "history_count": history_count(name),
            "memory_keys": sorted(memory_keys(name)),
        }
    return out


# --------------------------------------------------------------------------
# HISTORIAL (append-only)
# --------------------------------------------------------------------------
def append_turn(agent_name: str, role: str, content: str,
                meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Anade un turno al historial del agente (append-only)."""
    entry = {
        "ts": _now(),
        "agent": agent_name,
        "role": role or "user",
        "content": content or "",
        "meta": meta or {},
    }
    path = agent_dir(agent_name) / "history.jsonl"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError as exc:
        raise RuntimeError(f"no se pudo guardar el turno de {agent_name}: {exc}") from exc
    return entry


def get_history(agent_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Ultimos turnos del agente (mas recientes primero)."""
    path = agent_dir(agent_name) / "history.jsonl"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise RuntimeError(f"historial ilegible de {agent_name}: {exc}") from exc
    out: List[Dict[str, Any]] = []
    for line in lines[-max(1, int(limit or 50)):]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    out.reverse()
    return out


def history_count(agent_name: str) -> int:
    path = agent_dir(agent_name) / "history.jsonl"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return sum(1 for ln in fh if ln.strip())
    except (FileNotFoundError, OSError):
        return 0


# --------------------------------------------------------------------------
# MEMORIA PERSISTENTE
# --------------------------------------------------------------------------
def get_memory(agent_name: str) -> Dict[str, Any]:
    """Memoria persistente del agente (clave -> valor)."""
    data = _read_json(agent_dir(agent_name) / "memory.json", {})
    return data if isinstance(data, dict) else {}


def set_memory(agent_name: str, key: str, value: Any) -> Dict[str, Any]:
    """Guarda un valor en la memoria persistente del agente."""
    if not key:
        raise ValueError("clave de memoria vacia")
    memory = get_memory(agent_name)
    memory[key] = value
    memory["_updated_at"] = _now()
    _write_json(agent_dir(agent_name) / "memory.json", memory)
    return memory


def memory_keys(agent_name: str) -> List[str]:
    return [k for k in get_memory(agent_name) if not k.startswith("_")]


def merge_memory(agent_name: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza varias claves de memoria a la vez."""
    memory = get_memory(agent_name)
    for key, value in (patch or {}).items():
        if not key or key.startswith("_"):
            continue
        memory[key] = value
    memory["_updated_at"] = _now()
    _write_json(agent_dir(agent_name) / "memory.json", memory)
    return memory

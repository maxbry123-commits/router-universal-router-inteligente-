"""health_check.py - Probe determinista de dependencias del sistema.
Devuelve dict con 'ok' global y 'checks' por componente.
Nunca lanza excepción: todos los checks están envueltos."""
import importlib
import os
import sqlite3
from pathlib import Path


def _chk_env() -> dict:
    """Verifica que las env-vars requeridas existan."""
    required = ("ROUTER_API_KEY", "AGENT_HARNESS_URL")
    missing = [k for k in required if not os.getenv(k)]
    return {"ok": not missing, "missing": missing}


def _chk_db(path: str) -> dict:
    """Verifica que el archivo SQLite sea accesible y consultable."""
    p = Path(path)
    try:
        c = sqlite3.connect(p)
        c.execute("SELECT 1")
        c.close()
        return {"ok": True, "path": str(p)}
    except Exception as e:
        return {"ok": False, "path": str(p), "error": f"{type(e).__name__}:{e}"}


def _chk_import(mod: str) -> dict:
    """Verifica que un módulo sea importable."""
    try:
        importlib.import_module(mod)
        return {"ok": True, "module": mod}
    except Exception as e:
        return {"ok": False, "module": mod, "error": f"{type(e).__name__}:{e}"}


def _chk_dir(path: str) -> dict:
    """Verifica que un directorio exista y sea escribible."""
    p = Path(path)
    try:
        p.mkdir(parents=True, exist_ok=True)
        test = p / ".health_probe"
        test.write_text("ok", "utf-8")
        test.unlink()
        return {"ok": True, "path": str(p)}
    except Exception as e:
        return {"ok": False, "path": str(p), "error": f"{type(e).__name__}:{e}"}


def probe_all() -> dict:
    """Ejecuta todos los probes y devuelve estado global.
    'ok' = True solo si TODOS los checks pasan.
    Diseñado para /health y /capa/status."""
    checks = {
        "env": _chk_env(),
        "workspace": _chk_dir(os.getenv("WORKSPACE_ROOT", os.getcwd())),
        "cache_dir": _chk_dir(os.getenv("CACHE_DIR", "state/cache")),
        "checkpoint_dir": _chk_dir(os.getenv("CHECKPOINT_DIR", "state/checkpoints")),
        "conv_db": _chk_db(os.getenv("CONV_DB", "state/conversations.db")),
        "ltm_db": _chk_db(os.getenv("LTM_DB", "state/long_term.db")),
        "tool_registry": _chk_import("external.tools.tool_registry"),
        "context_manager": _chk_import("external.core.context_manager"),
        "semantic_cache": _chk_import("external.core.semantic_cache"),
        "conversation_store": _chk_import("external.history.conversation_store"),
        "long_term": _chk_import("external.memory.long_term"),
        "sandbox": _chk_import("router_llm_hf.sandbox"),
        "fs_tools": _chk_import("external.tools.fs_tools"),
        "shell_tool": _chk_import("external.tools.shell_tool"),
        "verify_tool": _chk_import("external.tools.verify_tool"),
    }
    ok = all(c.get("ok") for c in checks.values())
    failed = [k for k, v in checks.items() if not v.get("ok")]
    return {"ok": ok, "checks": checks, "failed": failed}


def probe_minimal() -> dict:
    """Probe rápido para /health del proxy: solo env + db + cache."""
    checks = {
        "env": _chk_env(),
        "conv_db": _chk_db(os.getenv("CONV_DB", "state/conversations.db")),
        "cache_dir": _chk_dir(os.getenv("CACHE_DIR", "state/cache")),
    }
    ok = all(c.get("ok") for c in checks.values())
    return {"ok": ok, "checks": checks}

"""Herramientas nativas para todas las fichas.

Los secretos se resuelven server-side desde el banco cifrado del Router (con
fallback a variables de entorno), nunca se devuelven al modelo ni se serializan
en prompts. Las fichas obtienen acceso al PluginHost, GitHub, Hugging Face y al
set de herramientas real ya usado por puente_chat.
"""
from __future__ import annotations

import os
from typing import Any

from integration.chat_mvp import github_tools as gh
from integration.plugin_host.host import get_host
from plugins.puente_chat import herramientas as herramientas_chat

HF_TOKEN_VARS = ("HF_CONTROL_JOBS_TOKEN", "HF_TOKEN", "HF_WRITE_TOKEN")


def _claves_banco(provider: str) -> list[str]:
    """Lee secretos solo dentro del proceso. Nunca expone refs ni valores fuera."""
    try:
        from plugins.banco.plugin import get_keys
        pares = get_keys(provider)
    except Exception:
        return []
    out: list[str] = []
    for _ref, secreto in pares:
        valor = str(secreto or "")
        if valor and valor not in out:
            out.append(valor)
    return out


def _montar_secretos_runtime() -> dict[str, bool]:
    """Hace visibles los tokens del banco al runtime/tools sin meterlos en JSON/prompts."""
    gh_keys = _claves_banco("github")
    hf_keys = _claves_banco("huggingface")
    if not os.getenv("GITHUB_TOKEN") and gh_keys:
        os.environ["GITHUB_TOKEN"] = gh_keys[0]
    if not os.getenv("HF_TOKEN") and hf_keys:
        os.environ["HF_TOKEN"] = hf_keys[0]
    return {
        "github": bool(os.getenv("GITHUB_TOKEN") or gh.accounts_from_env()),
        "huggingface": any(bool(os.getenv(v)) for v in HF_TOKEN_VARS),
    }


class HerramientasFicha:
    """Puerta unica de herramientas para FichaOS y su Harness."""

    def __init__(self) -> None:
        self._secretos = _montar_secretos_runtime()
        self.host = get_host()

    def capacidades(self) -> dict[str, Any]:
        """Manifiesto seguro: indica capacidades, nunca el valor de un token."""
        cuentas = gh.accounts_from_env()
        plugins = self.host.list_plugins()
        return {
            "plugin_host": True,
            "plugins": [
                {"id": p.get("id"), "status": p.get("status"), "enabled": bool(p.get("enabled"))}
                for p in plugins
            ],
            "tools": [t.get("function", {}).get("name") for t in herramientas_chat.TOOLS],
            "github": {
                "token_present": bool(cuentas),
                "accounts": sorted(cuentas),
                "actions": ["whoami", "list_repos", "get_file", "put_file", "github_api"],
                "secret_source": "bank_or_env",
            },
            "huggingface": {
                "token_present": any(bool(os.getenv(v)) for v in HF_TOKEN_VARS),
                "jobs_token_present": bool(os.getenv("HF_CONTROL_JOBS_TOKEN")),
                "token_envs_present": [v for v in HF_TOKEN_VARS if os.getenv(v)],
                "plugin": "hf_compute",
                "actions": ["hf_leer", "hf_escribir", "hf_api", "hf_almacenamiento"],
                "secret_source": "bank_or_env",
            },
        }

    def definiciones_modelo(self) -> list[dict[str, Any]]:
        """Schemas function-calling reales de GitHub/HF, sin secretos."""
        return list(herramientas_chat.TOOLS)

    def ejecutar_model_tool(self, nombre: str, args: dict[str, Any] | None = None) -> str:
        """Ejecuta una tool real; los tokens se quedan server-side."""
        return herramientas_chat.ejecutar(str(nombre), args or {})

    def plugin(self, plugin_id: str, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Acceso a cualquier herramienta registrada, respetando su ficha/acciones/interruptor."""
        return self.host.call(str(plugin_id), str(action), payload or {})

    def _github_token(self, account: str | None = None) -> tuple[str, str]:
        cuentas = gh.accounts_from_env()
        if not cuentas:
            raise RuntimeError("GITHUB_TOKEN_AUSENTE")
        cuenta = account or next(iter(cuentas))
        if cuenta not in cuentas:
            raise RuntimeError("GITHUB_ACCOUNT_NO_CONFIGURADA:" + str(cuenta))
        token = gh.token_for(cuenta)
        if not token:
            raise RuntimeError("GITHUB_TOKEN_AUSENTE:" + str(cuenta))
        return cuenta, token

    def github(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """GitHub real con token server-side; el token nunca forma parte del resultado."""
        p = payload or {}
        if action == "status":
            c = self.capacidades()["github"]
            return {"status": "ok" if c["token_present"] else "gap", **c}
        if action == "github_api":
            return {"status": "ok", "result": herramientas_chat.ejecutar("github_api", p)}
        cuenta, token = self._github_token(p.get("account"))
        if action == "whoami":
            result: Any = gh.whoami(token)
        elif action == "list_repos":
            result = gh.list_repos(token, per_page=int(p.get("per_page", 50)))
        elif action == "get_file":
            result = gh.get_file(token, str(p["repo"]), str(p["path"]), p.get("ref"))
        elif action == "put_file":
            result = gh.put_file(token, str(p["repo"]), str(p["path"]), str(p.get("content", "")), str(p.get("message", "ficha: update")), p.get("branch"))
        else:
            raise RuntimeError("GITHUB_ACTION_NO_PERMITIDA:" + str(action))
        return {"status": "ok", "account": cuenta, "result": result}

    def huggingface(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """HF real server-side y HF compute; nunca devuelve el token."""
        if action == "token_status":
            c = self.capacidades()["huggingface"]
            return {"status": "ok" if c["token_present"] else "gap", **c}
        if action in {"hf_leer", "hf_escribir", "hf_api", "hf_almacenamiento"}:
            return {"status": "ok", "result": herramientas_chat.ejecutar(action, payload or {})}
        return self.plugin("hf_compute", action, payload or {})

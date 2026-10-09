"""Herramientas nativas para todas las fichas.

Los secretos viven solo en el proceso/entorno del Router. Nunca se devuelven al
modelo ni se serializan en prompts. Las fichas obtienen acceso al PluginHost,
GitHub y Hugging Face mediante funciones Python controladas.
"""
from __future__ import annotations

import os
from typing import Any

from integration.chat_mvp import github_tools as gh
from integration.plugin_host.host import get_host

HF_TOKEN_VARS = ("HF_CONTROL_JOBS_TOKEN", "HF_TOKEN", "HF_WRITE_TOKEN")


class HerramientasFicha:
    """Puerta unica de herramientas para FichaOS y su Harness."""

    def __init__(self) -> None:
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
            "github": {
                "token_present": bool(cuentas),
                "accounts": sorted(cuentas),
                "actions": ["whoami", "list_repos", "get_file", "put_file"],
            },
            "huggingface": {
                "token_present": any(bool(os.getenv(v)) for v in HF_TOKEN_VARS),
                "jobs_token_present": bool(os.getenv("HF_CONTROL_JOBS_TOKEN")),
                "token_envs_present": [v for v in HF_TOKEN_VARS if os.getenv(v)],
                "plugin": "hf_compute",
            },
        }

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
        """HF compute a traves del PluginHost; otros plugins HF se invocan con plugin()."""
        if action == "token_status":
            c = self.capacidades()["huggingface"]
            return {"status": "ok" if c["token_present"] else "gap", **c}
        return self.plugin("hf_compute", action, payload or {})

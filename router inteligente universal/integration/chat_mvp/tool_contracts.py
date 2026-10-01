"""T11-H — typed tool contracts para Hermes/OpenClaw.

Adapters finos: NO copian motores. Cada tool apunta a la ruta real verificada
del motor en el repo; la invocación produce receipt/evidence y pasa por la
verificación de permisos mínimos del contrato. Hermes/OpenClaw no pueden
bypassear Sheriff: las tools de escritura exigen scope dentro de permissions.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

TOOLS: dict[str, dict] = {
    "download_extract": {
        "engine": "router inteligente universal/scripts/extract_guardian_repair_20260903.py",
        "kind": "extract", "tools_allowed": ["filesystem"],
        "permissions": {"read_paths": ["router inteligente universal/Componente open soure router inteligente universal/archives/"],
                        "write_paths": ["router inteligente universal/Componente open soure router inteligente universal/"]},
    },
    "search": {
        "engine": "chat router/11-EVIDENCIA/buscadores.py",
        "kind": "search", "tools_allowed": ["filesystem", "network"],
        "permissions": {"read_paths": ["chat router/"], "write_paths": []},
    },
    "fables_plug": {
        "engine": "router inteligente universal/integration/chat_mvp/fables_adapter.py",
        "kind": "adapter", "tools_allowed": ["filesystem"],
        "permissions": {"read_paths": ["router inteligente universal/enchufe/"], "write_paths": []},
    },
    "rdc_download": {
        "engine": "router inteligente universal/Componentes del Router/router inteligente software/componentes todos/scripts/research_download_router.py",
        "kind": "download", "tools_allowed": ["filesystem", "network"],
        "permissions": {"read_paths": ["router inteligente universal/Componentes del Router/"],
                        "write_paths": ["router inteligente universal/Componente open soure router inteligente universal/"]},
    },
    "deepseek_harness": {
        "engine": "router inteligente universal/deepseek-harness-router/DOWNLOAD_EXTRACT_MANIFEST.json",
        "kind": "harness", "tools_allowed": ["filesystem"],
        "permissions": {"read_paths": ["router inteligente universal/deepseek-harness-router/"], "write_paths": []},
    },
}

CALLERS = {"hermes", "openclaw"}


class ToolContractError(RuntimeError):
    pass


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_engines(root: Path | None = None) -> dict[str, str]:
    """Read-back: cada tool apunta a una ruta real; si no existe → BLOCKED."""
    root = root or ROOT
    return {name: ("VERIFIED" if (root / t["engine"]).exists() else "BLOCKED")
            for name, t in TOOLS.items()}


class ToolRegistry:
    """Registro con permisos mínimos; invocación → receipt tipado."""

    def __init__(self, root: Path | None = None):
        self.root = root or ROOT
        self.status = verify_engines(self.root)

    def contract(self, name: str) -> dict:
        tool = TOOLS.get(name)
        if tool is None:
            raise ToolContractError(f"TOOL_UNKNOWN:{name}")
        return {"tool": name, "status": self.status[name], **tool}

    def invoke(self, name: str, caller: str, args: dict,
               write_scope: tuple[str, ...] = ()) -> dict:
        contract = self.contract(name)
        if contract["status"] != "VERIFIED":
            raise ToolContractError(f"TOOL_BLOCKED:{name}")
        if caller not in CALLERS:
            raise ToolContractError(f"CALLER_UNAUTHORIZED:{caller}")
        prefixes = tuple(contract["permissions"]["write_paths"])
        for path in write_scope:
            if not any(str(path).startswith(p) for p in prefixes):
                raise ToolContractError(f"WRITE_SCOPE_DENIED:{path}")
        return {
            "receipt": f"rcpt-{_sha(name + caller + json.dumps(args, sort_keys=True))[:12]}",
            "tool": name, "caller": caller, "kind": contract["kind"],
            "engine": contract["engine"], "args_sha256": _sha(json.dumps(args, sort_keys=True)),
            "status": "DISPATCHED", "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

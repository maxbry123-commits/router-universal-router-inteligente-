"""Validated Fables v2 metadata registry for the Router chat."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import yaml

ENCHUFE = Path(__file__).resolve().parents[2] / "enchufe"
ROOT = Path(__file__).resolve().parents[3]


def _load(name: str, path: Path) -> ModuleType:
    existing = sys.modules.get(name)
    if existing is not None:
        if Path(existing.__file__).resolve() != path.resolve():
            raise RuntimeError(f"FABLES_MODULE_CONFLICT:{name}")
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"FABLES_MODULE_MISSING:{name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


contract = _load("ficha_contract_v2", next(ENCHUFE.glob("*ficha_contract_v2.py")))
validator = _load("fables_validator_v2", ENCHUFE / "validator_v2.py")
bus_module = _load("fables_universal_plugin_bus_v2", next(ENCHUFE.glob("*universal_plugin_bus_v2_integrated.py")))


class FablesCatalog:
    def __init__(self) -> None:
        self.bus = bus_module.UniversalPluginBus()
        self.seed()

    def register(self, ficha: dict) -> dict:
        try:
            verdict = validator.validar(ficha)
            if not verdict.valido:
                raise ValueError(",".join(verdict.errores))
            normalized = verdict.ficha_normalizada
            checked = contract.validar(normalized)
            if not checked.valido:
                raise ValueError(",".join(checked.errores))
            parsed = contract.dict_to_ficha(checked.ficha_normalizada)
        except (AttributeError, KeyError, TypeError) as exc:
            raise ValueError("FICHA_INVALID_STRUCTURE") from exc
        if parsed.estado not in {"draft", "testing"}:
            raise ValueError("FICHA_REQUIRES_TRIBUNAL_APPROVAL")
        if self.bus.registry.get(parsed.artifact_id) is not None:
            raise ValueError("FICHA_ALREADY_REGISTERED")
        interface = bus_module.InterfaceContract(plugin_id=parsed.artifact_id, version=parsed.version)
        native = bus_module.NativeInterface(wrapper_code="", import_path=parsed.ejecucion.entry_point)
        self.bus.registry.register(parsed.artifact_id, interface, native, "router_catalog", ficha=parsed)
        self.bus.registry.deactivate(parsed.artifact_id)
        return self.get(parsed.artifact_id)

    def get(self, artifact_id: str) -> dict | None:
        registration = self.bus.registry.get(artifact_id)
        if registration is None or registration.ficha is None:
            return None
        ficha = registration.ficha
        return {"id": registration.plugin_id, "status": registration.status.value, "version": ficha.version,
                "kind": ficha.ejecucion.kind, "entry_point": ficha.ejecucion.entry_point,
                "health": self.bus.check_plugin_health(artifact_id), "ports": {"role": ficha.contrato.rol}}

    def list(self) -> list[dict]:
        return [item for pid in sorted(self.bus.registry._plugins) if (item := self.get(pid)) is not None]

    def seed(self) -> None:
        for panel in ("chat", "archivos", "seguimiento", "canvas"):
            self.register(self._ficha(f"yaiwes.panel.{panel}", "tool", f"chat router/ui/panel-{panel}.js"))
        # Director 2026-10-03: todo se enchufa por el enchufe universal Fables (control maestro del Router 24/7)
        base = "router inteligente universal/integration/"
        for mod, path in (("banco", base + "chat_mvp/vault_bridge.py"), ("laboratorio", base + "chat_mvp/control_plane.py"),
                          ("fichas_maestras", base + "chat_mvp/control_plane.py"), ("puente_hf", base + "chat_mvp/control_plane.py"),
                          ("mcp", base + "chat_mvp/mcp_api.py"), ("memoria", "chat router/harness plugins/memoria/memoria_mcp_server.py"), ("memoria_orquestador", "chat router/memoria/agent-harness/cli_anything/memoria/memoria_cli.py"),
                          ("autoscale", base + "hf_worker_pool.py")):
            self.register(self._ficha(f"yaiwes.router.{mod}", "tool", path))
        agents_path = ROOT / "chat router/05-AGENTES/AGENTES.yaml"
        if agents_path.exists():
            data = yaml.safe_load(agents_path.read_text(encoding="utf-8"))
            for row in data["jerarquia"] + data["colmena_ingenieria"] + data["apoyo"]:
                self.register(self._ficha(f"yaiwes.agent.{row['id']}", "agent", str(agents_path)))

    @staticmethod
    def _ficha(artifact_id: str, kind: str, entry_point: str) -> dict:
        execution = {"kind": kind, "transport": "importlib", "runtime_type": "agent" if kind == "agent" else "compute",
                     "entry_point": entry_point}
        if kind == "agent":
            execution.update(max_steps=1, allowed_actions=["route"])
        return {"artifact_id": artifact_id, "version": "1.0.0", "estado": "testing",
                "contrato": {"rol": "service"}, "ejecucion": execution,
                "seguridad": {"sandbox": "process", "limites": {"timeout_ms": 5000}}}

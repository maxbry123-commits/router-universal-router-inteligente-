"""ENCHUFE GATE — aduana de la red.

Ningún conector entra a la red sin contrato válido. Mantiene la firma pública
v1.5 y, cuando una ficha declara campos v2.0, delega schema + invariantes al
Enchufe Universal v2 recuperado en el code root.

Fuente REUSE v1.5:
Documentos proyectos router inteligente universal/lote 1 documentos proyecto/2📌🔌ROUTER_UNIVERSAL_RED_CONEXIONES.md
Fuente PATCH v2.0:
Documentos proyectos router inteligente universal/lote 1 documentos proyecto/🧩🧩🔌🔌🔌FABLES CREO ESTA NUEVA VERSIÓN ENCHUFE_UNIVERSAL_v2🔌🔌🧩🧩🧩 enchufe para la fichas 🏗️🏗️🏗️🏗️✅✅✅✅.md
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

RE_ARTIFACT = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
RE_HASH = re.compile(r"^sha256:[a-f0-9]{64}$")
KINDS = {"code", "llm", "db", "api", "tool", "agent"}
TRANSPORTS = {"stdio", "importlib", "http", "sdk", "prompt", "mcp"}
SANDBOX = {"container", "process", "none"}
V2_MARKERS = {
    "categoria",
    "etapa",
    "perfiles",
    "repeticion",
    "repite_en",
    "activacion",
    "presupuesto",
    "telemetria",
    "evidencia",
    "failover",
    "salud",
    "firma",
    "trazas",
}


@dataclass(frozen=True)
class VeredictoGate:
    valido: bool
    errores: tuple[str, ...] = ()


def _es_v2(c: dict) -> bool:
    """Detecta ficha v2 sin romper fichas v1.5 existentes."""
    return bool(V2_MARKERS.intersection(c)) or c.get("ejecucion", {}).get("kind") == "agent"


def _validar_v2(c: dict) -> tuple[str, ...]:
    """Delega schema e invariantes; no duplica el contrato v2 dentro del Gate."""
    root = Path(__file__).resolve().parents[1]
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)

    try:
        from domain.schemas.enchufe_v2 import EnchufeV2
        from enchufe.validator_v2 import validar

        EnchufeV2.model_validate(c)
    except Exception as exc:  # fail-closed en frontera de conexión
        return (f"v2_schema_invalido:{type(exc).__name__}",)

    verdict = validar(c)
    return tuple(f"v2:{error}" for error in verdict.errores)


def validar_contrato_conexion(c: dict) -> VeredictoGate:
    """Chequeos duros antes de registrar un nodo en la red.

    La ruta v1.5 conserva exactamente la validación histórica. Las fichas que
    declaran semántica v2 pasan además por EnchufeV2 + validator_v2.
    """
    e: list[str] = []
    if not RE_ARTIFACT.match(c.get("artifact_id", "")):
        e.append("artifact_id_invalido")
    if c.get("estado") not in {"active", "testing"}:
        e.append(f"estado_no_conectable:{c.get('estado')}")
    if c.get("estado") == "active" and not RE_HASH.match(c.get("contract_hash", "")):
        e.append("active_requiere_hash_real")
    ej = c.get("ejecucion", {})
    if ej.get("kind") not in KINDS:
        e.append("kind_invalido")
    if ej.get("transport") not in TRANSPORTS:
        e.append("transport_invalido")
    seg = c.get("seguridad", {})
    if seg.get("sandbox") not in SANDBOX:
        e.append("sandbox_invalido")
    lim = seg.get("limites", {})
    if not (isinstance(lim.get("timeout_ms"), int) and lim["timeout_ms"] > 0):
        e.append("timeout_ms_requerido")
    if lim.get("deadline_ms", 0) < lim.get("timeout_ms", 1):
        e.append("deadline_menor_que_timeout")
    rol = c.get("contrato", {}).get("rol")
    if rol == "source" and c["contrato"].get("consume") is not None:
        e.append("source_no_consume")
    if rol == "sink" and c["contrato"].get("expone") is not None:
        e.append("sink_no_expone")
    if rol == "transform" and (
        not c["contrato"].get("consume") or not c["contrato"].get("expone")
    ):
        e.append("transform_requiere_ambos")

    if not e and _es_v2(c):
        e.extend(_validar_v2(c))

    return VeredictoGate(valido=not e, errores=tuple(e))


def datatype_de(io: dict | None) -> str:
    if not io:
        return ""
    dt = io.get("datatype", {})
    return f"{dt.get('family','')}.{dt.get('type','')}.v{dt.get('version',0)}"

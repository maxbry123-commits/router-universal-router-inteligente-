"""Pydantic v2 structural schema for Enchufe Universal v2.0.

Source of truth:
Documentos proyectos router inteligente universal/lote 1 documentos proyecto/
🧩🧩🔌🔌🔌FABLES CREO ESTA NUEVA VERSIÓN ENCHUFE_UNIVERSAL_v2🔌🔌🧩🧩🧩 enchufe para la fichas 🏗️🏗️🏗️🏗️✅✅✅✅.md

This layer mirrors the JSON Schema and compatibility defaults. Behavioral
invariants remain owned by enchufe/validator_v2.py; this module must not
invent LLM behavior policy.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Nivel = Literal["n0", "n1", "n2", "n3", "n4", "n5"]


class ModeloEnchufe(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Datatype(ModeloEnchufe):
    family: str
    tipo: str = Field(alias="type")
    version: int


class IO(ModeloEnchufe):
    datatype: Datatype
    schema_uri: str | None = None


class Contrato(ModeloEnchufe):
    rol: Literal["source", "transform", "sink", "service"]
    consume: IO | None = None
    expone: IO | None = None
    input_map: dict[str, Any] = Field(default_factory=dict)
    output_map: dict[str, Any] = Field(default_factory=dict)


class Ejecucion(ModeloEnchufe):
    kind: Literal["code", "llm", "db", "api", "tool", "agent"]
    transport: Literal["stdio", "importlib", "http", "sdk", "prompt", "mcp"]
    runtime_type: Literal["compute", "hybrid", "llm", "agent"]
    llm_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    idempotente: bool = False
    entry_point: str = ""


class Perfil(ModeloEnchufe):
    habilitada: bool = True
    iteraciones: int = Field(default=1, ge=1)
    simulaciones: int = Field(default=0, ge=0)
    criticas: int = Field(default=0, ge=0)
    muestras_k: int = Field(default=1, ge=1)


def perfiles_default() -> dict[Nivel, Perfil]:
    return {f"n{i}": Perfil() for i in range(6)}  # type: ignore[misc]


class Repeticion(ModeloEnchufe):
    max: int = Field(default=1, ge=1)
    condicion: Literal[
        "nunca",
        "si_falla_verificacion",
        "si_memoria_cambia",
        "siempre_por_nivel",
    ] = "nunca"
    backoff: str = "1000*2^n+rand(0,1000)"


class Activacion(ModeloEnchufe):
    eventos: list[str] = Field(default_factory=list)
    wake_words: list[str] = Field(default_factory=list)
    condicion: str = ""


class PresupuestoNivel(ModeloEnchufe):
    max_tokens: int | None = None
    max_ms: int | None = None
    max_costo_usd: float | None = None


class Telemetria(ModeloEnchufe):
    metricas: list[str] = Field(
        default_factory=lambda: ["tiempo", "errores", "reintentos"]
    )
    span_otel: bool = True


class Evidencia(ModeloEnchufe):
    produce: list[
        Literal["L1_static", "L2_build", "L3_runtime", "L4_feature"]
    ] = Field(default_factory=list)
    destino: str = "runtime/evidence/"


class Failover(ModeloEnchufe):
    sustituible_por: list[str] = Field(default_factory=list)
    compensacion: str = ""


class Limites(ModeloEnchufe):
    timeout_ms: int = Field(gt=0)
    deadline_ms: int | None = None
    max_memoria_mb: int | None = None


class Seguridad(ModeloEnchufe):
    sandbox: Literal["container", "process", "none"]
    permisos: list[str] = Field(default_factory=list)
    limites: Limites


class Salud(ModeloEnchufe):
    metodo: Literal["ping", "http", "exec", "ninguno"] = "ping"
    heartbeat_interval_s: int = 30


class Firma(ModeloEnchufe):
    gpg_key_id: str = "PENDIENTE"
    revocation_ref: str = "contracts/revocation_list.json"


class Trazas(ModeloEnchufe):
    task_id_requerido: Literal[True] = True
    trace_id_requerido: Literal[True] = True


class EnchufeV2(ModeloEnchufe):
    artifact_id: str = Field(pattern=r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    estado: Literal["draft", "testing", "active", "deprecated", "revoked"]
    contract_hash: str | None = Field(
        default=None, pattern=r"^sha256:[a-f0-9]{64}$"
    )

    # Defaults preserve the source contract's explicit v1.5 -> v2.0 compatibility.
    categoria: Literal["pipeline", "transversal", "acelerador"] = "pipeline"
    etapa: Literal["E", "P", "S", "T", "A"] = "P"

    contrato: Contrato
    ejecucion: Ejecucion
    perfiles: dict[Nivel, Perfil] = Field(default_factory=perfiles_default)
    repeticion: Repeticion = Field(default_factory=Repeticion)
    repite_en: list[
        Literal[
            "INPUT",
            "CONTEXT_LOADER",
            "EXEC_STATE",
            "ARTIFACT_ENGINE",
            "MEMORY",
            "MASTER_JSON",
            "CONTEXT_MANAGER",
        ]
    ] = Field(default_factory=list)
    activacion: Activacion = Field(default_factory=Activacion)
    presupuesto: dict[Nivel, PresupuestoNivel] = Field(default_factory=dict)
    telemetria: Telemetria = Field(default_factory=Telemetria)
    evidencia: Evidencia = Field(default_factory=Evidencia)
    failover: Failover = Field(default_factory=Failover)
    seguridad: Seguridad
    salud: Salud = Field(default_factory=Salud)
    firma: Firma = Field(default_factory=Firma)
    trazas: Trazas | None = None

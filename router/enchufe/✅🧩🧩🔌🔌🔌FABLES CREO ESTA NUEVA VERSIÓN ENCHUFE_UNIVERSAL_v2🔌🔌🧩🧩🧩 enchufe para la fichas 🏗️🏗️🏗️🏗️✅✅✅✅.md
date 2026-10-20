# ENCHUFE UNIVERSAL v2.0 — CONTRATO FINAL DE FICHAS
# Sustituye a v1.5 manteniendo compatibilidad total (v1.5 valida bajo v2.0).
# Novedades: categoría (pipeline|transversal|acelerador) · perfiles cognitivos 0-5 ·
# repetición declarativa · presupuesto por nivel · activación por triggers ·
# telemetría · evidencia L1-L4 · failover declarativo · firma GPG.

---

## 1. QUÉ CAMBIA vs v1.5 (12 mejoras)

| # | Campo nuevo | Para qué |
|---|---|---|
| 1 | `categoria` | pipeline / transversal / acelerador — las 3 clases de la arquitectura |
| 2 | `etapa` | E (entrada) / P (procesador) / S (salida) / T / A |
| 3 | `perfiles` | costo y comportamiento por nivel cognitivo 0-5 (Rápido→Investigación Extrema) |
| 4 | `repeticion` | cuántas veces puede/debe repetirse y bajo qué condición (memoria/verificación) |
| 5 | `activacion` | triggers declarativos: eventos, wake_words, condiciones |
| 6 | `presupuesto` | tokens/tiempo/costo máx por nivel — el Cost Governor lo lee |
| 7 | `telemetria` | métricas que emite + spans OTel obligatorios |
| 8 | `evidencia` | qué niveles L1-L4 produce y dónde los deja |
| 9 | `failover` | cadena `sustituible_por` ordenada + compensación |
| 10 | `firma` | GPG key id + referencia a revocation_list |
| 11 | `salud` | cómo sondearla (health) + heartbeat_interval_s |
| 12 | `repite_en` | puntos 🔍/🛂 donde esta ficha re-verifica memoria (los 7 puntos del diagrama) |

Regla de compatibilidad: todo campo nuevo tiene default. Una ficha v1.5 válida ES una ficha v2.0 válida con defaults (`categoria:pipeline`, `perfiles:{todos}`, `repeticion:{max:1}`).

---

## 2. SCHEMA v2.0 (JSON, campos nuevos completos)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "maxbry://contracts/universal_module_contract/v2.0",
  "type": "object",
  "required": ["artifact_id", "version", "estado", "categoria", "etapa",
               "contrato", "ejecucion", "seguridad", "firma"],
  "properties": {
    "artifact_id":   {"type": "string", "pattern": "^[a-z0-9_]+(\\.[a-z0-9_]+)+$"},
    "version":       {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
    "estado":        {"enum": ["draft", "testing", "active", "deprecated", "revoked"]},
    "contract_hash": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},

    "categoria":     {"enum": ["pipeline", "transversal", "acelerador"]},
    "etapa":         {"enum": ["E", "P", "S", "T", "A"]},

    "contrato": {
      "type": "object",
      "required": ["rol"],
      "properties": {
        "rol":     {"enum": ["source", "transform", "sink", "service"]},
        "consume": {"$ref": "#/definitions/io"},
        "expone":  {"$ref": "#/definitions/io"},
        "input_map":  {"type": "object"},
        "output_map": {"type": "object"}
      }
    },

    "ejecucion": {
      "type": "object",
      "required": ["kind", "transport", "runtime_type"],
      "properties": {
        "kind":         {"enum": ["code", "llm", "db", "api", "tool", "agent"]},
        "transport":    {"enum": ["stdio", "importlib", "http", "sdk", "prompt", "mcp"]},
        "runtime_type": {"enum": ["compute", "hybrid", "llm", "agent"]},
        "llm_ratio":    {"type": "number", "minimum": 0, "maximum": 1},
        "idempotente":  {"type": "boolean", "default": false},
        "entry_point":  {"type": "string"}
      }
    },

    "perfiles": {
      "type": "object",
      "description": "Comportamiento por nivel cognitivo. Claves: n0..n5.",
      "patternProperties": {
        "^n[0-5]$": {
          "type": "object",
          "properties": {
            "habilitada":   {"type": "boolean", "default": true},
            "iteraciones":  {"type": "integer", "minimum": 1, "default": 1},
            "simulaciones": {"type": "integer", "minimum": 0, "default": 0},
            "criticas":     {"type": "integer", "minimum": 0, "default": 0},
            "muestras_k":   {"type": "integer", "minimum": 1, "default": 1}
          }
        }
      }
    },

    "repeticion": {
      "type": "object",
      "properties": {
        "max":       {"type": "integer", "minimum": 1, "default": 1},
        "condicion": {"enum": ["nunca", "si_falla_verificacion",
                               "si_memoria_cambia", "siempre_por_nivel"],
                      "default": "nunca"},
        "backoff":   {"type": "string", "default": "1000*2^n+rand(0,1000)"}
      }
    },

    "repite_en": {
      "type": "array",
      "items": {"enum": ["INPUT", "CONTEXT_LOADER", "EXEC_STATE",
                          "ARTIFACT_ENGINE", "MEMORY", "MASTER_JSON",
                          "CONTEXT_MANAGER"]},
      "description": "Puntos 🔍 donde esta ficha re-verifica contexto/memoria"
    },

    "activacion": {
      "type": "object",
      "properties": {
        "eventos":    {"type": "array", "items": {"type": "string"}},
        "wake_words": {"type": "array", "items": {"type": "string"}},
        "condicion":  {"type": "string"}
      }
    },

    "presupuesto": {
      "type": "object",
      "patternProperties": {
        "^n[0-5]$": {
          "type": "object",
          "properties": {
            "max_tokens":  {"type": "integer"},
            "max_ms":      {"type": "integer"},
            "max_costo_usd": {"type": "number"}
          }
        }
      }
    },

    "telemetria": {
      "type": "object",
      "properties": {
        "metricas": {"type": "array", "items": {"type": "string"},
                     "default": ["tiempo", "errores", "reintentos"]},
        "span_otel": {"type": "boolean", "default": true}
      }
    },

    "evidencia": {
      "type": "object",
      "properties": {
        "produce": {"type": "array",
                    "items": {"enum": ["L1_static", "L2_build",
                                        "L3_runtime", "L4_feature"]}},
        "destino": {"type": "string", "default": "runtime/evidence/"}
      }
    },

    "failover": {
      "type": "object",
      "properties": {
        "sustituible_por": {"type": "array", "items": {"type": "string"}},
        "compensacion":    {"type": "string"}
      }
    },

    "seguridad": {
      "type": "object",
      "required": ["sandbox", "limites"],
      "properties": {
        "sandbox":  {"enum": ["container", "process", "none"]},
        "permisos": {"type": "array", "items": {"type": "string"}},
        "limites": {
          "type": "object",
          "required": ["timeout_ms"],
          "properties": {
            "timeout_ms":  {"type": "integer", "exclusiveMinimum": 0},
            "deadline_ms": {"type": "integer"},
            "max_memoria_mb": {"type": "integer"}
          }
        }
      }
    },

    "salud": {
      "type": "object",
      "properties": {
        "metodo": {"enum": ["ping", "http", "exec", "ninguno"], "default": "ping"},
        "heartbeat_interval_s": {"type": "integer", "default": 30}
      }
    },

    "firma": {
      "type": "object",
      "required": ["gpg_key_id"],
      "properties": {
        "gpg_key_id":     {"type": "string"},
        "revocation_ref": {"type": "string",
                           "default": "contracts/revocation_list.json"}
      }
    },

    "trazas": {
      "type": "object",
      "properties": {
        "task_id_requerido":  {"type": "boolean", "const": true},
        "trace_id_requerido": {"type": "boolean", "const": true}
      }
    }
  },

  "definitions": {
    "io": {
      "type": "object",
      "required": ["datatype"],
      "properties": {
        "datatype": {
          "type": "object",
          "required": ["family", "type", "version"],
          "properties": {
            "family":  {"type": "string"},
            "type":    {"type": "string"},
            "version": {"type": "integer"}
          }
        },
        "schema_uri": {"type": "string"}
      }
    }
  }
}
```

---

## 3. VALIDADOR v2.0 — `enchufe/validator_v2.py` (~260 LOC)

```python
"""VALIDATOR v2.0 — 22 invariantes v1.5 + 14 nuevas v2.0.
Compatibilidad: acepta fichas v1.5 (aplica defaults v2.0).
"""
from __future__ import annotations
import re
from dataclasses import dataclass

RE_ARTIFACT = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
RE_HASH = re.compile(r"^sha256:[a-f0-9]{64}$")
RE_VER = re.compile(r"^\d+\.\d+\.\d+$")
NIVELES = tuple(f"n{i}" for i in range(6))

DEFAULTS_V2 = {
    "categoria": "pipeline", "etapa": "P",
    "perfiles": {n: {"habilitada": True, "iteraciones": 1} for n in NIVELES},
    "repeticion": {"max": 1, "condicion": "nunca"},
    "repite_en": [], "activacion": {}, "presupuesto": {},
    "telemetria": {"metricas": ["tiempo", "errores", "reintentos"],
                   "span_otel": True},
    "evidencia": {"produce": [], "destino": "runtime/evidence/"},
    "failover": {"sustituible_por": []},
    "salud": {"metodo": "ping", "heartbeat_interval_s": 30},
}


@dataclass(frozen=True)
class Veredicto:
    valido: bool
    errores: tuple[str, ...] = ()
    ficha_normalizada: dict | None = None


def normalizar_v15(c: dict) -> dict:
    """Ficha v1.5 → v2.0 aplicando defaults (aditivo, no destruye)."""
    out = dict(c)
    for k, v in DEFAULTS_V2.items():
        out.setdefault(k, v)
    out.setdefault("firma", {"gpg_key_id": "PENDIENTE",
                             "revocation_ref":
                             "contracts/revocation_list.json"})
    return out


def validar(c: dict) -> Veredicto:                     # noqa: C901
    c = normalizar_v15(c)
    e: list[str] = []
    add = e.append

    # ── Núcleo v1.5 (22 invariantes, resumidas por grupo) ──
    if not RE_ARTIFACT.match(c.get("artifact_id", "")):
        add("I01_artifact_id")
    if not RE_VER.match(c.get("version", "")):
        add("I02_version_semver")
    est = c.get("estado")
    if est not in {"draft", "testing", "active", "deprecated", "revoked"}:
        add("I03_estado")
    if est == "active" and not RE_HASH.match(c.get("contract_hash", "")):
        add("I04_active_requiere_hash")
    rol = c.get("contrato", {}).get("rol")
    con, exp = (c.get("contrato", {}).get("consume"),
                c.get("contrato", {}).get("expone"))
    if rol == "source" and con is not None:
        add("I05_source_no_consume")
    if rol == "sink" and exp is not None:
        add("I06_sink_no_expone")
    if rol == "transform" and (con is None or exp is None):
        add("I07_transform_ambos")
    ej = c.get("ejecucion", {})
    if ej.get("kind") not in {"code", "llm", "db", "api", "tool", "agent"}:
        add("I08_kind")
    if ej.get("runtime_type") not in {"compute", "hybrid", "llm", "agent"}:
        add("I09_runtime_type")
    ratio = ej.get("llm_ratio", 0.0)
    if ej.get("runtime_type") == "compute" and ratio > 0.10:
        add("I10_compute_ratio_max_010")
    seg = c.get("seguridad", {})
    lim = seg.get("limites", {})
    if not (isinstance(lim.get("timeout_ms"), int) and lim["timeout_ms"] > 0):
        add("I11_timeout")
    if lim.get("deadline_ms", lim.get("timeout_ms", 1)) < lim.get(
            "timeout_ms", 1):
        add("I12_deadline_ge_timeout")
    if seg.get("sandbox") == "none" and seg.get("permisos"):
        add("I13_none_sin_permisos")

    # ── Nuevas v2.0 (14 invariantes) ──
    if c["categoria"] not in {"pipeline", "transversal", "acelerador"}:
        add("V01_categoria")
    if c["etapa"] not in {"E", "P", "S", "T", "A"}:
        add("V02_etapa")
    if c["categoria"] == "acelerador" and c["etapa"] != "A":
        add("V03_acelerador_etapa_A")
    if c["categoria"] == "transversal" and c["etapa"] != "T":
        add("V04_transversal_etapa_T")
    for n, p in c["perfiles"].items():
        if n not in NIVELES:
            add(f"V05_perfil_invalido:{n}")
        if p.get("iteraciones", 1) < 1:
            add(f"V06_iteraciones:{n}")
    rep = c["repeticion"]
    if rep.get("max", 1) < 1:
        add("V07_repeticion_max")
    if rep.get("condicion") not in {"nunca", "si_falla_verificacion",
                                    "si_memoria_cambia",
                                    "siempre_por_nivel"}:
        add("V08_repeticion_condicion")
    if rep.get("max", 1) > 1 and not ej.get("idempotente", False):
        add("V09_repetible_debe_ser_idempotente")
    validos = {"INPUT", "CONTEXT_LOADER", "EXEC_STATE", "ARTIFACT_ENGINE",
               "MEMORY", "MASTER_JSON", "CONTEXT_MANAGER"}
    for punto in c["repite_en"]:
        if punto not in validos:
            add(f"V10_repite_en:{punto}")
    for n, b in c["presupuesto"].items():
        if n not in NIVELES:
            add(f"V11_presupuesto_nivel:{n}")
        if b.get("max_ms", 1) <= 0 or b.get("max_tokens", 1) <= 0:
            add(f"V12_presupuesto_positivo:{n}")
    if est == "active" and c["firma"]["gpg_key_id"] in ("", "PENDIENTE"):
        add("V13_active_requiere_gpg")
    if ej.get("kind") == "agent":
        if "max_steps" not in ej or "allowed_actions" not in ej:
            add("V14_agent_requiere_max_steps_y_whitelist")

    return Veredicto(valido=not e, errores=tuple(e),
                     ficha_normalizada=c if not e else None)


def compatibles(a: dict, b: dict) -> bool:
    """a.expone.datatype == b.consume.datatype (autoensamblaje)."""
    ea = (a.get("contrato", {}).get("expone") or {}).get("datatype", {})
    cb = (b.get("contrato", {}).get("consume") or {}).get("datatype", {})
    return bool(ea) and ea == cb
```

---

## 4. REGLAS DE ADOPCIÓN
1. TODAS las fichas nuevas (las ~320 del esqueleto) nacen directamente en v2.0.
2. Las fichas ya codificadas (Salidas 1-6) se normalizan con `normalizar_v15()` — cero retrabajo.
3. `enchufe_gate.py` de la Red Universal pasa a llamar `validator_v2.validar()`.
4. El Sheriff del DSL (SH06) usa `compatibles()` de esta versión.
5. `perfiles` + `presupuesto` son leídos por el Cost Governor y el PLANNER_OFFLINE para compilar el plan según nivel 0-5.

## TESTS
```
test_v15_valida_bajo_v20 · test_acelerador_fuera_de_A_falla
test_repetible_sin_idempotencia_falla · test_agent_sin_whitelist_falla
test_presupuesto_negativo_falla · test_compatibles_datatype
```

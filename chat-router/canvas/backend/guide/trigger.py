"""trigger.py · N4-C · GUÍA VIVA — ACCIÓN → TRIGGER `yaiwes.trigger.v1` + RUNNER.

El motor gramatical descompone y clasifica la ACCIÓN; este módulo la convierte en
un CONTRATO `yaiwes.trigger.v1` validado contra el contrato real del repo
(`chat-router/Loop cola wachdog/Loop/nct_loop/trigger_contract.py`, leído en la
fase RESEARCH) y en un DESCRIPTOR RUNNER con fases/pasos independientes y el
semáforo de estado del runtime: STOP | HANDOFF | CONTINUE.

REGLAS DURAS (contrato real, no negociables)
  · Sólo campos TOP_FIELDS. CUALQUIER campo fuera de TOP_FIELDS ⇒ `UNKNOWN_FIELD`.
  · `steps` entre 1 y 32. `execution.max_model_calls` ∈ {0, 1} y debe coincidir
    con el número de pasos `kind == "MODEL"`.
  · `input_block_verbatim` literal + `source.sha256` (sha256 de los bytes del literal)
    + `source_anchor_ref` real cuando se declara `original_document_sha256`.
  · Handlers admitidos por el runtime: MODEL, TOOL, CHECK (kind de paso).
    Si la acción exige un handler que el runtime NO conecta (CODE, HUMAN) ⇒
    `UNBOUND_UNTIL_HANDLER_IS_CONNECTED` y bloqueo (STOP). Nunca una cadena
    vacía MODEL → inspect_workspace → CHECK.
  · Semáforo: STOP (bloqueo) · HANDOFF (pide aprobación humana) · CONTINUE.

Uso:
    from trigger import build_trigger, validate_trigger
    r = build_trigger("añadir reintento con backoff", input_block_verbatim=texto,
                      document_ref="source:guia/N4-C", section_id="N4C")
    validate_trigger(r["contrato"])   # levanta TriggerError si el contrato es inválido
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import PurePosixPath
from typing import Any


def _load_grammar():
    """Carga el motor gramatical hermano (mismo directorio) sin tocar sys.path."""
    try:
        import grammar as _g  # noqa: PLC0415
        return _g
    except ImportError:
        import importlib.util
        import pathlib

        spec = importlib.util.spec_from_file_location(
            "grammar", pathlib.Path(__file__).resolve().parent / "grammar.py"
        )
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


_GRAMMAR = _load_grammar()
decompose = _GRAMMAR.decompose
decompose_verbose = _GRAMMAR.decompose_verbose

SCHEMA = "yaiwes.trigger.v1"
RUNNER_SCHEMA = "yaiwes.guide.runner.v1"

# ── Contrato real (espejo de trigger_contract.py del repo) ───────────────────
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
REF_RE = re.compile(r"^ancla:[A-Za-z0-9_.-]{1,120}$")
ROLES = {"arquitecto", "auditor", "ejecutor_codigo", "frontend", "refactor_revision"}
CATEGORIES = {
    "constitucion", "auditoria", "investigacion", "arquitectura", "componentes",
    "backend", "frontend", "canvas", "verificacion", "refactoria", "github",
    "continuidad",
}
PREDICATES = {
    "always", "source_exists", "file_type_is", "requires_frontend",
    "requires_backend", "component_present", "prior_status", "approved_scope",
}
STEP_KINDS = {"MODEL", "TOOL", "CHECK"}
READ_OPS = {"inspect_workspace", "read_text", "verify_exists", "verify_contains"}
WRITE_OPS = {"create_directory", "write_text"}
OPS = READ_OPS | WRITE_OPS | {"finish"}
TOP_FIELDS = {
    "schema", "id", "loop_id", "name", "category", "enabled", "note", "role",
    "source", "input_block_verbatim", "attachments", "depends_on", "when",
    "execution", "steps", "outputs", "on_pass", "on_not_applicable", "on_blocked",
}
REQUIRED_TOP_FIELDS = TOP_FIELDS - {
    "note", "attachments", "depends_on", "when", "on_not_applicable",
    "on_pass", "on_blocked",
}
TRANSITIONS = {
    "on_pass": "NEXT",
    "on_not_applicable": "RECORD_AND_NEXT",
    "on_blocked": "FLAG_AND_STOP_DEPENDENTS",
}

# ── Semáforo del runtime ─────────────────────────────────────────────────────
SEMAPHORE = ("STOP", "HANDOFF", "CONTINUE")
HANDLER_RUNTIME = {"MODEL", "TOOL", "CHECK"}
HANDLER_SOLICITADOS = {"MODEL", "TOOL", "CODE", "HUMAN"}

# Mapeo de la vocabulario del INPUT BLOCK (node_id, condition, inputs, ...) al
# contrato real del repo (id, when, source/steps.args, ...).
MAPA_CAMPOS = {
    "node_id": "id",
    "depends_on": "depends_on",
    "condition": "when",
    "inputs": "source + steps[].args",
    "tool/handler": "steps[].kind + steps[].tool",
    "outputs": "outputs.required_fields",
    "acceptance": "outputs.acceptance",
    "input_block_verbatim": "input_block_verbatim",
    "source.sha256": "source.sha256",
    "source_anchor_ref": "source.source_anchor_ref",
}


class TriggerError(ValueError):
    """Error de contrato con código estable (FAIL_CLOSED)."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(code + ((": " + detail) if detail else ""))
        self.code = code
        self.detail = detail


# ── Utilidades ───────────────────────────────────────────────────────────────
def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fields(obj: Any, allowed: set[str], required: set[str], label: str) -> None:
    if not isinstance(obj, dict):
        raise TriggerError("BAD_TYPE", label)
    missing = required - obj.keys()
    if missing:
        raise TriggerError("MISSING_FIELD", label + " " + ",".join(sorted(missing)))
    unknown = obj.keys() - allowed
    if unknown:
        raise TriggerError("UNKNOWN_FIELD", label + " " + ",".join(sorted(unknown)))


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise TriggerError("BAD_ID", label)
    return value


def _safe_path(p: Any) -> str:
    if not isinstance(p, str) or not p or p.startswith("/") or "\\" in p or "\x00" in p:
        raise TriggerError("PATH_OUT_OF_SCOPE", str(p)[:90])
    path = PurePosixPath(p)
    if ":" in p or any(x in ("..", ".") for x in p.split("/")):
        raise TriggerError("PATH_OUT_OF_SCOPE", p[:90])
    return str(path)


# ── Validador (espejo de validate_contract del repo) ─────────────────────────
def validate_trigger(contract: Any, *, source_bytes: bytes | None = None) -> dict:
    """Valida un contrato `yaiwes.trigger.v1`. Devuelve el contrato o lanza TriggerError."""
    _fields(contract, TOP_FIELDS, REQUIRED_TOP_FIELDS, "trigger")
    if contract["schema"] != SCHEMA:
        raise TriggerError("UNKNOWN_SCHEMA")
    _id(contract["id"], "id")
    _id(contract["loop_id"], "loop_id")
    if not isinstance(contract["name"], str) or not contract["name"].strip() or len(contract["name"]) > 150:
        raise TriggerError("BAD_NAME")
    if contract["category"] not in CATEGORIES or contract["role"] not in ROLES:
        raise TriggerError("BAD_CATEGORY_OR_ROLE")
    if type(contract["enabled"]) is not bool:
        raise TriggerError("BAD_ENABLED")
    if not isinstance(contract.get("note", ""), str) or len(contract.get("note", "")) > 1200:
        raise TriggerError("BAD_NOTE")
    text = contract["input_block_verbatim"]
    if not isinstance(text, str) or not text:
        raise TriggerError("MISSING_VERBATIM")
    _fields(
        contract["source"],
        {"document_ref", "section_id", "sha256", "original_document_sha256", "source_anchor_ref"},
        {"document_ref", "section_id", "sha256"},
        "source",
    )
    _id(contract["source"]["section_id"], "section_id")
    if not isinstance(contract["source"]["document_ref"], str) or not contract["source"]["document_ref"].startswith("source:"):
        raise TriggerError("SOURCE_REF_INVALID")
    if not SHA_RE.fullmatch(contract["source"]["sha256"]):
        raise TriggerError("SOURCE_SHA_INVALID")
    if contract["source"].get("original_document_sha256") is not None:
        if not isinstance(contract["source"]["original_document_sha256"], str) or not SHA_RE.fullmatch(contract["source"]["original_document_sha256"]):
            raise TriggerError("DOCUMENT_SHA_INVALID")
        ref = contract["source"].get("source_anchor_ref")
        if not isinstance(ref, str) or not REF_RE.fullmatch(ref):
            raise TriggerError("DOCUMENT_ANCHOR_REQUIRED")
    raw = text.encode("utf-8") if source_bytes is None else source_bytes
    if source_bytes is not None and raw != text.encode("utf-8"):
        raise TriggerError("VERBATIM_BYTES_CHANGED")
    if sha256(raw) != contract["source"]["sha256"]:
        raise TriggerError("SOURCE_SHA_MISMATCH")
    for key in ("attachments", "depends_on"):
        values = contract.get(key, [])
        if not isinstance(values, list) or len(values) != len(set(map(str, values))) or len(values) > 100:
            raise TriggerError("BAD_LIST", key)
        for value in values:
            if key == "attachments":
                if not isinstance(value, str) or not REF_RE.fullmatch(value):
                    raise TriggerError("BAD_ANCHOR", str(value))
            else:
                _id(value, "depends_on")
    _fields(contract.get("when", {"predicate": "always", "args": {}}), {"predicate", "args"}, {"predicate", "args"}, "when")
    cond = contract.get("when", {"predicate": "always", "args": {}})
    if cond["predicate"] not in PREDICATES or not isinstance(cond["args"], dict):
        raise TriggerError("BAD_PREDICATE")
    _fields(
        contract["execution"],
        {"operation", "tool_profile", "max_model_calls", "write_paths", "timeout_s"},
        {"operation", "tool_profile", "max_model_calls", "write_paths"},
        "execution",
    )
    ex = contract["execution"]
    if ex["operation"] not in {"analyze", "inspect_source", "apply_approved_patch", "run_approved_test", "verify_artifacts"}:
        raise TriggerError("OPERATION_UNKNOWN")
    if ex["tool_profile"] not in ("read_only", "writer_n4", "verify_only"):
        raise TriggerError("BAD_PROFILE")
    if type(ex["max_model_calls"]) is not int or ex["max_model_calls"] not in (0, 1):
        raise TriggerError("MAX_CALLS_ONE")
    if type(ex.get("timeout_s", 120)) is not int or not 1 <= ex.get("timeout_s", 120) <= 900:
        raise TriggerError("BAD_TIMEOUT")
    if not isinstance(ex["write_paths"], list) or len(ex["write_paths"]) > 30:
        raise TriggerError("BAD_WRITE_PATHS")
    for path in ex["write_paths"]:
        _safe_path(path)
    if ex["tool_profile"] != "writer_n4" and ex["write_paths"]:
        raise TriggerError("READ_ONLY_WRITE_PATHS")
    _fields(
        contract["outputs"],
        {"required_fields", "acceptance", "require_tool_receipt", "require_readback"},
        {"required_fields", "acceptance", "require_tool_receipt", "require_readback"},
        "outputs",
    )
    out = contract["outputs"]
    if not isinstance(out["required_fields"], list) or any(not isinstance(k, str) or not k for k in out["required_fields"]):
        raise TriggerError("BAD_OUTPUT_FIELDS")
    if not isinstance(out["acceptance"], list) or any(not isinstance(k, str) or not k for k in out["acceptance"]):
        raise TriggerError("BAD_ACCEPTANCE")
    if type(out["require_tool_receipt"]) is not bool or type(out["require_readback"]) is not bool:
        raise TriggerError("BAD_OUTPUT_GATES")
    steps = contract["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= 32:
        raise TriggerError("STEPS_1_32")
    seen: dict[str, dict] = {}
    model_steps = 0
    for s in steps:
        _fields(s, {"id", "kind", "depends_on", "tool", "args"}, {"id", "kind", "depends_on"}, "step")
        sid = _id(s["id"], "step.id")
        if sid in seen:
            raise TriggerError("DUPLICATE_STEP", sid)
        if s["kind"] not in STEP_KINDS:
            raise TriggerError("UNKNOWN_STEP", sid)
        if s["kind"] == "MODEL":
            model_steps += 1
        if s["kind"] == "TOOL":
            if s.get("tool") not in OPS or not isinstance(s.get("args", {}), dict):
                raise TriggerError("UNKNOWN_TOOL", sid)
            if s["tool"] in WRITE_OPS and ex["tool_profile"] != "writer_n4":
                raise TriggerError("READ_ONLY_TOOL", sid)
            if "path" in s.get("args", {}):
                _safe_path(s["args"]["path"])
        elif "tool" in s or "args" in s:
            raise TriggerError("EXTRA_STEP_FIELDS", sid)
        if not isinstance(s["depends_on"], list) or len(s["depends_on"]) != len(set(map(str, s["depends_on"]))):
            raise TriggerError("BAD_STEP_DEPENDENCIES", sid)
        seen[sid] = s
    if model_steps != ex["max_model_calls"]:
        raise TriggerError("MODEL_STEP_COUNT")
    for sid, s in seen.items():
        if any(d not in seen for d in s["depends_on"]):
            raise TriggerError("UNKNOWN_STEP_DEPENDENCY", sid)
    visiting, visited = set(), set()

    def visit(sid: str) -> None:
        if sid in visiting:
            raise TriggerError("DAG_CYCLE", sid)
        if sid in visited:
            return
        visiting.add(sid)
        for dep in seen[sid]["depends_on"]:
            visit(dep)
        visiting.discard(sid)
        visited.add(sid)

    for sid in seen:
        visit(sid)
    for key, expected in TRANSITIONS.items():
        if contract.get(key, expected) != expected:
            raise TriggerError("BAD_TRANSITIONS", key)
    return contract


# ── Construcción del trigger desde una acción ───────────────────────────────
TIPO_CATEGORY = {
    "CREACION": "refactoria",
    "ELIMINACION": "refactoria",
    "REFACTOR": "refactoria",
    "VALIDACION": "verificacion",
    "TEST": "verificacion",
    "AUDITORIA": "auditoria",
    "DEPLOY": "github",
    "CONVERSION": "backend",
    "RENDER": "frontend",
    "DOCS": "arquitectura",
    "SEGURIDAD": "auditoria",
}
TIPO_ROLE = {
    "CREACION": "ejecutor_codigo",
    "ELIMINACION": "ejecutor_codigo",
    "REFACTOR": "refactor_revision",
    "VALIDACION": "auditor",
    "TEST": "auditor",
    "AUDITORIA": "auditor",
    "DEPLOY": "ejecutor_codigo",
    "CONVERSION": "ejecutor_codigo",
    "RENDER": "frontend",
    "DOCS": "arquitecto",
    "SEGURIDAD": "auditor",
}

APROBACION_RE = re.compile(
    r"(?i)(autoriz|aprobaci|permiso|permission|approv|advertencia|warning|"
    r"credencial|secret|token|rotar|rotate|permiso)"
)


def _needs_approval(text: str) -> tuple[bool, str]:
    m = APROBACION_RE.search(text or "")
    if m:
        return True, m.group(0)
    return False, ""


def _slug(text: str, fallback: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9]+", "_", (text or "").strip().lower()).strip("_")
    raw = raw[:60] or fallback
    if not re.match(r"^[A-Za-z0-9_]", raw):
        raw = fallback + "_" + raw
    return raw


def build_trigger(
    action_text: str,
    *,
    input_block_verbatim: str,
    document_ref: str,
    section_id: str,
    target_path: str | None = None,
    guide_catalog_path: str | None = None,
    loop_id: str = "guia_viva",
    trigger_id: str | None = None,
    handler: str = "MODEL",
    apply_patch: bool = False,
    source_anchor_ref: str | None = None,
    original_document_sha256: str | None = None,
    timeout_s: int = 120,
    gui_actions: list[dict] | None = None,
    match_contains: str | None = None,
) -> dict:
    """Construye el contrato `yaiwes.trigger.v1` + el descriptor RUNNER de una acción.

    Devuelve:
        {"contrato": dict|None, "runner": dict, "estado": str, "semaforo": str,
         "gramatica": dict, "validado": bool, "error": str|None}
    """
    handler = (handler or "MODEL").upper()
    grammar_out = decompose_verbose(action_text)
    needs_approval, approval_hint = _needs_approval(action_text)

    # 1 · Handler solicitado por la acción vs handlers que conecta el runtime.
    unbound_reason = ""
    if handler not in HANDLER_SOLICITADOS:
        unbound_reason = f"HANDLER_{handler}_NO_SOPORTADO"
    elif handler not in HANDLER_RUNTIME:
        unbound_reason = f"UNBOUND_UNTIL_HANDLER_IS_CONNECTED:{handler}"

    catalog_path = guide_catalog_path or "chat-router/canvas/backend/guide/guide_actions.json"
    write_path = target_path if apply_patch else None

    # 2 · Fases del pipeline → pasos independientes del contrato.
    steps: list[dict] = []
    pasos: list[dict] = []

    def add_step(step_id: str, kind: str, depends_on: list[str], tool: str | None = None,
                 args: dict | None = None, fase: str = "", semaforo: str = "CONTINUE",
                 nota: str = "") -> None:
        st: dict[str, Any] = {"id": step_id, "kind": kind, "depends_on": list(depends_on)}
        if kind == "TOOL":
            st["tool"] = tool
            st["args"] = dict(args or {})
        steps.append(st)
        pasos.append({
            "indice": len(pasos) + 1,
            "fase": fase,
            "paso": step_id,
            "kind": kind,
            "tool": tool,
            "dependencias": list(depends_on),
            "independiente": not depends_on,
            "semaforo": semaforo,
            "nota": nota,
        })

    add_step("f1_descompresion", "TOOL", [], "read_text" if target_path else "inspect_workspace",
             {"path": target_path} if target_path else {},
             fase="descompresion", nota="se lee el código objetivo y se sigue su flujo paso a paso")
    add_step("f2_gramatica", "CHECK", ["f1_descompresion"], fase="gramatica",
             nota="descomposición gramatical determinista (sujeto + verbo + adjetivo)")
    if handler == "MODEL":
        add_step("f3_descubrimiento", "MODEL", ["f2_gramatica"], fase="discovery",
                 nota="la IA convierte la evidencia descubierta en la opción de código")
        model_calls = 1
    else:
        add_step("f3_descubrimiento", "TOOL", ["f2_gramatica"], "read_text",
                 {"path": catalog_path}, fase="discovery",
                 nota="el motor de descubrimiento devuelve opciones; sin llamada a modelo")
        model_calls = 0
    add_step("f4_match", "TOOL", ["f3_descubrimiento"],
             ("verify_contains" if (target_path and match_contains) else ("verify_exists" if target_path else "inspect_workspace")),
             ({"path": target_path, "contains": match_contains} if (target_path and match_contains)
              else ({"path": target_path} if target_path else {})),
             fase="match", nota="MIRROR de la acción contra el ejemplo de la guía")
    add_step("f5_autorizacion", "CHECK", ["f4_match"], fase="autorizacion",
             semaforo="HANDOFF" if needs_approval else "CONTINUE",
             nota=("la acción habla de autorización/advertencia: se escala a aprobación"
                   if needs_approval else "no se detecta indicio de autorización"))
    if apply_patch and target_path:
        add_step("f6_disparo", "TOOL", ["f5_autorizacion"], "write_text",
                 {"path": target_path, "text_from_model": "patch"}, fase="trigger",
                 nota="el RUNNER escribe SÓLO las líneas seleccionadas por match.py")
    add_step("f7_cierre", "TOOL", [], "finish", {}, fase="fases",
             nota="cierre del trigger con recibos")

    effective = [s for s in steps if s["kind"] in ("MODEL", "TOOL")]
    if len(effective) < 2:
        unbound_reason = unbound_reason or "CADENA_VACIA_MODEL_INSPECT_CHECK"

    tool_profile = "writer_n4" if (apply_patch and target_path) else "read_only"
    operation = "apply_approved_patch" if tool_profile == "writer_n4" else "analyze"
    write_paths = [target_path] if tool_profile == "writer_n4" and target_path else []

    source: dict[str, Any] = {
        "document_ref": document_ref,
        "section_id": section_id,
        "sha256": sha256(input_block_verbatim.encode("utf-8")),
    }
    if original_document_sha256:
        source["original_document_sha256"] = original_document_sha256
    if source_anchor_ref:
        source["source_anchor_ref"] = source_anchor_ref

    contract = {
        "schema": SCHEMA,
        "id": trigger_id or _slug(action_text, "accion"),
        "loop_id": loop_id,
        "name": (action_text or "accion")[:150],
        "category": TIPO_CATEGORY.get(grammar_out["tipo"], "backend"),
        "enabled": True,
        "note": f"guía viva · {grammar_out['tipo']} · verbo={grammar_out['verbo'] or '-'}",
        "role": TIPO_ROLE.get(grammar_out["tipo"], "ejecutor_codigo"),
        "source": source,
        "input_block_verbatim": input_block_verbatim,
        "attachments": [source_anchor_ref] if source_anchor_ref else [],
        "depends_on": [],
        "when": {"predicate": "always", "args": {}},
        "execution": {
            "operation": operation,
            "tool_profile": tool_profile,
            "max_model_calls": model_calls,
            "write_paths": write_paths,
            "timeout_s": int(timeout_s),
        },
        "steps": steps,
        "outputs": {
            "required_fields": ["patch", "evidencia"],
            "acceptance": [
                "el parche cambia SOLO las líneas declaradas por match.py",
                "la evidencia procede de una URL verificada (o NO_EVIDENCE)",
            ],
            "require_tool_receipt": True,
            "require_readback": bool(tool_profile == "writer_n4"),
        },
        "on_pass": "NEXT",
        "on_not_applicable": "RECORD_AND_NEXT",
        "on_blocked": "FLAG_AND_STOP_DEPENDENTS",
    }

    # 3 · Estado del runtime (FAIL_CLOSED).
    validated = True
    error = None
    if unbound_reason:
        validated = False
        error = unbound_reason
        contract = None
    else:
        try:
            validate_trigger(contract, source_bytes=input_block_verbatim.encode("utf-8"))
        except TriggerError as exc:
            validated = False
            error = exc.code + ((": " + exc.detail) if exc.detail else "")

    if not validated:
        semaforo = "STOP"
        estado = "UNBOUND_UNTIL_HANDLER_IS_CONNECTED"
    elif needs_approval:
        semaforo = "HANDOFF"
        estado = "READY_ESCALADO"
    else:
        semaforo = "CONTINUE"
        estado = "READY"

    runner = {
        "schema": RUNNER_SCHEMA,
        "trigger_id": contract["id"] if contract else (trigger_id or _slug(action_text, "accion")),
        "loop_id": loop_id,
        "estado": estado,
        "semaforo": semaforo,
        "handler": {
            "tipo": handler,
            "bound": handler in HANDLER_RUNTIME,
            "permitidos_por_runtime": sorted(HANDLER_RUNTIME),
            "detalle": unbound_reason or "handler conectado por el runtime",
        },
        "bloqueo": error,
        "fases": pasos,
        "pasos_independientes": sum(1 for p in pasos if p["independiente"]),
        "escalado_aprobacion": {
            "requiere": needs_approval,
            "pista": approval_hint,
            "destino": "usuario/IA" if needs_approval else None,
        },
        "source": {
            "sha256": source["sha256"],
            "anchor_refs": ([source_anchor_ref] if source_anchor_ref else []),
        },
        "recibos": [],
        "mapa_campos_input_block": MAPA_CAMPOS,
        "gramatica": {
            "objetivo": grammar_out["objetivo"],
            "sujeto": grammar_out["sujeto"],
            "verbo": grammar_out["verbo"],
            "adjetivo": grammar_out["adjetivo"],
            "estado": grammar_out["estado"],
            "tipo": grammar_out["tipo"],
        },
    }
    if gui_actions:
        runner["acciones_guia"] = gui_actions

    return {
        "contrato": contract,
        "runner": runner,
        "estado": estado,
        "semaforo": semaforo,
        "validado": validated,
        "error": error,
        "gramatica": {
            "objetivo": grammar_out["objetivo"],
            "sujeto": grammar_out["sujeto"],
            "verbo": grammar_out["verbo"],
            "adjetivo": grammar_out["adjetivo"],
            "estado": grammar_out["estado"],
            "tipo": grammar_out["tipo"],
        },
    }


def _primary_signal(action_text: str) -> str:
    """Toma la palabra más significativa de la acción para `verify_contains`."""
    toks = [t for t in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ_]{4,}", action_text or "") if t.lower() != "para"]
    return toks[0] if toks else (action_text or "accion")[:40]


def fingerprint(contract: dict) -> str:
    """Huella determinista de un contrato (sha256 canónico)."""
    return sha256(canonical(contract))


__all__ = [
    "SCHEMA",
    "RUNNER_SCHEMA",
    "TOP_FIELDS",
    "SEMAPHORE",
    "HANDLER_RUNTIME",
    "TriggerError",
    "validate_trigger",
    "build_trigger",
    "fingerprint",
    "canonical",
    "sha256",
]

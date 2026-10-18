#!/usr/bin/env python3
"""mode_router.py - Router de modos del chat (backend). Sin dependencias externas.

Punto de entrada unico para Devin:
    routed = route_request(registry, payload)           # antes de cargar la ficha del modelo
    ficha  = routed["ficha"]                            # entregar a tu cargador/ensamblador existente
Precedencia fija: button_lock > slash_command > auto_classifier > default_mode (FAIL-CLOSED en id desconocido).
"""
from __future__ import annotations
import asyncio, hashlib, itertools, json, re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from validate_modes import validate_registry


class ModeError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


# ---------------------------------------------------------------- carga
def load_registry(path: str, strict: bool = False) -> dict:
    with open(path, encoding="utf-8") as f:
        reg = json.load(f)
    errs = validate_registry(reg, strict=strict)
    if errs:
        raise ModeError("REGISTRY_INVALID", "; ".join(errs))
    return reg


def _modes(reg: dict) -> dict:
    return {m["id"]: m for m in reg["modes"]}


# ---------------------------------------------------------------- resolucion
SLASH_RE = re.compile(r"^\s*(/[\w-]+)(?:\s+(.*))?$", re.S | re.UNICODE)


def parse_slash(reg: dict, text: str):
    """Devuelve (mode_id | 'auto' | None, texto_sin_slash)."""
    m = SLASH_RE.match(text or "")
    if not m:
        return None, text
    cmd, rest = m.group(1).lower(), (m.group(2) or "").strip()
    if cmd == reg["selector"].get("auto_slash", "/auto"):
        return "auto", rest
    for mode in reg["modes"]:
        if mode["slash"].lower() == cmd:
            return mode["id"], rest
    return None, text  # no es un slash de modo: se deja intacto (puede ser otro comando del chat)


def classify_auto(reg: dict, text: str):
    for r in sorted(reg["auto_classifier"]["rules"], key=lambda r: r["priority"]):
        if re.search(r["pattern"], text or "", re.I | re.S):
            return r["then_mode"], r["id"]
    return reg["selector"]["default_mode"], "fallback"


@dataclass
class Resolution:
    mode_id: str
    source: str
    text: str
    reason: str


def _gate_ok(reg: dict, mode: dict, source: str, text: str) -> bool:
    if not mode["autonomous_loop"]:
        return True
    g = reg["selector"]["gate"]
    if source in ("button_lock", "slash_command"):
        return True
    return any(re.match(rf"^\s*{re.escape(w)}\b", text or "") for w in g["trigger_words"])


def resolve_mode(reg: dict, text: str, mode_request: Optional[dict] = None) -> Resolution:
    modes = _modes(reg)
    mr = mode_request or {}
    req_id, src = mr.get("mode_id"), mr.get("source")
    text = text or ""

    if req_id not in (None, "auto"):
        if req_id not in modes:
            raise ModeError("UNKNOWN_MODE", f"mode_id '{req_id}' no existe en el registro")
        if src != "button":
            raise ModeError("BAD_SOURCE", "un mode_id explicito exige source='button'")
        mode_id, source, clean, reason = req_id, "button_lock", text, "boton activo"
    else:
        slash_id, rest = parse_slash(reg, text)
        if slash_id and slash_id != "auto":
            mode_id, source, clean, reason = slash_id, "slash_command", rest, "comando slash"
        else:
            if slash_id == "auto":
                text = rest
            mode_id, rule = classify_auto(reg, text)
            source = "auto_classifier" if rule != "fallback" else "default_mode"
            clean, reason = text, f"regla {rule}"

    mode = modes[mode_id]
    if mode["autonomous_loop"] and source in ("auto_classifier", "default_mode"):
        raise ModeError("AUTO_FORBIDDEN", f"{mode_id} es autonomo: solo por boton o slash")
    if not _gate_ok(reg, mode, source, clean):
        raise ModeError("GATE_FAILED", f"{mode_id} requiere disparador (boton, slash o palabra de gate)")
    return Resolution(mode_id, source, clean, reason)


# ---------------------------------------------------------------- objetivo + ficha
def validate_objective(reg: dict, obj: dict) -> list:
    sch = reg["objective_schema"]
    errs = []
    for k in sch["required"]:
        if k not in obj or obj[k] in (None, "", []):
            errs.append(f"objetivo: falta o vacio '{k}'")
    for k in sch["list_fields"]:
        v = obj.get(k)
        if v is not None and (not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v)):
            errs.append(f"objetivo: '{k}' debe ser lista de textos no vacios")
    return errs


def render_system_block(reg: dict, mode: dict, objective: Optional[dict] = None) -> str:
    L = [f"# MODO ACTIVO: {mode['label']} ({mode['id']})"]
    if objective is not None:
        errs = validate_objective(reg, objective)
        if errs:
            raise ModeError("OBJECTIVE_INVALID", "; ".join(errs))
        L += ["## OBJETIVO (fijo; se reinyecta en cada iteracion)", f"Meta: {objective['goal']}",
              "Hecho cuando: " + "; ".join(objective["done_when"]),
              "Restricciones: " + "; ".join(objective["constraints"]),
              "Fuera de alcance: " + "; ".join(objective["out_of_scope"]),
              "Entregables: " + "; ".join(objective["deliverables"])]
    if mode["autonomous_loop"] or mode["no_escalation"]:
        L += ["## REGLAS DE AUTONOMIA"] + [f"- {r}" for r in reg["autonomy_rules"]]
    L += ["## REGLAS DEL MODO"] + [f"- {r}" for r in mode["prompt_block"]]
    return "\n".join(L)


def build_ficha(reg: dict, mode_id: str, objective: Optional[dict] = None) -> dict:
    mode = _modes(reg).get(mode_id)
    if mode is None:
        raise ModeError("UNKNOWN_MODE", mode_id)
    return {
        "mode_id": mode_id,
        "base_mode": mode["base_mode"],
        "autonomous_loop": mode["autonomous_loop"],
        "reasoning": mode["reasoning"],
        "tool_choice": mode["tool_choice"],
        "tools": list(reg["tools_profiles"][mode["tools_profile"]]),
        "pipeline": mode["pipeline"],
        "research": mode["research"],
        "parallel": mode["parallel"],
        "limits": mode["limits"],
        "guards": mode["guards"],
        "termination": mode["termination"],
        "ui_thinking_toggle": reg["selector"]["ui_thinking_toggle_policy"],  # mode_wins
        "prompt_import_slot": mode["prompt_import_slot"],
        "system_block": render_system_block(reg, mode, objective),
    }


def route_request(reg: dict, payload: dict, objective: Optional[dict] = None,
                  emit: Optional[Callable[[str, dict], None]] = None) -> dict:
    """payload: {'message': str, 'mode_request': {'mode_id': ..., 'source': 'button'|'auto'}, ...}"""
    res = resolve_mode(reg, payload.get("message", ""), payload.get("mode_request"))
    ficha = build_ficha(reg, res.mode_id, objective)
    out = {"mode_id": res.mode_id, "source": res.source, "reason": res.reason,
           "message": res.text, "ficha": ficha}
    if emit:
        emit("mode_resolved", {"mode_id": res.mode_id, "source": res.source, "reason": res.reason})
    return out


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- inmutables (anti auto-sabotaje)
def _get(d: dict, path: str):
    cur: Any = d
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def immutable_violations(old: dict, new: dict) -> list:
    """Usalo en m08 antes de aceptar un cambio al registro: lista de secciones inmutables alteradas."""
    return [p for p in old["immutable_sections"] if _get(old, p) != _get(new, p)]


# ---------------------------------------------------------------- pool paralelo + cola + watchdog
@dataclass
class PoolTask:
    id: str
    fn: Callable[[], Awaitable[Any]]
    priority: int = 100          # menor numero = mas prioridad
    retries: int = 1
    timeout_s: float = 300.0     # watchdog: estancamiento


@dataclass(order=True)
class _Item:
    priority: int
    seq: int
    task: PoolTask = field(compare=False)
    attempts: int = field(default=0, compare=False)


class ParallelPool:
    """Hasta max_running en ejecucion; el excedente espera en cola por prioridad."""

    def __init__(self, max_running: int = 10, queue_max: int = 1000, hard_cap: int = 10,
                 on_event: Optional[Callable[[str, dict], None]] = None):
        if max_running > hard_cap:
            raise ModeError("CAP_EXCEEDED", f"max_running {max_running} > tope {hard_cap}")
        self.max_running, self.queue_max, self.on_event = max_running, queue_max, on_event
        self.peak_running = 0

    def _emit(self, name: str, **data):
        if self.on_event:
            self.on_event(name, data)

    async def run(self, tasks: list) -> dict:
        if not tasks:
            return {}
        if len(tasks) > self.max_running + self.queue_max:
            raise ModeError("QUEUE_FULL", f"{len(tasks)} tareas > {self.max_running}+{self.queue_max}")
        q: asyncio.PriorityQueue = asyncio.PriorityQueue()
        seq = itertools.count()
        results: dict = {}
        state = {"running": 0, "pending": len(tasks)}
        for i, t in enumerate(tasks):
            q.put_nowait(_Item(t.priority, next(seq), t))
            if i >= self.max_running:
                self._emit("task_queued", id=t.id)

        async def worker():
            while True:
                if state["pending"] == 0:
                    return
                try:
                    item = await asyncio.wait_for(q.get(), timeout=0.05)
                except asyncio.TimeoutError:
                    continue
                t = item.task
                state["running"] += 1
                self.peak_running = max(self.peak_running, state["running"])
                self._emit("task_started", id=t.id, attempt=item.attempts + 1)
                err, val = None, None
                try:
                    val = await asyncio.wait_for(t.fn(), t.timeout_s)
                except asyncio.TimeoutError:
                    err = "timeout"
                    self._emit("watchdog_stall", id=t.id)
                except Exception as ex:  # noqa: BLE001
                    err = repr(ex)
                finally:
                    state["running"] -= 1
                if err is None:
                    results[t.id] = {"status": "passed", "value": val, "attempts": item.attempts + 1}
                    state["pending"] -= 1
                elif item.attempts < t.retries:
                    item.attempts += 1
                    q.put_nowait(item)
                else:
                    results[t.id] = {"status": "blocked_with_evidence", "error": err, "attempts": item.attempts + 1}
                    self._emit("task_blocked", id=t.id, error=err)
                    state["pending"] -= 1

        await asyncio.gather(*[worker() for _ in range(min(self.max_running, len(tasks)))])
        return results


if __name__ == "__main__":
    import sys
    reg = load_registry(sys.argv[1] if len(sys.argv) > 1 else "modes_registry.json")
    msg = " ".join(sys.argv[2:]) or "hola"
    r = route_request(reg, {"message": msg, "mode_request": {"mode_id": "auto", "source": "auto"}})
    print(json.dumps({k: r[k] for k in ("mode_id", "source", "reason", "message")}, ensure_ascii=False))

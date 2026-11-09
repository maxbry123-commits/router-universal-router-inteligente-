"""prompt_layouts.py - La gobernanza va en 'system'; la tarea va sola en 'user'.
Si el modelo igual responde 'entendido', se detecta y se reintenta con otro layout (con evidencia)."""
import hashlib, re

NO_ACK_RULE = ("Tu respuesta es el RESULTADO de la tarea del usuario. Prohibido responder con acuse de recibo "
               "('entendido', 'listo', 'esperando instrucciones') o resumir estas reglas.")

ACK_PATTERNS = [
    r"(?i)\bentendido\b", r"(?i)esperando\s+(tus\s+|sus\s+|las\s+)?instrucciones",
    r"(?i)no se (proporcion[oó]|recibi[oó]|incluy[oó]).{0,40}(tarea|bloque|instrucci)",
    r"(?i)\b(listo|preparado)\s+para\s+(comenzar|empezar|recibir|ayudar)",
    r"(?i)por favor\s+(proporciona|indica|env[ií]a|comparte).{0,40}(tarea|instrucci)",
    r"(?i)cu[aá]l es (la|tu) tarea", r"(?i)\bunderstood\b", r"(?i)awaiting (your )?(instructions|task)",
    r"(?i)no task (was )?provided",
]
DEFAULT_ORDER = ["A_system_user", "B_tarea_etiquetada", "C_gobernanza_minima", "D_solo_tarea"]


class LayoutError(Exception):
    pass


def compact(text: str, max_chars: int = 1200) -> str:
    out, n = [], 0
    for ln in text.splitlines():
        if n + len(ln) + 1 > max_chars:
            break
        out.append(ln); n += len(ln) + 1
    return "\n".join(out)


def assemble(layout: str, gobernanza: str, tarea: str) -> list:
    if layout == "A_system_user":
        return [{"role": "system", "content": gobernanza + "\n\n" + NO_ACK_RULE},
                {"role": "user", "content": tarea}]
    if layout == "B_tarea_etiquetada":
        return [{"role": "system", "content": gobernanza + "\n\n" + NO_ACK_RULE},
                {"role": "user", "content": f"<tarea>\n{tarea}\n</tarea>\nEjecuta <tarea> ahora y entrega el resultado."}]
    if layout == "C_gobernanza_minima":
        return [{"role": "system", "content": compact(gobernanza) + "\n\n" + NO_ACK_RULE},
                {"role": "user", "content": tarea}]
    if layout == "D_solo_tarea":     # ultimo recurso: sin gobernanza; el resultado se valida con checks deterministas
        return [{"role": "user", "content": tarea}]
    raise LayoutError(f"layout desconocido {layout}")


def assert_task_present(messages: list, tarea: str) -> str:
    """FAIL-CLOSED: la tarea debe ir textual en el ultimo mensaje 'user'. Devuelve su sha256 para la traza."""
    users = [m for m in messages if m.get("role") == "user"]
    if not users or tarea not in users[-1]["content"]:
        raise LayoutError("la tarea NO esta en el ultimo mensaje user (problema de cableado, no del modelo)")
    return hashlib.sha256(tarea.encode("utf-8")).hexdigest()[:12]


def is_ack_only(text: str, tool_calls=None, min_chars: int = 400):
    if tool_calls:
        return False, "hay tool_calls"
    t = (text or "").strip()
    if not t:
        return True, "respuesta vacia"
    if len(t) < min_chars:
        for p in ACK_PATTERNS:
            if re.search(p, t):
                return True, f"acuse de recibo (patron {p[:24]}...)"
    return False, "ok"


def run_with_fallback(call_model, gobernanza: str, tarea: str, layouts=DEFAULT_ORDER, min_chars: int = 400) -> dict:
    """call_model(messages) -> {'text': str, 'tool_calls': list}. Usalo solo en modos de ejecucion (no en /rapido)."""
    attempts = []
    for lay in layouts:
        msgs = assemble(lay, gobernanza, tarea)
        sha = assert_task_present(msgs, tarea)
        resp = call_model(msgs) or {}
        ack, why = is_ack_only(resp.get("text", ""), resp.get("tool_calls"), min_chars)
        attempts.append({"layout": lay, "task_sha": sha, "ack": ack, "why": why})
        if not ack:
            return {"ok": True, "layout": lay, "response": resp, "attempts": attempts}
    return {"ok": False, "layout": None, "response": None, "attempts": attempts, "state": "blocked_with_evidence"}

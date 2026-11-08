import hashlib
import re
from research_engine import ResearchEngine

class GapBlockedError(Exception):
    pass

class GapUnresolvedError(Exception):
    pass

BLOCKING = ("API_KEY_MISSING", "PERMISSION_DENIED", "BILLING_REQUIRED", "NO_INTERNET")

def detect_gap(text: str):
    m = re.search(r"GAP(?:_DETECTADO)?:\s*(.+)", text, re.IGNORECASE)
    return m.group(1).strip() if m else None

def _key(text: str) -> str:
    return hashlib.sha256(text.lower().encode("utf-8")).hexdigest()

class GapResolutionLoop:
    def __init__(self, engine: ResearchEngine, max_rounds: int = 3):
        self.engine = engine
        self.max_rounds = max_rounds

    async def run(self, model_call_fn, initial_prompt: str, format_ok=None) -> str:
        prompt = initial_prompt
        seen_gaps = set()
        seen_urls = set()
        for _ in range(self.max_rounds):
            out = await model_call_fn(prompt)
            gap = detect_gap(out)
            bad_format = format_ok is not None and not format_ok(out)
            if gap is None and not bad_format:
                return out
            if gap and any(b in gap.upper() for b in BLOCKING):
                raise GapBlockedError(gap)
            trigger = gap or initial_prompt[:120]
            if gap:
                k = _key(gap)
                if k in seen_gaps:
                    raise GapUnresolvedError("mismo gap repetido sin evidencia nueva")
                seen_gaps.add(k)
            res = await self.engine.run(trigger, seen_urls)
            if res["status"] != "OK":
                raise GapUnresolvedError(f"investigacion sin resultado util: {res['status']}")
            seen_urls.update(res["sources"])
            prompt = (f"{res['pack']}\n\n[INSTRUCCION]\n{initial_prompt[:500]}\n"
                      f"Resuelve: {trigger}. Si aun falta informacion responde GAP: <descripcion>; "
                      f"si no, devuelve la salida pedida.")
        raise GapUnresolvedError("rondas agotadas con el gap abierto")

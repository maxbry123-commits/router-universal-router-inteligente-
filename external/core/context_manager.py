"""context_manager.py - Compactación de contexto al 75% de ventana.
Determinista: mismo input -> mismo output. Sin LLM para resumir."""
import os
from typing import List, Dict

MAX_TOKENS = int(os.getenv("CTX_MAX_TOKENS", "8000"))
COMPACT_AT = float(os.getenv("CTX_COMPACT_RATIO", "0.75"))


def _estimate_tokens(text: str) -> int:
    """Estimación conservadora: 1 token ≈ 4 chars."""
    return max(1, len(text) // 4)


class ContextManager:
    def __init__(self, system: str = "", max_tokens: int = MAX_TOKENS):
        self.system = system
        self.max_tokens = max_tokens
        self.messages: List[Dict] = []

    def _total(self) -> int:
        base = _estimate_tokens(self.system)
        return base + sum(_estimate_tokens(m.get("content", ""))
                          for m in self.messages)

    def add(self, role: str, content: str) -> None:
        """Añade mensaje. Si cruza el umbral, compacta automáticamente."""
        self.messages.append({"role": role, "content": content})
        if self._total() > self.max_tokens * COMPACT_AT:
            self._compact()

    def _compact(self) -> None:
        """Resume el head (determinista) y conserva el tail intacto."""
        keep_tail = max(2, len(self.messages) // 4)
        head = self.messages[:-keep_tail]
        tail = self.messages[-keep_tail:]
        if not head:
            return
        user_bits = [m["content"][:60].replace("\n", " ")
                     for m in head if m["role"] == "user"]
        summary = "Summary: " + "; ".join(user_bits)[:500]
        self.messages = [{"role": "system", "content": summary}] + tail

    def snapshot(self) -> List[Dict]:
        """Devuelve la lista completa incluyendo system inicial."""
        base = [{"role": "system", "content": self.system}] if self.system else []
        return base + list(self.messages)

    def reset(self) -> None:
        self.messages = []

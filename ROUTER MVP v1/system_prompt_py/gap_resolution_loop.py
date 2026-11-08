import re
from typing import Callable, Optional, Awaitable
from web_search_tool import WebSearchTool

class GapBlockedError(Exception):
    pass

class GapResolutionLoop:
    BLOCKING_KEYWORDS = ["API_KEY_MISSING", "PERMISSION_DENIED", "BILLING_REQUIRED", "NO_INTERNET"]

    def __init__(self, max_rounds: int = 5, search_tool: Optional[WebSearchTool] = None):
        self.max_rounds = max_rounds
        self.search_tool = search_tool or WebSearchTool()
        self.history = []

    def detect_gap(self, model_output: str) -> Optional[str]:
        match = re.search(r"GAP(?:_DETECTADO)?:\s*(.+)", model_output, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def is_blocking(self, gap: str) -> bool:
        return any(kw in gap.upper() for kw in self.BLOCKING_KEYWORDS)

    async def resolve(self, gap: str) -> str:
        self.history.append({"gap": gap, "round": len(self.history) + 1})
        return await self.search_tool.search(gap)

    async def run_with_loop(self, model_call_fn: Callable[[str], Awaitable[str]], initial_prompt: str) -> str:
        current_prompt = initial_prompt
        for round_num in range(1, self.max_rounds + 1):
            model_output = await model_call_fn(current_prompt)
            gap = self.detect_gap(model_output)
            if not gap:
                return model_output
            if self.is_blocking(gap):
                raise GapBlockedError(f"Gap bloqueante: {gap}")
            context = await self.resolve(gap)
            current_prompt = f"[CONTEXTO RECUPERADO]\n{context}\n\n[INSTRUCCIÓN]\nResuelve el gap: {gap}\nSi falta info, reporta GAP_DETECTADO. Si no, TERMINADO."
        return model_output

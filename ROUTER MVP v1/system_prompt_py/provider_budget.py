import asyncio
from typing import Dict

class ProviderBudget:
    def __init__(self):
        self.budgets = {"groq": 8, "nvidia": 12}
        self.usage: Dict[str, Dict[str, int]] = {"groq": {}, "nvidia": {}}
        self._lock = asyncio.Lock()

    async def can_use(self, provider: str, session_id: str) -> bool:
        async with self._lock:
            used = self.usage[provider].get(session_id, 0)
            return used < self.budgets.get(provider, 10)

    async def record(self, provider: str, session_id: str):
        async with self._lock:
            self.usage[provider][session_id] = self.usage[provider].get(session_id, 0) + 1

    async def reset_session(self, session_id: str):
        async with self._lock:
            for p in self.usage:
                self.usage[p].pop(session_id, None)

BUDGET = ProviderBudget()

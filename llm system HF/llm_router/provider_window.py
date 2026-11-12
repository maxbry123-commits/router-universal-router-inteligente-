import asyncio
import time
from collections import defaultdict, deque

WINDOW_S = 114.0
LIMITS = {"groq": 8, "nvidia": 12}
BILLING_WORDS = ("insufficient", "balance", "credit", "billing", "payment", "saldo", "quota exceeded")

class ProviderHTTPError(Exception):
    def __init__(self, provider: str, status: int, retry_after: float = None, body: str = ""):
        super().__init__(f"{provider} HTTP {status}")
        self.provider = provider
        self.status = status
        self.retry_after = retry_after
        self.body = body

class ProviderRateLimited(Exception):
    pass

class NoBalanceError(Exception):
    pass

def is_no_balance(err: Exception) -> bool:
    if not isinstance(err, ProviderHTTPError):
        return False
    if err.status == 402:
        return True
    return err.status == 403 and any(w in err.body.lower() for w in BILLING_WORDS)

class ProviderWindow:
    def __init__(self, limits: dict = None, window_s: float = WINDOW_S, clock=time.monotonic, sleep=asyncio.sleep):
        self.limits = dict(LIMITS if limits is None else limits)
        self.window_s = window_s
        self.clock = clock
        self.sleep = sleep
        self.calls = defaultdict(deque)
        self.waited_s = 0.0

    async def acquire(self, provider: str) -> None:
        limit = self.limits.get(provider, 10)
        q = self.calls[provider]
        while True:
            now = self.clock()
            while q and now - q[0] >= self.window_s:
                q.popleft()
            if len(q) < limit:
                q.append(now)
                return
            wait = q[0] + self.window_s - now
            self.waited_s += wait
            await self.sleep(wait)

    async def backoff(self, retry_after, budget: dict) -> bool:
        budget["attempt"] += 1
        if budget["left"] <= 0:
            return False
        base = retry_after if retry_after else min(2 ** budget["attempt"], 16)
        wait = min(base, budget["left"])
        budget["left"] -= wait
        self.waited_s += wait
        await self.sleep(wait)
        return True

WINDOW = ProviderWindow()

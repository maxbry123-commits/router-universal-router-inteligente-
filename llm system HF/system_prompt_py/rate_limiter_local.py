# rate_limiter_local.py
import aiosqlite
import time
import asyncio
from pathlib import Path

class SQLiteTokenBucket:
    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        elif Path("/data").is_dir():
            self.db_path = "/data/rate_limit.db"
        else:
            self.db_path = "/tmp/rate_limit.db"
        self._lock = asyncio.Lock()
        self._initialized = False

    async def _init(self):
        if self._initialized:
            return
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS buckets (
                    key TEXT PRIMARY KEY,
                    tokens REAL NOT NULL,
                    last_update REAL NOT NULL
                )
            """)
            await db.commit()
        self._initialized = True

    async def acquire(self, key: str, capacity: int, refill_rate: float, tokens: int = 1) -> bool:
        await self._init()
        async with self._lock:
            now = time.time()
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT tokens, last_update FROM buckets WHERE key = ?", (key,)
                ) as cursor:
                    row = await cursor.fetchone()

                if row:
                    current_tokens, last_update = row
                else:
                    current_tokens, last_update = capacity, now

                elapsed = now - last_update
                current_tokens = min(capacity, current_tokens + elapsed * refill_rate)

                if current_tokens >= tokens:
                    new_tokens = current_tokens - tokens
                    allowed = True
                else:
                    new_tokens = current_tokens
                    allowed = False

                await db.execute(
                    "INSERT OR REPLACE INTO buckets (key, tokens, last_update) VALUES (?, ?, ?)",
                    (key, new_tokens, now)
                )
                await db.commit()
                return allowed

LOCAL_LIMITER = SQLiteTokenBucket()

PROVIDER_CONFIG = {
    "groq": {"capacity": 30, "refill_rate": 30/60},
    "nvidia": {"capacity": 40, "refill_rate": 40/60},
}

async def wait_for_slot_local(provider: str, est_tokens: int = 1) -> bool:
    cfg = PROVIDER_CONFIG.get(provider)
    if not cfg:
        return True
    return await LOCAL_LIMITER.acquire(
        key=provider,
        capacity=cfg["capacity"],
        refill_rate=cfg["refill_rate"],
        tokens=est_tokens
    )

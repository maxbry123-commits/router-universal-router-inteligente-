# temp_cache.py
import aiosqlite
import json
import time
import asyncio

class TempCache:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = "/tmp/temp_cache.db", ttl_s: int = 3600):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = db_path
        self.ttl_s = ttl_s
        self._lock = asyncio.Lock()

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            await db.commit()

    async def set(self, key: str, value, ttl_s: int = None):
        ttl = ttl_s or self.ttl_s
        expires = time.time() + ttl
        serialized = value if isinstance(value, str) else json.dumps(value)
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                    (key, serialized, expires)
                )
                await db.commit()

    async def get(self, key: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
        if not row:
            return None
        value, expires_at = row
        if time.time() > expires_at:
            await self.delete(key)
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def delete(self, key: str):
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM cache WHERE key = ?", (key,))
                await db.commit()

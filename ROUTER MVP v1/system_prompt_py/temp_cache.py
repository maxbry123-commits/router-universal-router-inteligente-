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

    def __init__(self, db_path="/tmp/temp_cache.db", ttl_s=3600):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = db_path
        self.ttl_s = ttl_s
        self._lock = asyncio.Lock()

    async def _init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, expires_at REAL)")
            await db.commit()

    async def set(self, key, value, ttl_s=None):
        await self._init()
        ttl = ttl_s or self.ttl_s
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)", (key, json.dumps(value), time.time() + ttl))
                await db.commit()

    async def get(self, key):
        await self._init()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value, expires_at FROM cache WHERE key = ?", (key,)) as cur:
                row = await cur.fetchone()
        if not row:
            return None
        value, expires_at = row
        if time.time() > expires_at:
            await self.delete(key)
            return None
        return json.loads(value)

    async def delete(self, key):
        await self._init()
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM cache WHERE key = ?", (key,))
                await db.commit()

import aiosqlite
import json
import time

class SQLiteMemory:
    def __init__(self, db_path="/data/memory.db"):
        self.db_path = db_path
        self._initialized = False

    async def _init(self):
        if self._initialized:
            return
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT, ts REAL)")
            await db.commit()
        self._initialized = True

    async def set(self, key, value):
        await self._init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO memory VALUES (?, ?, ?)", (key, json.dumps(value), time.time()))
            await db.commit()

    async def get(self, key):
        await self._init()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM memory WHERE key = ?", (key,)) as cur:
                row = await cur.fetchone()
        return json.loads(row[0]) if row else None

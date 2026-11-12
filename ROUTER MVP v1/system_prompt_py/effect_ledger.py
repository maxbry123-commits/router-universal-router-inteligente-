import aiosqlite
import hashlib
import json
import time

class EffectLedger:
    def __init__(self, db_path: str = "/tmp/effect_ledger.db"):
        self.db_path = db_path
        self._initialized = False

    async def _init(self):
        if self._initialized:
            return
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS effects (effect_id TEXT PRIMARY KEY, result TEXT NOT NULL, created_at REAL NOT NULL)")
            await db.commit()
        self._initialized = True

    def _make_effect_id(self, tool_name: str, identity_args: dict) -> str:
        payload = f"{tool_name}:{json.dumps(identity_args, sort_keys=True)}"
        return hashlib.sha256(payload.encode()).hexdigest()

    async def execute_once(self, tool_name: str, identity_args: dict, fn, *args, **kwargs):
        await self._init()
        effect_id = self._make_effect_id(tool_name, identity_args)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT result FROM effects WHERE effect_id = ?", (effect_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0])
            result = await fn(*args, **kwargs)
            await db.execute("INSERT INTO effects (effect_id, result, created_at) VALUES (?, ?, ?)", (effect_id, json.dumps(result, default=str), time.time()))
            await db.commit()
            return result

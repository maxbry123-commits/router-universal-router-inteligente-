import time
import hashlib
from temp_cache import TempCache

class DeduplicationLayer:
    def __init__(self, cache: TempCache, ttl_s: int = 60):
        self.cache = cache
        self.ttl_s = ttl_s

    def _hash_request(self, task: str, source: str) -> str:
        payload = f"{source}:{task}"
        return hashlib.sha256(payload.encode()).hexdigest()

    async def check_and_store(self, task: str, source: str) -> tuple[bool, str]:
        req_hash = self._hash_request(task, source)
        cached_response = await self.cache.get(f"dedup_{req_hash}")
        if cached_response:
            return True, cached_response
        return False, ""

    async def store_response(self, task: str, source: str, response: str):
        req_hash = self._hash_request(task, source)
        await self.cache.set(f"dedup_{req_hash}", response, ttl_s=self.ttl_s)

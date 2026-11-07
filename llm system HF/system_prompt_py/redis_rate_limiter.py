# redis_rate_limiter.py
import os
import time

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

LUA_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local tokens_requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
local current_tokens = tonumber(bucket[1]) or capacity
local last_update = tonumber(bucket[2]) or now
local elapsed = (now - last_update) / 1000
current_tokens = math.min(capacity, current_tokens + elapsed * refill_rate)
local allowed = 0
local remaining = math.floor(current_tokens)
local retry_after = 0
if current_tokens >= tokens_requested then
    allowed = 1
    remaining = math.floor(current_tokens - tokens_requested)
    current_tokens = current_tokens - tokens_requested
else
    local needed = tokens_requested - current_tokens
    retry_after = math.ceil(needed / refill_rate)
end
redis.call('HMSET', key, 'tokens', current_tokens, 'last_update', now)
redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) * 2)
return {allowed, remaining, retry_after}
"""

class RedisTokenBucket:
    def __init__(self, redis_url: str = None):
        if redis is None:
            raise ImportError("redis package not installed")
        self.redis = redis.from_url(redis_url or os.getenv("REDIS_URL", "redis://localhost:6379"))
        self.script = self.redis.register_script(LUA_SCRIPT)

    async def acquire(self, key: str, capacity: int, refill_rate: float, tokens: int = 1) -> bool:
        now_ms = int(time.time() * 1000)
        result = await self.script(
            keys=[f"ratelimit:token:{key}"],
            args=[capacity, refill_rate, tokens, now_ms]
        )
        return result[0] == 1

REDIS_LIMITER = None
if os.getenv("REDIS_URL") and redis is not None:
    try:
        REDIS_LIMITER = RedisTokenBucket()
    except Exception:
        REDIS_LIMITER = None

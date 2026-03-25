import asyncio
import redis.asyncio as redis
from app.config import settings

class MockRedis:
    def __init__(self):
        self.data = {}
        self.zsets = {}
        self.sets = {}
        self.counters = {}

    async def close(self):
        pass

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.data[key] = value

    async def exists(self, key):
        return key in self.data or key in self.zsets or key in self.sets or key in self.counters

    async def incr(self, key):
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    async def expire(self, key, ttl):
        pass

    async def sadd(self, key, value):
        if key not in self.sets:
            self.sets[key] = set()
        self.sets[key].add(value)

    async def scard(self, key):
        return len(self.sets.get(key, set()))

    async def lpush(self, key, value):
        if key not in self.data:
            self.data[key] = []
        self.data[key].insert(0, value)

    async def lrange(self, key, start, end):
        lst = self.data.get(key, [])
        if end == -1:
            return lst[start:]
        return lst[start:end+1]

    async def zadd(self, key, mapping):
        if key not in self.zsets:
            self.zsets[key] = []
        for member, score in mapping.items():
            self.zsets[key].append((member, score))

    async def zremrangebyscore(self, key, min_score, max_score):
        if key in self.zsets:
            self.zsets[key] = [(m, s) for m, s in self.zsets[key] if not (min_score <= s <= max_score)]

    async def zcard(self, key):
        return len(self.zsets.get(key, []))

    async def delete(self, key):
        self.data.pop(key, None)
        self.zsets.pop(key, None)
        self.sets.pop(key, None)
        self.counters.pop(key, None)

    async def keys(self, pattern):
        # Very simple glob match for mock
        prefix = pattern.replace("*", "")
        all_keys = list(self.data.keys()) + list(self.zsets.keys()) + list(self.sets.keys()) + list(self.counters.keys())
        return [k for k in all_keys if k.startswith(prefix)]

class RedisClient:
    def __init__(self, host=settings.REDIS_HOST, port=settings.REDIS_PORT):
        if settings.MOCK_MODE:
            print("[STORAGE] REDIS Mock active.")
            self.client = MockRedis()
        else:
            self.client = redis.Redis(host=host, port=port, decode_responses=True)

    async def close(self):
        await self.client.close()

    async def set_value(self, key, value, ttl=None):
        await self.client.set(key, value, ex=ttl)

    async def get_value(self, key):
        return await self.client.get(key)

    async def increment_counter(self, key, ttl=None):
        count = await self.client.incr(key)
        if ttl:
            await self.client.expire(key, ttl)
        return count

    async def add_to_list(self, key, value):
        await self.client.lpush(key, value)

    async def get_list(self, key, start=0, end=-1):
        return await self.client.lrange(key, start, end)

    async def record_request(self, ip, timestamp):
        window_key = f"ip_requests:{ip}"
        await self.client.zadd(window_key, {str(timestamp): timestamp})
        window_start = timestamp - settings.TIME_WINDOW
        await self.client.zremrangebyscore(window_key, 0, window_start)
        count = await self.client.zcard(window_key)
        await self.client.expire(window_key, settings.TIME_WINDOW + 60)
        return count

    async def is_ip_banned(self, ip):
        return await self.client.exists(f"banned:{ip}")

    async def ban_ip(self, ip, duration=settings.BAN_TIME):
        await self.client.set(f"banned:{ip}", 1, ex=duration)

redis_client = RedisClient()

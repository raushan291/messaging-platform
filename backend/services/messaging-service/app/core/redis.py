import redis.asyncio as redis
from app.core.config import settings

redis_client: redis.Redis | None = None

async def connect_redis():
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    await redis_client.ping()
    print("Redis connected")

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        print("Redis closed")

def get_redis() -> redis.Redis:
    if not redis_client:
        raise RuntimeError("Redis not initialized")
    return redis_client

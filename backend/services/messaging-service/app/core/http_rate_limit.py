from fastapi import HTTPException
from app.core.redis import get_redis

async def user_rate_limit(user_id: str, action: str, limit: int, window: int):
    redis = get_redis()

    key = f"rate:{action}:{user_id}"

    count = await redis.get(key)

    if count and int(count) >= limit:
        raise HTTPException(429, "Too many requests")

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    await pipe.execute()
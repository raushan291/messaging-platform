from app.core.config import settings
from app.core.redis import get_redis


# message rate limit
async def is_rate_limited(user_id: str, conversation_id: str) -> bool:
    redis = get_redis()
    key = f"rate:{user_id}:{conversation_id}"

    count = await redis.get(key)

    if count and int(count) >= settings.MESSAGE_RATE_LIMIT:
        return True

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, settings.MESSAGE_RATE_WINDOW)
    await pipe.execute()

    return False


# duplicate message protection
async def is_duplicate_message(user_id: str, content: str) -> bool:
    redis = get_redis()

    key = f"dup:{user_id}:{hash(content)}"

    count = await redis.get(key)
    count = int(count) if count else 0

    if count >= 3:  # allow 3 repeats
        return True

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 10)
    await pipe.execute()

    return False


# spam burst detection
async def is_spam_burst(user_id: str) -> bool:
    redis = get_redis()
    key = f"burst:{user_id}"

    count = await redis.get(key)
    count = int(count) if count else 0

    if count >= 8:  # 8 messages in 5 sec
        return True

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 5)
    await pipe.execute()

    return False


# websocket connection limit
async def can_open_connection(user_id: str) -> bool:
    redis = get_redis()
    key = f"conn:{user_id}"

    count = await redis.get(key)
    if count and int(count) >= settings.MAX_CONNECTIONS_PER_USER:
        return False

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 3600)
    await pipe.execute()

    return True


# close connection
async def close_connection(user_id: str):
    redis = get_redis()
    key = f"conn:{user_id}"
    await redis.decr(key)
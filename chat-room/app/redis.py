import aioredis

redis = aioredis.from_url("redis://localhost", decode_responses=True)


async def increment_unread(item_id: str, user_id: str):
    await redis.incr(f"unread_msg_{item_id}_{user_id}")


async def get_unread(item_id: str, user_id: str) -> int:
    count = await redis.get(f"unread_msg_{item_id}_{user_id}")
    return int(count) if count else 0


async def reset_unread(item_id: str, user_id: str):
    await redis.delete(f"unread_msg_{item_id}_{user_id}")

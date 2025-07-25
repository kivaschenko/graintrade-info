from .database import database
from .schemas import UserInResponse, ItemInResponse


# ---------------
# GET User models


async def get_user_by_username(username: str) -> UserInResponse:
    query = """
        SELECT id, username, email, full_name, phone, hashed_password, disabled
        FROM users
        WHERE username = $1
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, username)
        return UserInResponse(**row)


async def get_user_by_id(user_id: int) -> UserInResponse:
    query = """
        SELECT id, username, email, full_name, phone, disabled, hashed_password
        FROM users
        WHERE id = $1 AND disabled = 'false'
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, user_id)
    return UserInResponse(**row)


# ------------------
# GET Item models


async def get_item_by_id(item_id: int) -> ItemInResponse:
    query = """
        SELECT i.id, i.uuid, i.category_id, i.offer_type, i.title, i.description, i.price, i.currency, 
        i.amount, i.measure, i.terms_delivery, i.country, i.region, i.latitude, i.longitude, i.created_at,
        u.username AS owner_id
        FROM items i
        JOIN items_users iu ON i.id = iu.item_id
        JOIN users u ON iu.user_id = u.id
        WHERE i.id = $1
        LIMIT 1
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, item_id)
    return ItemInResponse(**row)

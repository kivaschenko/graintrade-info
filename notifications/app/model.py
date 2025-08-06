from typing import List
from .database import database
from .schemas import (
    UserInResponse,
    ItemInResponse,
    CategoryInResponse,
    PreferencesSchema,
)


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


# ------------------
# GET Category models


async def get_all_categories() -> List[CategoryInResponse]:
    """Retrive all categories from view with their parent categories."""
    query = """
        SELECT id, name, description, ua_name, ua_description, parent_category, parent_category_ua
        FROM categories_hierarchy
        
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query)
        return [CategoryInResponse(**row) for row in rows]


# ------------------
# Users Preferences


async def get_all_users_preferences() -> List[PreferencesSchema]:
    query = """
        SELECT user_id, notify_new_messages, notify_new_items, interested_categories, full_name, email
        FROM user_notification_preferences,
        JOIN users ON user_notification_preferences.user_id = users.id
        WHERE users.disabled = 'false' AND user_notification_preferences.notify_new_items = 'true'
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query)
        return [PreferencesSchema(**row) for row in rows]

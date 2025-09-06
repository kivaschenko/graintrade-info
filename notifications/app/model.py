from typing import List
from .database import database
from .schemas import (
    UserInResponse,
    ItemInResponse,
    CategoryInResponse,
    PreferencesSchema,
    SubscriptionInResponse,
    TarifInResponse,
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


async def get_category_by_name(name: str) -> CategoryInResponse:
    """Retrieve a category by its name."""
    query = """
        SELECT id, name, description, ua_name, ua_description, parent_category, parent_category_ua
        FROM categories_hierarchy
        WHERE name = $1
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, name)
        if row:
            return CategoryInResponse(**row)
        return None


async def get_category_by_id(category_id: int) -> CategoryInResponse:
    """Retrieve a category by its ID."""
    query = """
        SELECT id, name, description, ua_name, ua_description, parent_category, parent_category_ua
        FROM categories_hierarchy
        WHERE id = $1
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, category_id)
        if row:
            return CategoryInResponse(**row)
        return None


# ------------------
# Users Preferences


async def get_all_users_preferences() -> List[PreferencesSchema]:
    query = """
        SELECT 
            unp.user_id, 
            unp.notify_new_messages, 
            unp.notify_new_items, 
            unp.interested_categories, 
            unp.country,
            unp.language,
            u.full_name,
            u.username,
            u.email
        FROM user_notification_preferences AS unp
        JOIN users AS u ON unp.user_id = u.id
        WHERE u.disabled = 'false' AND unp.notify_new_items = 'true'
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query)
        return [PreferencesSchema(**row) for row in rows]


# ------------------
# Subscription models


async def get_user_subscritpion_by_order_id(order_id: str) -> SubscriptionInResponse:
    query = """
        SELECT id, user_id, tarif_id, start_date, end_date, order_id, status, created_at
        FROM subscriptions
        WHERE order_id = $1
    """
    query_tarif = """
        SELECT id, name, description, price, currency, scope, terms, items_limit, map_views_limit, geo_search_limit, navigation_limit, created_at
        FROM tarifs
        WHERE id = $1
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, order_id)
        if row is None:
            raise ValueError("Subscription with the given order_id does not exist.")
        subscription = SubscriptionInResponse(**row)
        tarif_row = await connection.fetchrow(query_tarif, subscription.tarif_id)
        if tarif_row is not None:
            subscription.tarif = TarifInResponse(**tarif_row)
        return subscription

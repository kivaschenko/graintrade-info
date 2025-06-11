from typing import List
import uuid
from ..database import database
from ..schemas import (
    SubscriptionInDB,
    SubscriptionInResponse,
    TarifInResponse,
)


# -------------------
# CRUD operations for Subscription
async def create(subscription: SubscriptionInDB) -> SubscriptionInResponse:
    query = """
        INSERT INTO subscriptions (user_id, tarif_id, start_date, end_date, order_id, status)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, user_id, tarif_id, start_date, end_date, order_id, status, created_at
    """
    if subscription.order_id is None:
        subscription.order_id = (
            "order_" + str(subscription.user_id) + "_" + str(subscription.tarif_id)
        )
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(
            query,
            subscription.user_id,
            subscription.tarif_id,
            subscription.start_date,
            subscription.end_date,
            subscription.order_id,
            subscription.status,
        )
        new_subscription = SubscriptionInResponse(**row)
        return new_subscription


async def create_free_subscription(user_id: int) -> SubscriptionInResponse:
    order_id = str(uuid.uuid4())
    query = """
        INSERT INTO subscriptions (user_id, tarif_id, start_date, end_date, order_id, status)
        SELECT $1, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '30 days', $2, 'active'
        FROM tarifs 
        WHERE scope = 'free'
        LIMIT 1
        RETURNING id, user_id, tarif_id, start_date, end_date, order_id, status, created_at
    """
    async with database.pool.acquire() as connection:
        async with connection.transaction():
            try:
                row = await connection.fetchrow(query, user_id, order_id)
                if row is None:
                    raise ValueError("No free tarif found")
                return SubscriptionInResponse(**row)
            except Exception as e:
                raise ValueError(f"Failed to create subscription: {str(e)}")


async def update_status_by_order_id(status: str, order_id: str):
    if status not in ["active", "inactive", "expired"]:
        raise ValueError(
            "Invalid status value. Must be 'active', 'inactive', or 'expired'."
        )
    query = """
        UPDATE subscriptions
        SET status = $1
        WHERE order_id = $2
        RETURNING id, user_id, order_id, status
"""
    clean_query = """
        UPDATE subscriptions
        SET status = 'inactive'
        WHERE user_id = $1 AND order_id <> $2
        RETURNING id, user_id, order_id, status
"""
    async with database.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(query, status, order_id)
            if row is None:
                raise ValueError("Subscription with the given order_id does not exist.")
            # Clean up other subscriptions for the same user
            user_id = row["user_id"]
            await conn.execute(clean_query, user_id, order_id)
        return row


async def get_by_id(subscription_id: int) -> SubscriptionInResponse:
    query = """
        SELECT id, user_id, tarif_id, start_date, end_date, status, created_at
        FROM subscriptions
        WHERE id = $1
    """
    query_tarif = """
        SELECT id, name, description, price, currency, scope, terms
        FROM tarifs
        WHERE id = $1
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, subscription_id)
        subscription = SubscriptionInResponse(**row)
        tarif_row = await connection.fetchrow(query_tarif, subscription.tarif_id)
        if tarif_row is not None:
            subscription.tarif = TarifInResponse(**tarif_row)
        return subscription


async def delete(subscription_id: int) -> None:
    query = "UPDATE subscriptions SET status = 'inactive' WHERE id = $1"
    async with database.pool.acquire() as connection:
        await connection.execute(query, subscription_id)


async def get_by_user_id(user_id: int) -> SubscriptionInResponse:
    query = """
        SELECT id, user_id, tarif_id, start_date, end_date, order_id, status, created_at
        FROM subscriptions
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 1
    """
    query_tarif = """
        SELECT id, name, description, price, currency, scope, terms, 
        items_limit, map_views_limit, geo_search_limit, navigation_limit, created_at 
        FROM tarifs
        WHERE id = $1
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, user_id)
        subscription = SubscriptionInResponse(**row)
        tarif_row = await connection.fetchrow(query_tarif, subscription.tarif_id)
        if tarif_row is not None:
            subscription.tarif = TarifInResponse(**tarif_row)
        return subscription


async def get_subscription_usage_for_user(user_id: int) -> List[SubscriptionInResponse]:
    query = "SELECT * FROM get_subscription_usage($1)"
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, user_id)
        return row

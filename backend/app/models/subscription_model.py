from typing import List

from ..database import database
from ..schemas import (
    SubscriptionInDB,
    SubscriptionInResponse,
    TarifInResponse,
    SubscriptionStatus,
)


async def create(subscription: SubscriptionInDB) -> SubscriptionInResponse:
    query = """
        INSERT INTO subscriptions (user_id, tarif_id, start_date, end_date, status)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, user_id, tarif_id, start_date, end_date, status, created_at
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(
            query,
            subscription.user_id,
            subscription.tarif_id,
            subscription.start_date,
            subscription.end_date,
            subscription.status,
        )
        new_subscription = SubscriptionInResponse(**row)
        return new_subscription


async def update_status(status: str, payment_id: str):
    query = """
        UPDATE subscriptions
        SET status = $1
        WHERE payment_id = $2
        RETURNING id, payment_id, status
"""
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, status, payment_id)
        return row


async def update_payment_id(payment_id: str, id: int):
    query = """
        UPDATE subscriptions
        SET payment_id = $1
        WHERE id = $2
        RETURNING id, payment_id
"""
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, payment_id, id)
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
        SELECT id, user_id, tarif_id, start_date, end_date, status, created_at
        FROM subscriptions
        WHERE user_id = $1 AND status = 'active' AND end_date > NOW()
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

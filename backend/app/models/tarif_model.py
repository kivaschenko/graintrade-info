from typing import List

from ..database import database
from ..schemas import TarifInResponse


async def get_all() -> List[TarifInResponse]:
    query = """SELECT id, name, description, price, currency, scope, terms, ua_name, ua_description, ua_terms, ua_price, ua_currency,
        items_limit, map_views_limit, geo_search_limit, navigation_limit, notify_new_messages, notify_new_items, created_at 
        FROM tarifs
        ORDER BY price ASC"""
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query)
        try:
            tarifs = [TarifInResponse(**row) for row in rows]
        except Exception as e:
            raise ValueError(f"Error parsing tarifs: {e}")
        return tarifs


async def get_by_id(tarif_id: int) -> TarifInResponse:
    query = """
        SELECT id, name, description, price, currency, scope, terms, ua_name, ua_description, ua_terms, ua_terms, ua_price, ua_currency,
        items_limit, map_views_limit, geo_search_limit, navigation_limit, notify_new_messages, notify_new_items, created_at 
        FROM tarifs
        WHERE id = $1
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, tarif_id)
        return TarifInResponse(**row)


async def get_tarif_by_scope(scope: str) -> TarifInResponse:
    query = """
        SELECT id, name, description, price, currency, scope, terms, ua_name, ua_description, ua_terms, ua_price, ua_currency,
        items_limit, map_views_limit, geo_search_limit, navigation_limit, notify_new_messages, notify_new_items, created_at 
        FROM tarifs
        WHERE scope = $1
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, scope)
        return TarifInResponse(**row)

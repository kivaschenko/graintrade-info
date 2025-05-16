from typing import List

from ..database import database
from ..schemas import TarifInResponse


async def get_all() -> List[TarifInResponse]:
    query = """SELECT 
        id, name, description, price, currency, scope, terms, items_limit, map_views_limit 
        FROM tarifs"""
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query)
        return [TarifInResponse(**row) for row in rows]


async def get_by_id(tarif_id: int) -> TarifInResponse:
    query = """
        SELECT id, name, description, price, currency, scope, terms, created_at
        FROM tarifs
        WHERE id = $1
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, tarif_id)
        return TarifInResponse(**row)


async def get_tarif_by_scope(scope: str) -> TarifInResponse:
    query = """
        SELECT id, name, description, price, currency, scope, terms, created_at
        FROM tarifs
        WHERE scope = $1
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, scope)
        return TarifInResponse(**row)

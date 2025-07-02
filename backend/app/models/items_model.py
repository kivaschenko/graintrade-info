import asyncpg
import logging
from typing import List, Optional
from ..database import database
from ..schemas import ItemInDB, ItemInResponse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def get_all(offset: int = 0, limit: int = 10) -> List[ItemInResponse]:
    """Get all items according offset and limit cause."""
    query = """
        SELECT 
            id, uuid, category_id, offer_type, title, description, price, currency, 
            amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        FROM items
        ORDER BY id DESC
        OFFSET $1
        LIMIT $2
    """
    try:
        async with database.pool.acquire() as conn:
            rows = await conn.fetch(query, offset, limit)
            return [ItemInResponse(**row) for row in rows]
    except asyncpg.exceptions.InvalidTextRepresentationError as e:
        # Handle specific error for invalid text representation
        logging.error(f"Invalid text representation error: {e}")
        return []


async def create(item: ItemInDB, user_id: int) -> ItemInResponse:
    query = """
        INSERT INTO items (category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, geom)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::numeric, $13::numeric, ST_SetSRID(ST_MakePoint($13::numeric, $12::numeric), 4326))
        RETURNING id, uuid, category_id, offer_type, title, description, price, currency, 
                amount, measure, terms_delivery, country, region, latitude, longitude, created_at
    """
    query2 = """INSERT INTO items_users (item_id, user_id) VALUES ($1, $2)"""
    query3 = "SELECT increment_items_count($1)"
    async with database.pool.acquire() as conn:
        # Open a transaction
        async with conn.transaction():
            row = await conn.fetchrow(
                query,
                item.category_id,
                item.offer_type,
                item.title,
                item.description,
                item.price,
                item.currency,
                item.amount,
                item.measure,
                item.terms_delivery,
                item.country,
                item.region,
                item.latitude,
                item.longitude,
            )
            new_item = ItemInResponse(**row)
            await conn.execute(query2, new_item.id, user_id)
            await conn.execute(query3, user_id)
            return new_item
    return None


async def delete(item_id: int, user_id: int) -> None:
    query = "DELETE FROM items_users WHERE item_id = $1 AND user_id = $2"
    query2 = "DELETE FROM items WHERE id = $1"
    try:
        async with database.pool.acquire() as conn:
            # Open a transaction
            async with conn.transaction():
                await conn.execute(query, item_id, user_id)
                await conn.execute(query2, item_id)
    except asyncpg.exceptions.ForeignKeyViolationError:
        raise ValueError("Item does not belong to the user")


async def get_items_by_user_id(user_id: int) -> List[ItemInResponse]:
    query = """
        SELECT i.id, i.uuid, i.category_id, i.offer_type, i.title, i.description, 
        i.price, i.currency, i.amount, i.measure, i.terms_delivery, i.country, 
        i.region, i.latitude, i.longitude, i.created_at
        FROM items i
        JOIN items_users iu ON i.id = iu.item_id
        WHERE iu.user_id = $1
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query, user_id)
    return [ItemInResponse(**row) for row in rows]


async def find_in_distance(
    longitude: float, latitude: float, distance: int
) -> List[ItemInResponse]:
    query = """
        SELECT id, uuid, category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        FROM items
        WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography, $3)
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query, longitude, latitude, distance)
    return [ItemInResponse(**row) for row in rows]


async def get_filtered_items(
    min_price: float = 0.0,
    max_price: float = 999999.0,
    currency: str = "USD",
    min_amount: int = 0,
    max_amount: int = 999999,
    measure: str = "metric ton",
    terms_delivery: str = "EXW",
    country: str = "Ukraine",
    region: str = "",
) -> List[ItemInResponse]:
    query = """
        SELECT 
            id, uuid, category_id, offer_type, title, description, 
            price, currency, amount, measure, terms_delivery, 
            country, region, latitude, longitude, created_at
        FROM items
        WHERE ($1::float IS NULL OR price >= $1) 
            AND ($2::float IS NULL OR price <= $2) 
            AND ($3::text IS NULL OR currency = $3) 
            AND ($4::int IS NULL OR amount >= $4) 
            AND ($5::int IS NULL OR amount <= $5) 
            AND ($6::text IS NULL OR measure = $6) 
            AND ($7::text IS NULL OR terms_delivery = $7) 
            AND ($8::text IS NULL OR country = $8) 
            AND ($9::text IS NULL OR region = $9)
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            query,
            min_price,
            max_price,
            currency,
            min_amount,
            max_amount,
            measure,
            terms_delivery,
            country,
            region,
        )
    return [ItemInResponse(**row) for row in rows]


async def items_count(user_id: int) -> int:
    async with database.pool.acquire() as conn:
        return await conn.fetchval("SELECT increment_items_count($1)", user_id)


async def get_by_id(item_id: int) -> ItemInResponse:
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


async def map_views_increment(user_id: int):
    query = "SELECT increment_map_views($1)"
    async with database.pool.acquire() as conn:
        counter = await conn.fetchval(query, user_id)
        return counter


async def get_geo_items_by_category(category_id: int) -> dict:
    query = """
        SELECT 
            id, uuid, category_id, offer_type, title, description, price, 
            currency, amount, measure, terms_delivery, country, region, 
            latitude, longitude, created_at,
        ST_AsGeoJSON(geom) AS geometry
        FROM items
        WHERE category_id = $1
        AND geom IS NOT NULL
        ORDER BY id DESC
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query, category_id)
        features = [
            {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {k: row[k] for k in row.keys() if k != "geometry"},
            }
            for row in rows
        ]
    return {"type": "FeatureCollection", "features": features}


async def get_all_geo_items() -> dict:
    query = """
        SELECT 
            id, uuid, category_id, offer_type, title, description, price, 
            currency, amount, measure, terms_delivery, country, region, 
            latitude, longitude, created_at,
        ST_AsGeoJSON(geom) AS geometry
        FROM items
        WHERE geom IS NOT NULL
        ORDER BY id DESC
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query)
        features = [
            {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {k: row[k] for k in row.keys() if k != "geometry"},
            }
            for row in rows
        ]
    return {"type": "FeatureCollection", "features": features}


async def get_filtered_items_geo_json(
    category_id: Optional[int] = None,
    offer_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    currency: Optional[str] = None,
    country: Optional[str] = None,
    min_amount: Optional[int] = None,
    max_amount: Optional[int] = None,
    measure: Optional[str] = None,
    incoterm: Optional[str] = None,
) -> dict:
    conditions = ["geom IS NOT NULL"]
    query_params = []
    param_idx = 1

    if category_id is not None:
        conditions.append(f"category_id = ${param_idx}")
        query_params.append(category_id)
        param_idx += 1
    if offer_type and offer_type != "all":
        conditions.append(f"offer_type = ${param_idx}")
        query_params.append(offer_type)
        param_idx += 1
    if min_price is not None:
        conditions.append(f"price >= ${param_idx}")
        query_params.append(min_price)
        param_idx += 1
    if max_price is not None:
        conditions.append(f"price <= ${param_idx}")
        query_params.append(max_price)
        param_idx += 1
    if currency and currency != "all":
        conditions.append(f"currency = ${param_idx}")
        query_params.append(currency.upper())
        param_idx += 1
    if country and country != "all":
        conditions.append(f"country ILIKE ${param_idx}")
        query_params.append(country)
        param_idx += 1
    if min_amount is not None:
        conditions.append(f"amount >= ${param_idx}")
        query_params.append(min_amount)
        param_idx += 1
    if max_amount is not None:
        conditions.append(f"amount <= ${param_idx}")
        query_params.append(max_amount)
        param_idx += 1
    if measure and measure != "all":
        conditions.append(f"measure = ${param_idx}")
        query_params.append(measure)
        param_idx += 1
    if incoterm and incoterm != "all":
        conditions.append(f"terms_delivery ILIKE ${param_idx}")
        query_params.append(incoterm)
        param_idx += 1

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT 
            id, uuid, category_id, offer_type, title, description, price, 
            currency, amount, measure, terms_delivery, country, 
            region, latitude, longitude, created_at,
        ST_AsGeoJSON(geom) AS geometry
        FROM items
        {where_clause}
        ORDER BY id DESC
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query, *query_params)
        features = [
            {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {k: row[k] for k in row.keys() if k != "geometry"},
            }
            for row in rows
        ]
    return {"type": "FeatureCollection", "features": features}

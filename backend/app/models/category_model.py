import asyncpg
from typing import List, Optional
from ..database import database
from ..schemas import (
    CategoryInDB,
    CategoryInResponse,
    ItemInResponse,
)


async def create(category: CategoryInDB) -> CategoryInResponse:
    query = """
        INSERT INTO categories (name, description, ua_name, ua_description)
        VALUES ($1, $2, $3, $4)
        RETURNING id, name, description, ua_name, ua_description
    """
    async with database.pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                query,
                category.name,
                category.description,
                category.ua_name,
                category.ua_description,
            )
            return CategoryInResponse(**row)
        except asyncpg.exceptions.UniqueViolationError:
            raise ValueError("Category with this name already exists")


async def get_all() -> List[CategoryInResponse]:
    """Retrive all categories from view with their parent categories."""
    query = """
        SELECT id, name, description, ua_name, ua_description, parent_category, parent_category_ua
        FROM categories_hierarchy
        
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query)
        return [CategoryInResponse(**row) for row in rows]


async def get_by_id(category_id: int) -> CategoryInResponse:
    query = """
        SELECT id, name, description, ua_name, ua_description, parent_category
        FROM categories
        WHERE id = $1
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, category_id)
        if row is None:
            raise ValueError("Category not found")
        return CategoryInResponse(**row)


async def update(category_id: int, category: CategoryInDB) -> CategoryInResponse:
    query = """
        UPDATE categories
        SET name = $2, description = $3, ua_name = $4, ua_description = $5
        WHERE id = $1
        RETURNING id, name, description, ua_name, ua_description
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            query,
            category_id,
            category.name,
            category.description,
            category.ua_name,
            category.ua_description,
        )
        if row is None:
            raise ValueError("Category not found")
        return CategoryInResponse(**row)


async def delete(category_id: int) -> None:
    query = """
        DELETE FROM categories
        WHERE id = $1
    """
    async with database.pool.acquire() as conn:
        await conn.execute(query, category_id)


async def get_by_id_with_items(
    category_id: int,
    offset: int,
    limit: int,
    offer_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    currency: Optional[str] = None,
    country: Optional[str] = None,
    min_amount: Optional[int] = None,
    max_amount: Optional[int] = None,
    measure: Optional[str] = None,
    incoterm: Optional[str] = None,
) -> tuple[CategoryInResponse, List[ItemInResponse], int]:
    conditions = [
        "category_id = $1",
    ]
    query_params = []
    param_idx = 4

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

    query = """
        SELECT id, name, description, ua_name, ua_description, parent_category, parent_category_ua
        FROM categories_hierarchy 
        WHERE id = $1
    """
    query2 = f"""
        SELECT 
            id, uuid, category_id, offer_type, title, description, price, currency, 
            amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        FROM items
        {where_clause}
        ORDER BY id DESC
        OFFSET $2
        LIMIT $3
    """
    print(
        f"Executing query: {query2} with params: {category_id}, {offset}, {limit}, {query_params}"
    )
    query_count = "SELECT COUNT(*) FROM items WHERE category_id = $1"
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, category_id)
        if row is None:
            raise ValueError("Category not found")
        category = CategoryInResponse(**row)
        items = await conn.fetch(query2, category_id, offset, limit, *query_params)
        total_items_row = await conn.fetchrow(query_count, category_id)
        total_items = total_items_row["count"] if total_items_row else 0
        if items:
            items_list = [ItemInResponse(**item) for item in items]
        else:
            items_list = []
        return category, items_list, total_items

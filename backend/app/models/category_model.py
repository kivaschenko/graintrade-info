import asyncpg
from typing import List
from ..database import database
from ..schemas import (
    CategoryInDB,
    CategoryInResponse,
    CategoryWithItems,
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
    query = """
        SELECT id, name, description, ua_name, ua_description
        FROM categories
    """
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(query)
        return [CategoryInResponse(**row) for row in rows]


async def get_by_id(category_id: int) -> CategoryInResponse:
    query = """
        SELECT id, name, description, ua_name, ua_description
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
    category_id: int, offset: int, limit: int
) -> CategoryWithItems:
    query = """
        SELECT c.id, c.name, c.description, c.ua_name, c.ua_description, i.id, i.title
        FROM categories c
        JOIN items i ON c.id = i.category_id
        WHERE c.id = $1
    """
    query2 = """
        SELECT id, uuid, category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        FROM items
        WHERE category_id = $1
        ORDER BY id DESC
        OFFSET $2
        LIMIT $3
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, category_id)
        if row is None:
            raise ValueError("Category not found")
        category = CategoryWithItems(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            ua_name=row["ua_name"],
            ua_description=row["ua_description"],
            items=[],
        )
        items = await conn.fetch(query2, category_id, offset, limit)
        print(f"Items within category query: {items}")
        if items:
            category.items = [ItemInResponse(**item) for item in items]
        return category

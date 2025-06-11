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
    category_id: int, offset: int, limit: int
) -> tuple[CategoryInResponse, List[ItemInResponse]]:
    query = """
        SELECT id, name, description, ua_name, ua_description, parent_category, parent_category_ua
        FROM categories_hierarchy 
        WHERE id = $1
    """
    query2 = """
        SELECT 
            id, uuid, category_id, offer_type, title, description, price, currency, 
            amount, measure, terms_delivery, country, region, latitude, longitude, created_at
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
        category = CategoryInResponse(**row)
        items = await conn.fetch(query2, category_id, offset, limit)
        if items:
            items_list = [ItemInResponse(**item) for item in items]
        return category, items_list

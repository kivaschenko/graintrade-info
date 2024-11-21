from typing import List
from abc import ABC, abstractmethod
import asyncpg
from app.routers.schemas import (
    CategoryInDB,
    CategoryInResponse,
    CategoryInResponseWithItems,
)


class AbstractCategoryRepository(ABC):
    @abstractmethod
    async def create(self, category: CategoryInDB) -> CategoryInResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[CategoryInResponse]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, category_id: int) -> CategoryInResponse:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self, category_id: int, category: CategoryInDB
    ) -> CategoryInResponse:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, category_id: int) -> None:
        raise NotImplementedError


class AsyncpgCategoryRepository(AbstractCategoryRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def create(self, category: CategoryInDB) -> CategoryInResponse:
        query = """
            INSERT INTO categories (name, description, ua_name, ua_description)
            VALUES ($1, $2, $3, $4)
            RETURNING id, name, description, ua_name, ua_description
        """
        async with self.conn as connection:
            try:
                row = await connection.fetchrow(
                    query,
                    category.name,
                    category.description,
                    category.ua_name,
                    category.ua_description,
                )
                return CategoryInResponse(**row)
            except asyncpg.exceptions.UniqueViolationError:
                raise ValueError("Category with this name already exists")

    async def get_all(self) -> List[CategoryInResponse]:
        query = """
            SELECT id, name, description, ua_name, ua_description
            FROM categories
        """
        async with self.conn as connection:
            rows = await connection.fetch(query)
            return [CategoryInResponse(**row) for row in rows]

    async def get_by_id(self, category_id: int) -> CategoryInResponse:
        query = """
            SELECT id, name, description, ua_name, ua_description
            FROM categories
            WHERE id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, category_id)
            if row is None:
                raise ValueError("Category not found")
            return CategoryInResponse(**row)

    async def update(
        self, category_id: int, category: CategoryInDB
    ) -> CategoryInResponse:
        query = """
            UPDATE categories
            SET name = $2, description = $3, ua_name = $4, ua_description = $5
            WHERE id = $1
            RETURNING id, name, description, ua_name, ua_description
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
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

    async def delete(self, category_id: int) -> None:
        query = """
            DELETE FROM categories
            WHERE id = $1
        """
        async with self.conn as connection:
            await connection.execute(query, category_id)

    async def get_by_id_with_items(
        self, category_id: int
    ) -> CategoryInResponseWithItems:
        query = """
            SELECT c.id, c.name, c.description, c.ua_name, c.ua_description, i.id, i.title
            FROM categories c
            JOIN items i ON c.id = i.category_id
            WHERE c.id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, category_id)
            if row is None:
                raise ValueError("Category not found")
            return CategoryInResponseWithItems(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                ua_name=row["ua_name"],
                ua_description=row["ua_description"],
                items=[{"id": row["id"], "title": row["title"]}],
            )

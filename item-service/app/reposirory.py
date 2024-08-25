# repository.py
# is responsible for interacting with the database. It contains functions to create, retrieve,
# update, and delete items from the database. It uses the asyncpg library to interact with the
# PostgreSQL database. The repository pattern is used to separate the data access logic from the
# business logic of the application. The repository pattern makes it easier to test the data access
# logic in isolation from the rest of the application.
from typing import List
from abc import ABC, abstractmethod
import asyncpg
from .schemas import ItemInDB, ItemInResponse


class AbstractItemRepository(ABC):
    @abstractmethod
    async def create(self, item: ItemInDB) -> ItemInResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[ItemInResponse]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, item_id: int) -> ItemInResponse:
        raise NotImplementedError

    @abstractmethod
    async def update(self, item_id: int, item: ItemInDB) -> ItemInResponse:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, item_id: int) -> None:
        raise NotImplementedError


class AsyncpgItemRepository(AbstractItemRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def create(self, item: ItemInDB, user_id: int) -> ItemInResponse:
        query = """
            INSERT INTO items (title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, geom)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::numeric, $11::numeric, ST_SetSRID(ST_MakePoint($11::numeric, $10::numeric), 4326))
            RETURNING id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
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
            item = ItemInResponse(**row)
        return item

    async def get_all(self, offset: int, limit: int) -> List[ItemInResponse]:
        query = """
            SELECT id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
            FROM items
            ORDER BY id DESC
            OFFSET $1
            LIMIT $2
        """
        async with self.conn as connection:
            rows = await connection.fetch(query, offset, limit)
        return [ItemInResponse(**row) for row in rows]

    async def get_by_id(self, item_id: int) -> ItemInResponse:
        query = """
            SELECT id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
            FROM items
            WHERE id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, item_id)
        return ItemInResponse(**row)

    async def update(
        self, item_id: int, user_id: int, item: ItemInDB
    ) -> ItemInResponse:
        query = """
            UPDATE items
            SET title = $1, description = $2, price = $3, currency = $4, amount = $5, measure = $6, terms_delivery = $7, country = $8, region = $9, latitude = $10, longitude = $11
            WHERE id = $12 AND id IN (SELECT item_id FROM items_users WHERE user_id = $13)
            RETURNING id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
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
                item_id,
                user_id,
            )
        return ItemInResponse(**row)

    async def delete(self, item_id: int, user_id: int) -> None:
        query = """
            DELETE FROM items_users
            WHERE item_id = $1, user_id = $2
        """
        query2 = """
            DELETE FROM items
            WHERE id = $1
        """
        try:
            async with self.conn as connection:
                await connection.execute(query, item_id, user_id)
                await connection.execute(query2, item_id)
        except asyncpg.exceptions.ForeignKeyViolationError:
            raise ValueError("Item does not belong to the user")

    async def get_items_by_user_id(self, user_id: int) -> List[ItemInResponse]:
        query = """
            SELECT i.id, i.title, i.description, i.price, i.currency, i.amount, i.measure, i.terms_delivery, i.country, i.region, i.latitude, i.longitude, i.created_at
            FROM items i
            JOIN items_users iu ON i.id = iu.item_id
            WHERE iu.user_id = $1
        """
        async with self.conn as connection:
            rows = await connection.fetch(query, user_id)
        return [ItemInResponse(**row) for row in rows]

    async def find_in_distance(
        self, longitude: float, latitude: float, distance: int
    ) -> List[ItemInResponse]:
        query = """
            SELECT id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
            FROM items
            WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography, $3)
        """
        async with self.conn as connection:
            rows = await connection.fetch(query, longitude, latitude, distance)
        return [ItemInResponse(**row) for row in rows]

    async def get_filtered_items(
        self,
        min_price: float,
        max_price: float,
        currency: str,
        min_amount: int,
        max_amount: int,
        measure: str,
        terms_delivery: str,
        country: str,
        region: str,
    ) -> List[ItemInResponse]:
        query = """
            SELECT id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
            FROM items
            WHERE (price >= $1 OR $1 IS NULL) AND (price <= $2 OR $2 IS NULL) AND (currency = $3 OR $3 IS NULL) AND (amount >= $4 OR $4 IS NULL) AND (amount <= $5 OR $5 IS NULL) AND (measure = $6 OR $6 IS NULL) AND (terms_delivery = $7 OR $7 IS NULL) AND (country = $8 OR $8 IS NULL) AND (region = $9 OR $9 IS NULL)
        """
        async with self.conn as connection:
            rows = await connection.fetch(
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

    async def create_many(
        self, items: List[ItemInDB], user_id: int
    ) -> List[ItemInResponse]:
        query = """
            INSERT INTO items (title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, geom)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::numeric, $11::numeric, ST_SetSRID(ST_MakePoint($11::numeric, $10::numeric), 4326))
            RETURNING id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        """
        query2 = """
            INSERT INTO items_users (item_id, user_id)
            VALUES ($1, $2)
        """
        async with self.conn as connection:
            items_list = []
            for item in items:
                row = await connection.fetchrow(
                    query,
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
                items_list.append(ItemInResponse(**row))
                await connection.execute(query2, row["id"], user_id)
        return items_list


# User and Item repositories


class AbstractItemUserRepository(ABC):
    @abstractmethod
    async def add_item_to_user(self, user_id: int, item_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove_item_from_user(self, user_id: int, item_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_items_by_user_id(self, user_id: int) -> List[int]:
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> None:
        raise NotImplementedError


class AsyncpgItemUserRepository(AbstractItemUserRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def add_item_to_user(self, user_id: int, item_id: int) -> None:
        query = """
            INSERT INTO items_users (user_id, item_id)
            VALUES ($1, $2)
        """
        async with self.conn as connection:
            await connection.execute(query, user_id, item_id)

    async def remove_item_from_user(self, user_id: int, item_id: int) -> None:
        query = """
            DELETE FROM items_users
            WHERE user_id = $1 AND item_id = $2
        """
        query2 = """
            DELETE FROM items
            WHERE id = $1
        """
        async with self.conn as connection:
            await connection.execute(query, user_id, item_id)
            await connection.execute(query2, item_id)

    async def get_items_by_user_id(self, user_id: int) -> List[int]:
        query = """
            SELECT item_id
            FROM items_users
            WHERE user_id = $1
        """
        async with self.conn as connection:
            rows = await connection.fetch(query, user_id)
        return [row["item_id"] for row in rows]

    async def delete_all(self) -> None:
        query = """
            DELETE FROM items_users
        """
        async with self.conn as connection:
            await connection.execute(query)

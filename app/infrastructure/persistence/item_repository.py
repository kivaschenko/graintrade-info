from abc import ABC, abstractmethod
import asyncpg
from typing import List
from datetime import date, timedelta, timezone
from app.domain.entities.item import ItemInDB, ItemInResponse


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

    async def create(self, item: ItemInDB, username: str) -> ItemInResponse:
        query = """
            INSERT INTO items (title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, geom)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::numeric, $11::numeric, ST_SetSRID(ST_MakePoint($11::numeric, $10::numeric), 4326))
            RETURNING id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        """
        query2 = """
            INSERT INTO items_users (item_id, user_id)
            VALUES ($1, (SELECT id FROM users WHERE username = $2))
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
            await connection.execute(query2, item.id, username)
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

    async def update(self, item_id: int, item: ItemInDB) -> ItemInResponse:
        query = """
            UPDATE items
            SET title = $1, description = $2, price = $3, currency = $4, amount = $5, measure = $6, terms_delivery = $7, country = $8, region = $9, latitude = $10, longitude = $11
            WHERE id = $12
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
            )
        return ItemInResponse(**row)

    async def delete(self, item_id: int) -> None:
        query = """
            DELETE FROM items
            WHERE id = $1
        """
        query2 = """
            DELETE FROM items_users
            WHERE item_id = $1
        """
        async with self.conn as connection:
            await connection.execute(query, item_id)
            await connection.execute(query2, item_id)

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


class InMemoryItemRepository(AbstractItemRepository):
    def __init__(self) -> None:
        self.items = {}
        self.current_id = 1

    async def create(
        self, item: ItemInDB, username: str = "test_user_123"
    ) -> ItemInResponse:
        item_id = self.current_id
        self.current_id += 1
        item_dict = item.model_dump()
        item_dict["id"] = item_id
        item_dict["created_at"] = date.today().isoformat()
        self.items[item_id] = item_dict
        return ItemInResponse(**item_dict)

    async def get_all(self) -> List[ItemInResponse]:
        return [item for item in self.items.values()]

    async def get_by_id(self, item_id: int) -> ItemInResponse:
        item = self.items.get(item_id)
        if item:
            return ItemInResponse(**item)
        return None

    async def update(self, item_id: int, item: ItemInDB) -> ItemInResponse:
        if item_id not in self.items:
            return None
        item_dict = item.model_dump()
        item_dict["id"] = item_id
        item_dict["created_at"] = self.items[item_id]["created_at"]
        self.items[item_id] = item_dict
        return ItemInResponse(**item_dict)

    async def delete(self, item_id: int) -> None:
        if item_id in self.items:
            del self.items[item_id]
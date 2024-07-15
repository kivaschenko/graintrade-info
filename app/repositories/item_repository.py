from abc import ABC, abstractmethod
import asyncpg
from typing import List
from app.schemas import ItemInDB, ItemInResponse


class ItemRepository(ABC):
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

    @abstractmethod
    async def delete_all(self) -> None:
        pass


class AsyncpgItemRepository(ItemRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def create(self, item: ItemInDB) -> ItemInResponse:
        query = """
            INSERT INTO items (title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
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
            print(row, type(row))
        return ItemInResponse(**row)

    async def get_all(self) -> List[ItemInResponse]:
        query = """
            SELECT id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
            FROM items
            ORDER BY id DESC LIMIT 100
        """
        async with self.conn as connection:
            rows = await connection.fetch(query)
            print(f"rows: {rows}")
        return [ItemInResponse(**row) for row in rows]

    async def get_by_id(self, item_id: int) -> ItemInResponse:
        query = """
            SELECT id, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
            FROM items
            WHERE id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, item_id)
            print(f"row: {row}")
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
            print(f"row: {row}")
        return ItemInResponse(**row)

    async def delete(self, item_id: int) -> None:
        query = """
            DELETE FROM items
            WHERE id = $1
        """
        async with self.conn as connection:
            await connection.execute(query, item_id)

    async def delete_all(self) -> None:
        query = """
            DELETE FROM items
        """
        async with self.conn as connection:
            await connection.execute(query)

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


class FakeItemRepository(ItemRepository):
    def __init__(self, items: list = []) -> None:
        self.items = items

    async def create(self, item: ItemInDB) -> ItemInResponse:
        item_id = len(self.items) + 1
        item_in_response = ItemInResponse(id=item_id, **item.model_dump())
        self.items.append(item_in_response)
        return item_in_response

    async def get_all(self) -> List[ItemInResponse]:
        return self.items

    async def get_by_id(self, item_id: int) -> ItemInResponse:
        for item in self.items:
            if item.id == item_id:
                return item

    async def update(self, item_id: int, item: ItemInDB) -> ItemInResponse:
        for i, item_in_response in enumerate(self.items):
            if item_in_response.id == item_id:
                self.items[i] = ItemInResponse(id=item_id, **item.model_dump())
                return self.items[i]

    async def delete(self, item_id: int) -> None:
        for i, item in enumerate(self.items):
            if item.id == item_id:
                del self.items[i]
                break

    async def delete_all(self) -> None:
        self.items = []

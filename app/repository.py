# repository.py
# is responsible for interacting with the database. It contains functions to create, retrieve,
# update, and delete items from the database. It uses the asyncpg library to interact with the
# PostgreSQL database. The repository pattern is used to separate the data access logic from the
# business logic of the application. The repository pattern makes it easier to test the data access
# logic in isolation from the rest of the application.
from typing import List
from abc import ABC, abstractmethod
import asyncpg
from .schemas import ItemInDB, ItemInResponse, UserInDB, UserInResponse


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
            INSERT INTO items (category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, geom)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::numeric, $13::numeric, ST_SetSRID(ST_MakePoint($13::numeric, $12::numeric), 4326))
            RETURNING id, uuid, category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        """
        query2 = """INSERT INTO items_users (item_id, user_id) VALUES ($1, $2)"""
        async with self.conn as connection:
            try:
                row = await connection.fetchrow(
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
                item = ItemInResponse(**row)
                await connection.execute(query2, item.id, user_id)
                return item
            except asyncpg.exceptions.ConnectionFailureError:
                raise ValueError("Connection to the database failed")

    async def get_all(self, offset: int, limit: int) -> List[ItemInResponse]:
        query = """
            SELECT id, uuid, category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
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
            SELECT id, uuid, category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
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
            SET category_id = $1, offer_type = $2, title = $3, description = $4, price = $5, currency = $6, amount = $7, measure = $8, terms_delivery = $9, country = $10, region = $11, latitude = $12, longitude = $13, geom = ST_SetSRID(ST_MakePoint($13::numeric, $12::numeric), 4326)
            WHERE id = $14 AND id IN (SELECT item_id FROM items_users WHERE user_id = $15)
            RETURNING id, uuid, category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
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
                item_id,
                user_id,
            )
        return ItemInResponse(**row)

    async def delete(self, item_id: int, user_id: int) -> None:
        query = "DELETE FROM items_users WHERE item_id = $1 AND user_id = $2"
        query2 = "DELETE FROM items WHERE id = $1"
        try:
            async with self.conn as connection:
                await connection.execute(query, item_id, user_id)
                await connection.execute(query2, item_id)
        except asyncpg.exceptions.ForeignKeyViolationError:
            raise ValueError("Item does not belong to the user")

    async def get_items_by_user_id(self, user_id: int) -> List[ItemInResponse]:
        query = """
            SELECT i.id, i.uuid, i.category_id, i.offer_type, i.title, i.description, i.price, i.currency, i.amount, i.measure, i.terms_delivery, i.country, i.region, i.latitude, i.longitude, i.created_at
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
            SELECT id, uuid, category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
            FROM items
            WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography, $3)
        """
        async with self.conn as connection:
            rows = await connection.fetch(query, longitude, latitude, distance)
        return [ItemInResponse(**row) for row in rows]

    async def get_filtered_items(
        self,
        min_price: float = None,
        max_price: float = None,
        currency: str = None,
        min_amount: int = None,
        max_amount: int = None,
        measure: str = None,
        terms_delivery: str = None,
        country: str = None,
        region: str = None,
    ) -> List[ItemInResponse]:
        query = """
            SELECT id, uuid, category_id, offer_type, title, description, price, currency, amount, measure, terms_delivery, country, region, latitude, longitude, created_at
            FROM items
            WHERE ($1::float IS NULL OR price >= $1) AND ($2::float IS NULL OR price <= $2) AND ($3::text IS NULL OR currency = $3) AND ($4::int IS NULL OR amount >= $4) AND ($5::int IS NULL OR amount <= $5) AND ($6::text IS NULL OR measure = $6) AND ($7::text IS NULL OR terms_delivery = $7) AND ($8::text IS NULL OR country = $8) AND ($9::text IS NULL OR region = $9)
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


class AbstractUserRepository(ABC):
    @abstractmethod
    async def create(self, user: UserInDB) -> UserInResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[UserInResponse]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> UserInResponse:
        raise NotImplementedError

    @abstractmethod
    async def update(self, user_id: int, user: UserInDB) -> UserInResponse:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> None:
        pass


class AsyncpgUserRepository(AbstractUserRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def create(self, user: UserInDB) -> UserInResponse:
        query = """
            INSERT INTO users (username, email, full_name, hashed_password)
            VALUES ($1, $2, $3, $4)
            RETURNING id, username, email, full_name, hashed_password, disabled
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                user.username,
                user.email,
                user.full_name,
                user.hashed_password,
            )
        return UserInResponse(**row)

    async def get_all(self) -> List[UserInResponse]:
        query = """
            SELECT id, username, email, full_name, disabled, hashed_password
            FROM users
        """
        async with self.conn as connection:
            rows = await connection.fetch(query)
        return [UserInResponse(**row) for row in rows]

    async def get_by_id(self, user_id: int) -> UserInResponse:
        query = """
            SELECT id, username, email, full_name, disabled, hashed_password
            FROM users
            WHERE id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, user_id)
        return UserInResponse(**row)

    async def update(self, user_id: int, user: UserInDB) -> UserInResponse:
        query = """
            UPDATE users
            SET username = $1, email = $2, full_name = $3, hashed_password = $4
            WHERE id = $5
            RETURNING id, username, email, full_name, disabled, hashed_password
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                user.username,
                user.email,
                user.full_name,
                user.hashed_password,
                user_id,
            )
        return UserInResponse(**row)

    async def delete(self, user_id: int) -> None:
        query = """
            DELETE FROM users
            WHERE id = $1
        """
        async with self.conn as connection:
            await connection.execute(query, user_id)

    async def delete_all(self) -> None:
        query = """
            DELETE FROM users
        """
        async with self.conn as connection:
            await connection.execute(query)

    async def get_by_username(self, username: str) -> UserInResponse:
        query = """
            SELECT id, username, email, full_name, hashed_password, disabled
            FROM users
            WHERE username = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, username)
        return UserInResponse(**row)

    async def get_by_email(self, email: str) -> UserInResponse:
        query = """
            SELECT id, username, email, full_name, disabled, hashed_password
            FROM users
            WHERE email = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, email)
        return UserInResponse(**row)

    async def get_by_username_and_email(
        self, username: str, email: str
    ) -> UserInResponse:
        query = """
            SELECT id, username, email, full_name, disabled, hashed_password
            FROM users
            WHERE username = $1 AND email = $2
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, username, email)
        return UserInResponse(**row)


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

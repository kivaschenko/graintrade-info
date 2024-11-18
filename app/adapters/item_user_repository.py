from typing import List
from abc import ABC, abstractmethod
import asyncpg


# User and Item repositories
# The AbstractItemUserRepository class defines the interface for interacting with the items_users table in the database.
# It contains abstract methods for adding and removing items from users, getting items by user ID, and deleting all items.
# The AsyncpgItemUserRepository class implements the methods defined in the AbstractItemUserRepository class.


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

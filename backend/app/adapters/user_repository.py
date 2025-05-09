from typing import List
from abc import ABC, abstractmethod
import asyncpg
from ..routers.schemas import UserInDB, UserInResponse

# User repositories
# The AbstractUserRepository class defines the interface for interacting with users in the database.
# It contains abstract methods for creating, retrieving, updating, and deleting users. The AsyncpgUserRepository


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
            INSERT INTO users (username, email, full_name, phone, hashed_password)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, username, email, full_name, phone, hashed_password, disabled
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                user.username,
                user.email,
                user.full_name,
                user.phone,
                user.hashed_password,
            )
        return UserInResponse(**row)

    async def get_all(self) -> List[UserInResponse]:
        query = """
            SELECT id, username, email, full_name, phone, disabled, hashed_password
            FROM users
        """
        async with self.conn as connection:
            rows = await connection.fetch(query)
        return [UserInResponse(**row) for row in rows]

    async def get_by_id(self, user_id: int) -> UserInResponse:
        query = """
            SELECT id, username, email, full_name, phone, disabled, hashed_password
            FROM users
            WHERE id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, user_id)
        return UserInResponse(**row)

    async def update(self, user_id: int, user: UserInDB) -> UserInResponse:
        query = """
            UPDATE users
            SET username = $1, email = $2, full_name = $3, hashed_password = $4, phone = $5
            WHERE id = $6
            RETURNING id, username, email, full_name, phone, disabled, hashed_password
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                user.username,
                user.email,
                user.full_name,
                user.hashed_password,
                user.phone,
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
            SELECT id, username, email, full_name, phone, hashed_password, disabled
            FROM users
            WHERE username = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, username)
        return UserInResponse(**row)

    async def get_by_email(self, email: str) -> UserInResponse:
        query = """
            SELECT id, username, email, full_name, phone, disabled, hashed_password
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
            SELECT id, username, email, full_name, phone, disabled, hashed_password
            FROM users
            WHERE username = $1 AND email = $2
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, username, email)
        return UserInResponse(**row)

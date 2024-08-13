from abc import ABC, abstractmethod
import asyncpg
from typing import List
from app.domain.subscription import SubscribtionInDB, SubscribtionInResponse


class AbstractSubscribtionRepository(ABC):
    @abstractmethod
    async def create(self, subscribtion: SubscribtionInDB) -> SubscribtionInResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[SubscribtionInResponse]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, subscribtion_id: int) -> SubscribtionInResponse:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self, subscribtion_id: int, item: SubscribtionInDB
    ) -> SubscribtionInResponse:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, item_id: int) -> None:
        raise NotImplementedError


class AsyncpgSubscribtionRepository(AbstractSubscribtionRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def create(self, subscribtion: SubscribtionInDB) -> SubscribtionInResponse:
        query = """
            INSERT INTO subscribtions (user_id, tarif_id, start_date, end_date, status)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, user_id, tarif_id, start_date, end_date, status, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                subscribtion.user_id,
                subscribtion.tarif_id,
                subscribtion.start_date,
                subscribtion.end_date,
                subscribtion.status,
            )
            subscribtion = SubscribtionInResponse(**row)
            return subscribtion

    async def get_all(self) -> List[SubscribtionInResponse]:
        query = """
            SELECT id, user_id, tarif_id, start_date, end_date, status, created_at
            FROM subscribtions
        """
        async with self.conn as connection:
            rows = await connection.fetch(query)
            return [SubscribtionInResponse(**row) for row in rows]

    async def get_by_id(self, subscribtion_id: int) -> SubscribtionInResponse:
        query = """
            SELECT id, user_id, tarif_id, start_date, end_date, status, created_at
            FROM subscribtions
            WHERE id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, subscribtion_id)
            return SubscribtionInResponse(**row)

    async def update(
        self, subscribtion_id: int, subscribtion: SubscribtionInDB
    ) -> SubscribtionInResponse:
        query = """
            UPDATE subscribtions
            SET user_id = $1, tarif_id = $2, start_date = $3, end_date = $4, status = $5
            WHERE id = $6
            RETURNING id, user_id, tarif_id, start_date, end_date, status, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                subscribtion.user_id,
                subscribtion.tarif_id,
                subscribtion.start_date,
                subscribtion.end_date,
                subscribtion.status,
                subscribtion_id,
            )
            return SubscribtionInResponse(**row)

    async def delete(self, subscribtion_id: int) -> None:
        query = """
            DELETE FROM subscribtions
            WHERE id = $1
        """
        async with self.conn as connection:
            await connection.execute(query, subscribtion_id)

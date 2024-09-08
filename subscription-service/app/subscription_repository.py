from abc import ABC, abstractmethod
import asyncpg
from typing import List
from app.schemas import SubscriptionInDB, SubscriptionInResponse


class AbstractSubscriptionRepository(ABC):
    @abstractmethod
    async def create(self, subscription: SubscriptionInDB) -> SubscriptionInResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[SubscriptionInResponse]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, subscription_id: int) -> SubscriptionInResponse:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self, subscription_id: int, item: SubscriptionInDB
    ) -> SubscriptionInResponse:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, item_id: int) -> None:
        raise NotImplementedError


class AsyncpgSubscriptionRepository(AbstractSubscriptionRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def create(self, subscription: SubscriptionInDB) -> SubscriptionInResponse:
        query = """
            INSERT INTO subscriptions (user_id, tarif_id, start_date, end_date, status)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, user_id, tarif_id, start_date, end_date, status, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                subscription.user_id,
                subscription.tarif_id,
                subscription.start_date,
                subscription.end_date,
                subscription.status,
            )
            subscription = SubscriptionInResponse(**row)
            return subscription

    async def get_all(self) -> List[SubscriptionInResponse]:
        query = """
            SELECT id, user_id, tarif_id, start_date, end_date, status, created_at
            FROM subscriptions
        """
        async with self.conn as connection:
            rows = await connection.fetch(query)
            return [SubscriptionInResponse(**row) for row in rows]

    async def get_by_id(self, subscription_id: int) -> SubscriptionInResponse:
        query = """
            SELECT id, user_id, tarif_id, start_date, end_date, status, created_at
            FROM subscriptions
            WHERE id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, subscription_id)
            if row is None:
                return None
            return SubscriptionInResponse(**row)

    async def update(
        self, subscription_id: int, subscription: SubscriptionInDB
    ) -> SubscriptionInResponse:
        query = """
            UPDATE subscriptions
            SET user_id = $1, tarif_id = $2, start_date = $3, end_date = $4, status = $5
            WHERE id = $6
            RETURNING id, user_id, tarif_id, start_date, end_date, status, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                subscription.user_id,
                subscription.tarif_id,
                subscription.start_date,
                subscription.end_date,
                subscription.status,
                subscription_id,
            )
            return SubscriptionInResponse(**row)

    async def delete(self, subscription_id: int) -> None:
        query = """
            DELETE FROM subscriptions
            WHERE id = $1
        """
        async with self.conn as connection:
            await connection.execute(query, subscription_id)
    
    async def get_by_user_id(self, user_id: int) -> List[SubscriptionInResponse]:
        query = """
            SELECT id, user_id, tarif_id, start_date, end_date, status, created_at
            FROM subscriptions
            WHERE user_id = $1 AND status = 'active' AND end_date > NOW()
            ORDER BY created_at DESC
        """
        async with self.conn as connection:
            rows = await connection.fetch(query, user_id)
            return [SubscriptionInResponse(**row) for row in rows]

    async def get_by_tarif_id(self, tarif_id: int) -> List[SubscriptionInResponse]:
        query = """
            SELECT id, user_id, tarif_id, start_date, end_date, status, created_at
            FROM subscriptions
            WHERE tarif_id = $1 AND status = 'active' AND end_date > NOW()
            ORDER BY created_at DESC
        """
        async with self.conn as connection:
            rows = await connection.fetch(query, tarif_id)
            return [SubscriptionInResponse(**row) for row in rows]
from abc import ABC, abstractmethod
import asyncpg
from typing import List
from app.routers.schemas import PaymentInDB, PaymentInResponse


class AbstractPaymentRepository(ABC):
    @abstractmethod
    async def create(self, payment: PaymentInDB) -> PaymentInResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[PaymentInResponse]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, payment_id: int) -> PaymentInResponse:
        raise NotImplementedError


class AsyncpgPaymentRepository(AbstractPaymentRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def create(self, payment: PaymentInDB) -> PaymentInResponse:
        query = """
            INSERT INTO payments (user_id, amount, currency, status, created_at)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, user_id, amount, currency, status, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                payment.user_id,
                payment.amount,
                payment.currency,
                payment.status,
                payment.created_at,
            )
            payment = PaymentInResponse(**row)
            return payment

    async def get_all(self) -> List[PaymentInResponse]:
        query = """
            SELECT id, user_id, amount, currency, status, created_at
            FROM payments
        """
        async with self.conn as connection:
            rows = await connection.fetch(query)
            return [PaymentInResponse(**row) for row in rows]

    async def get_by_id(self, payment_id: int) -> PaymentInResponse:
        query = """
            SELECT id, user_id, amount, currency, status, created_at
            FROM payments
            WHERE id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, payment_id)
            return PaymentInResponse(**row)

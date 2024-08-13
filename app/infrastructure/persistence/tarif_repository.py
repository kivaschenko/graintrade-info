from abc import ABC, abstractmethod
import asyncpg
from typing import List
from app.domain.tarif import TarifInDB, TarifInResponse


class AbstractTarifRepository(ABC):
    @abstractmethod
    async def create(self, tarif: TarifInDB) -> TarifInResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[TarifInResponse]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, tarif_id: int) -> TarifInResponse:
        raise NotImplementedError

    @abstractmethod
    async def update(self, tarif_id: int, item: TarifInDB) -> TarifInResponse:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, item_id: int) -> None:
        raise NotImplementedError


class AsyncpgTarifRepository(AbstractTarifRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def create(self, tarif: TarifInDB) -> TarifInResponse:
        query = """
            INSERT INTO tarifs (name, description, price, currency, scope, terms)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, name, description, price, currency, scope, terms, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                tarif.name,
                tarif.description,
                tarif.price,
                tarif.currency,
                tarif.scope,
                tarif.terms,
            )
            tarif = TarifInResponse(**row)
            return tarif

    async def get_all(self) -> List[TarifInResponse]:
        query = """
            SELECT id, name, description, price, currency, scope, terms, created_at
            FROM tarifs
        """
        async with self.conn as connection:
            rows = await connection.fetch(query)
            return [TarifInResponse(**row) for row in rows]

    async def get_by_id(self, tarif_id: int) -> TarifInResponse:
        query = """
            SELECT id, name, description, price, currency, scope, terms, created_at
            FROM tarifs
            WHERE id = $1
        """
        async with self.conn as connection:
            row = await connection.fetchrow(query, tarif_id)
            return TarifInResponse(**row)

    async def update(self, tarif_id: int, tarif: TarifInDB) -> TarifInResponse:
        query = """
            UPDATE tarifs
            SET name = $1, description = $2, price = $3, currency = $4, scope = $5, terms = $6
            WHERE id = $7
            RETURNING id, name, description, price, currency, scope, terms, created_at
        """
        async with self.conn as connection:
            row = await connection.fetchrow(
                query,
                tarif.name,
                tarif.description,
                tarif.price,
                tarif.currency,
                tarif.scope,
                tarif.terms,
                tarif_id,
            )
            return TarifInResponse(**row)

    async def delete(self, tarif_id: int) -> None:
        query = """
            DELETE FROM tarifs
            WHERE id = $1
        """
        async with self.conn as connection:
            await connection.execute(query, tarif_id)

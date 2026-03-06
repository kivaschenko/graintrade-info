import pytest
import asyncpg
from app.routers.schemas import TarifInDB, TarifInResponse
from app.tarif_repository import AsyncpgTarifRepository


@pytest.fixture
async def db_connection():
    conn = await asyncpg.connect(dsn="postgresql://user:password@localhost/testdb")
    yield conn
    await conn.close()


@pytest.fixture
async def tarif_repo(db_connection):
    return AsyncpgTarifRepository(conn=db_connection)


@pytest.mark.asyncio
async def test_create_tarif(tarif_repo):
    tarif = TarifInDB(
        name="Basic",
        description="Basic plan",
        price=9.99,
        currency="USD",
        scope="basic",
        terms="monthly",
    )
    created_tarif = await tarif_repo.create(tarif)
    assert created_tarif.name == tarif.name
    assert created_tarif.price == tarif.price


@pytest.mark.asyncio
async def test_get_all_tarifs(tarif_repo):
    tarifs = await tarif_repo.get_all()
    assert isinstance(tarifs, list)


@pytest.mark.asyncio
async def test_get_tarif_by_id(tarif_repo):
    tarif_id = 1
    tarif = await tarif_repo.get_by_id(tarif_id)
    assert tarif.id == tarif_id


@pytest.mark.asyncio
async def test_update_tarif(tarif_repo):
    tarif_id = 1
    updated_data = TarifInDB(
        name="Premium",
        description="Premium plan",
        price=19.99,
        currency="USD",
        scope="premium",
        terms="monthly",
    )
    updated_tarif = await tarif_repo.update(tarif_id, updated_data)
    assert updated_tarif.name == updated_data.name
    assert updated_tarif.price == updated_data.price


@pytest.mark.asyncio
async def test_delete_tarif(tarif_repo):
    tarif_id = 1
    await tarif_repo.delete(tarif_id)
    with pytest.raises(asyncpg.exceptions.NoDataFoundError):
        await tarif_repo.get_by_id(tarif_id)

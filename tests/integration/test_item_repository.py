import pytest
import asyncpg

from app.infrastructure.persistence.item_repository import AsyncpgItemRepository
from app.infrastructure.persistence.user_repository import AsyncpgUserRepository
from app.domain.entities.item import ItemInDB
from app.domain.entities.user import UserInDB
from .test_config import TEST_DATABASE_URL


@pytest.fixture(scope="module")
async def db_connection():
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    yield conn
    await conn.close()


@pytest.fixture(scope="module")
async def fake_user(db_connection=db_connection):
    user_repository = AsyncpgUserRepository(db_connection)
    user_data = UserInDB(
        username="testuser",
        email="test-user@email.com",
        full_name="Test User",
        hashed_password="hashed_password",
    )
    user = await user_repository.create(user_data)
    yield user
    await user_repository.delete(user.id)


@pytest.fixture(scope="module")
async def repo(db_connection):
    repository = AsyncpgItemRepository(db_connection)
    yield repository


@pytest.fixture(scope="function", autouse=True)
async def clean_db(db_connection):
    await db_connection.execute("TRUNCATE TABLE items RESTART IDENTITY CASCADE;")
    yield
    await db_connection.execute("TRUNCATE TABLE items RESTART IDENTITY CASCADE;")
    await db_connection.execute(
        "DELETE FROM users WHERE username='testuser' AND email='test-user@email.com';"
    )


# Test create item
@pytest.mark.asyncio
async def test_create_item(repo):
    async for repository in repo:
        item = ItemInDB(
            title="Test Item",
            description="A test item",
            price=10.0,
            currency="USD",
            amount=5,
            measure="kg",
            terms_delivery="FOB",
            country="USA",
            region="CA",
            latitude=34.0522,
            longitude=-118.2437,
        )
        created_item = await repository.create(item, "testuser")
        assert created_item.id == 1
        assert created_item.title == "Test Item"
        assert created_item.description == "A test item"
        assert created_item.price == 10.0
        assert created_item.currency == "USD"
        assert created_item.amount == 5
        assert created_item.measure == "kg"
        assert created_item.terms_delivery == "FOB"
        assert created_item.country == "USA"
        assert created_item.region == "CA"
        assert created_item.latitude == 34.0522
        assert created_item.longitude == -118.2437
        assert created_item.created_at is not None


# Test get all items
@pytest.mark.asyncio
async def test_get_all_items(repo):
    async for repository in repo:
        item1 = ItemInDB(
            title="Test Item 1",
            description="A test item 1",
            price=10.0,
            currency="USD",
            amount=1,
            measure="piece",
            terms_delivery="FOB",
            country="USA",
            region="CA",
            latitude=34.0522,
            longitude=-118.2437,
        )
        item2 = ItemInDB(
            title="Test Item 2",
            description="A test item 2",
            price=20.0,
            currency="USD",
            amount=2,
            measure="piece",
            terms_delivery="CIF",
            country="USA",
            region="NY",
            latitude=40.7128,
            longitude=-74.0060,
        )
        username = "test_user"
        await repository.create(item1, username)
        await repository.create(item2, username)
        items = await repository.get_all(0, 10)
        assert len(items) == 2
        assert items[0].title == item2.title
        assert items[1].title == item1.title

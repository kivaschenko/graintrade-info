import pytest
from app.domain.entities.item import ItemInDB
from app.infrastructure.persistence.item_repository import InMemoryItemRepository


@pytest.fixture
def repo():
    return InMemoryItemRepository()


@pytest.mark.asyncio
async def test_create_item(repo):
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
    created_item = await repo.create(item)
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


@pytest.mark.asyncio
async def test_get_item(repo):
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
    created_item = await repo.create(item)
    retrieved_item = await repo.get_by_id(created_item.id)
    assert retrieved_item == created_item


@pytest.mark.asyncio
async def test_get_all_items(repo):
    item1 = ItemInDB(
        title="Test Item 1",
        description="A test item 1",
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
    item2 = ItemInDB(
        title="Test Item 2",
        description="A test item 2",
        price=20.0,
        currency="USD",
        amount=10,
        measure="kg",
        terms_delivery="FOB",
        country="USA",
        region="CA",
        latitude=34.0522,
        longitude=-118.2437,
    )
    await repo.create(item1)
    await repo.create(item2)
    items = await repo.get_all()
    assert len(items) == 2
    assert items[0]["title"] == "Test Item 1"
    assert items[1]["title"] == "Test Item 2"


@pytest.mark.asyncio
async def test_update_item(repo):
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
    created_item = await repo.create(item)
    updated_item = ItemInDB(
        title="Updated Item",
        description="An updated item",
        price=20.0,
        currency="USD",
        amount=10,
        measure="kg",
        terms_delivery="FOB",
        country="USA",
        region="CA",
        latitude=34.0522,
        longitude=-118.2437,
    )
    updated_item = await repo.update(created_item.id, updated_item)
    assert updated_item.id == 1
    assert updated_item.title == "Updated Item"
    assert updated_item.description == "An updated item"
    assert updated_item.price == 20.0
    assert updated_item.currency == "USD"
    assert updated_item.amount == 10
    assert updated_item.measure == "kg"
    assert updated_item.terms_delivery == "FOB"
    assert updated_item.country == "USA"
    assert updated_item.region == "CA"
    assert updated_item.latitude == 34.0522
    assert updated_item.longitude == -118.2437
    assert updated_item.created_at is not None


@pytest.mark.asyncio
async def test_delete_item(repo):
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
    created_item = await repo.create(item)
    await repo.delete(created_item.id)
    items = await repo.get_all()
    assert len(items) == 0

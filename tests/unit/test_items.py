import pytest
from app.domain.entities.item import ItemInDB
from app.infrastructure.persistence.item_repository import InMemoryItemRepository


@pytest.mark.asyncio
async def test_create_item():
    repo = InMemoryItemRepository()
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

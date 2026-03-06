import pytest
from unittest.mock import AsyncMock
from app.adapters.item_repository import AsyncpgItemRepository
from app.routers.schemas import ItemInDB, ItemInResponse
from collections import namedtuple

# Create a Record-like namedtuple
FakeRecord = namedtuple(
    "FakeRecord",
    [
        "id",
        "uuid",
        "category_id",
        "offer_type",
        "title",
        "description",
        "price",
        "currency",
        "amount",
        "measure",
        "terms_delivery",
        "country",
        "region",
        "latitude",
        "longitude",
        "created_at",
    ],
)


@pytest.mark.asyncio
async def test_create_item_unit():
    # Mock the asyncpg connection
    mock_conn = AsyncMock()

    # Define the input item
    mock_item = ItemInDB(
        category_id=1,
        offer_type="sell",
        title="Test Wheat",
        description="Test description",
        price=100.0,
        currency="USD",
        amount=20,
        measure="tons",
        terms_delivery="FOB",
        country="Ukraine",
        region="Kyiv",
        latitude=50.4501,
        longitude=30.5234,
    )

    # Define the mock return value for fetchrow

    mock_record = FakeRecord(
        id=1,
        uuid="fake-uuid",
        category_id=1,
        offer_type="sell",
        title="Test Wheat",
        description="Mock test order",
        price=100.0,
        currency="USD",
        amount=20,
        measure="tons",
        terms_delivery="FOB",
        country="Ukraine",
        region="Kyiv",
        latitude=50.45,
        longitude=30.52,
        created_at="2024-04-22T00:00:00",
    )
    # Configure the mock to return the expected row
    mock_conn.fetchrow = AsyncMock(
        return_value=mock_record,
    )
    mock_conn.execute = AsyncMock()

    # Create an instance of the repository with the mock connection
    repo = AsyncpgItemRepository(mock_conn)

    # Call the create method
    result = await repo.create(mock_item, user_id=1)

    # Assert that the result matches the expected output
    assert isinstance(result, ItemInResponse)
    assert result.id == 1
    assert result.uuid == "fake-uuid"
    assert result.title == "Test Wheat"
    assert result.description == "Mock test order"
    assert result.price == 100.0
    assert result.currency == "USD"
    assert result.amount == 20
    assert result.measure == "tons"
    assert result.terms_delivery == "FOB"
    assert result.country == "Ukraine"
    assert result.region == "Kyiv"
    assert result.latitude == 50.45
    assert result.longitude == 30.52

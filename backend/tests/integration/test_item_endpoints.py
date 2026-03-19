import pytest


@pytest.mark.asyncio
async def test_create_order_endpoint(test_client):
    payload = {
        "category_id": 1,
        "offer_type": "sell",
        "title": "Wheat",
        "description": "Test wheat order",
        "price": 250,
        "currency": "USD",
        "amount": 100,
        "measure": "tons",
        "terms_delivery": "EXW",
        "country": "Ukraine",
        "region": "Lviv",
        "latitude": 49.84,
        "longitude": 24.03,
    }

    response = await test_client.post("/items", json=payload)
    assert response.status_code == 201
    assert "title" in response.json()

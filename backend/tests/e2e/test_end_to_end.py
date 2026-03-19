import requests


BASE_URL = "http://localhost:8000"


def test_order_workflow():
    url = f"{BASE_URL}/items"
    payload = {
        "category_id": 1,
        "offer_type": "sell",
        "title": "Corn",
        "description": "Fresh corn",
        "price": 150,
        "currency": "USD",
        "amount": 200,
        "measure": "tons",
        "terms_delivery": "CIF",
        "country": "Ukraine",
        "region": "Odesa",
        "latitude": 46.48,
        "longitude": 30.73,
    }

    r = requests.post(url, json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Corn"
    assert data["country"] == "Ukraine"


def test_health_endpoint():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_items_listing_includes_created_item():
    create_payload = {
        "category_id": 1,
        "offer_type": "buy",
        "title": "Wheat",
        "description": "Bulk wheat request",
        "price": 190,
        "currency": "USD",
        "amount": 150,
        "measure": "tons",
        "terms_delivery": "FOB",
        "country": "Ukraine",
        "region": "Kyiv",
        "latitude": 50.45,
        "longitude": 30.52,
    }

    post_response = requests.post(f"{BASE_URL}/items", json=create_payload)
    assert post_response.status_code == 201

    list_response = requests.get(f"{BASE_URL}/items", params={"limit": 5})
    assert list_response.status_code == 200
    payload = list_response.json()
    assert "items" in payload
    assert payload["total_items"] >= 1
    assert any(item["title"] == "Wheat" for item in payload["items"])


def test_protected_endpoint_rejects_invalid_token():
    headers = {"Authorization": "Bearer invalid-token"}
    payload = {
        "category_id": 1,
        "offer_type": "sell",
        "title": "Invalid",
        "description": "Should fail",
        "price": 100,
        "currency": "USD",
        "amount": 10,
        "measure": "tons",
        "terms_delivery": "CIF",
        "country": "Ukraine",
        "region": "Lviv",
        "latitude": 49.84,
        "longitude": 24.03,
    }
    response = requests.post(f"{BASE_URL}/items", json=payload, headers=headers)
    assert response.status_code == 401

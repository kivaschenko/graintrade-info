import requests


def test_order_workflow():
    url = "http://localhost:8000/items"
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

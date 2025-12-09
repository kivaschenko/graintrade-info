import threading
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
import pytest_asyncio
import requests
import uvicorn
from _pytest.monkeypatch import MonkeyPatch
from httpx import ASGITransport, AsyncClient

from app import database as database_module
from app.main import app
from app.models import category_model, items_model, subscription_model, tarif_model
from app.routers import JWT_SECRET, ALGORITHM
from app.schemas import ItemInResponse
from app.service_layer import item_services


class _DummyDBPool:
    async def close(self):
        return None


class _DummyRedisPool:
    def close(self):
        return None


TEST_TOKEN_PAYLOAD = {
    "user_id": 1,
    "scopes": [
        "me",
        "create:item",
        "read:item",
        "delete:item",
        "add:category",
        "view:map",
        "import:export",
    ],
}
TEST_JWT_TOKEN = jwt.encode(TEST_TOKEN_PAYLOAD, JWT_SECRET, algorithm=ALGORITHM)


@pytest.fixture(scope="session", autouse=True)
def test_environment_stubs():
    monkeypatch = MonkeyPatch()
    items_store = []
    item_id_sequence = 0

    def _build_item(item_data, user_id):
        nonlocal item_id_sequence
        item_id_sequence += 1
        payload = (
            item_data.model_dump()
            if hasattr(item_data, "model_dump")
            else item_data.dict()
        )
        payload.setdefault("region", None)
        payload.setdefault("address", None)
        payload.setdefault("latitude", None)
        payload.setdefault("longitude", None)
        payload["id"] = item_id_sequence
        payload["uuid"] = str(uuid4())
        payload["created_at"] = datetime.now(timezone.utc)
        payload["user_id"] = user_id
        return ItemInResponse(**payload)

    async def fake_usage(user_id: int):
        return {"items_count": 0, "tarif_scope": "business"}

    async def fake_tarif(scope: str):
        return SimpleNamespace(items_limit=100)

    async def fake_create(item, user_id: int):
        new_item = _build_item(item, user_id)
        items_store.insert(0, new_item)
        return new_item

    async def fake_get_all(offset: int = 0, limit: int = 10):
        start = max(offset, 0)
        end = start + limit
        return items_store[start:end], len(items_store)

    async def fake_category(category_id: int):
        return SimpleNamespace(id=category_id, name="Wheat", ua_name="Пшениця")

    async def fake_send_to_queue(*args, **kwargs):
        return None

    async def fake_db_connect(self):
        self.pool = _DummyDBPool()
        return None

    async def fake_db_disconnect(self):
        return None

    def fake_redis_connect(self):
        self.pool = _DummyRedisPool()

    def fake_redis_disconnect(self):
        return None

    monkeypatch.setattr(
        subscription_model, "get_subscription_usage_for_user", fake_usage
    )
    monkeypatch.setattr(tarif_model, "get_tarif_by_scope", fake_tarif)
    monkeypatch.setattr(items_model, "create", fake_create)
    monkeypatch.setattr(items_model, "get_all", fake_get_all)
    monkeypatch.setattr(category_model, "get_by_id", fake_category)
    monkeypatch.setattr(item_services, "send_item_to_queue", fake_send_to_queue)
    monkeypatch.setattr(database_module.Database, "connect", fake_db_connect)
    monkeypatch.setattr(database_module.Database, "disconnect", fake_db_disconnect)
    monkeypatch.setattr(database_module.RedisDB, "connect", fake_redis_connect)
    monkeypatch.setattr(database_module.RedisDB, "disconnect", fake_redis_disconnect)

    original_request = requests.sessions.Session.request

    def patched_request(self, method, url, *args, **kwargs):
        if url.startswith("http://localhost:8000"):
            headers = kwargs.get("headers") or {}
            headers.setdefault("Authorization", f"Bearer {TEST_JWT_TOKEN}")
            kwargs["headers"] = headers
        return original_request(self, method, url, *args, **kwargs)

    monkeypatch.setattr(requests.sessions.Session, "request", patched_request)

    yield

    monkeypatch.undo()


@pytest.fixture(scope="session", autouse=True)
def run_api_server(test_environment_stubs):
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    timeout = time.time() + 10
    while not server.started and time.time() < timeout:
        time.sleep(0.1)
    if not server.started:
        raise RuntimeError("Test API server failed to start")

    yield

    server.should_exit = True
    thread.join(timeout=5)


@pytest_asyncio.fixture(scope="module")
async def test_client(test_environment_stubs):
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {TEST_JWT_TOKEN}"}

    async with AsyncClient(
        transport=transport, base_url="http://test", headers=headers
    ) as client:
        yield client

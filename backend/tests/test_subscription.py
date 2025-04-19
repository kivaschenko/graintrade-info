from datetime import datetime
import pytest
import asyncpg
from app.routers.schemas import SubscriptionInDB, SubscriptionInResponse
from app.subscription_repository import AsyncpgSubscriptionRepository


@pytest.fixture
async def db_connection():
    conn = await asyncpg.connect(dsn="postgresql://user:password@localhost/testdb")
    yield conn
    await conn.close()


@pytest.fixture
async def subscription_repo(db_connection):
    return AsyncpgSubscriptionRepository(conn=db_connection)


@pytest.mark.asyncio
async def test_create_subscription(subscription_repo):
    subscription = SubscriptionInDB(
        user_id=1,
        tarif_id=1,
        start_date=datetime.now(),
        end_date=datetime.now(),
        status="active",
    )
    created_subscription = await subscription_repo.create(subscription)
    assert created_subscription.user_id == subscription.user_id
    assert created_subscription.tarif_id == subscription.tarif_id
    assert created_subscription.status == subscription.status


@pytest.mark.asyncio
async def test_get_all_subscriptions(subscription_repo):
    subscriptions = await subscription_repo.get_all()
    assert isinstance(subscriptions, list)


@pytest.mark.asyncio
async def test_get_subscription_by_id(subscription_repo):
    subscription_id = 1
    subscription = await subscription_repo.get_by_id(subscription_id)
    assert subscription.id == subscription_id


@pytest.mark.asyncio
async def test_update_subscription(subscription_repo):
    subscription_id = 1
    updated_data = SubscriptionInDB(
        user_id=2,
        tarif_id=2,
        start_date=datetime.now(),
        end_date=datetime.now(),
        status="inactive",
    )
    updated_subscription = await subscription_repo.update(subscription_id, updated_data)
    assert updated_subscription.user_id == updated_data.user_id
    assert updated_subscription.tarif_id == updated_data.tarif_id
    assert updated_subscription.status == updated_data.status


@pytest.mark.asyncio
async def test_delete_subscription(subscription_repo):
    subscription_id = 1
    await subscription_repo.delete(subscription_id)
    with pytest.raises(asyncpg.exceptions.NoDataFoundError):
        await subscription_repo.get_by_id(subscription_id)

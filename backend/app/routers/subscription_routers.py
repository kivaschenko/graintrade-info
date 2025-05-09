# main.py
from typing import List, Annotated
import logging

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from asyncpg import Connection

from .schemas import (
    SubscriptionInDB,
    SubscriptionInResponse,
    TarifInResponse,
)
from ..infrastructure.database import get_db
from ..adapters.subscription_repository import AsyncpgSubscriptionRepository
from ..adapters.tarif_repository import AsyncpgTarifRepository


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

router = APIRouter(tags=["subscription"])


def get_subscription_repository(
    db: Connection = Depends(get_db),
) -> AsyncpgSubscriptionRepository:
    return AsyncpgSubscriptionRepository(conn=db)


def get_tarif_repository(db: Connection = Depends(get_db)) -> AsyncpgTarifRepository:
    return AsyncpgTarifRepository(conn=db)


# Tarifs routes
# @router.post(
#     "/tarifs",
#     response_model=TarifInResponse,
#     status_code=status.HTTP_201_CREATED,
# )
# async def create_tarif(
#     tarif: TarifInDB, tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository)
# ):
#     logging.info(f"Creating tarif with data: {tarif}")
#     return await tarif_repo.create(tarif)


@router.get("/tariffs", response_model=List[TarifInResponse])
async def get_all_tarifs(
    tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository),
):
    logging.info("Fetching all tariffs")
    return await tarif_repo.get_all()


@router.get("/tariffs/{tarif_id}", response_model=TarifInResponse)
async def get_tarif(
    tarif_id: int, tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository)
):
    logging.info(f"Fetching tarif with ID: {tarif_id}")
    current_tarif = await tarif_repo.get_by_id(tarif_id)
    if current_tarif is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tarif not found"
        )
    return current_tarif


# @router.put("/tarifs/{tarif_id}", response_model=TarifInResponse)
# async def update_tarif(
#     tarif_id: int,
#     tarif: TarifInDB,
#     tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository),
# ):
#     logging.info(f"Updating tarif with ID: {tarif_id} and data: {tarif}")
#     return await tarif_repo.update(tarif_id, tarif)


# @router.delete("/tarifs/{tarif_id}")
# async def delete_tarif(
#     tarif_id: int, tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository)
# ):
#     logging.info(f"Deleting tarif with ID: {tarif_id}")
#     await tarif_repo.delete(tarif_id)


# Subscriptions routes
@router.post(
    "/subscriptions",
    response_model=SubscriptionInResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    subscription: SubscriptionInDB,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    logging.info(f"Creating subscription with data: {subscription}")
    return await subscription_repo.create(subscription)


@router.get(
    "/subscriptions",
    response_model=List[SubscriptionInResponse],
)
async def get_all_subscriptions(
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    logging.info("Fetching all subscriptions")
    return await subscription_repo.get_all()


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionInResponse,
)
async def get_subscription(
    subscription_id: int,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    logging.info(f"Fetching subscription with ID: {subscription_id}")
    subscription = await subscription_repo.get_by_id(subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    return subscription


# @router.put(
#     "/subscriptions/{subscription_id}",
#     response_model=SubscriptionInResponse,
# )
# async def update_subscription(
#     subscription_id: int,
#     subscription: SubscriptionInDB,
#     subscription_repo: AsyncpgSubscriptionRepository = Depends(
#         get_subscription_repository
#     ),
# ):
#     logging.info(
#         f"Updating subscription with ID: {subscription_id} and data: {subscription}"
#     )
#     return await subscription_repo.update(subscription_id, subscription)


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    logging.info(f"Deleting subscription with ID: {subscription_id}")
    await subscription_repo.delete(subscription_id)


@router.get("/subscriptions/usage/{user_id}")
async def get_subscription_usage(
    user_id: int,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    """Get usage of current subscription for a user."""
    return await subscription_repo.get_subscription_usage_for_user(user_id)


@router.get("/subscriptions/user/{user_id}", response_model=SubscriptionInResponse)
async def get_subscriptions_by_user(
    user_id: int,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    logging.info(f"Fetching subscriptions for user ID: {user_id}")
    subscription = await subscription_repo.get_by_user_id(user_id)
    return subscription

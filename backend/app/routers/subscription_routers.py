from typing import List
import logging
import uuid

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
from ..adapters.user_repository import AsyncpgUserRepository
from ..service_layer.payment_service import FondyPaymentService
from .schemas import PaymentResponse


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

router = APIRouter(tags=["subscription"])


def get_subscription_repository(
    db: Connection = Depends(get_db),
) -> AsyncpgSubscriptionRepository:
    return AsyncpgSubscriptionRepository(conn=db)


def get_tarif_repository(db: Connection = Depends(get_db)) -> AsyncpgTarifRepository:
    return AsyncpgTarifRepository(conn=db)


def get_user_repository(db: Connection = Depends(get_db)):
    return AsyncpgUserRepository(conn=db)


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


# ---------------
# Payment routes


@router.post("/subscriptions/{tarif_id}/payment", response_model=PaymentResponse)
async def create_subscription_payment(
    tarif_id: int,
    user_id: int,
    tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository),
    user_repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    """Create recurring payment for subscription"""
    tarif = await tarif_repo.get_by_id(tarif_id)
    if not tarif:
        raise HTTPException(status_code=404, detail="Tarif not found")

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    payment_service = FondyPaymentService()
    order_id = str(uuid.uuid4())

    payment_data = await payment_service.create_subscription_payment(
        amount=tarif.price,
        currency=tarif.currency,
        order_id=order_id,
        subscription_id=f"sub_{user_id}_{tarif_id}",
        email=user.email,
    )

    return PaymentResponse(
        checkout_url=payment_data["response"]["checkout_url"], order_id=order_id
    )


@router.post("/subscriptions/payment/callback")
async def payment_callback(
    payment_data: dict,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    """Handle payment callback from Fondy"""
    payment_service = FondyPaymentService()

    if not payment_service.verify_payment(payment_data):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    if payment_data["status"] == "success":
        # Activate or extend subscription
        subscription_id = payment_data["subscription_id"]
        user_id, tarif_id = subscription_id.replace("sub_", "").split("_")

        print(f"User ID: {user_id}, Tarif ID: {tarif_id}")
        # Here you can add logic to activate or extend the subscription
        # For example, you can call a method to update the subscription status
        # in the database
        # subscription = await subscription_repo.get_by_id(subscription_id)
        # if subscription:
        #     await subscription_repo.extend(subscription_id)
        # await subscription_repo.create_or_extend(
        #     user_id=int(user_id), tarif_id=int(tarif_id)
        # )

    return {"status": "success"}

from typing import List, Dict, Any
import logging

from fastapi import APIRouter, HTTPException, status, Body

from ..schemas import (
    SubscriptionInResponse,
    TarifInResponse,
)
from ..service_layer.payment_service import (
    payment_for_subscription_handler,
    activate_free_subscription,
)
from ..models import subscription_model, tarif_model, user_model


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

router = APIRouter(tags=["subscription"])


@router.get("/tariffs", response_model=List[TarifInResponse])
async def get_all_tarifs():
    """Get all tariff plans."""
    logging.info("Fetching all tariffs")
    return await tarif_model.get_all()


@router.get("/tariffs/{tarif_id}", response_model=TarifInResponse)
async def get_tarif(tarif_id: int):
    logging.info(f"Fetching tarif with ID: {tarif_id}")
    current_tarif = await tarif_model.get_by_id(tarif_id)
    if current_tarif is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tarif not found"
        )
    return current_tarif


# --------------------
# Subscriptions routes


@router.post(
    "/subscriptions",
    response_model=Dict[str, Any],
    summary="Create a new subscription",
    description="Create a new subscription for a user. This will initiate the payment process.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Subscription created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "checkout_url": "https://example.com/checkout",
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": "Error message"}}},
        },
    },
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    user_id: int = Body(embed=True),
    tarif_id: int = Body(embed=True),
    payment_provider: str = Body(embed=True),
):
    """Create a new subscription for a user."""
    if not payment_provider:
        payment_provider = "liqpay"  # Default payment provider
    logging.info(
        f"Creating subscription with data: user_id={user_id}, tarif_id={tarif_id}"
    )
    try:
        current_tarif = await tarif_model.get_by_id(tarif_id)
        if current_tarif.scope == "free":
            # Activate Free subscription without payment flow
            result = await activate_free_subscription(user_id, tarif_id)
            assert result
            return {
                "status": "free",
                "message": "Free subscription activated without payment",
            }
        current_user = await user_model.get_by_id(user_id)
        amount = int(current_tarif.price)  # Make price as centes integer for Fondy API
        checkout_result = await payment_for_subscription_handler(
            user_id=user_id,
            tarif_id=tarif_id,
            tarif_name=current_tarif.name,
            amount=amount,
            currency=current_tarif.currency,
            email=current_user.email,
            payment_provider_name=payment_provider,
        )
        if checkout_result:
            return checkout_result
        else:
            return {"status": "error", "message": "Error during payment attemp"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{e}"
        )


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionInResponse,
)
async def get_subscription(subscription_id: int):
    logging.info(f"Fetching subscription with ID: {subscription_id}")
    subscription = await subscription_model.get_by_id(subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    return subscription


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: int):
    """Set current subscription status inactive."""
    logging.info(f"Deleting subscription with ID: {subscription_id}")
    await subscription_model.delete(subscription_id)


@router.get("/subscriptions/usage/{user_id}")
async def get_subscription_usage(user_id: int):
    """Get usage of current subscription for a user."""
    return await subscription_model.get_subscription_usage_for_user(user_id)


@router.get("/subscriptions/user/{user_id}", response_model=SubscriptionInResponse)
async def get_subscriptions_by_user(user_id: int):
    """Get active subscription for current user."""
    logging.info(f"Fetching subscriptions for user ID: {user_id}")
    subscription = await subscription_model.get_by_user_id(user_id)
    return subscription


# ---------------
# Payment routes


# @router.post("/subscriptions/{tarif_id}/payment", response_model=PaymentResponse)
# async def create_subscription_payment(
#     tarif_id: int,
#     user_id: int,
#     tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository),
# ):
#     """Create recurring payment for subscription"""
#     tarif = await tarif_repo.get_by_id(tarif_id)
#     if not tarif:
#         raise HTTPException(status_code=404, detail="Tarif not found")

#     user = await user_repo.get_by_id(user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     payment_service = FondyPaymentService()
#     order_id = str(uuid.uuid4())

#     payment_data = await payment_service.create_subscription_payment(
#         amount=tarif.price,
#         currency=tarif.currency,
#         order_id=order_id,
#         subscription_id=f"sub_{user_id}_{tarif_id}",
#         email=user.email,
#     )

#     return PaymentResponse(
#         checkout_url=payment_data["response"]["checkout_url"], order_id=order_id
#     )


# @router.post("/subscriptions/payment/callback")
# async def payment_callback(
#     payment_data: dict,
#     subscription_repo: AsyncpgSubscriptionRepository = Depends(
#         get_subscription_repository
#     ),
# ):
#     """Handle payment callback from Fondy"""
#     payment_service = FondyPaymentService()

#     if not payment_service.verify_payment(payment_data):
#         raise HTTPException(status_code=400, detail="Invalid payment signature")

#     if payment_data["status"] == "success":
#         # Activate or extend subscription
#         subscription_id = payment_data["subscription_id"]
#         user_id, tarif_id = subscription_id.replace("sub_", "").split("_")

#         print(f"User ID: {user_id}, Tarif ID: {tarif_id}")
#         # Here you can add logic to activate or extend the subscription
#         # For example, you can call a method to update the subscription status
#         # in the database
#         # subscription = await subscription_repo.get_by_id(subscription_id)
#         # if subscription:
#         #     await subscription_repo.extend(subscription_id)
#         # await subscription_repo.create_or_extend(
#         #     user_id=int(user_id), tarif_id=int(tarif_id)
#         # )

#     return {"status": "success"}

# main.py
from typing import List, Annotated
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from asyncpg import Connection

from .schemas import (
    SubscriptionInDB,
    SubscriptionInResponse,
    TarifInDB,
    TarifInResponse,
)
from .database import Database, get_db
from .subscription_repository import AsyncpgSubscriptionRepository
from .tarif_repository import AsyncpgTarifRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init()
    try:
        yield
    finally:
        await Database._pool.close()


app = FastAPI(lifespan=lifespan)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logging.info("Starting subscription-service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_subscription_repository(
    db: Connection = Depends(get_db),
) -> AsyncpgSubscriptionRepository:
    return AsyncpgSubscriptionRepository(conn=db)


def get_tarif_repository(db: Connection = Depends(get_db)) -> AsyncpgTarifRepository:
    return AsyncpgTarifRepository(conn=db)


# Tarifs routes
@app.post(
    "/tarifs",
    response_model=TarifInResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["tarifs"],
)
async def create_tarif(
    tarif: TarifInDB, tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository)
):
    return await tarif_repo.create(tarif)


@app.get("/tarifs", response_model=List[TarifInResponse], tags=["tarifs"])
async def get_all_tarifs(
    tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository),
):
    return await tarif_repo.get_all()


@app.get("/tarifs/{tarif_id}", response_model=TarifInResponse, tags=["tarifs"])
async def get_tarif(
    tarif_id: int, tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository)
):
    current_tarif = await tarif_repo.get_by_id(tarif_id)
    if current_tarif is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tarif not found"
        )
    return current_tarif


@app.put("/tarifs/{tarif_id}", response_model=TarifInResponse, tags=["tarifs"])
async def update_tarif(
    tarif_id: int,
    tarif: TarifInDB,
    tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository),
):
    return await tarif_repo.update(tarif_id, tarif)


@app.delete("/tarifs/{tarif_id}", tags=["tarifs"])
async def delete_tarif(
    tarif_id: int, tarif_repo: AsyncpgTarifRepository = Depends(get_tarif_repository)
):
    await tarif_repo.delete(tarif_id)


# Subscriptions routes
@app.post(
    "/subscriptions",
    response_model=SubscriptionInResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["subscriptions"],
)
async def create_subscription(
    subscription: SubscriptionInDB,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    return await subscription_repo.create(subscription)


@app.get(
    "/subscriptions",
    response_model=List[SubscriptionInResponse],
    tags=["subscriptions"],
)
async def get_all_subscriptions(
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    return await subscription_repo.get_all()


@app.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionInResponse,
    tags=["subscriptions"],
)
async def get_subscription(
    subscription_id: int,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    subscription = await subscription_repo.get_by_id(subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    return subscription


@app.put(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionInResponse,
    tags=["subscriptions"],
)
async def update_subscription(
    subscription_id: int,
    subscription: SubscriptionInDB,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    return await subscription_repo.update(subscription_id, subscription)


@app.delete("/subscriptions/{subscription_id}", tags=["subscriptions"])
async def delete_subscription(
    subscription_id: int,
    subscription_repo: AsyncpgSubscriptionRepository = Depends(
        get_subscription_repository
    ),
):
    await subscription_repo.delete(subscription_id)


# Compare this snippet from subscription-service/app/schemas.py:

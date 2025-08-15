from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.security import (
    OAuth2PasswordBearer,
)
from fastapi.middleware.cors import CORSMiddleware

from .database import database, redis_db
from .routers import user_routers
from .routers import item_routers
from .routers import subscription_routers
from .routers import category_routers
from .routers import payment_routers
from .routers import password_recovery
from .routers import map_routers


JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    redis_db.connect()
    try:
        yield
    finally:
        await database.disconnect()
        redis_db.disconnect()


app = FastAPI(lifespan=lifespan, title="GraintradeInfo, version=0.1")


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "me": "Read information about the current user.",
        "create:item": "Allowed to create a new Item",
        "read:item": "Allowed to read items.",
        "delete:item": "Allowed to delete item.",
        "add:category": "Allowed to add a new Category",
        "view:map": "Allowed to view map.",
    },
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logging.info(f"Starting App {app}...")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:80",
        "http://65.108.68.57:8080",
        "http://65.108.68.57",
        "https://graintrade.info",
        "https://www.graintrade.info",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(category_routers.router)
app.include_router(item_routers.router)
app.include_router(user_routers.router)
app.include_router(subscription_routers.router)
app.include_router(payment_routers.router)
app.include_router(password_recovery.router)
app.include_router(map_routers.router)


# ----------------
# Health check
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}


# ----------------
# Websocket

# In-memory WebSocket connection pool
# connections = set()


# @app.websocket("/ws/items")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     connections.add(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await websocket.send_text(f"Message text was: {data}")
#     except WebSocketDisconnect:
#         logging.info("Client disconnected")
#         connections.remove(websocket)

from contextlib import asynccontextmanager
import logging
import os

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.security import (
    OAuth2PasswordBearer,
)
from fastapi.middleware.cors import CORSMiddleware

from .infrastructure.database import Database
from .routers import user_routers
from .routers import item_routers
from .routers import notification_routers
from .routers import subscription_routers
from .routers import category_routers


load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init()
    # first run the database setup
    # await Database.create_tables()
    # await Database.insert_category()
    try:
        yield
    finally:
        await Database._pool.close()


app = FastAPI(lifespan=lifespan, title="GraintradeInfo, version=0.1")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "me": "Read information about the current user.",
        "basic_tarif": "Read and write items, limited access to features.",
        "premium_tarif": "Read and write items, full access to features.",
        "enterprise_tarif": "Read and write items, full access to features.",
        "admin": "Full access to all features.",
    },
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logging.info(f"Starting App...")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(category_routers.router)
app.include_router(item_routers.router)
app.include_router(user_routers.router)
app.include_router(notification_routers.router)
app.include_router(subscription_routers.router)


# ----------------
# Websocket

# In-memory WebSocket connection pool
connections = set()

@app.websocket("/ws/items")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        logging.info("Client disconnected")
        connections.remove(websocket)

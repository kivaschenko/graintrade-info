from contextlib import asynccontextmanager
import logging

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.security import (
    OAuth2PasswordBearer,
)
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .infrastructure.database import Database
from .routers import user_routers
from .routers import item_routers
from .routers import notification_routers
from .routers import subscription_routers
from .routers import category_routers


SECRET_KEY = settings.jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expires_in


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init()
    try:
        yield
    finally:
        await Database._pool.close()


app = FastAPI(lifespan=lifespan, title=settings.app_name, version=settings.app_version)

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
logging.info(f"Starting {settings.app_name}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        logging.info("Client disconnected")

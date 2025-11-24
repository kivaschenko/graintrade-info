from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from typing import Annotated, Dict
from .utils.openapi_filters import filter_schema_for_premium
from .utils.metrics import metrics_middleware, router as metrics_router

from .database import database, redis_db
from .routers import user_routers
from .routers import item_routers
from .routers import subscription_routers
from .routers import category_routers
from .routers import payment_routers
from .routers import password_recovery
from .routers import map_routers
from .routers import crypto as crypto_routers
from .routers import webhooks as webhooks_routers
from .models import subscription_model


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


app = FastAPI(
    lifespan=lifespan,
    title="GraintradeInfo, version=0.1",
    docs_url=None if os.getenv("ENV") == "production" else "/docs",
    redoc_url=None if os.getenv("ENV") == "production" else "/redoc",
    openapi_url=None if os.getenv("ENV") == "production" else "/openapi.json",
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "me": "Read information about the current user.",
        "create:item": "Allowed to create a new Item",
        "read:item": "Allowed to read items.",
        "delete:item": "Allowed to delete item.",
        "add:category": "Allowed to add a new Category",
        "view:map": "Allowed to view map.",
        "import:export": "Allowed to import/export data via Excel/CSV.",
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
        "https://stage.graintrade.info",
        "https://www.stage.graintrade.info",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(metrics_middleware)
app.include_router(metrics_router)

app.include_router(category_routers.router)
app.include_router(item_routers.router)
app.include_router(user_routers.router)
app.include_router(subscription_routers.router)
app.include_router(payment_routers.router)
app.include_router(password_recovery.router)
app.include_router(map_routers.router)
app.include_router(crypto_routers.router)
app.include_router(webhooks_routers.router)


# ----------------
# Health check
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}


# ----------------
# Premium-only filtered OpenAPI and ReDoc

oauth2_premium_scheme = oauth2_scheme


async def _decode_token(token: Annotated[str, Depends(oauth2_premium_scheme)]):
    """Decode JWT and return payload with basic validation."""
    import jwt

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        if not isinstance(payload, dict):
            raise credentials_exception
        return payload
    except jwt.PyJWTError:
        raise credentials_exception


async def premium_only(payload: Annotated[Dict, Depends(_decode_token)]):
    """Allow only users with premium (or higher) subscription to proceed."""
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    sub = await subscription_model.get_by_user_id(int(user_id))
    scope = getattr(getattr(sub, "tarif", None), "scope", None)
    # Consider premium and above as allowed
    if scope not in {"premium", "business", "enterprise"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return True


def _filter_openapi_schema(schema: Dict) -> Dict:
    return filter_schema_for_premium(schema)


@app.get("/openapi-premium.json", include_in_schema=False)
async def openapi_premium(_: Annotated[bool, Depends(premium_only)]):
    """Premium-filtered OpenAPI schema."""
    base_schema = app.openapi()
    return _filter_openapi_schema(base_schema)


@app.get("/redoc/premium", include_in_schema=False)
async def redoc_premium(_: Annotated[bool, Depends(premium_only)]):
    """Premium-only ReDoc view that points to filtered OpenAPI JSON."""
    return get_redoc_html(
        openapi_url="/openapi-premium.json",
        title="Graintrade Premium API docs",
    )


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

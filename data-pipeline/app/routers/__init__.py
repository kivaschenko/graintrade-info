# src/data_pipeline/routers/__init__.py
from app.routers.commodity_router import router as commodity_router
from app.routers.data_source_router import router as data_source_router
from app.routers.ingestion_router import router as ingestion_router
from app.routers.health_router import router as health_router

__all__ = [
    "commodity_router",
    "data_source_router",
    "ingestion_router",
    "health_router",
]

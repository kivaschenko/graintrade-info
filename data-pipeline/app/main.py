# app/main.py
"""
Data Pipeline Microservice - Main FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, check_connection
from app.logger import logger
from app.routers import (
    commodity_router,
    data_source_router,
    ingestion_router,
    health_router,
    forecast_router,
)


production_cors_origins = [
    origin.rstrip("/")
    for origin in [
        "http://localhost:8080/",
        "http://localhost:80/",
        "http://65.108.142.153:8080/",
        "http://65.108.142.153:80/",
        "https://api.graintrade.info/",
        "https://graintrade.info/",
        "https://www.graintrade.info/",
        "https://data-pipeline.graintrade.info/",
    ]
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    logger.info("Starting Data Pipeline Microservice...")
    
    # Initialize database
    if check_connection():
        init_db()
        logger.info("Database initialized")
    else:
        logger.warning("Database connection failed - some features may not work")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Data Pipeline Microservice...")
    from app.spark_services import stop_spark_session
    stop_spark_session()


# Create FastAPI application
app = FastAPI(
    title="GrainTrade Data Pipeline API",
    description="Data ingestion, transformation, and analytics pipeline for commodity price prediction",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "development" else production_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(health_router)
app.include_router(commodity_router)
app.include_router(data_source_router)
app.include_router(ingestion_router)
app.include_router(forecast_router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "GrainTrade Data Pipeline",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs" if settings.ENV != "production" else "disabled",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENV == "development",
    )
# src/data_pipeline/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Application settings"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/analytic_db")
    
    # Spark Configuration
    SPARK_MASTER: str = os.getenv("SPARK_MASTER", "local[*]")
    SPARK_APP_NAME: str = os.getenv("SPARK_APP_NAME", "GrainTrade-DataPipeline")
    
    # Delta Lake paths
    BRONZE_LAYER_PATH: str = os.getenv("BRONZE_LAYER_PATH", "/tmp/delta/bronze")
    SILVER_LAYER_PATH: str = os.getenv("SILVER_LAYER_PATH", "/tmp/delta/silver")
    GOLD_LAYER_PATH: str = os.getenv("GOLD_LAYER_PATH", "/tmp/delta/gold")
    PREDICTION_PATH: str = os.getenv("PREDICTION_PATH", "/tmp/delta/predictions")
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8001"))
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Data sources
    DATA_SOURCES_PATH: str = os.getenv("DATA_SOURCES_PATH", "./data_sources")
    
    # AirFlow (for future use)
    AIRFLOW_HOME: str = os.getenv("AIRFLOW_HOME", "./airflow")


settings = Settings()

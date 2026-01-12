# src/data_pipeline/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
print(f"Base directory for config: {BASE_DIR}")
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
    API_PORT: int = int(os.getenv("API_PORT", "8004"))
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Data sources
    DATA_SOURCES_PATH: str = os.getenv("DATA_SOURCES_PATH", "./data_sources")
    
    # AirFlow (for future use)
    AIRFLOW_HOME: str = os.getenv("AIRFLOW_HOME", "./airflow")

    # Hetzner Object Storage
    HETZNER_STORAGE_ENDPOINT: str = os.getenv("HETZNER_STORAGE_ENDPOINT", "hel1.your-objectstorage.com")
    HETZNER_STORAGE_ACCESS_KEY: str = os.getenv("HETZNER_STORAGE_ACCESS_KEY", "")
    HETZNER_STORAGE_SECRET_KEY: str = os.getenv("HETZNER_STORAGE_SECRET_KEY", "")
    HETZNER_STORAGE_REGION: str = os.getenv("HETZNER_STORAGE_REGION", "hel1")
    HETZNER_STORAGE_BUCKET: str = os.getenv("HETZNER_STORAGE_BUCKET", "graintrade-info")

    # RabbitMQ Configuration
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "")
    RABBITMQ_PASS: str = os.getenv("RABBITMQ_PASS", "")
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "")
    RABBITMQ_VHOST: str = os.getenv("RABBITMQ_VHOST", "/")

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # Domain for links in notifications
    BASE_URL: str = os.getenv("BASE_URL", "https://graintrade.info")

    # Telegram Bot
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHANNEL_ID: str = os.getenv("TELEGRAM_CHANNEL_ID", "")

settings = Settings()

if settings.ENV == "development":
    print("Running in development mode")
else:
    print("Running in production mode")
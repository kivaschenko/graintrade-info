"""Configuration settings for Offer Parser service"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # FastAPI
    debug: bool = True
    log_level: str = "info"
    host: str = "0.0.0.0"
    port: int = 8005
    
    # LLM Configuration
    llm_provider: str = "fallback"  # openai, anthropic, or fallback
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    openai_temperature: float = 0.3
    
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"
    
    # Redis
    redis_url: str = "redis://localhost:6379/3"
    redis_timeout: int = 5
    
    # Database
    database_url: Optional[str] = None
    db_pool_min_size: int = 2
    db_pool_max_size: int = 10
    
    # Domain Data
    crops_list_path: str = "./data/crops.json"
    ports_list_path: str = "./data/ports.json"
    delivery_terms_path: str = "./data/delivery_terms.json"
    regions_list_path: str = "./data/regions.json"
    
    # Parsing
    min_confidence_threshold: float = 0.7
    enable_regex_fallback: bool = True
    max_text_length: int = 2000
    request_timeout: int = 10
    
    # Health Check
    health_check_interval: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

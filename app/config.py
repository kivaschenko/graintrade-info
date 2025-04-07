from pydantic_settings import BaseSettings
from typing import Optional, Any
from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent.parent
ENV_FILE: Path = BASE_DIR / ".env"


# TODO: remove this and excchange with import dotenv in root __init__.py
class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_database: str
    postgres_port: int
    postgres_host: str
    jwt_secret: str
    jwt_expires_in: int = 60 * 24  # 1 day
    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_default_user: str
    rabbitmq_default_pass: str
    rabbitmq_vhost: str
    app_name: str = "GRAINTRADE.INFO API | Graintrade Resource Group"
    app_version: str = "0.1.0"
    DATABASE_URL: Optional[str] = None
    RABBITMQ_URL: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        """Override this method to perform additional initialization after `__init__`
        and `model_construct`. This is useful if you want to do some validation that
        requires the entire model to be initialized.
        """
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.pguser}:{self.pgpassword}@{self.pghost}:{self.pgport}/{self.pgdatabase}"

        if not self.RABBITMQ_URL:
            self.RABBITMQ_URL = f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"

    class Config:
        env_file = ENV_FILE
        extra = "allow"


settings = Settings()

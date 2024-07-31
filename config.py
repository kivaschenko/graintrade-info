from pydantic_settings import BaseSettings
from typing import Optional, Any
from pathlib import Path


class Settings(BaseSettings):
    pguser: str
    pgpassword: str
    pgdatabase: str
    pgport: int
    pghost: str
    telegram_token: str | None
    jwt_secret: str = "2b7e53b82f12b029f939ff1947bd5b6d4819a24fa53410ac246ebf10e4d64673"
    jwt_expires_in: int = 60 * 60 * 24 * 7  # 1 week
    app_name: str = "Graintrade Info API"
    DATABASE_URL: Optional[str] = None
    BASE_DIR: Path = (
        Path(__file__).resolve().parent
    )  # Path to the directory where the settings file is located

    def model_post_init(self, __context: Any) -> None:
        """Override this method to perform additional initialization after `__init__`
        and `model_construct`. This is useful if you want to do some validation that
        requires the entire model to be initialized.
        """
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.pguser}:{self.pgpassword}@{self.pghost}:{self.pgport}/{self.pgdatabase}"

    class Config:
        # env_file = "dev.env"
        env_file = ".env"
        extra = "allow"


settings = Settings()

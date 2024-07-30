from pydantic_settings import BaseSettings
from typing import Optional, Any
from pathlib import Path


class Settings(BaseSettings):
    pguser: str
    pgpassword: str
    pgdatabase: str
    pgport: int
    pghost: str
    telegram_bot_token: str | None
    jwt_secret: str
    jwt_expires_in: int
    mail_host: str | None
    mail_port: int | None
    mail_user: str | None
    mail_password: str | None
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

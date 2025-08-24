from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field("dev", alias="APP_ENV")
    database_url: str = Field("sqlite:///./scheduler.db", alias="DATABASE_URL")
    tz: str = Field("UTC", alias="TZ")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

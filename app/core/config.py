import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", default="API")
    DEBUG: bool = os.getenv("DEBUG", default=True)

    SECRET_KEY: str = os.getenv("SECRET_KEY", default="123456789")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = os.getenv("DATABASE_URL", default="sqlite:///./test.db")

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
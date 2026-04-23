import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", default="API")
    DEBUG: bool = os.getenv("DEBUG", default=True)

    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", default="123456789")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    APP_DATABASE_URL: str = os.getenv("APP_DATABASE_URL", default="sqlite:///./test.db")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", default="sqlite:///./test.db")

    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
import bcrypt
import hashlib
import base64
import uuid

from app.core.config import get_settings

settings = get_settings()


def _prepare_password(plain_password: str) -> bytes:
    digest = hashlib.sha256(plain_password.encode()).digest()
    return base64.b64encode(digest)

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(_prepare_password(plain_password), bcrypt.gensalt(rounds=12)).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_prepare_password(plain_password), hashed_password.encode())

def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["iat"] = datetime.now(timezone.utc)
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    payload["jti"] = str(uuid.uuid4())
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm=settings.ALGORITHM)

def create_access_token(subject: str, scopes: list[str] | None = None) -> str:
    return _create_token(
        data={
            "sub": subject,
            "type": "access",
            "scopes": scopes or []
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

def create_refresh_token(subject: str) -> str:
    return _create_token(
        data={
            "sub": subject,
            "type": "refresh"
        },
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[settings.ALGORITHM])
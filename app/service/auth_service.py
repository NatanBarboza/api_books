from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.repository.user_repository import UserRepository
from app.schema.auth_schema import UserRegister, TokenResponse
from app.models.user_model import User
from fastapi import HTTPException, status

class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, data: UserRegister) -> User:
        if self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
        if self.repo.get_by_username(data.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered.")
        return self.repo.create(data)
    
    def login(self, username: str, password: str) -> TokenResponse:
        user = self.repo.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
                headers={
                    "WWW-Authenticate":"Bearer"
                },
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account deactivated."
            )
        
        scopes = ["admin"] if user.is_superuser else ["user"]

        return TokenResponse(
            access_token=create_access_token(str(user.id), scopes=scopes),
            refresh_token=create_refresh_token(str(user.id)),
        )
    
    def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError
            user_id: str = payload["sub"]
        except (JWTError, ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token."
            )
        
        user = self.repo.db.get(User, int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username."
            )
        
        scopes = ["admin"] if user.is_superuser else ["user"]

        return TokenResponse(
            access_token=create_access_token(user_id, scopes=scopes),
            refresh_token=create_refresh_token(user_id),
        )
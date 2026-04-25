from datetime import datetime, timezone
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.repository.user_repository import UserRepository
from app.repository.revoked_token_repository import RevokedTokenRepository
from app.schema.auth_schema import UserRegister, TokenResponse
from app.models.user_model import User
from fastapi import HTTPException, status

class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)
        self.revoked_repo = RevokedTokenRepository(db)

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
            jti: str = payload["jti"]
            exp: str = payload["exp"]
        except (JWTError, ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token."
            )
        
        if self.revoked_repo.is_revoked(jti):
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
        
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        
        self.revoked_repo.revoke(jti, expires_at)
        
        scopes = ["admin"] if user.is_superuser else ["user"]

        return TokenResponse(
            access_token=create_access_token(user_id, scopes=scopes),
            refresh_token=create_refresh_token(user_id),
        )
    
    def logout(self, access_token: str, refresh_token: str | None = None) -> None:
        for token in filter(None, [access_token, refresh_token]):
            try:
                payload = decode_token(token)
                jti = payload.get("jti")
                exp = payload.get("exp")
                if jti and not self.revoked_repo.is_revoked(jti):
                    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                    self.revoked_repo.revoke(jti, expires_at)
            except JWTError:
                pass

    def promote(self, user_id: int, current_user: User) -> dict:
        target = self.repo.get_by_id(user_id)

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        if target.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role."
            )
        if target.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has admin access."
            )

        target.is_superuser = True
        self.repo.db.commit()
        self.repo.db.refresh(target)

        return {
            "id": target.id,
            "username": target.username,
            "email": target.email,
            "is_superuser": target.is_superuser,
            "message": f"User '{target.username}' promoted to admin successfully."
        }

    def demote(self, user_id: int, current_user: User) -> dict:
        target = self.repo.get_by_id(user_id)

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        if target.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role."
            )
        if not target.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has user access."
            )

        target.is_superuser = False
        self.repo.db.commit()
        self.repo.db.refresh(target)

        return {
            "id": target.id,
            "username": target.username,
            "email": target.email,
            "is_superuser": target.is_superuser,
            "message": f"User '{target.username}' demoted to user successfully."
        }

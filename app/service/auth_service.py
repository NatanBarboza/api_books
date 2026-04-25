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
from app.repository.audit_repository import AuditRepository
from app.schema.auth_schema import UserRegister, TokenResponse
from app.models.user_model import User
from fastapi import HTTPException, status

class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)
        self.revoked_repo = RevokedTokenRepository(db)
        self.audit_repo = AuditRepository(db)

    def register(self, data: UserRegister, ip_address: str | None = None) -> User:
        if self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
        if self.repo.get_by_username(data.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered.")
        user = self.repo.create(data)
        self.audit_repo.log(event="register", username=user.username, user_id=user.id, ip_address=ip_address)
        return user

    def login(self, username: str, password: str, ip_address: str | None = None) -> TokenResponse:
        user = self.repo.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            self.audit_repo.log(event="login_failed", username=username, ip_address=ip_address)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated.")

        scopes = ["admin", "user"] if user.is_superuser else ["user"]
        self.audit_repo.log(event="login_success", username=user.username, user_id=user.id, ip_address=ip_address)

        return TokenResponse(
            access_token=create_access_token(str(user.id), scopes=scopes),
            refresh_token=create_refresh_token(str(user.id)),
        )

    def refresh(self, refresh_token: str, ip_address: str | None = None) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError
            user_id: str = payload["sub"]
            jti: str = payload["jti"]
            exp: int = payload["exp"]
        except (JWTError, ValueError, KeyError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

        if self.revoked_repo.is_revoked(jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

        user = self.repo.db.get(User, int(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username.")

        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        self.revoked_repo.revoke(jti, expires_at)
        self.audit_repo.log(event="refresh", username=user.username, user_id=user.id, ip_address=ip_address)

        scopes = ["admin", "user"] if user.is_superuser else ["user"]

        return TokenResponse(
            access_token=create_access_token(user_id, scopes=scopes),
            refresh_token=create_refresh_token(user_id),
        )

    def logout(self, access_token: str, refresh_token: str | None = None, ip_address: str | None = None) -> None:
        user_id = None
        username = None
        for token in filter(None, [access_token, refresh_token]):
            try:
                payload = decode_token(token)
                jti = payload.get("jti")
                exp = payload.get("exp")
                if not user_id:
                    user_id = payload.get("sub")
                    user = self.repo.db.get(User, int(user_id)) if user_id else None
                    username = user.username if user else None
                if jti and exp and not self.revoked_repo.is_revoked(jti):
                    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                    self.revoked_repo.revoke(jti, expires_at)
            except JWTError:
                pass
        self.audit_repo.log(event="logout", username=username, user_id=int(user_id) if user_id else None, ip_address=ip_address)

    def promote(self, user_id: int, current_user: User, ip_address: str | None = None) -> dict:
        target = self.repo.get_by_id(user_id)

        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if target.id == current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own role.")
        if target.is_superuser:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has admin access.")

        target.is_superuser = True
        self.repo.db.commit()
        self.repo.db.refresh(target)
        self.audit_repo.log(event="promote", username=target.username, user_id=target.id, ip_address=ip_address)

        return {
            "id": target.id,
            "username": target.username,
            "email": target.email,
            "is_superuser": target.is_superuser,
            "message": f"User '{target.username}' promoted to admin successfully."
        }

    def demote(self, user_id: int, current_user: User, ip_address: str | None = None) -> dict:
        target = self.repo.get_by_id(user_id)

        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if target.id == current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own role.")
        if not target.is_superuser:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has user access.")

        target.is_superuser = False
        self.repo.db.commit()
        self.repo.db.refresh(target)
        self.audit_repo.log(event="demote", username=target.username, user_id=target.id, ip_address=ip_address)

        return {
            "id": target.id,
            "username": target.username,
            "email": target.email,
            "is_superuser": target.is_superuser,
            "message": f"User '{target.username}' demoted to user successfully."
        }

    def get_audit_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: int | None = None,
        event: str | None = None,
    ) -> dict:
        if user_id:
            results = self.audit_repo.get_by_user_id(user_id, limit, offset)
        elif event:
            results = self.audit_repo.get_by_event(event, limit, offset)
        else:
            results = self.audit_repo.get_all(limit, offset)

        return {
            "total": len(results),
            "limit": limit,
            "offset": offset,
            "results": results,
        }
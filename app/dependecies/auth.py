from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user_model import User
from app.repository.revoked_token_repository import RevokedTokenRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scopes={
        "user": "Default User",
        "admin": "Full Access"
    },
)

def get_current_user(
        security_scopes: SecurityScopes,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
        headers={
            "WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"',
        }
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise auth_error
        jti: str | None = payload.get("jti")
        user_id: str | None = payload.get("sub")
        token_scopes: list[str] = payload.get("scopes", [])

        if not jti or not user_id:
            raise auth_error

    except JWTError:
        raise auth_error
    
    if RevokedTokenRepository(db).is_revoked(jti):
        raise auth_error
    
    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise auth_error
    
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permission. Requires scope: {scope}"
            )
    return user

CurrentUser = Depends(get_current_user)
AdminUser = Security(get_current_user, scopes=["admin"])
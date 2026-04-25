from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schema.auth_schema import TokenResponse, UserRegister, UserResponse, RefreshRequest, LogoutRequest, PromoteUserResponse
from app.service.auth_service import AuthService
from app.dependecies.auth import CurrentUser, get_current_user
from app.core.config import get_settings
from app.core.limiter import limiter

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
def register(request: Request, data: UserRegister, db: Session = Depends(get_db)):
    return AuthService(db).register(data)

@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return AuthService(db).login(form.username, form.password)

@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(body.refresh_token)

@router.get("/me", response_model=UserResponse)
def me(user = CurrentUser):
    return user

@router.post("/logout", status_code=204)
def logout(body: LogoutRequest, db: Session = Depends(get_db), _user = CurrentUser):
    AuthService(db).logout(
        access_token=body.access_token,
        refresh_token=body.refresh_token,
    )

@router.patch("/users/{user_id}/promote", response_model=PromoteUserResponse)
def promote_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Security(get_current_user, scopes=["admin"]),
):
    return AuthService(db).promote(user_id, current_user)


@router.patch("/users/{user_id}/demote", response_model=PromoteUserResponse)
def demote_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Security(get_current_user, scopes=["admin"]),
):
    return AuthService(db).demote(user_id, current_user)
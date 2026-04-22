from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schema.auth_schema import TokenResponse, UserRegister, UserResponse, RefreshRequest, LogoutRequest
from app.service.auth_service import AuthService
from app.dependecies.auth import CurrentUser

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    return AuthService(db).register(data)

@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
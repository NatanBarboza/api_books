from pydantic import BaseModel, EmailStr, field_validator
import re

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v:str) -> str:
        if len(v) < 8:
            raise ValueError("Password must have at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least 1 uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least 1 number.")
        return v
    
    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError("Username must be between 3 and 30 alphanumeric characters.")
        return v
    
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    access_token: str
    refresh_token: str | None = None

class PromoteUserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_superuser: bool
    message: str

    model_config = {"from_attributes": True}
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


# What client sends to register
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


# What we return to client (never return password!)
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# Login request
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Token response
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ProfileResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phoneNumber: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phoneNumber: Optional[str] = None

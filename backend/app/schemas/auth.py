"""Authentication and public user contracts."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def normalize_email(value: str) -> str:
    return value.strip().casefold()


def validate_password_strength(value: str) -> str:
    if len(value) < 10 or len(value) > 128:
        raise ValueError("password must contain between 10 and 128 characters")
    if not re.search(r"[a-z]", value) or not re.search(r"[A-Z]", value) or not re.search(r"\d", value):
        raise ValueError("password must include an uppercase letter, a lowercase letter, and a number")
    return value


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("name must contain at least two visible characters")
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: EmailStr) -> str:
        return normalize_email(str(value))

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_password_strength(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: EmailStr) -> str:
        return normalize_email(str(value))


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=4096)


class LogoutRequest(RefreshRequest):
    pass


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(gt=0)


class AuthResponse(BaseModel):
    success: bool = True
    user: UserResponse
    tokens: AuthTokens


class UserEnvelope(BaseModel):
    success: bool = True
    user: UserResponse


class LogoutResponse(BaseModel):
    success: bool = True

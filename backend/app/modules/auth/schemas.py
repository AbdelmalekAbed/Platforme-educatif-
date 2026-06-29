from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.core.permissions import Role


# --- Auth Schemas ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = None
    role: Role = Role.STUDENT


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# --- User Schemas ---

class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: Role
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


# --- Student Profile ---

class StudentProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    date_of_birth: Optional[str] = None
    school_level: Optional[str] = None
    school_name: Optional[str] = None
    city: Optional[str] = None

    model_config = {"from_attributes": True}


class StudentProfileUpdate(BaseModel):
    date_of_birth: Optional[str] = None
    school_level: Optional[str] = None
    school_name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None

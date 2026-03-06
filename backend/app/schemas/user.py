"""
User & Auth Schemas

Pydantic schemas for user registration, login, and JWT tokens.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=128)
    role: str = "farmer"
    region: Optional[str] = None
    preferred_language: str = "en"


class UserLogin(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    phone: str
    email: Optional[str]
    role: str
    region: Optional[str]
    preferred_language: str
    accessibility_settings: Dict[str, Any]
    is_onboarded: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    region: Optional[str] = None
    preferred_language: Optional[str] = None
    accessibility_settings: Optional[Dict[str, Any]] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

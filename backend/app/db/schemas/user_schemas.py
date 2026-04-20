"""
Pydantic schemas for User-related request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# --- Request Schemas ---

class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, examples=["user@example.com"])
    username: str = Field(..., min_length=3, max_length=100, examples=["johndoe"])
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255, examples=["John Doe"])


class UserLogin(BaseModel):
    email: str = Field(..., examples=["user@example.com"])
    password: str = Field(...)


# --- Response Schemas ---

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfile(UserResponse):
    """Extended profile with stats."""
    total_borrows: int = 0
    active_borrows: int = 0


# --- Token Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

"""
User schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_admin": False,
                "created_at": "2025-01-01T00:00:00"
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

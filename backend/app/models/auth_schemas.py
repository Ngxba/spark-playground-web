"""
Pydantic schemas for authentication
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class UserSignUpRequest(BaseModel):
    """Schema for user sign up request"""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123"
            }
        }


class UserSignInRequest(BaseModel):
    """Schema for user sign in request"""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "SecurePass123"
            }
        }


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "john_doe",
                "email": "john@example.com",
                "is_active": True,
                "is_verified": False,
                "created_at": "2024-01-01T00:00:00",
                "last_login": None
            }
        }


class TokenResponse(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "john_doe",
                    "email": "john@example.com",
                    "is_active": True,
                    "is_verified": False,
                    "created_at": "2024-01-01T00:00:00",
                    "last_login": None
                }
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid credentials"
            }
        }

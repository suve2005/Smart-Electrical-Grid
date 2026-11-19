"""Pydantic models for request/response schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# Response models
class RoleResponse(BaseModel):
    role_id: int
    role_name: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    employee_id_hash: str  # This will be the hashed value (internal use)
    fullname: str
    email: str
    nic_hash: str  # This will be the hashed value (internal use)
    role: RoleResponse
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Response for login/refresh endpoints."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    firebase_uid: str
    email: str


class LogoutResponse(BaseModel):
    """Response for logout endpoint."""
    message: str = "Successfully logged out"
    revoked: bool = True


# Request models
class RegisterRequest(BaseModel):
    """Request body for user registration."""
    email: EmailStr
    fullname: str = Field(..., min_length=2, max_length=100)
    nic: str = Field(..., min_length=5, max_length=20)
    employee_id: str = Field(..., min_length=1, max_length=50)
    firebase_id_token: str = Field(..., description="Firebase ID token from client")


class LoginRequest(BaseModel):
    """Request body for user login."""
    firebase_id_token: str = Field(..., description="Firebase ID token from client")
    email: Optional[EmailStr] = None  # Optional, extracted from token during verification


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    firebase_id_token: str = Field(..., description="Current Firebase ID token")


class LogoutRequest(BaseModel):
    """Request body for logout."""
    firebase_id_token: str = Field(..., description="Current Firebase ID token")


# Error response models
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[dict] = None

    class Config:
        from_attributes = True
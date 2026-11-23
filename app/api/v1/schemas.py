"""Pydantic request and response schemas for authentication and users."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RoleResponse(BaseModel):
    role_id: int
    role_name: str


class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    fullname: str
    email: str
    role: RoleResponse
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AuthResponse(BaseModel):
    """Profile returned after Firebase authentication is checked by the API."""
    user: UserResponse
    firebase_uid: str
    email: str


class LogoutResponse(BaseModel):
    message: str = "Signed out on the client."
    revoked: bool = False


class RegisterRequest(BaseModel):
    """Profile fields plus the Firebase ID token for the newly created account."""
    email: EmailStr
    fullname: str = Field(..., min_length=2, max_length=100)
    nic: str = Field(..., min_length=5, max_length=20)
    employee_id: str = Field(..., min_length=1, max_length=50)
    firebase_id_token: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    firebase_id_token: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    firebase_id_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel):
    firebase_id_token: str = Field(..., min_length=1)


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None

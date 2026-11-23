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


class UserStatusUpdate(BaseModel):
    """Request body for PATCH /users/{user_id}/status endpoint."""
    is_active: bool


class APIError(BaseModel):
    """Standardized error response format following the contract-first principle."""
    error: str  # Machine-readable error code (e.g. "VALIDATION_ERROR", "NOT_FOUND")
    message: str  # Human-readable explanation
    details: Optional[dict] = None  # Additional context when helpful


class ErrorResponse(BaseModel):
    """Wrapper for standardized API error responses."""
    error: APIError

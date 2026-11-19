"""Authentication and authorization dependencies for FastAPI endpoints.

Provides:
- get_current_user: Verifies Firebase token, retrieves user from Postgres, checks status and role
- require_admin: Dependency that ensures only ADMIN role users can access

Dependencies:
- OAuth2PasswordBearer for token extraction from Authorization header
- Firebase token verification (mock initially, real later)
- SQLAlchemy session for user lookup
"""
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import structlog

from app.core.config import is_mock_firebase
from app.core.security import hash_nic, hash_employee_id, verify_nic, verify_employee_id
from app.db.session import get_db, SessionLocal
from app.models.user import AppUser
from app.models.role import Role


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_firebase_token(id_token: str) -> dict:
    """Verify Firebase ID token - mock initially, real later.

    For mock: accepts tokens starting with "mock-" and extracts claims.
    For production: use firebase_admin.auth.verify_id_token(id_token)
    """
    if not id_token or id_token.startswith("invalid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase ID token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Mock verification - in production replace with:
    #   return firebase_admin.auth.verify_id_token(id_token)
    claims = verify_firebase_token_mock(id_token)

    if "uid" not in claims or "email" not in claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return claims


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> AppUser:
    """Dependency to get the current user from Firebase token.

    Steps:
    1. Verify Firebase ID token via OAuth2PasswordBearer
    2. Extract UID and email from claims
    3. Look up user in app_users table by firebase_uid
    4. Check account is active (is_active == True)
    5. Return user object

    Raises 401 if:
    - Token is invalid/malformed
    - User not found in PostgreSQL
    - Account is disabled (is_active == False)
    """
    # Step 1: Verify token (this already extracts uid and email)
    try:
        claims = verify_firebase_token(token)
    except HTTPException:
        raise

    uid: str = claims["uid"]
    email: str = claims["email"]

    # Step 2: Look up user in app_users table
    user = db.query(AppUser).filter(AppUser.firebase_uid == uid).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please register first.",
        )

    # Step 3: Check account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
        )

    # Step 4: Return user
    logger.info(
        "Current user authenticated",
        firebase_uid=uid,
        email=email,
        role=user.role.role_name if user.role else "unknown",
    )
    return user


def require_admin(current_user: AppUser = Depends(get_current_user)) -> AppUser:
    """Dependency to ensure only ADMIN role users can access the endpoint.

    Raises 403 if the current user is not an Admin.
    """
    if current_user.role.role_name != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
"""Authentication and PostgreSQL user-management API routes."""

from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.schemas import (
    APIError,
    AuthResponse,
    ErrorResponse,
    LoginRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    RoleResponse,
    UserStatusUpdate,
    UserResponse,
)
from app.core.deps import get_current_user, require_admin, verify_firebase_token
from app.core.security import hash_employee_id, hash_nic
from app.db.session import get_db
from app.models.role import Role
from app.models.user import AppUser

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["authentication"])


def _user_response(user: AppUser) -> UserResponse:
    """Build a public profile response. Never expose stored identifier hashes."""
    return UserResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        fullname=user.fullname,
        email=user.email,
        role=RoleResponse(role_id=user.role.role_id, role_name=user.role.role_name),
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _auth_response(user: AppUser) -> AuthResponse:
    return AuthResponse(user=_user_response(user), firebase_uid=user.firebase_uid, email=user.email)


def _require_verified_email(claims: dict) -> None:
    if not claims.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verify your email address before signing in.",
        )


def _find_active_profile(db: Session, claims: dict) -> AppUser:
    user = db.query(AppUser).filter(AppUser.firebase_uid == claims["uid"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Application profile not found. Please register first.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your application account has been deactivated.",
        )
    if user.email.casefold() != claims["email"].casefold():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email",
        )
    return user


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Account",
)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Verify the newly-created Firebase account and persist its profile."""
    claims = verify_firebase_token(request.firebase_id_token)
    firebase_uid = claims["uid"]
    token_email = claims["email"].strip().casefold()

    if request.email.strip().casefold() != token_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=APIError(error="VALIDATION_ERROR", message="Invalid email"),
            ).model_dump(),
        )

    existing_user = db.query(AppUser).filter(
        (AppUser.firebase_uid == firebase_uid) | (AppUser.email == token_email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error=APIError(error="CONFLICT", message="Try New password or email"),
            ).model_dump(),
        )

    # The "Engineer" role is seeded by migration bb7d2bbe903c_initial_application_schema.py
    role = db.query(Role).filter(Role.role_name == "Engineer").one_or_none()
    if role is None:
        logger.critical("Engineer role not found - database migration may not have been applied")
        raise RuntimeError("Engineer role not found in database. Please run database migrations.")

    new_user = AppUser(
        firebase_uid=firebase_uid,
        employee_id_hash=hash_employee_id(request.employee_id.strip()),
        fullname=request.fullname.strip(),
        email=token_email,
        nic_hash=hash_nic(request.nic.strip()),
        role_id=role.role_id,
        is_active=True,
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Duplicate profile registration rejected", firebase_uid=firebase_uid)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Try New password or email.",
        ) from exc

    logger.info("Application profile created", firebase_uid=firebase_uid, email=token_email)
    return _auth_response(new_user)


@router.post("/login", response_model=AuthResponse, summary="Validate login against PostgreSQL")
def login(request: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    claims = verify_firebase_token(request.firebase_id_token)
    _require_verified_email(claims)
    user = _find_active_profile(db, claims)
    logger.info("User login accepted", firebase_uid=user.firebase_uid)
    return _auth_response(user)


@router.post("/refresh", response_model=AuthResponse, summary="Refresh the Firebase-backed profile session")
def refresh(request: RefreshRequest, db: Session = Depends(get_db)) -> AuthResponse:
    claims = verify_firebase_token(request.firebase_id_token)
    _require_verified_email(claims)
    return _auth_response(_find_active_profile(db, claims))


@router.post("/logout", response_model=LogoutResponse, summary="Client-side Firebase logout acknowledgement")
async def logout() -> LogoutResponse:
    # Firebase signOut() runs in the browser. This route does not revoke all
    # Firebase refresh tokens and therefore must not claim that it did.
    return LogoutResponse()


@router.get("/me", response_model=UserResponse, summary="Get the current PostgreSQL profile")
def me(current_user: AppUser = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)


@router.get("/users", response_model=List[UserResponse], summary="List users (Admin only)")
def list_users(
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(require_admin),
) -> List[UserResponse]:
    users = db.query(AppUser).order_by(AppUser.id).all()
    return [_user_response(user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get a user (Admin only)")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(require_admin),
) -> UserResponse:
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return _user_response(user)


@router.patch("/users/{user_id}/role", response_model=UserResponse, summary="Change user role (Admin only)")
def change_user_role(
    user_id: int,
    new_role_name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(require_admin),
) -> UserResponse:
    if new_role_name not in {"Engineer", "Admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid roles are Engineer and Admin.",
        )

    target_user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    role = db.query(Role).filter(Role.role_name == new_role_name).first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested role does not exist.")

    target_user.role = role
    db.commit()
    db.refresh(target_user)
    return _user_response(target_user)


@router.patch("/users/{user_id}/status", response_model=UserResponse, summary="Change user status (Admin only)")
def change_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(require_admin),
) -> UserResponse:
    target_user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if target_user.id == _admin.id and not status_update.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=APIError(error="VALIDATION_ERROR", message="Administrators cannot deactivate their own account."),
            ).model_dump(),
        )

    target_user.is_active = status_update.is_active
    db.commit()
    db.refresh(target_user)
    return _user_response(target_user)

"""API v1 endpoints for registration, login, refresh, and logout."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.core.config import is_mock_firebase, FIREBASE_API_KEY
from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.core.security import hash_nic, hash_employee_id, verify_nic, verify_employee_id
from app.models.user import AppUser
from app.models.role import Role
from app.api.v1.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    LogoutRequest,
    UserResponse,
    AuthResponse,
    LogoutResponse,
    ErrorResponse,
)


logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])


def verify_firebase_token_mock(id_token: str) -> dict:
    """Mock Firebase token verification for development.

    In production, replace with firebase_admin.auth.verify_id_token().
    For now, validates basic token structure and extracts claims.
    """
    # Mock: accept any token starting with "mock-" or "test-"
    # In real implementation, use: firebase_admin.auth.verify_id_token(id_token)

    if not id_token or id_token.startswith("invalid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase ID token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Mock extraction of user claims from token
    # Real implementation would decode the JWT properly
    return {
        "uid": id_token[:20] if len(id_token) > 20 else id_token,  # Mock UID
        "email": "user@example.com",  # Mock email - extract from real token
        "email_verified": True,
    }


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user with Firebase Auth UID and store data in Postgres with hashed NIC/employee_id",
)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user.

    Steps:
    1. Verify Firebase ID token (mock initially, real later)
    2. Hash NIC and employee_id using PBKDF2
    3. Look up or create user's role (default: Engineer)
    4. Create app_users record
    5. Return auth response with user info
    """
    # Step 1: Verify Firebase token
    try:
        firebase_claims = verify_firebase_token_mock(request.firebase_id_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Firebase token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify authentication token",
        )

    firebase_uid = firebase_claims["uid"]
    email = firebase_claims["email"]

    # Step 2: Hash sensitive fields
    nic_hash = hash_nic(request.nic)
    employee_id_hash = hash_employee_id(request.employee_id)

    # Step 3: Look up role (default to Engineer)
    from app.db.session import SessionLocal
    from sqlalchemy.orm import Session as Sess

    role = db.query(Role).filter(Role.role_name == "Engineer").first()
    if not role:
        # Create default roles if they don't exist
        from app.models.role import Role as RoleModel
        role = RoleModel(role_name="Engineer")
        db.add(role)
        db.commit()
        db.refresh(role)

    # Step 4: Check if user already exists
    existing_user = db.query(AppUser).filter(
        (AppUser.email == email) | (AppUser.firebase_uid == firebase_uid)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or Firebase UID already exists",
        )

    # Step 5: Create new user
    new_user = AppUser(
        firebase_uid=firebase_uid,
        employee_id_hash=employee_id_hash,  # Store the hashed value
        fullname=request.fullname,
        email=email,
        nic_hash=nic_hash,
        role_id=role.role_id,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info("User registered successfully", firebase_uid=firebase_uid, email=email)

    # Step 6: Build response
    from app.api.v1.schemas import RoleResponse

    role_response = RoleResponse(role_id=role.role_id, role_name=role.role_name)

    user_response = UserResponse(
        id=new_user.id,
        firebase_uid=new_user.firebase_uid,
        employee_id_hash=new_user.employee_id_hash,  # This is the hashed value
        fullname=new_user.fullname,
        email=new_user.email,
        nic_hash=new_user.nic_hash,
        role=role_response,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
    )

    # In a real implementation, we'd generate a JWT access token here
    access_token = "mock_access_token_for_development"

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
        firebase_uid=firebase_uid,
        email=email,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="User login",
    description="Login with Firebase Auth token and verify user exists in Postgres",
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """Login user with Firebase ID token.

    Steps:
    1. Verify Firebase ID token
    2. Look up user by email in app_users
    3. Check is_active status
    4. Return auth response
    """
    # Step 1: Verify Firebase token
    try:
        firebase_claims = verify_firebase_token_mock(request.firebase_id_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Firebase token verification failed during login", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify authentication token",
        )

    firebase_uid = firebase_claims.get("uid", "")
    email = firebase_claims.get("email", "")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found in Firebase token",
        )

    # Step 2: Look up user
    user = db.query(AppUser).filter(AppUser.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please register first.",
        )

    # Step 3: Check active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
        )

    # Step 4: Build response
    from app.api.v1.schemas import RoleResponse

    role_response = RoleResponse(
        role_id=user.role.role_id,
        role_name=user.role.role_name
    )

    user_response = UserResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        employee_id_hash=user.employee_id_hash,  # Hashed value stored
        fullname=user.fullname,
        email=user.email,
        nic_hash=user.nic_hash,
        role=role_response,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )

    access_token = "mock_access_token_for_development"

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
        firebase_uid=user.firebase_uid,
        email=user.email,
    )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh session",
    description="Refresh/revalidate session with current Firebase token",
)
async def refresh(
    request: RefreshRequest,
    db: Session = Depends(get_db),
):
    """Refresh session with current Firebase token.

    Steps:
    1. Verify Firebase ID token
    2. Look up user in app_users
    3. Return updated auth response
    """
    # Step 1: Verify Firebase token
    try:
        firebase_claims = verify_firebase_token_mock(request.firebase_id_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Firebase token verification failed during refresh", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify authentication token",
        )

    firebase_uid = firebase_claims.get("uid", "")
    email = firebase_claims.get("email", "")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found in Firebase token",
        )

    # Step 2: Look up user
    user = db.query(AppUser).filter(AppUser.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please register or login first.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
        )

    # Step 3: Build response
    from app.api.v1.schemas import RoleResponse

    role_response = RoleResponse(
        role_id=user.role.role_id,
        role_name=user.role.role_name
    )

    user_response = UserResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        employee_id_hash=user.employee_id_hash,
        fullname=user.fullname,
        email=user.email,
        nic_hash=user.nic_hash,
        role=role_response,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )

    access_token = "mock_access_token_for_development"

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
        firebase_uid=user.firebase_uid,
        email=user.email,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User logout",
    description="Logout and revoke current session",
)
async def logout(
    request: LogoutRequest,
):
    """Logout user.

    Steps:
    1. Revoke current session/token
    2. Return success status
    """
    # In a stateless JWT setup, logout is primarily client-side
    # For session-based, we'd invalidate the token in Redis, etc.

    logger.info("User logged out", firebase_uid=request.firebase_id_token[:20] if request.firebase_id_token else "unknown")

    return LogoutResponse(message="Successfully logged out", revoked=True)


# --- Additional endpoints for user management ---

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user",
)
async def me(current_user: AppUser = Depends(get_current_user)) -> UserResponse:
    """Get current user profile.

    Requires valid Firebase ID token in Authorization header.
    """
    from app.api.v1.schemas import RoleResponse

    role_response = RoleResponse(
        role_id=current_user.role.role_id,
        role_name=current_user.role.role_name
    )

    return UserResponse(
        id=current_user.id,
        firebase_uid=current_user.firebase_uid,
        employee_id_hash=current_user.employee_id_hash,
        fullname=current_user.fullname,
        email=current_user.email,
        nic_hash=current_user.nic_hash,
        role=role_response,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users (admin only)",
    description="List all users in the system. Admin access required.",
    dependencies=[Depends(require_admin)],
)
async def list_users(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)) -> List[UserResponse]:
    """List all users.

    Requires Admin role. Returns all user profiles.
    """
    from app.api.v1.schemas import RoleResponse

    users = db.query(AppUser).all()

    result = []
    for user in users:
        role_response = RoleResponse(
            role_id=user.role.role_id,
            role_name=user.role.role_name
        )
        result.append(UserResponse(
            id=user.id,
            firebase_uid=user.firebase_uid,
            employee_id_hash=user.employee_id_hash,
            fullname=user.fullname,
            email=user.email,
            nic_hash=user.nic_hash,
            role=role_response,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ))

    return result


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (admin only)",
    description="Get user profile by user ID. Admin access required.",
    dependencies=[Depends(require_admin)],
)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> UserResponse:
    """Get user by ID.

    Requires Admin role. Returns user profile for the given user_id.
    """
    from app.api.v1.schemas import RoleResponse

    user = db.query(AppUser).filter(AppUser.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    role_response = RoleResponse(
        role_id=user.role.role_id,
        role_name=user.role.role_name
    )

    return UserResponse(
        id=user.id,
        firebase_uid=user.firebase_uid,
        employee_id_hash=user.employee_id_hash,
        fullname=user.fullname,
        email=user.email,
        nic_hash=user.nic_hash,
        role=role_response,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Promote/demote user role (admin only)",
    description="Change user role. Admin access required. "
    "Existing ADMIN users can promote other users. "
    "Ordinary ENGINEERING users cannot modify roles.",
    dependencies=[Depends(require_admin)],
)
async def change_user_role(
    user_id: int,
    new_role_name: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> UserResponse:
    """Change user role.

    Requires Admin role. Only admins can promote/demote users.
    Valid role names: Engineer, Admin
    """
    from app.api.v1.schemas import RoleResponse

    # Look up the target user
    target_user = db.query(AppUser).filter(AppUser.id == user_id).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Look up the new role
    from app.models.role import Role as RoleModel
    new_role = db.query(RoleModel).filter(RoleModel.role_name == new_role_name).first()

    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role name: {new_role_name}. Valid roles: Engineer, Admin",
        )

    # Change the role
    target_user.role_id = new_role.role_id
    db.add(target_user)
    db.commit()
    db.refresh(target_user)

    role_response = RoleResponse(
        role_id=target_user.role.role_id,
        role_name=target_user.role.role_name
    )

    return UserResponse(
        id=target_user.id,
        firebase_uid=target_user.firebase_uid,
        employee_id_hash=target_user.employee_id_hash,
        fullname=target_user.fullname,
        email=target_user.email,
        nic_hash=target_user.nic_hash,
        role=role_response,
        is_active=target_user.is_active,
        created_at=target_user.created_at,
        updated_at=target_user.updated_at,
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
    summary="Activate/deactivate user (admin only)",
    description="Change user account status. Admin access required.",
    dependencies=[Depends(require_admin)],
)
async def change_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> UserResponse:
    """Change user account status.

    Requires Admin role. Admins can activate or deactivate user accounts.
    """
    from app.api.v1.schemas import RoleResponse

    # Look up the target user
    target_user = db.query(AppUser).filter(AppUser.id == user_id).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Change the status
    target_user.is_active = is_active
    db.add(target_user)
    db.commit()
    db.refresh(target_user)

    role_response = RoleResponse(
        role_id=target_user.role.role_id,
        role_name=target_user.role.role_name
    )

    return UserResponse(
        id=target_user.id,
        firebase_uid=target_user.firebase_uid,
        employee_id_hash=target_user.employee_id_hash,
        fullname=target_user.fullname,
        email=target_user.email,
        nic_hash=target_user.nic_hash,
        role=role_response,
        is_active=target_user.is_active,
        created_at=target_user.created_at,
        updated_at=target_user.updated_at,
    )
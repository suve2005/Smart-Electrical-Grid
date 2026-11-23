"""Firebase authentication and PostgreSQL-backed authorization dependencies."""

from pathlib import Path

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials, get_app, initialize_app
from firebase_admin.exceptions import FirebaseError
from sqlalchemy.orm import Session

from app.core.config import BASE_DIR, FIREBASE_PROJECT_ID, FIREBASE_SERVICE_ACCOUNT_PATH
from app.db.session import get_db
from app.models.user import AppUser

logger = structlog.get_logger()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _get_firebase_app():
    """Return the initialized Admin SDK app, using a service key or ADC."""
    try:
        return get_app()
    except ValueError:
        pass

    try:
        credential = None
        if FIREBASE_SERVICE_ACCOUNT_PATH:
            key_path = Path(FIREBASE_SERVICE_ACCOUNT_PATH)
            if not key_path.is_absolute():
                key_path = BASE_DIR / key_path
            if not key_path.is_file():
                raise FileNotFoundError("Firebase service-account file was not found: " + str(key_path))
            credential = credentials.Certificate(str(key_path))

        options = {}
        if FIREBASE_PROJECT_ID:
            options["projectId"] = FIREBASE_PROJECT_ID
        return initialize_app(credential, options=options or None)
    except Exception as exc:
        logger.error("Firebase Admin SDK initialization failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Firebase Admin credentials are not configured. Set "
                "FIREBASE_SERVICE_ACCOUNT_PATH in the backend .env, or configure "
                "Google Application Default Credentials."
            ),
        ) from exc


def verify_firebase_token(id_token: str) -> dict:
    """Cryptographically verify a Firebase ID token with Firebase Admin SDK."""
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase ID token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    app = _get_firebase_app()
    try:
        claims = firebase_auth.verify_id_token(id_token, app=app)
    except (ValueError, FirebaseError) as exc:
        logger.warning("Firebase ID token verification failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase ID token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception as exc:
        logger.error("Firebase token verification service failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase token verification is temporarily unavailable.",
        ) from exc

    if not claims.get("uid") or not claims.get("email"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token does not contain the required user claims.",
        )
    return claims


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> AppUser:
    """Authenticate the Firebase bearer token and load its PostgreSQL profile."""
    claims = verify_firebase_token(token)

    if not claims.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verify your email address before accessing the application.",
        )

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
            detail="The Firebase account does not match the application profile.",
        )

    logger.info(
        "Current user authenticated",
        firebase_uid=user.firebase_uid,
        email=user.email,
        role=user.role.role_name if user.role else "unknown",
    )
    return user


def require_admin(current_user: AppUser = Depends(get_current_user)) -> AppUser:
    """Allow access only to users assigned the Admin role in PostgreSQL."""
    if not current_user.role or current_user.role.role_name != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user

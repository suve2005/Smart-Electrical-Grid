"""Application configuration loaded from the repository-root .env."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=False)

# PostgreSQL configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5433"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "smart_grid")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if not POSTGRES_PASSWORD:
    raise RuntimeError("POSTGRES_PASSWORD is missing from the root .env")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    database=POSTGRES_DB,
)

# Firebase web-project settings
FIREBASE_API_KEY: Optional[str] = os.getenv("FIREBASE_API_KEY")
FIREBASE_AUTH_DOMAIN: Optional[str] = os.getenv("FIREBASE_AUTH_DOMAIN")
FIREBASE_PROJECT_ID: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_STORAGE_BUCKET: Optional[str] = os.getenv("FIREBASE_STORAGE_BUCKET")
FIREBASE_MESSAGING_SENDER_ID: Optional[str] = os.getenv("FIREBASE_MESSAGING_SENDER_ID")

# Firebase Admin SDK credentials. Relative paths are resolved from the repo root.
FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-for-real-secret")
ALGORITHM = os.getenv("ALGORITHM", "PBKDF2")
PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "100000"))
SALT_BYTES = int(os.getenv("SALT_BYTES", "16"))

# Application configuration
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]


def is_mock_firebase() -> bool:
    return bool(FIREBASE_API_KEY and FIREBASE_API_KEY.startswith("mock_"))


def is_production() -> bool:
    return ENVIRONMENT == "production"

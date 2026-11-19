"""Configuration settings loaded from environment variables.
Supports both development (mock Firebase) and production (real Firebase) setups.
"""
import os
from pathlib import Path
from typing import Optional

# Base directory (parent of the app directory)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
def load_env() -> None:
    """Load environment variables from .env file in base directory."""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

# Firebase Configuration
FIREBASE_API_KEY: Optional[str] = os.getenv("FIREBASE_API_KEY")
FIREBASE_AUTH_DOMAIN: Optional[str] = os.getenv("FIREBASE_AUTH_DOMAIN")
FIREBASE_PROJECT_ID: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_STORAGE_BUCKET: Optional[str] = os.getenv("FIREBASE_STORAGE_BUCKET")
FIREBASE_MESSAGING_SENDER_ID: Optional[str] = os.getenv("FIREBASE_MESSAGING_SENDER_ID")

# Database Configuration
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/smart_grid")

# Security Configuration
SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production-for-real-secret")
ALGORITHM: str = os.getenv("ALGORITHM", "PBKDF2")
PBKDF2_ITERATIONS: int = int(os.getenv("PBKDF2_ITERATIONS", "100000"))
SALT_BYTES: int = int(os.getenv("SALT_BYTES", "16"))

# Application Settings
DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

# CORS settings (add origins as needed)
CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []


def is_mock_firebase() -> bool:
    """Check if we're using mock Firebase configuration."""
    return FIREBASE_API_KEY and FIREBASE_API_KEY.startswith("mock_")


def is_production() -> bool:
    """Check if running in production environment."""
    return ENVIRONMENT == "production"
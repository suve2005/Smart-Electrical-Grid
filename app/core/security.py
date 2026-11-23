"""PBKDF2-HMAC-SHA256 hashing for sensitive profile identifiers."""

import base64
import hashlib
import hmac
import os
from typing import Optional

from app.core.config import PBKDF2_ITERATIONS, SALT_BYTES


def hash_nic(nic: str, iterations: Optional[int] = None, salt_bytes: Optional[int] = None) -> str:
    """Return a salted PBKDF2 hash in the format salt_base64:hash_base64."""
    rounds = iterations or PBKDF2_ITERATIONS
    salt = os.urandom(salt_bytes or SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha256", nic.encode("utf-8"), salt, rounds)
    return base64.b64encode(salt).decode("ascii") + ":" + base64.b64encode(derived).decode("ascii")


def verify_nic(nic: str, stored_hash: str, iterations: Optional[int] = None) -> bool:
    """Verify a value against its stored salted PBKDF2 hash."""
    try:
        salt_b64, hash_b64 = stored_hash.split(":", 1)
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(hash_b64, validate=True)
        actual = hashlib.pbkdf2_hmac(
            "sha256", nic.encode("utf-8"), salt, iterations or PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def hash_employee_id(employee_id: str, iterations: Optional[int] = None, salt_bytes: Optional[int] = None) -> str:
    """Hash an employee ID using the same PBKDF2 format as NIC values."""
    return hash_nic(employee_id, iterations, salt_bytes)


def verify_employee_id(employee_id: str, stored_hash: str) -> bool:
    """Verify an employee ID against its stored salted PBKDF2 hash."""
    return verify_nic(employee_id, stored_hash)

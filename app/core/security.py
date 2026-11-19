"""Security utilities for hashing NIC and employee_id fields.
Uses PBKDF2-HMAC-SHA256 for salted key derivation.
Also provides Firebase mock token verification.
Format: {salt_base64}:{hash_base64}
"""
import base64
import os
from typing import Tuple

# PBKDF2 configuration
PBKDF2_ITERATIONS = 100000  # Can be overridden via environment
SALT_BYTES = 16  # 128-bit salt


def hash_nic(nic: str, iterations: int = None, salt_bytes: int = None) -> str:
    """Hash a NIC number using PBKDF2-HMAC-SHA256.

    Args:
        nic: The NIC number to hash
        iterations: PBKDF2 iteration count (uses default from config if None)
        salt_bytes: Salt size in bytes (uses default from config if None)

    Returns:
        String in format "base64_salt:base64_hash"
    """
    iterations = iterations or PBKDF2_ITERATIONS
    salt_bytes = salt_bytes or SALT_BYTES

    # Generate random salt
    salt = os.urandom(salt_bytes)
    salt_b64 = base64.b64encode(salt).decode('utf-8')

    # Derive key using PBKDF2-HMAC-SHA256
    dk = base64.b64encode(
        __import__('hashlib').pbkdf2_hmac(
            'sha256',
            nic.encode('utf-8'),
            salt,
            iterations
        )
    ).decode('utf-8')

    return f"{salt_b64}:{dk}"


def verify_nic(nic: str, stored_hash: str) -> bool:
    """Verify a NIC number against a stored PBKDF2 hash.

    Args:
        nic: The NIC number to verify
        stored_hash: The stored hash string in "salt:hash" format

    Returns:
        True if the NIC matches, False otherwise
    """
    try:
        salt_b64, hash_b64 = stored_hash.split(':', 1)
        salt = base64.b64decode(salt_b64)

        dk = __import__('hashlib').pbkdf2_hmac(
            'sha256',
            nic.encode('utf-8'),
            salt,
            PBKDF2_ITERATIONS
        )

        stored_dk = base64.b64decode(hash_b64)

        # Constant-time comparison using bytes
        return __import__('hmac').compare_digest(dk, stored_dk)
    except (ValueError, IndexError):
        return False


def hash_employee_id(employee_id: str, iterations: int = None, salt_bytes: int = None) -> str:
    """Hash an employee ID using PBKDF2-HMAC-SHA256.

    Same approach as hash_nic but for employee_id field.

    Args:
        employee_id: The employee ID to hash
        iterations: PBKDF2 iteration count
        salt_bytes: Salt size in bytes

    Returns:
        String in format "base64_salt:base64_hash"
    """
    return hash_nic(employee_id, iterations, salt_bytes)


def verify_employee_id(employee_id: str, stored_hash: str) -> bool:
    """Verify an employee ID against a stored PBKDF2 hash.

    Same approach as verify_nic but for employee_id field.
    """
    return verify_nic(employee_id, stored_hash)
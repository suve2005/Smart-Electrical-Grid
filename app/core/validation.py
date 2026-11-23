"""Validation utilities for user input and authentication assertions."""


def verify_email_match(firebase_email: str, user_email: str) -> bool:
    """
    Compare two email addresses for equality, case-insensitive.

    This is used to verify that a Firebase-authenticated email matches
    the email submitted by the user, preventing account mismatch attacks.

    Args:
        firebase_email: Email from Firebase ID token claims
        user_email: Email submitted by the user in their request

    Returns:
        True if emails match (case-insensitive), False otherwise
    """
    return firebase_email.casefold() == user_email.casefold()


def sanitize_email(email: str) -> str:
    """
    Sanitize an email address by stripping whitespace.

    Args:
        email: Raw email string

    Returns:
        Stripped email string
    """
    return email.strip().casefold()
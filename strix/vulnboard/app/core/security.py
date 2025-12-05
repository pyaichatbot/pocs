"""Security utilities - placeholder for proper security checks (partially unused in vulnerable flows)."""

import hashlib
from typing import Optional


def hash_password(password: str) -> str:
    """Hash password using SHA256 (intentionally weak for demo - should use bcrypt/argon2)."""
    # VULNERABILITY: Weak password hashing - SHA256 is not suitable for passwords
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed


def check_authorization(user_id: int, resource_user_id: int, user_role: str = "user") -> bool:
    """
    Check if user is authorized to access a resource.
    VULNERABILITY: This function exists but is intentionally NOT called in vulnerable routes,
    leading to IDOR (Insecure Direct Object Reference) vulnerabilities.
    """
    # This should be called in user routes but is intentionally bypassed
    if user_role == "admin":
        return True
    return user_id == resource_user_id


def sanitize_input(input_str: str) -> str:
    """
    Basic input sanitization.
    VULNERABILITY: This function exists but is intentionally NOT used in all places,
    leading to XSS vulnerabilities.
    """
    # This should be used but is intentionally bypassed in some templates
    return input_str.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#x27;")


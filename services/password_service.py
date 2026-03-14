"""
Password hashing and verification using SHA-256.
Supports migration from plain-text passwords (legacy).
"""
from __future__ import annotations

import hashlib

# Salt for additional security (change in production if desired)
_PEPPER = "maternal_tracker_2026"


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return hashlib.sha256((password + _PEPPER).encode("utf-8")).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against stored hash.
    Supports legacy plain-text passwords: if stored value is not a valid
    SHA-256 hex (64 chars), falls back to plain comparison for migration.
    """
    if not stored_hash:
        return False
    # SHA-256 hex digest is 64 characters
    if len(stored_hash) == 64 and all(c in "0123456789abcdef" for c in stored_hash.lower()):
        return hash_password(password) == stored_hash
    # Legacy plain-text
    return password == stored_hash


def is_hashed(value: str) -> bool:
    """Check if a stored value appears to be a hash (not plain text)."""
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value.lower())

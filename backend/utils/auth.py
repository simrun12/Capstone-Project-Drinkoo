"""
Authentication utilities for DRINKOO FastAPI backend.

The current implementation supports the planned non-production admin/password login.
Production branches must replace this with environment-backed credentials and stronger
password hashing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..config import DEFAULT_PASSWORD, DEFAULT_USERNAME, TOKEN_EXPIRY_HOURS


@dataclass(frozen=True)
class AuthenticatedUser:
    """Simple authenticated user representation for the current DRINKOO demo."""

    user_id: int
    username: str
    role: str


def verify_development_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Validate the default development admin login."""

    if username != DEFAULT_USERNAME or password != DEFAULT_PASSWORD:
        return None

    return {
        "user_id": 1,
        "username": DEFAULT_USERNAME,
        "role": "admin",
        "token": "dev-token-admin",
        "expires_at": time.time() + (TOKEN_EXPIRY_HOURS * 60 * 60),
    }


def is_default_admin_user(username: str) -> bool:
    """Return whether the username matches the default admin account."""

    return username == DEFAULT_USERNAME

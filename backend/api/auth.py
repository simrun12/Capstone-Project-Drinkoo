"""Authentication routes for DRINKOO."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..utils.auth import AuthenticatedUser, verify_development_login

router = APIRouter(prefix="/auth", tags=["authentication"])

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    """Return the bearer token from FastAPI credentials."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    return credentials.credentials


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)] = None,
) -> AuthenticatedUser:
    """Validate the current request token and return the authenticated user."""

    token = _extract_bearer_token(credentials)

    if token != "dev-token-admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(user_id=1, username="admin", role="admin")


async def require_admin(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    """Require admin authorization for protected routes."""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role is required for this action",
        )

    return current_user


@router.post("/login")
def login(username: str, password: str) -> dict[str, object]:
    """Log in using the default development admin credentials."""

    user_payload = verify_development_login(username=username, password=password)

    if user_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return {
        "message": "Login successful",
        "token_type": "Bearer",
        "access_token": user_payload["token"],
        "user": {
            "user_id": user_payload["user_id"],
            "username": user_payload["username"],
            "role": user_payload["role"],
        },
    }


@router.post("/logout")
def logout(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, str]:
    """Log out the current user."""

    return {"message": f"{current_user.username} logged out successfully"}


@router.get("/me")
def me(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict[str, object]:
    """Return the current authenticated user."""

    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
    }

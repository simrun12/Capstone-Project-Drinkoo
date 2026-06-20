"""
Observability API.

- /status is the only public endpoint (used by the frontend status indicator).
  It returns no per-user data, only an aggregate health flag.
- /events, /chatbot-failures, /metrics, /frontend-event require admin auth.
  /frontend-event accepts any authenticated user and records client telemetry.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from .auth import get_current_user, require_admin
from ..utils.auth import AuthenticatedUser
from ..utils import observability as obs

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/status")
def public_status() -> Dict[str, Any]:
    """Public health indicator — safe for the login page."""
    return obs.get_health_snapshot()


class FrontendEvent(BaseModel):
    event_type: str = Field(..., max_length=80)
    category: str = Field(..., max_length=40)
    severity: str = Field("info", max_length=20)
    session_id: Optional[str] = Field(None, max_length=64)
    path: Optional[str] = Field(None, max_length=200)
    success: Optional[bool] = None
    duration_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


@router.post("/frontend-event")
def ingest_frontend_event(
    payload: FrontendEvent,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, str]:
    """Record a client-side telemetry event for the authenticated user only."""
    obs.log_event(
        event_type=payload.event_type,
        category=payload.category,
        severity=payload.severity if payload.severity in {"debug", "info", "warning", "error", "critical"} else "info",
        source="frontend",
        user=current_user.username,
        session_id=payload.session_id,
        path=payload.path,
        success=payload.success,
        duration_ms=payload.duration_ms,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=payload.details,
    )
    return {"status": "recorded"}


@router.get("/events")
def list_events(
    limit: int = 100,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    since_minutes: Optional[int] = None,
    _admin: AuthenticatedUser = Depends(require_admin),
) -> Dict[str, Any]:
    """Admin-only: list recent events."""
    events = obs.fetch_recent_events(
        limit=min(limit, 500),
        category=category,
        severity=severity,
        since_minutes=since_minutes,
    )
    return {"count": len(events), "events": events}


@router.get("/chatbot-failures")
def list_chatbot_failures(
    limit: int = 100,
    _admin: AuthenticatedUser = Depends(require_admin),
) -> Dict[str, Any]:
    """Admin-only: list recent chatbot interactions flagged as failures."""
    failures = obs.fetch_chatbot_failures(limit=min(limit, 500))
    return {"count": len(failures), "failures": failures}


@router.get("/metrics")
def get_metrics(
    window_minutes: int = 60,
    _admin: AuthenticatedUser = Depends(require_admin),
) -> Dict[str, Any]:
    """Admin-only: aggregate metrics for the observability dashboard."""
    return obs.aggregate_metrics(window_minutes=max(1, min(window_minutes, 1440)))

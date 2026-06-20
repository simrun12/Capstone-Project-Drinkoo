"""
DRINKOO observability layer.

Logs user journeys, request lifecycle, chatbot interactions, and failures to the
internal SQLite database. Data is never returned to end users — only admin-role
accounts can query event logs via /api/v1/observability/*.

Design notes:
- User identity and IP are stored as one-way SHA-256 hashes to support
  per-user analytics without exposing PII across admins.
- Writes are best-effort: logger never raises into request flow.
- A bounded in-memory ring buffer mirrors the last N events for the
  /status endpoint so the frontend indicator can render without admin auth.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

from ..config import DATABASE_PATH


_LOCK = threading.Lock()
_RECENT_EVENTS: deque = deque(maxlen=500)
_HEALTH_STATE: Dict[str, Any] = {
    "last_error_at": None,
    "last_success_at": None,
    "consecutive_errors": 0,
    "total_requests": 0,
    "total_errors": 0,
    "started_at": time.time(),
}


def _hash(value: Optional[str]) -> Optional[str]:
    """Return a short, stable hash for a possibly-sensitive value."""
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _connect() -> sqlite3.Connection:
    """Open a dedicated connection so logging never collides with request DB use."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=2.0)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def log_event(
    event_type: str,
    category: str,
    severity: str = "info",
    *,
    source: str = "backend",
    user: Optional[str] = None,
    session_id: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    duration_ms: Optional[int] = None,
    success: Optional[bool] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Record a single observability event.

    Failures inside this function are swallowed — observability must never break
    the request path.
    """
    payload = json.dumps(details, default=str)[:4000] if details else None
    user_hash = _hash(user)
    ip_hash = _hash(ip)
    ua = (user_agent or "")[:200]
    timestamp = datetime.utcnow().isoformat()

    try:
        with _LOCK:
            conn = _connect()
            try:
                conn.execute(
                    """
                    INSERT INTO event_logs (
                        timestamp, event_type, category, severity, user_hash,
                        session_id, source, path, status_code, duration_ms,
                        success, ip_hash, user_agent, details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        event_type,
                        category,
                        severity,
                        user_hash,
                        session_id,
                        source,
                        path,
                        status_code,
                        duration_ms,
                        int(success) if success is not None else None,
                        ip_hash,
                        ua,
                        payload,
                    ),
                )
                conn.commit()
            finally:
                conn.close()
    except Exception as exc:  # noqa: BLE001 - never propagate
        print(f"[observability] failed to write event: {exc}")

    _update_health(severity, success, status_code)
    _RECENT_EVENTS.append(
        {
            "timestamp": timestamp,
            "type": event_type,
            "category": category,
            "severity": severity,
            "path": path,
            "status_code": status_code,
            "success": success,
        }
    )


def log_chatbot_failure(
    question: str,
    answer: Optional[str],
    *,
    source: Optional[str],
    confidence: Optional[str],
    failure_reason: str,
    similarity_score: Optional[float] = None,
    duration_ms: Optional[int] = None,
    user: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """Record a chatbot interaction the user likely found unhelpful."""
    try:
        with _LOCK:
            conn = _connect()
            try:
                conn.execute(
                    """
                    INSERT INTO chatbot_failures (
                        timestamp, user_hash, session_id, question, answer,
                        source, confidence, failure_reason, similarity_score, duration_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.utcnow().isoformat(),
                        _hash(user),
                        session_id,
                        question[:1000],
                        (answer or "")[:2000],
                        source,
                        confidence,
                        failure_reason,
                        similarity_score,
                        duration_ms,
                    ),
                )
                conn.commit()
            finally:
                conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"[observability] failed to write chatbot failure: {exc}")


def _update_health(severity: str, success: Optional[bool], status_code: Optional[int]) -> None:
    now = time.time()
    _HEALTH_STATE["total_requests"] += 1
    is_failure = (
        severity in ("error", "critical")
        or success is False
        or (status_code is not None and status_code >= 500)
    )
    if is_failure:
        _HEALTH_STATE["last_error_at"] = now
        _HEALTH_STATE["consecutive_errors"] += 1
        _HEALTH_STATE["total_errors"] += 1
    else:
        _HEALTH_STATE["last_success_at"] = now
        _HEALTH_STATE["consecutive_errors"] = 0


def get_health_snapshot() -> Dict[str, Any]:
    """Return safe public health data for the status indicator."""
    now = time.time()
    last_error = _HEALTH_STATE["last_error_at"]
    consecutive = _HEALTH_STATE["consecutive_errors"]

    if consecutive >= 5:
        status = "degraded"
    elif last_error and now - last_error < 30:
        status = "degraded"
    else:
        status = "online"

    return {
        "status": status,
        "uptime_seconds": int(now - _HEALTH_STATE["started_at"]),
        "checked_at": datetime.utcnow().isoformat(),
    }


def fetch_recent_events(
    *,
    limit: int = 100,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    since_minutes: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Admin-only: pull recent events from the persistent log."""
    clauses: List[str] = []
    params: List[Any] = []
    if category:
        clauses.append("category = ?")
        params.append(category)
    if severity:
        clauses.append("severity = ?")
        params.append(severity)
    if since_minutes:
        cutoff = (datetime.utcnow() - timedelta(minutes=since_minutes)).isoformat()
        clauses.append("timestamp >= ?")
        params.append(cutoff)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(int(limit))

    conn = _connect()
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT event_id, timestamp, event_type, category, severity, user_hash,
                   session_id, source, path, status_code, duration_ms, success, details
            FROM event_logs
            {where}
            ORDER BY event_id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    return [dict(r) for r in rows]


def fetch_chatbot_failures(limit: int = 100) -> List[Dict[str, Any]]:
    """Admin-only: pull recent chatbot failures."""
    conn = _connect()
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT failure_id, timestamp, user_hash, session_id, question, answer,
                   source, confidence, failure_reason, similarity_score, duration_ms
            FROM chatbot_failures
            ORDER BY failure_id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def aggregate_metrics(window_minutes: int = 60) -> Dict[str, Any]:
    """Admin-only: aggregate counts for the dashboard."""
    cutoff = (datetime.utcnow() - timedelta(minutes=window_minutes)).isoformat()
    conn = _connect()
    try:
        conn.row_factory = sqlite3.Row
        by_category = conn.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM event_logs
            WHERE timestamp >= ?
            GROUP BY category
            ORDER BY count DESC
            """,
            (cutoff,),
        ).fetchall()
        by_severity = conn.execute(
            """
            SELECT severity, COUNT(*) AS count
            FROM event_logs
            WHERE timestamp >= ?
            GROUP BY severity
            """,
            (cutoff,),
        ).fetchall()
        slowest = conn.execute(
            """
            SELECT path, MAX(duration_ms) AS max_ms, AVG(duration_ms) AS avg_ms, COUNT(*) AS n
            FROM event_logs
            WHERE timestamp >= ? AND duration_ms IS NOT NULL
            GROUP BY path
            ORDER BY max_ms DESC
            LIMIT 10
            """,
            (cutoff,),
        ).fetchall()
        chat_total = conn.execute(
            "SELECT COUNT(*) FROM chatbot_failures WHERE timestamp >= ?",
            (cutoff,),
        ).fetchone()[0]
    finally:
        conn.close()

    return {
        "window_minutes": window_minutes,
        "by_category": [dict(r) for r in by_category],
        "by_severity": [dict(r) for r in by_severity],
        "slowest_paths": [dict(r) for r in slowest],
        "chatbot_failures": chat_total,
    }

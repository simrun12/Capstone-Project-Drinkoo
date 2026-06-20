"""
FastAPI application entrypoint for DRINKOO.

Run from the project root:
    uvicorn backend.main:app --reload

Run from the backend folder:
    uvicorn main:app --reload
"""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.analytics import router as analytics_router
from .api.auth import router as auth_router
from .api.chatbot import router as chatbot_router
from .api.observability import router as observability_router
from .api.shipments import router as shipments_router
from .api.skus import router as skus_router
from .api.states import router as states_router
from .api.upload import router as upload_router
from .config import API_PREFIX, APP_DESCRIPTION, APP_NAME, APP_VERSION
from .database.schema import initialize_database
from .utils import observability as obs

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(states_router, prefix=API_PREFIX)
app.include_router(skus_router, prefix=API_PREFIX)
app.include_router(shipments_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(upload_router, prefix=API_PREFIX)
app.include_router(chatbot_router, prefix=API_PREFIX)
app.include_router(observability_router, prefix=API_PREFIX)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Log every API request with timing and outcome."""
    start = time.perf_counter()
    status_code = 500
    error_detail = None
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:  # noqa: BLE001
        error_detail = repr(exc)[:500]
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        path = request.url.path
        # Skip noisy static assets and the status endpoint itself
        if not (path.startswith("/styles") or path.startswith("/js") or path.endswith("/status")):
            severity = "info"
            if status_code >= 500:
                severity = "error"
            elif status_code >= 400:
                severity = "warning"
            obs.log_event(
                event_type="http_request",
                category="request",
                severity=severity,
                source="backend",
                user=request.headers.get("x-user"),
                session_id=request.headers.get("x-session-id"),
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                success=200 <= status_code < 400,
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                details={"method": request.method, "error": error_detail} if error_detail else {"method": request.method},
            )


@app.on_event("startup")
def startup_initialize_database() -> None:
    """Ensure the SQLite schema exists when the API starts."""

    initialize_database()


@app.get("/health")
def health() -> dict[str, str]:
    """Return API health status."""

    return {"status": "healthy"}


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/styles", StaticFiles(directory=FRONTEND_DIR / "styles"), name="styles")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

    @app.get("/")
    def serve_login() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/dashboard")
    @app.get("/dashboard.html")
    def serve_dashboard() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "dashboard.html")

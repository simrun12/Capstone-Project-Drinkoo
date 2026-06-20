"""Shipment and tracking routes for DRINKOO."""

from __future__ import annotations

from datetime import date, datetime
import random
import string
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from .auth import require_admin
from ..database.db import get_db
from ..utils.validators import VALID_SHIPMENT_STATUS, is_valid_quantity

router = APIRouter(prefix="/shipments", tags=["shipments"])


class ShipmentCreate(BaseModel):
    """Request body for creating a DRINKOO shipment."""

    state_code: str = Field(..., min_length=2, max_length=2)
    sku_id: int
    quantity: int
    tracking_code: Optional[str] = None
    shipment_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: str = "pending"


class ShipmentStatusUpdate(BaseModel):
    """Request body for updating shipment status."""

    status: str
    delivery_date: Optional[date] = None


def generate_tracking_code() -> str:
    """Generate a unique DRINKOO shipment tracking code."""

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"DRINKOO-{timestamp}-{random_suffix}"


def _get_shipment_or_404(tracking_code: str) -> dict[str, object]:
    """Fetch a shipment by tracking code or raise a 404 error."""

    db = get_db()
    shipment = db.fetch_one(
        """
        SELECT
            shipments.*,
            skus.sku_code,
            skus.sku_name,
            skus.flavor_profile,
            states.state_name
        FROM shipments
        JOIN skus ON skus.sku_id = shipments.sku_id
        JOIN states ON states.state_code = shipments.state_code
        WHERE shipments.shipment_tracking_code = ?
        """,
        (tracking_code,),
    )

    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    return shipment


@router.get("")
def list_shipments(
    state_code: str | None = None,
    status_filter: str = Query("all", alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    """List shipments with optional state and status filters."""

    db = get_db()
    params: list[object] = []
    where_clause = "WHERE 1 = 1"

    if state_code:
        where_clause += " AND shipments.state_code = ?"
        params.append(state_code.strip().upper())

    if status_filter != "all":
        where_clause += " AND shipments.status = ?"
        params.append(status_filter)

    params.extend([limit, offset])

    shipments = db.fetch_all(
        f"""
        SELECT
            shipments.shipment_id,
            shipments.shipment_tracking_code,
            shipments.state_code,
            states.state_name,
            shipments.sku_id,
            skus.sku_code,
            skus.sku_name,
            shipments.quantity,
            shipments.shipment_date,
            shipments.expected_delivery_date,
            shipments.delivery_date,
            shipments.status,
            shipments.shipping_cost,
            shipments.created_date
        FROM shipments
        JOIN states ON states.state_code = shipments.state_code
        JOIN skus ON skus.sku_id = shipments.sku_id
        {where_clause}
        ORDER BY shipments.shipment_date DESC
        LIMIT ? OFFSET ?
        """,
        tuple(params),
    )

    return {
        "total_count": len(shipments),
        "limit": limit,
        "offset": offset,
        "shipments": shipments,
    }


@router.post("")
def create_shipment(payload: ShipmentCreate, current_user=Depends(require_admin)) -> dict[str, object]:
    """Create a new DRINKOO shipment."""

    db = get_db()
    normalized_state_code = payload.state_code.strip().upper()

    state = db.fetch_one("SELECT * FROM states WHERE state_code = ?", (normalized_state_code,))
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")

    sku = db.fetch_one("SELECT * FROM skus WHERE sku_id = ?", (payload.sku_id,))
    if sku is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    if not is_valid_quantity(payload.quantity):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quantity must be greater than zero",
        )

    if payload.status not in VALID_SHIPMENT_STATUS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Status must be one of: {', '.join(sorted(VALID_SHIPMENT_STATUS))}",
        )

    tracking_code = payload.tracking_code or generate_tracking_code()
    shipment_date = payload.shipment_date or date.today()
    shipping_cost = float(sku["shipping_cost_per_unit"]) * payload.quantity

    try:
        db.execute(
            """
            INSERT INTO shipments (
                shipment_tracking_code,
                state_code,
                sku_id,
                quantity,
                shipment_date,
                expected_delivery_date,
                status,
                shipping_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tracking_code,
                normalized_state_code,
                payload.sku_id,
                payload.quantity,
                shipment_date.isoformat(),
                payload.expected_delivery_date.isoformat() if payload.expected_delivery_date else None,
                payload.status,
                shipping_cost,
            ),
        )
        db.commit()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Shipment could not be created. Tracking code may already exist.",
        ) from exc

    return {"message": "Shipment created successfully", "shipment": _get_shipment_or_404(tracking_code)}


@router.get("/{tracking_code}")
def track_shipment(tracking_code: str) -> dict[str, object]:
    """Track a shipment by tracking code."""

    shipment = _get_shipment_or_404(tracking_code)
    return {"shipment": shipment}


@router.put("/{tracking_code}/status")
def update_shipment_status(
    tracking_code: str,
    payload: ShipmentStatusUpdate,
    current_user=Depends(require_admin),
) -> dict[str, object]:
    """Update shipment status."""

    _get_shipment_or_404(tracking_code)

    if payload.status not in VALID_SHIPMENT_STATUS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Status must be one of: {', '.join(sorted(VALID_SHIPMENT_STATUS))}",
        )

    db = get_db()
    db.execute(
        "UPDATE shipments SET status = ?, delivery_date = ? WHERE shipment_tracking_code = ?",
        (
            payload.status,
            payload.delivery_date.isoformat() if payload.delivery_date else None,
            tracking_code,
        ),
    )
    db.commit()

    return {"message": "Shipment status updated successfully", "shipment": _get_shipment_or_404(tracking_code)}


@router.get("/by-state/{state_code}")
def get_shipments_by_state(
    state_code: str,
    status_filter: str = Query("all", alias="status"),
) -> dict[str, object]:
    """Return shipments for a selected state."""

    normalized_state_code = state_code.strip().upper()
    db = get_db()

    state = db.fetch_one("SELECT * FROM states WHERE state_code = ?", (normalized_state_code,))
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")

    params: list[object] = [normalized_state_code]
    status_clause = ""

    if status_filter != "all":
        status_clause = " AND shipments.status = ?"
        params.append(status_filter)

    shipments = db.fetch_all(
        f"""
        SELECT
            shipments.shipment_id,
            shipments.shipment_tracking_code,
            shipments.state_code,
            shipments.sku_id,
            skus.sku_code,
            skus.sku_name,
            shipments.quantity,
            shipments.shipment_date,
            shipments.expected_delivery_date,
            shipments.delivery_date,
            shipments.status,
            shipments.shipping_cost
        FROM shipments
        JOIN skus ON skus.sku_id = shipments.sku_id
        WHERE shipments.state_code = ?{status_clause}
        ORDER BY shipments.shipment_date DESC
        """,
        tuple(params),
    )

    return {
        "state_code": normalized_state_code,
        "shipments": shipments,
    }

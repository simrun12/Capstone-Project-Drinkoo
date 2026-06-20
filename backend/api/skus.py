"""SKU management routes for DRINKOO."""

from __future__ import annotations

from decimal import Decimal
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from .auth import require_admin
from .common import rows_to_dicts
from ..config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..database.db import get_db
from ..utils.validators import is_valid_currency_value, is_valid_sku_size

router = APIRouter(prefix="/skus", tags=["skus"])


class SKUCreate(BaseModel):
    """Request body for creating a DRINKOO SKU."""

    sku_code: str = Field(..., min_length=3, max_length=50)
    sku_name: str = Field(..., min_length=3, max_length=100)
    flavor_profile: str = Field(..., min_length=2, max_length=80)
    drink_size_ml: int
    manufacturing_cost_per_unit: Decimal
    shipping_cost_per_unit: Decimal
    retail_price: Decimal
    sku_category: str = "soda"
    status: str = "active"


class SKUUpdate(BaseModel):
    """Request body for updating a DRINKOO SKU."""

    sku_name: str | None = None
    flavor_profile: str | None = None
    drink_size_ml: int | None = None
    manufacturing_cost_per_unit: Decimal | None = None
    shipping_cost_per_unit: Decimal | None = None
    retail_price: Decimal | None = None
    sku_category: str | None = None
    image_path: str | None = None
    status: str | None = None


def _get_sku_or_404(sku_id: int) -> dict[str, object]:
    """Fetch a SKU or raise a 404 error."""

    db = get_db()
    sku = db.fetch_one("SELECT * FROM skus WHERE sku_id = ?", (sku_id,))

    if sku is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    return sku


def _validate_sku_payload(payload: SKUCreate | SKUUpdate) -> None:
    """Validate SKU business rules before database writes."""

    if payload.drink_size_ml is not None and not is_valid_sku_size(payload.drink_size_ml):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="DRINKOO SKU sizes must be 1000ml or 1500ml only",
        )

    cost_fields = [
        "manufacturing_cost_per_unit",
        "shipping_cost_per_unit",
        "retail_price",
    ]

    for field_name in cost_fields:
        value = getattr(payload, field_name, None)
        if value is not None and not is_valid_currency_value(value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field_name} must be zero or a positive number",
            )


@router.get("")
def list_skus(
    category: str | None = None,
    status_filter: str = Query("active", alias="status"),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    """List SKUs with optional category and status filters."""

    db = get_db()
    params: list[object] = []
    where_clause = "WHERE 1 = 1"

    if category:
        where_clause += " AND sku_category = ?"
        params.append(category)

    if status_filter != "all":
        where_clause += " AND status = ?"
        params.append(status_filter)

    params.extend([limit, offset])

    skus = db.fetch_all(
        f"""
        SELECT
            sku_id,
            sku_code,
            sku_name,
            flavor_profile,
            drink_size_ml,
            manufacturing_cost_per_unit,
            shipping_cost_per_unit,
            retail_price,
            sku_category,
            image_path,
            status,
            created_date
        FROM skus
        {where_clause}
        ORDER BY sku_id
        LIMIT ? OFFSET ?
        """,
        tuple(params),
    )
    total_count = db.fetch_scalar(
        f"SELECT COUNT(*) FROM skus {where_clause}",
        tuple(params[:-2]),
    )

    return {
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "skus": skus,
    }


@router.post("")
def create_sku(payload: SKUCreate, current_user=Depends(require_admin)) -> dict[str, object]:
    """Create a new DRINKOO SKU."""

    _validate_sku_payload(payload)
    db = get_db()

    try:
        db.execute(
            """
            INSERT INTO skus (
                sku_code,
                sku_name,
                flavor_profile,
                drink_size_ml,
                manufacturing_cost_per_unit,
                shipping_cost_per_unit,
                retail_price,
                sku_category,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.sku_code,
                payload.sku_name,
                payload.flavor_profile,
                payload.drink_size_ml,
                float(payload.manufacturing_cost_per_unit),
                float(payload.shipping_cost_per_unit),
                float(payload.retail_price),
                payload.sku_category,
                payload.status,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SKU code already exists",
        ) from exc

    created_sku = db.fetch_one("SELECT * FROM skus ORDER BY sku_id DESC LIMIT 1")
    return {"message": "SKU created successfully", "sku": created_sku}


@router.get("/{sku_id}")
def get_sku(sku_id: int) -> dict[str, object]:
    """Return one SKU by ID."""

    return _get_sku_or_404(sku_id)


@router.put("/{sku_id}")
def update_sku(sku_id: int, payload: SKUUpdate, current_user=Depends(require_admin)) -> dict[str, object]:
    """Update an existing DRINKOO SKU."""

    _get_sku_or_404(sku_id)
    _validate_sku_payload(payload)

    updates: list[str] = []
    params: list[object] = []

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        if value is None:
            continue

        if field_name in {
            "manufacturing_cost_per_unit",
            "shipping_cost_per_unit",
            "retail_price",
        }:
            value = float(value)

        updates.append(f"{field_name} = ?")
        params.append(value)

    if not updates:
        return {"message": "No fields were provided for update", "sku": _get_sku_or_404(sku_id)}

    params.append(sku_id)
    db = get_db()
    db.execute(
        f"UPDATE skus SET {', '.join(updates)} WHERE sku_id = ?",
        tuple(params),
    )
    db.commit()

    return {"message": "SKU updated successfully", "sku": _get_sku_or_404(sku_id)}


@router.get("/by-state/{state_code}")
def get_skus_by_state(state_code: str) -> dict[str, object]:
    """Return active SKUs allocated to a selected state."""

    normalized_state_code = state_code.strip().upper()
    db = get_db()

    state_exists = db.fetch_scalar("SELECT COUNT(*) FROM states WHERE state_code = ?", (normalized_state_code,))
    if not state_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")

    rows = db.fetch_all(
        """
        SELECT
            sd.distribution_id,
            sd.state_code,
            sd.sku_id,
            sd.quantity_allocated,
            sd.distribution_percentage,
            s.sku_code,
            s.sku_name,
            s.flavor_profile,
            s.drink_size_ml,
            s.sku_category,
            s.status
        FROM sku_distribution sd
        JOIN skus s ON s.sku_id = sd.sku_id
        WHERE sd.state_code = ? AND s.status = 'active'
        ORDER BY sd.quantity_allocated DESC, s.sku_name
        """,
        (normalized_state_code,),
    )

    return {
        "state_code": normalized_state_code,
        "skus": rows,
    }

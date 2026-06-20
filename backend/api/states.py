"""State, customer, and SKU distribution routes for DRINKOO."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from .common import rows_to_dicts
from ..config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..database.db import get_db

router = APIRouter(prefix="/states", tags=["states"])


def _get_state_or_404(state_code: str) -> dict[str, object]:
    """Fetch a state record or raise a 404 error."""

    db = get_db()
    state = db.fetch_one("SELECT * FROM states WHERE state_code = ?", (state_code,))

    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")

    return state


@router.get("")
def list_states() -> list[dict[str, object]]:
    """List all Indian states and union territories covered by DRINKOO."""

    db = get_db()
    states = db.fetch_all(
        """
        SELECT
            state_code,
            state_name,
            capital_city,
            population_category,
            expected_customer_count
        FROM states
        ORDER BY state_name
        """
    )
    return states


@router.get("/{state_code}/data")
def get_state_data(state_code: str) -> dict[str, object]:
    """Return state-wide DRINKOO summary data."""

    normalized_state_code = state_code.strip().upper()
    state = _get_state_or_404(normalized_state_code)
    db = get_db()

    customer_count = db.fetch_scalar(
        "SELECT COUNT(*) FROM customers WHERE state_code = ?",
        (normalized_state_code,),
    )
    available_sku_count = db.fetch_scalar(
        """
        SELECT COUNT(DISTINCT sd.sku_id)
        FROM sku_distribution sd
        JOIN skus s ON s.sku_id = sd.sku_id
        WHERE sd.state_code = ? AND s.status = 'active'
        """,
        (normalized_state_code,),
    )
    pending_shipments = db.fetch_scalar(
        "SELECT COUNT(*) FROM shipments WHERE state_code = ? AND status = 'pending'",
        (normalized_state_code,),
    )
    total_revenue = db.fetch_scalar(
        "SELECT COALESCE(SUM(revenue), 0) FROM sales WHERE state_code = ?",
        (normalized_state_code,),
    )

    return {
        "state": state,
        "metrics": {
            "customer_count": customer_count,
            "available_sku_count": available_sku_count,
            "pending_shipments": pending_shipments,
            "total_revenue": total_revenue,
        },
    }


@router.get("/{state_code}/customers")
def get_state_customers(
    state_code: str,
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    """Return customers in a selected state."""

    normalized_state_code = state_code.strip().upper()
    _get_state_or_404(normalized_state_code)
    db = get_db()

    customers = db.fetch_all(
        """
        SELECT
            customer_id,
            external_id,
            customer_name,
            city_name,
            district_name,
            customer_segment,
            customer_tier,
            registration_date
        FROM customers
        WHERE state_code = ?
        ORDER BY customer_id
        LIMIT ? OFFSET ?
        """,
        (normalized_state_code, limit, offset),
    )
    total_count = db.fetch_scalar(
        "SELECT COUNT(*) FROM customers WHERE state_code = ?",
        (normalized_state_code,),
    )

    return {
        "state_code": normalized_state_code,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "customers": customers,
    }


@router.get("/{state_code}/sku-distribution")
def get_state_sku_distribution(state_code: str) -> dict[str, object]:
    """Return SKU distribution for a selected state."""

    normalized_state_code = state_code.strip().upper()
    _get_state_or_404(normalized_state_code)
    db = get_db()

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
        WHERE sd.state_code = ?
        ORDER BY sd.quantity_allocated DESC, s.sku_name
        """,
        (normalized_state_code,),
    )

    return {
        "state_code": normalized_state_code,
        "sku_distribution": rows,
    }


@router.get("/{state_code}/shipments")
def get_state_shipments(
    state_code: str,
    status_filter: str = Query("all", alias="status"),
) -> dict[str, object]:
    """Return shipments for a selected state."""

    normalized_state_code = state_code.strip().upper()
    _get_state_or_404(normalized_state_code)
    db = get_db()

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

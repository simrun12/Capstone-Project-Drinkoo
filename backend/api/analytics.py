"""Analytics routes for DRINKOO."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from ..config import MAX_PAGE_SIZE
from ..database.db import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def get_dashboard_metrics() -> dict[str, object]:
    """Return high-level DRINKOO platform metrics for the dashboard."""

    db = get_db()

    return {
        "total_customers": db.fetch_scalar("SELECT COUNT(*) FROM customers"),
        "total_active_skus": db.fetch_scalar("SELECT COUNT(*) FROM skus WHERE status = 'active'"),
        "total_pending_shipments": db.fetch_scalar("SELECT COUNT(*) FROM shipments WHERE status = 'pending'"),
        "total_shipments": db.fetch_scalar("SELECT COUNT(*) FROM shipments"),
        "total_sales_revenue": db.fetch_scalar("SELECT COALESCE(SUM(revenue), 0) FROM sales"),
        "total_states_covered": db.fetch_scalar("SELECT COUNT(*) FROM states"),
    }


@router.get("/sales-by-state")
def get_sales_by_state() -> list[dict[str, object]]:
    """Return sales revenue grouped by state."""

    db = get_db()
    return db.fetch_all(
        """
        SELECT
            states.state_code,
            states.state_name,
            states.capital_city,
            COALESCE(SUM(sales.revenue), 0) AS total_revenue,
            COALESCE(SUM(sales.quantity_sold), 0) AS total_units_sold
        FROM states
        LEFT JOIN sales ON sales.state_code = states.state_code
        GROUP BY states.state_code, states.state_name, states.capital_city
        ORDER BY total_revenue DESC
        """
    )


@router.get("/top-skus")
def get_top_skus(limit: int = Query(10, ge=1, le=MAX_PAGE_SIZE)) -> list[dict[str, object]]:
    """Return top-performing SKUs by units sold and revenue."""

    db = get_db()
    return db.fetch_all(
        """
        SELECT
            skus.sku_id,
            skus.sku_code,
            skus.sku_name,
            skus.flavor_profile,
            skus.drink_size_ml,
            skus.sku_category,
            COALESCE(SUM(sales.quantity_sold), 0) AS total_units_sold,
            COALESCE(SUM(sales.revenue), 0) AS total_revenue
        FROM skus
        LEFT JOIN sales ON sales.sku_id = skus.sku_id
        GROUP BY
            skus.sku_id,
            skus.sku_code,
            skus.sku_name,
            skus.flavor_profile,
            skus.drink_size_ml,
            skus.sku_category
        ORDER BY total_units_sold DESC, total_revenue DESC
        LIMIT ?
        """,
        (limit,),
    )


@router.get("/sales-by-sku/{sku_id}")
def get_sales_by_sku(sku_id: int) -> dict[str, object]:
    """Return sales performance for a selected SKU."""

    db = get_db()
    sku = db.fetch_one("SELECT * FROM skus WHERE sku_id = ?", (sku_id,))

    if sku is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    performance = db.fetch_one(
        """
        SELECT
            COALESCE(SUM(quantity_sold), 0) AS total_units_sold,
            COALESCE(SUM(revenue), 0) AS total_revenue,
            COUNT(*) AS sales_transaction_count
        FROM sales
        WHERE sku_id = ?
        """,
        (sku_id,),
    )

    return {
        "sku": sku,
        "performance": performance,
    }

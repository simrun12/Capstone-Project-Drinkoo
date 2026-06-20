"""
Seed DRINKOO database with dummy data.

This script:
1. Initializes the SQLite schema.
2. Inserts 36 Indian regions.
3. Inserts 1,000 dummy customers.
4. Inserts 50 beverage SKUs.
5. Inserts statistically relevant SKU distribution records.
6. Inserts a default admin user for development.

Run from the backend folder:
    python scripts/seed_database.py

Or run from the project root:
    python backend/scripts/seed_database.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

# Allow imports when running from project root or backend folder.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.schema import initialize_database
from utils.dummy_data import generate_customers, generate_regions, generate_sku_distribution, generate_skus


def _insert_or_ignore(db: sqlite3.Connection, table_name: str, columns: list[str], rows: list[tuple]) -> None:
    """Insert rows while safely ignoring duplicate records."""

    placeholders = ", ".join(["?"] * len(columns))
    column_names = ", ".join(columns)
    sql = f"INSERT OR IGNORE INTO {table_name} ({column_names}) VALUES ({placeholders})"
    db.executemany(sql, rows)


def seed_database(db_path: str | None = None) -> None:
    """Populate the DRINKOO database with reusable dummy data."""

    db = initialize_database(db_path) if db_path else initialize_database()
    connection = db.connection

    if connection is None:
        raise RuntimeError("Database connection was not initialized.")

    # Insert regions first because customers and shipments reference state_code.
    region_rows = generate_regions()
    _insert_or_ignore(
        connection,
        "states",
        ["state_code", "state_name", "capital_city", "population_category", "expected_customer_count"],
        region_rows,
    )

    customer_rows = generate_customers(total_customers=1000, seed=42)
    _insert_or_ignore(
        connection,
        "customers",
        [
            "external_id",
            "customer_name",
            "state_code",
            "state_name",
            "city_name",
            "district_name",
            "customer_email",
            "customer_phone",
            "region_size",
            "customer_segment",
            "customer_tier",
            "registration_date",
        ],
        customer_rows,
    )

    sku_rows = generate_skus(total_skus=50, seed=42)
    _insert_or_ignore(
        connection,
        "skus",
        [
            "sku_code",
            "sku_name",
            "flavor_profile",
            "drink_size_ml",
            "manufacturing_cost_per_unit",
            "shipping_cost_per_unit",
            "retail_price",
            "sku_category",
            "status",
        ],
        sku_rows,
    )

    # Distribution records need numeric SKU ids after insertion.
    sku_ids = [row[0] for row in connection.execute("SELECT sku_id FROM skus ORDER BY sku_id").fetchall()]
    distribution_rows = generate_sku_distribution(sku_ids, seed=42)
    _insert_or_ignore(
        connection,
        "sku_distribution",
        ["state_code", "sku_id", "quantity_allocated", "distribution_percentage"],
        distribution_rows,
    )

    # Development-only default admin user.
    _insert_or_ignore(
        connection,
        "users",
        ["username", "password_hash", "role", "is_active"],
        [("admin", "password", "admin", 1)],
    )

    connection.commit()

    print("DRINKOO dummy data seeded successfully.")
    print(f"Regions: {len(region_rows)}")
    print(f"Customers: {len(customer_rows)}")
    print(f"SKUs: {len(sku_rows)}")
    print(f"Distribution records: {len(distribution_rows)}")


if __name__ == "__main__":
    seed_database()

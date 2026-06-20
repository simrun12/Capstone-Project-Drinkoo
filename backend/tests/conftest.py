"""
Conftest for DRINKOO pytest fixtures.
Provides common fixtures for testing.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_db_path():
    """Create a temporary test database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def test_db_connection(test_db_path):
    """Create a connection to test database."""
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    yield conn
    conn.close()


@pytest.fixture
def initialized_test_db(test_db_connection):
    """Initialize test database with schema."""
    from backend.database.schema import init_states, init_customers, init_skus, init_users
    
    # Create tables
    init_states(test_db_connection)
    init_customers(test_db_connection)
    init_skus(test_db_connection)
    init_users(test_db_connection)
    
    test_db_connection.commit()
    yield test_db_connection


@pytest.fixture
def test_auth_token():
    """Provide test authentication token."""
    return "dev-token-admin"


@pytest.fixture
def sample_sku_data():
    """Sample SKU data for testing."""
    return {
        "sku_code": "TEST-SKU-001",
        "sku_name": "Test Cola",
        "category": "Soda",
        "size_ml": 1000,
        "unit_price": 50.0,
        "quantity_in_stock": 1000
    }


@pytest.fixture
def sample_shipment_data():
    """Sample shipment data for testing."""
    return {
        "state_code": "MH",
        "sku_id": 1,
        "quantity": 100,
        "shipping_cost": 500.0
    }

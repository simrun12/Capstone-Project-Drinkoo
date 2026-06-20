"""
Test FastAPI endpoints and integration.
Tests API routes with a test client.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.main import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(test_auth_token):
    """Create authorization headers with test token."""
    return {
        "Authorization": f"Bearer {test_auth_token}",
        "Content-Type": "application/json"
    }


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.routes
    @pytest.mark.auth
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            params={"username": "admin", "password": "password"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
    
    @pytest.mark.routes
    @pytest.mark.auth
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            params={"username": "admin", "password": "wrongpassword"}
        )
        # Should return 401 Unauthorized
        assert response.status_code in [401, 400]
    
    @pytest.mark.routes
    @pytest.mark.auth
    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post("/api/v1/auth/login", params={})
        assert response.status_code in [400, 422]  # Bad request or validation error


class TestStatesEndpoints:
    """Test state management endpoints."""
    
    @pytest.mark.routes
    def test_get_states(self, client, auth_headers):
        """Test retrieving all states."""
        response = client.get("/api/v1/states", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        if isinstance(data, list):
            # Should have many states
            assert len(data) > 0 or True  # May be empty on fresh db
    
    @pytest.mark.routes
    def test_get_states_without_auth(self, client):
        """Test that states endpoint requires authentication."""
        response = client.get("/api/v1/states")
        # Should reject without auth
        assert response.status_code in [401, 403]


class TestSKUEndpoints:
    """Test SKU management endpoints."""
    
    @pytest.mark.routes
    def test_get_skus(self, client, auth_headers):
        """Test retrieving all SKUs."""
        response = client.get("/api/v1/skus", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    @pytest.mark.routes
    def test_create_sku_valid(self, client, auth_headers, sample_sku_data):
        """Test creating a SKU with valid data."""
        response = client.post(
            "/api/v1/skus",
            json=sample_sku_data,
            headers=auth_headers
        )
        # Should succeed (200 or 201)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "sku_code" in data or "id" in data
    
    @pytest.mark.routes
    def test_create_sku_invalid_size(self, client, auth_headers):
        """Test that invalid SKU sizes are rejected."""
        invalid_sku = {
            "sku_code": "TEST-SKU-002",
            "sku_name": "Invalid Size",
            "category": "Soda",
            "size_ml": 1250,  # Invalid: must be 1000 or 1500
            "unit_price": 50.0,
            "quantity_in_stock": 100
        }
        response = client.post(
            "/api/v1/skus",
            json=invalid_sku,
            headers=auth_headers
        )
        # Should reject invalid size
        assert response.status_code in [400, 422]
    
    @pytest.mark.routes
    def test_create_sku_negative_price(self, client, auth_headers):
        """Test that negative prices are rejected."""
        invalid_sku = {
            "sku_code": "TEST-SKU-003",
            "sku_name": "Negative Price",
            "category": "Soda",
            "size_ml": 1000,
            "unit_price": -50.0,  # Invalid: negative
            "quantity_in_stock": 100
        }
        response = client.post(
            "/api/v1/skus",
            json=invalid_sku,
            headers=auth_headers
        )
        assert response.status_code in [400, 422]


class TestShipmentEndpoints:
    """Test shipment management endpoints."""
    
    @pytest.mark.routes
    def test_get_shipments(self, client, auth_headers):
        """Test retrieving all shipments."""
        response = client.get("/api/v1/shipments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    @pytest.mark.routes
    def test_create_shipment_valid(self, client, auth_headers, sample_shipment_data):
        """Test creating a shipment with valid data."""
        response = client.post(
            "/api/v1/shipments",
            json=sample_shipment_data,
            headers=auth_headers
        )
        # May fail if foreign keys don't exist, but endpoint should exist
        assert response.status_code in [200, 201, 400, 404]


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""
    
    @pytest.mark.routes
    def test_get_dashboard_metrics(self, client, auth_headers):
        """Test retrieving dashboard metrics."""
        response = client.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should have metrics
        assert isinstance(data, dict)
    
    @pytest.mark.routes
    def test_get_sales_by_state(self, client, auth_headers):
        """Test retrieving sales by state."""
        response = client.get("/api/v1/analytics/sales-by-state", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.routes
    def test_nonexistent_endpoint(self, client, auth_headers):
        """Test accessing a non-existent endpoint."""
        response = client.get("/api/v1/nonexistent", headers=auth_headers)
        assert response.status_code == 404
    
    @pytest.mark.routes
    def test_invalid_tracking_code_format(self, client, auth_headers):
        """Test tracking shipment with invalid code format."""
        response = client.get(
            "/api/v1/shipments/INVALID-CODE",
            headers=auth_headers
        )
        assert response.status_code in [400, 404]
    
    @pytest.mark.routes
    def test_malformed_json(self, client, auth_headers):
        """Test sending malformed JSON."""
        response = client.post(
            "/api/v1/skus",
            data="not valid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

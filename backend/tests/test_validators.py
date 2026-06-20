"""
Test validators for DRINKOO business rules.
Tests input validation and DRINKOO-specific constraints.
"""

import pytest
from backend.utils.validators import (
    is_valid_sku_size,
    is_valid_currency_value,
    is_valid_quantity,
    is_valid_tracking_code,
    VALID_SKU_SIZE_ML,
    VALID_SHIPMENT_STATUS
)


class TestSkuSizeValidator:
    """Test SKU size validation (must be 1000ml or 1500ml)."""
    
    @pytest.mark.validators
    def test_valid_sku_sizes(self):
        """Test that valid SKU sizes (1000, 1500) return True."""
        assert is_valid_sku_size(1000) is True
        assert is_valid_sku_size(1500) is True
    
    @pytest.mark.validators
    def test_invalid_sku_sizes(self):
        """Test that invalid SKU sizes return False."""
        assert is_valid_sku_size(500) is False
        assert is_valid_sku_size(1250) is False  # Not allowed (was mentioned as invalid)
        assert is_valid_sku_size(2000) is False
        assert is_valid_sku_size(0) is False
        assert is_valid_sku_size(-1000) is False
    
    @pytest.mark.validators
    def test_sku_size_edge_cases(self):
        """Test edge cases for SKU size validation."""
        assert is_valid_sku_size(None) is False
        assert is_valid_sku_size("1000") is False  # Must be numeric
        assert is_valid_sku_size(1000.5) is False  # Must be integer


class TestCurrencyValidator:
    """Test currency value validation."""
    
    @pytest.mark.validators
    def test_valid_currency_values(self):
        """Test that valid currency values return True."""
        assert is_valid_currency_value(50.0) is True
        assert is_valid_currency_value(0.0) is True
        assert is_valid_currency_value(1000) is True
        assert is_valid_currency_value(0.01) is True
        # Strings can be converted to Decimal
        assert is_valid_currency_value("50.0") is True
        assert is_valid_currency_value("1000") is True
    
    @pytest.mark.validators
    def test_invalid_currency_values(self):
        """Test that invalid currency values return False."""
        assert is_valid_currency_value(-50.0) is False
        assert is_valid_currency_value(-0.01) is False
    
    @pytest.mark.validators
    def test_currency_edge_cases(self):
        """Test edge cases for currency validation."""
        assert is_valid_currency_value(None) is False
        # Invalid strings
        assert is_valid_currency_value("not a number") is False


class TestQuantityValidator:
    """Test quantity validation."""
    
    @pytest.mark.validators
    def test_valid_quantities(self):
        """Test that valid quantities return True."""
        assert is_valid_quantity(1) is True
        assert is_valid_quantity(100) is True
        assert is_valid_quantity(10000) is True
    
    @pytest.mark.validators
    def test_invalid_quantities(self):
        """Test that invalid quantities return False."""
        assert is_valid_quantity(0) is False  # Must be > 0
        assert is_valid_quantity(-1) is False
        assert is_valid_quantity(-100) is False
    
    @pytest.mark.validators
    def test_quantity_edge_cases(self):
        """Test edge cases for quantity validation."""
        assert is_valid_quantity(None) is False
        assert is_valid_quantity("100") is False
        assert is_valid_quantity(100.5) is False


class TestTrackingCodeValidator:
    """Test tracking code format validation."""
    
    @pytest.mark.validators
    def test_valid_tracking_codes(self):
        """Test that valid tracking codes return True."""
        # Format: DRINKOO- followed by at least 8 alphanumeric/dash chars
        valid_codes = [
            "DRINKOO-20260615120000-ABC123",
            "DRINKOO-20260101000000-XYZ999",
            "DRINKOO-20261231235959-AAA000",
            "DRINKOO-ABC123456",      # 8 chars exactly
            "DRINKOO-2026061512",     # 10 digits (valid per regex)
        ]
        for code in valid_codes:
            assert is_valid_tracking_code(code) is True, f"Code should be valid: {code}"
    
    @pytest.mark.validators
    def test_invalid_tracking_codes(self):
        """Test that invalid tracking codes return False."""
        invalid_codes = [
            "INVALID-20260615120000-ABC123",  # Wrong prefix
            "DRINKOO-2026",                   # Too short (less than 8 chars)
            "DRINKOO-AB",                     # Too short
            "drinkoo-20260615120000-ABC123",  # Lowercase prefix
        ]
        for code in invalid_codes:
            assert is_valid_tracking_code(code) is False, f"Code should be invalid: {code}"
    
    @pytest.mark.validators
    def test_tracking_code_edge_cases(self):
        """Test edge cases for tracking code validation."""
        # None and int should cause TypeError in current implementation
        try:
            result = is_valid_tracking_code(None)
            assert result is False
        except TypeError:
            pass
        
        try:
            result = is_valid_tracking_code(123)
            assert result is False
        except TypeError:
            pass


class TestValidatorConstants:
    """Test validator configuration constants."""
    
    @pytest.mark.validators
    def test_valid_sku_sizes_constant(self):
        """Test VALID_SKU_SIZE_ML constant."""
        assert 1000 in VALID_SKU_SIZE_ML
        assert 1500 in VALID_SKU_SIZE_ML
        assert len(VALID_SKU_SIZE_ML) == 2
    
    @pytest.mark.validators
    def test_valid_shipment_status_constant(self):
        """Test VALID_SHIPMENT_STATUS constant."""
        expected_statuses = {"pending", "in_transit", "delivered", "failed"}
        assert VALID_SHIPMENT_STATUS == expected_statuses

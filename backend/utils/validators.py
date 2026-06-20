"""Input validators for DRINKOO API requests."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional, Tuple

VALID_SKU_SIZE_ML = {1000, 1500}
VALID_SHIPMENT_STATUS = {"pending", "in_transit", "delivered", "failed"}


def is_valid_sku_size(drink_size_ml: int) -> bool:
    """Validate DRINKOO SKU size values."""

    return drink_size_ml in VALID_SKU_SIZE_ML


def is_valid_currency_value(value: Decimal | int | float | str) -> bool:
    """Validate cost and price values."""

    try:
        numeric_value = Decimal(str(value))
    except Exception:
        return False

    return numeric_value >= 0


def is_valid_quantity(quantity: int) -> bool:
    """Validate shipment and SKU quantity values."""

    return isinstance(quantity, int) and quantity > 0


def is_valid_tracking_code(tracking_code: str) -> bool:
    """Validate shipment tracking code format."""

    return bool(re.match(r"^DRINKOO-[A-Z0-9-]{8,}$", tracking_code))


def normalize_state_code(state_code: str) -> str:
    """Normalize state code input."""

    return state_code.strip().upper()


def parse_positive_integer(value: str | int, field_name: str) -> int:
    """Parse and validate a positive integer request parameter."""

    try:
        parsed_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer") from exc

    if parsed_value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")

    return parsed_value


def parse_decimal(value: str | int | float, field_name: str) -> Decimal:
    """Parse and validate a non-negative decimal value."""

    try:
        decimal_value = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{field_name} must be a valid number") from exc

    if decimal_value < 0:
        raise ValueError(f"{field_name} cannot be negative")

    return decimal_value

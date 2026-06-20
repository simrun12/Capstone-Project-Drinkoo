"""
Dummy data generation utilities for DRINKOO.

This module creates statistically relevant sample customers, SKUs, and SKU
distribution records for DRINKOO's beverage management platform.

Key assumptions:
- Customers are spread across all 28 Indian states and 8 union territories.
- Customer counts are based on population category, so larger states receive
  more customers.
- SKU sizes are limited to 1L and 1.5L to match beverage packaging standards.
- The first 10 SKUs are soda flavors. The remaining 40 cover other beverage
  categories.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Iterable, List, Tuple

# ---------------------------------------------------------------------------
# Indian states and union territories
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IndianRegion:
    """A state or union territory with a representative capital city."""

    state_code: str
    state_name: str
    capital_city: str
    population_category: str


INDIAN_REGIONS: Tuple[IndianRegion, ...] = (
    IndianRegion("AP", "Andhra Pradesh", "Amaravati", "large"),
    IndianRegion("AR", "Arunachal Pradesh", "Itanagar", "small"),
    IndianRegion("AS", "Assam", "Dispur", "medium"),
    IndianRegion("BR", "Bihar", "Patna", "large"),
    IndianRegion("CT", "Chhattisgarh", "Raipur", "medium"),
    IndianRegion("GA", "Goa", "Panaji", "small"),
    IndianRegion("GJ", "Gujarat", "Gandhinagar", "large"),
    IndianRegion("HR", "Haryana", "Chandigarh", "medium"),
    IndianRegion("HP", "Himachal Pradesh", "Shimla", "small"),
    IndianRegion("JH", "Jharkhand", "Ranchi", "medium"),
    IndianRegion("KA", "Karnataka", "Bengaluru", "large"),
    IndianRegion("KL", "Kerala", "Thiruvananthapuram", "large"),
    IndianRegion("MP", "Madhya Pradesh", "Bhopal", "large"),
    IndianRegion("MH", "Maharashtra", "Mumbai", "large"),
    IndianRegion("MN", "Manipur", "Imphal", "small"),
    IndianRegion("ML", "Meghalaya", "Shillong", "small"),
    IndianRegion("MZ", "Mizoram", "Aizawl", "small"),
    IndianRegion("NL", "Nagaland", "Kohima", "small"),
    IndianRegion("OR", "Odisha", "Bhubaneswar", "medium"),
    IndianRegion("PB", "Punjab", "Chandigarh", "medium"),
    IndianRegion("RJ", "Rajasthan", "Jaipur", "large"),
    IndianRegion("SK", "Sikkim", "Gangtok", "small"),
    IndianRegion("TN", "Tamil Nadu", "Chennai", "large"),
    IndianRegion("TG", "Telangana", "Hyderabad", "large"),
    IndianRegion("TR", "Tripura", "Agartala", "small"),
    IndianRegion("UP", "Uttar Pradesh", "Lucknow", "large"),
    IndianRegion("UT", "Uttarakhand", "Dehradun", "small"),
    IndianRegion("WB", "West Bengal", "Kolkata", "large"),
    IndianRegion("AN", "Andaman and Nicobar Islands", "Port Blair", "small"),
    IndianRegion("CH", "Chandigarh", "Chandigarh", "small"),
    IndianRegion("DN", "Dadra and Nagar Haveli and Daman and Diu", "Daman", "small"),
    IndianRegion("DL", "Delhi", "New Delhi", "large"),
    IndianRegion("JK", "Jammu and Kashmir", "Srinagar", "small"),
    IndianRegion("LA", "Ladakh", "Leh", "small"),
    IndianRegion("LD", "Lakshadweep", "Kavaratti", "small"),
    IndianRegion("PY", "Puducherry", "Puducherry", "small"),
)

REGION_COUNTS: Dict[str, int] = {
    "small": 10,
    "medium": 34,
    "large": 68,
}

CATEGORY_WEIGHTS: Dict[str, int] = {
    "soda": 10,
    "juice": 10,
    "energy_drink": 8,
    "water": 8,
    "iced_tea": 5,
    "coconut_water": 4,
    "sparkling_water": 3,
    "sports_drink": 2,
}

SODA_FLAVORS: Tuple[str, ...] = (
    "Cola",
    "Orange",
    "Lemon Lime",
    "Mango",
    "Strawberry",
    "Apple",
    "Grape",
    "Blueberry",
    "Guava",
    "Ginger Lime",
)

OTHER_FLAVORS: Tuple[str, ...] = (
    "Orange Juice",
    "Apple Juice",
    "Mango Nectar",
    "Mixed Fruit Juice",
    "Pomegranate Juice",
    "Pineapple Juice",
    "Lemon Tea",
    "Peach Iced Tea",
    "Coconut Water",
    "Plain Water",
    "Sparkling Lemon",
    "Sparkling Orange",
    "Sports Berry",
    "Sports Citrus",
    "Energy Berry",
    "Energy Tropical",
    "Energy Citrus",
    "Energy Mango",
    "Energy Cola",
    "Energy Orange",
    "Ginger Ale",
    "Tonic Water",
    "Grape Soda",
    "Green Apple Soda",
    "Lychee Soda",
    "Watermelon Soda",
    "Pineapple Soda",
    "Peach Soda",
    "Vanilla Cream Soda",
    "Blackcurrant Soda",
    "Passion Fruit Soda",
    "Dragon Fruit Soda",
    "Kiwi Soda",
    "Cranberry Soda",
    "Raspberry Soda",
    "Mint Lime Soda",
    "Tamarind Soda",
    "Jamun Soda",
    "Rose Lemonade",
    "Masala Soda",
)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _weighted_random_choice(items: Iterable[str], weights: Dict[str, int]) -> str:
    """Return a random item using category weights."""

    values = list(items)
    weight_values = [weights[item] for item in values]
    return random.choices(values, weights=weight_values, k=1)[0]


def _calculate_customer_counts(total_customers: int = 1000) -> Dict[str, int]:
    """Distribute customers across regions based on population category."""

    total_weight = sum(REGION_COUNTS[region.population_category] for region in INDIAN_REGIONS)
    raw_counts = {
        region.state_code: (total_customers * REGION_COUNTS[region.population_category]) / total_weight
        for region in INDIAN_REGIONS
    }

    customer_counts: Dict[str, int] = {region.state_code: max(1, int(raw_counts[region.state_code])) for region in INDIAN_REGIONS}

    while sum(customer_counts.values()) < total_customers:
        largest_region = max(INDIAN_REGIONS, key=lambda region: raw_counts[region.state_code] - customer_counts[region.state_code])
        customer_counts[largest_region.state_code] += 1

    while sum(customer_counts.values()) > total_customers:
        smallest_region = min(
            (region for region in INDIAN_REGIONS if customer_counts[region.state_code] > 1),
            key=lambda region: raw_counts[region.state_code] - customer_counts[region.state_code],
        )
        customer_counts[smallest_region.state_code] -= 1

    return customer_counts


def _normalize_customer_counts(customer_counts: Dict[str, int], total_customers: int) -> Dict[str, int]:
    """Adjust rounding errors to match the exact customer total."""

    normalized_counts = dict(customer_counts)
    difference = total_customers - sum(normalized_counts.values())

    if difference > 0:
        for region in sorted(INDIAN_REGIONS, key=lambda item: REGION_COUNTS[item.population_category], reverse=True):
            while difference > 0:
                normalized_counts[region.state_code] += 1
                difference -= 1
                if normalized_counts[region.state_code] >= REGION_COUNTS[region.population_category]:
                    break

    elif difference < 0:
        for region in sorted(INDIAN_REGIONS, key=lambda item: REGION_COUNTS[item.population_category]):
            while difference < 0 and normalized_counts[region.state_code] > 1:
                normalized_counts[region.state_code] -= 1
                difference += 1

    return normalized_counts


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------

def generate_regions() -> List[Tuple[str, str, str, str, int]]:
    """Create state/UT master records for insertion."""

    customer_counts = _calculate_customer_counts()
    return [
        (
            region.state_code,
            region.state_name,
            region.capital_city,
            region.population_category,
            customer_counts[region.state_code],
        )
        for region in INDIAN_REGIONS
    ]


def generate_customers(total_customers: int = 1000, seed: int | None = 42) -> List[Tuple[str, str, str, str, str, str, str, str, str, str, str]]:
    """Generate 1,000 dummy customers across all Indian states and union territories."""

    if seed is not None:
        random.seed(seed)

    customer_counts = _normalize_customer_counts(_calculate_customer_counts(total_customers), total_customers)
    first_names = (
        "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
        "Meera", "Ananya", "Diya", "Saanvi", "Aadhya", "Myra", "Kiara", "Navya", "Riya", "Pari",
        "Rohan", "Karan", "Rahul", "Amit", "Nikhil", "Siddharth", "Arjun", "Vikram", "Aditya", "Raj",
        "Priya", "Sneha", "Pooja", "Anjali", "Neha", "Kavita", "Ritu", "Preeti", "Simran", "Nisha",
    )
    last_names = (
        "Sharma", "Verma", "Patel", "Singh", "Kumar", "Reddy", "Nair", "Das", "Gupta", "Joshi",
        "Mehta", "Chopra", "Malhotra", "Rao", "Khan", "Ali", "Chatterjee", "Bose", "Desai", "Pillai",
        "Yadav", "Mishra", "Jain", "Kulkarni", "Menon", "Iyer", "Rathore", "Bhatia", "Kapoor", "Dutta",
    )

    customers: List[Tuple[str, str, str, str, str, str, str, str, str, str, str]] = []
    customer_number = 1

    for region in INDIAN_REGIONS:
        region_customer_count = customer_counts[region.state_code]

        for index in range(region_customer_count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            customer_name = f"{first_name} {last_name}"
            customer_email = f"customer{customer_number:04d}@drinkoo.example"
            customer_phone = f"+91{random.randint(6000000000, 9999999999)}"
            region_size = region.population_category
            customer_segment = random.choices(
                ["distributor", "retailer", "individual"],
                weights=[1, 3, 6],
                k=1,
            )[0]
            customer_tier = random.choices(
                ["standard", "silver", "gold", "platinum"],
                weights=[6, 2, 1.5, 0.5],
                k=1,
            )[0]
            registration_date = date.today() - timedelta(days=random.randint(0, 730))

            customers.append(
                (
                    f"CUST{customer_number:04d}",
                    customer_name,
                    region.state_code,
                    region.state_name,
                    region.capital_city,
                    region.capital_city,
                    customer_email,
                    customer_phone,
                    region_size,
                    customer_segment,
                    customer_tier,
                    registration_date.isoformat(),
                )
            )
            customer_number += 1

    random.shuffle(customers)
    return customers


def generate_skus(total_skus: int = 50, seed: int | None = 42) -> List[Tuple[str, str, str, int, float, float, float, str, str]]:
    """Generate 50 beverage SKUs with clear metadata."""

    if seed is not None:
        random.seed(seed)

    skus: List[Tuple[str, str, str, int, float, float, float, str, str]] = []

    for index, flavor in enumerate(SODA_FLAVORS, start=1):
        sku_code = f"SKU-SODA-{index:03d}"
        sku_name = f"DRINKOO Soda {flavor}"
        drink_size_ml = random.choice([1000, 1500])
        manufacturing_cost = round(random.uniform(18.0, 42.0), 2)
        shipping_cost = round(random.uniform(5.0, 12.0), 2)
        retail_price = round(manufacturing_cost + shipping_cost + random.uniform(20.0, 35.0), 2)
        status = "active"
        skus.append((sku_code, sku_name, flavor, drink_size_ml, manufacturing_cost, shipping_cost, retail_price, "soda", status))

    for index, flavor in enumerate(OTHER_FLAVORS, start=11):
        category = _weighted_random_choice(
            [
                "juice",
                "energy_drink",
                "water",
                "iced_tea",
                "coconut_water",
                "sparkling_water",
                "sports_drink",
            ],
            CATEGORY_WEIGHTS,
        )
        sku_code = f"SKU-{category.upper()[:4]}-{index:03d}"
        sku_name = f"DRINKOO {category.replace('_', ' ').title()} {flavor}"
        drink_size_ml = random.choice([1000, 1500])
        manufacturing_cost = round(random.uniform(16.0, 55.0), 2)
        shipping_cost = round(random.uniform(4.0, 15.0), 2)
        retail_price = round(manufacturing_cost + shipping_cost + random.uniform(22.0, 45.0), 2)
        status = "active"
        skus.append((sku_code, sku_name, flavor, drink_size_ml, manufacturing_cost, shipping_cost, retail_price, category, status))

    return skus


def generate_sku_distribution(
    skus: List[int | Tuple[str, str, str, int, float, float, float, str, str]],
    seed: int | None = 42,
) -> List[Tuple[str, int, int, float]]:
    """Create statistically relevant SKU distribution by state."""

    if seed is not None:
        random.seed(seed)

    customer_counts = _calculate_customer_counts()
    distribution_records: List[Tuple[str, int, int, float]] = []

    for region in INDIAN_REGIONS:
        customer_count = customer_counts[region.state_code]
        population_category = region.population_category

        if population_category == "large":
            sku_pool_size = 40
        elif population_category == "medium":
            sku_pool_size = 28
        else:
            sku_pool_size = 18

        selected_skus = random.sample(skus, sku_pool_size)
        selected_sku_ids: List[int] = []

        for sku in selected_skus:
            if isinstance(sku, int):
                selected_sku_ids.append(sku)
            else:
                selected_sku_ids.append(int(sku[0].split("-")[-1]))

        allocated_quantities = [
            max(1, int(customer_count * random.uniform(1.2, 3.8)))
            for _ in selected_sku_ids
        ]
        total_allocated_quantity = sum(allocated_quantities)

        for sku_id, quantity_allocated in zip(selected_sku_ids, allocated_quantities):
            distribution_percentage = round(
                (quantity_allocated / max(1, total_allocated_quantity)) * 100,
                2,
            )
            distribution_records.append(
                (region.state_code, sku_id, quantity_allocated, distribution_percentage)
            )

    return distribution_records

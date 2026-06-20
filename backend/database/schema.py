"""
SQLite database schema for DRINKOO platform.
Creates all tables with proper indexes and constraints.
"""

from datetime import datetime

from .db import get_db, DrinkooDatabase


SCHEMA_SQL = """
-- States master table
CREATE TABLE IF NOT EXISTS states (
    state_code TEXT PRIMARY KEY,
    state_name TEXT NOT NULL UNIQUE,
    capital_city TEXT NOT NULL,
    population_category TEXT NOT NULL CHECK(population_category IN ('small', 'medium', 'large')),
    expected_customer_count INTEGER NOT NULL DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE NOT NULL,
    customer_name TEXT NOT NULL,
    state_code TEXT NOT NULL,
    state_name TEXT NOT NULL,
    city_name TEXT NOT NULL,
    district_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT,
    region_size TEXT NOT NULL CHECK(region_size IN ('small', 'medium', 'large')),
    customer_segment TEXT NOT NULL CHECK(customer_segment IN ('distributor', 'retailer', 'individual')),
    customer_tier TEXT NOT NULL DEFAULT 'standard' CHECK(customer_tier IN ('standard', 'silver', 'gold', 'platinum')),
    registration_date DATE NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_code) REFERENCES states(state_code)
);

-- SKUs (Stock Keeping Units) table
CREATE TABLE IF NOT EXISTS skus (
    sku_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_code TEXT UNIQUE NOT NULL,
    sku_name TEXT NOT NULL,
    flavor_profile TEXT NOT NULL,
    drink_size_ml INTEGER NOT NULL CHECK(drink_size_ml IN (1000, 1500)),
    manufacturing_cost_per_unit DECIMAL(10, 2) NOT NULL,
    shipping_cost_per_unit DECIMAL(10, 2) NOT NULL,
    retail_price DECIMAL(10, 2) NOT NULL,
    sku_category TEXT NOT NULL CHECK(sku_category IN ('soda', 'juice', 'energy_drink', 'water', 'iced_tea', 'coconut_water', 'sparkling_water', 'sports_drink')),
    image_path TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SKU Distribution by state
CREATE TABLE IF NOT EXISTS sku_distribution (
    distribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT NOT NULL,
    sku_id INTEGER NOT NULL,
    quantity_allocated INTEGER NOT NULL DEFAULT 0,
    distribution_percentage DECIMAL(5, 2) NOT NULL CHECK(distribution_percentage >= 0 AND distribution_percentage <= 100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id),
    UNIQUE(state_code, sku_id)
);

-- Shipments and tracking
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_tracking_code TEXT UNIQUE NOT NULL,
    state_code TEXT NOT NULL,
    sku_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    shipment_date TIMESTAMP NOT NULL,
    delivery_date TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'in_transit', 'delivered')),
    shipping_cost DECIMAL(10, 2) NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
);

-- Sales transactions table
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_reference TEXT UNIQUE NOT NULL,
    sku_id INTEGER NOT NULL,
    state_code TEXT NOT NULL,
    customer_id INTEGER,
    quantity_sold INTEGER NOT NULL CHECK(quantity_sold > 0),
    sale_date DATE NOT NULL,
    revenue DECIMAL(12, 2) NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id),
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- SKU Images
CREATE TABLE IF NOT EXISTS sku_images (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    image_filename TEXT NOT NULL,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id) ON DELETE CASCADE
);

-- Users for authentication
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer' CHECK(role IN ('admin', 'viewer', 'analyst')),
    is_active BOOLEAN DEFAULT 1,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages (RAG chatbot history)
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    response_text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sources_used TEXT,
    is_human BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Vector embeddings for RAG
CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL CHECK(source_type IN ('sku', 'shipment', 'customer', 'policy', 'regional_insight')),
    source_id TEXT NOT NULL,
    source_text TEXT NOT NULL,
    embedding_vector TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_type, source_id)
);

-- Observability event log (internal, admin-only)
CREATE TABLE IF NOT EXISTS event_logs (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info' CHECK(severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    user_hash TEXT,
    session_id TEXT,
    source TEXT NOT NULL CHECK(source IN ('backend', 'frontend')),
    path TEXT,
    status_code INTEGER,
    duration_ms INTEGER,
    success BOOLEAN,
    ip_hash TEXT,
    user_agent TEXT,
    details TEXT
);

-- Chatbot failure tracking (admin-only)
CREATE TABLE IF NOT EXISTS chatbot_failures (
    failure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_hash TEXT,
    session_id TEXT,
    question TEXT NOT NULL,
    answer TEXT,
    source TEXT,
    confidence TEXT,
    failure_reason TEXT NOT NULL,
    similarity_score REAL,
    duration_ms INTEGER
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_event_logs_timestamp ON event_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_event_logs_category ON event_logs(category);
CREATE INDEX IF NOT EXISTS idx_event_logs_severity ON event_logs(severity);
CREATE INDEX IF NOT EXISTS idx_event_logs_session ON event_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_failures_timestamp ON chatbot_failures(timestamp);
CREATE INDEX IF NOT EXISTS idx_customers_state_code ON customers(state_code);
CREATE INDEX IF NOT EXISTS idx_customers_city_name ON customers(city_name);
CREATE INDEX IF NOT EXISTS idx_customers_external_id ON customers(external_id);
CREATE INDEX IF NOT EXISTS idx_sku_distribution_state ON sku_distribution(state_code);
CREATE INDEX IF NOT EXISTS idx_sku_distribution_sku ON sku_distribution(sku_id);
CREATE INDEX IF NOT EXISTS idx_shipments_tracking_code ON shipments(shipment_tracking_code);
CREATE INDEX IF NOT EXISTS idx_shipments_state ON shipments(state_code);
CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status);
CREATE INDEX IF NOT EXISTS idx_shipments_sku ON shipments(sku_id);
CREATE INDEX IF NOT EXISTS idx_sales_sku ON sales(sku_id);
CREATE INDEX IF NOT EXISTS idx_sales_state ON sales(state_code);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sku_images_sku ON sku_images(sku_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_type, source_id);
"""


def initialize_database(db_path: str = None) -> DrinkooDatabase:
    """Initialize database with schema."""
    db = get_db() if db_path is None else DrinkooDatabase(db_path)
    
    # Split and execute each statement
    statements = SCHEMA_SQL.split(';')
    for statement in statements:
        statement = statement.strip()
        if statement:
            db.execute(statement)
    
    db.commit()
    print("✓ Database schema initialized successfully")
    return db


def reset_database(db_path: str = None) -> None:
    """Reset database (drop all tables and recreate)."""
    db = get_db() if db_path is None else DrinkooDatabase(db_path)
    
    # Drop all tables
    tables = [
        'embeddings', 'chat_messages', 'users', 'sku_images',
        'shipments', 'sku_distribution', 'skus', 'customers', 'states'
    ]
    
    for table in tables:
        db.execute(f'DROP TABLE IF EXISTS {table}')
    
    db.commit()
    print("✓ All tables dropped")
    
    # Recreate schema
    initialize_database(db_path)


if __name__ == "__main__":
    # Initialize database when script is run directly
    initialize_database()

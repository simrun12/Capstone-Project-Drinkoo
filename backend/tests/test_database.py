"""
Test database layer and schema.
Tests database connections, queries, and schema integrity.
"""

import pytest
import sqlite3
from backend.database.schema import initialize_database, SCHEMA_SQL


class TestDatabaseSchema:
    """Test database schema creation and structure."""
    
    @pytest.mark.database
    def test_create_states_table(self, test_db_connection):
        """Test states table creation."""
        statements = SCHEMA_SQL.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and 'states' in statement.lower() and 'CREATE TABLE' in statement:
                test_db_connection.execute(statement)
        test_db_connection.commit()
        
        # Verify table exists
        cursor = test_db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='states'"
        )
        assert cursor.fetchone() is not None
    
    @pytest.mark.database
    def test_schema_initialization(self, test_db_connection):
        """Test that full schema initializes without errors."""
        statements = SCHEMA_SQL.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                test_db_connection.execute(statement)
        test_db_connection.commit()
        
        # Verify all tables exist
        expected_tables = [
            'states', 'customers', 'skus', 'sku_distribution', 
            'shipments', 'sales', 'sku_images', 'users', 
            'chat_messages', 'embeddings'
        ]
        
        for table_name in expected_tables:
            cursor = test_db_connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            assert cursor.fetchone() is not None, f"Table {table_name} not created"


class TestDatabaseIntegrity:
    """Test database foreign key constraints and integrity."""
    
    @pytest.mark.database
    def test_foreign_key_constraint_states(self, test_db_connection):
        """Test that foreign keys are enforced."""
        # PRAGMA foreign_keys should be ON in fixture
        pragma = test_db_connection.execute("PRAGMA foreign_keys").fetchone()
        assert pragma[0] == 1  # Should be enabled
    
    @pytest.mark.database
    def test_schema_initialization(self, test_db_connection):
        """Test that full schema initializes without errors."""
        statements = SCHEMA_SQL.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                test_db_connection.execute(statement)
        test_db_connection.commit()
        
        # Verify states table has been created
        cursor = test_db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='states'"
        )
        assert cursor.fetchone() is not None


class TestDatabaseQueries:
    """Test common database query patterns."""
    
    @pytest.mark.database
    def test_insert_and_retrieve_state(self, test_db_connection):
        """Test inserting and retrieving a state."""
        # Create states table from SCHEMA_SQL
        statements = SCHEMA_SQL.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and 'CREATE TABLE IF NOT EXISTS states' in statement:
                test_db_connection.execute(statement)
        test_db_connection.commit()
        
        test_db_connection.execute(
            "INSERT INTO states (state_code, state_name, capital_city, population_category) VALUES (?, ?, ?, ?)",
            ('MH', 'Maharashtra', 'Mumbai', 'large')
        )
        test_db_connection.commit()
        
        cursor = test_db_connection.execute(
            "SELECT state_code, state_name FROM states WHERE state_code = ?",
            ('MH',)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 'MH'
        assert row[1] == 'Maharashtra'
    
    @pytest.mark.database
    def test_unique_constraint_on_state_code(self, test_db_connection):
        """Test that state_code is unique."""
        # Create states table
        statements = SCHEMA_SQL.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and 'CREATE TABLE IF NOT EXISTS states' in statement:
                test_db_connection.execute(statement)
        test_db_connection.commit()
        
        test_db_connection.execute(
            "INSERT INTO states (state_code, state_name, capital_city, population_category) VALUES (?, ?, ?, ?)",
            ('MH', 'Maharashtra', 'Mumbai', 'large')
        )
        test_db_connection.commit()
        
        # Try to insert duplicate
        with pytest.raises(sqlite3.IntegrityError):
            test_db_connection.execute(
                "INSERT INTO states (state_code, state_name, capital_city, population_category) VALUES (?, ?, ?, ?)",
                ('MH', 'Maharashtra Duplicate', 'Mumbai', 'large')
            )
            test_db_connection.commit()

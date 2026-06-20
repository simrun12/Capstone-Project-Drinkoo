"""
Database initialization and connection management for DRINKOO.
Uses SQLite with vector extension support for RAG embeddings.
"""

import sqlite3
import json
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from ..config import DATABASE_PATH, DEBUG


class DrinkooDatabase:
    """Main database class for DRINKOO platform."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """Initialize database connection."""
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> None:
        """Create database connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self.connection.execute('PRAGMA foreign_keys = ON')
            if DEBUG:
                print(f"Database connected: {self.db_path}")
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query with parameters."""
        if self.connection is None:
            self.connect()
        return self.connection.execute(sql, params)
    
    def execute_many(self, sql: str, params_list: List[tuple]) -> None:
        """Execute multiple SQL statements."""
        if self.connection is None:
            self.connect()
        self.connection.executemany(sql, params_list)
        self.connection.commit()
    
    def commit(self) -> None:
        """Commit current transaction."""
        if self.connection:
            self.connection.commit()
    
    def rollback(self) -> None:
        """Rollback current transaction."""
        if self.connection:
            self.connection.rollback()
    
    def close(self) -> None:
        """Close the database connection."""
        self.disconnect()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database operations."""
        try:
            self.connect()
            yield self.connection
            self.commit()
        except Exception as e:
            self.rollback()
            raise e
    
    def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all results from query."""
        cursor = self.execute(sql, params)
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch single result from query."""
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def fetch_scalar(self, sql: str, params: tuple = ()) -> Any:
        """Fetch single scalar value."""
        cursor = self.execute(sql, params)
        result = cursor.fetchone()
        return result[0] if result else None


# Global database instance
_db_instance: Optional[DrinkooDatabase] = None


def get_db() -> DrinkooDatabase:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DrinkooDatabase()
        _db_instance.connect()
    return _db_instance


def close_db() -> None:
    """Close database connection."""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None

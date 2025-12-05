"""Database connection and helpers - intentionally vulnerable for demo purposes."""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.config import DATABASE_PATH
from app.core.security import hash_password


class Database:
    """Database connection handler - intentionally misused in some services."""
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database with schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Insert or update default users with hashed passwords
        admin_password_hash = hash_password('admin123')
        user_password_hash = hash_password('user123')
        
        # Update or insert admin user
        cursor.execute("""
            UPDATE users SET password = ?, email = ?, role = ?
            WHERE username = 'admin'
        """, (admin_password_hash, 'admin@vulnboard.local', 'admin'))
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO users (username, password, email, role)
                VALUES (?, ?, ?, ?)
            """, ('admin', admin_password_hash, 'admin@vulnboard.local', 'admin'))
        
        # Update or insert user
        cursor.execute("""
            UPDATE users SET password = ?, email = ?, role = ?
            WHERE username = 'user'
        """, (user_password_hash, 'user@vulnboard.local', 'user'))
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO users (username, password, email, role)
                VALUES (?, ?, ?, ?)
            """, ('user', user_password_hash, 'user@vulnboard.local', 'user'))
        
        # Insert sample posts
        cursor.execute("""
            INSERT OR IGNORE INTO posts (user_id, title, content)
            SELECT id, 'Welcome Post', 'This is a sample post for testing.'
            FROM users WHERE username = 'admin'
        """)
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.
        VULNERABILITY: This method uses parameterized queries correctly,
        but some services bypass this and use unsafe string concatenation.
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id
    
    def unsafe_query(self, query: str) -> List[Dict[str, Any]]:
        """
        VULNERABILITY: Unsafe query method that allows SQL injection.
        This is intentionally vulnerable for demonstration purposes.
        DO NOT USE IN PRODUCTION - Always use parameterized queries.
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            # VULNERABILITY: Direct string concatenation - SQL Injection risk
            cursor.execute(query)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except sqlite3.Error as e:
            # For demo purposes, catch SQL errors and raise a custom exception
            # that includes the error message to demonstrate the vulnerability
            conn.close()
            raise ValueError(f"SQL Error (demonstrates SQL injection vulnerability): {str(e)}")


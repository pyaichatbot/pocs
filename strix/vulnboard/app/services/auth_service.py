"""Authentication service - follows SRP and DIP principles."""

from typing import Optional, Dict
from app.core.db import Database
from app.core.security import hash_password, verify_password
from app.models.user import User


class AuthService:
    """Authentication service following Single Responsibility Principle."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        Uses parameterized queries correctly.
        """
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        hashed_password = hash_password(password)
        results = self.db.execute_query(query, (username, hashed_password))
        
        if results:
            return User.from_dict(results[0])
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID using parameterized query."""
        query = "SELECT id, username, email, role, created_at FROM users WHERE id = ?"
        results = self.db.execute_query(query, (user_id,))
        
        if results:
            return User.from_dict(results[0])
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username using parameterized query."""
        query = "SELECT id, username, email, role, created_at FROM users WHERE username = ?"
        results = self.db.execute_query(query, (username,))
        
        if results:
            return User.from_dict(results[0])
        return None


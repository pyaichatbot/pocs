"""Search service - intentionally unsafe query building (SQL injection vulnerability)."""

from typing import List, Dict, Any
from app.core.db import Database
from app.models.post import Post


class SearchService:
    """Business logic with intentionally unsafe query building."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def search_posts_safe(self, search_term: str) -> List[Post]:
        """
        Safe search using parameterized queries.
        This method is correct but intentionally not used in the vulnerable route.
        """
        query = "SELECT * FROM posts WHERE title LIKE ? OR content LIKE ?"
        search_pattern = f"%{search_term}%"
        results = self.db.execute_query(query, (search_pattern, search_pattern))
        return [Post.from_dict(row) for row in results]
    
    def search_posts_unsafe(self, search_term: str) -> List[Post]:
        """
        VULNERABILITY: SQL Injection
        Unsafe search using string concatenation - allows SQL injection attacks.
        Example attack: search_term = "'; DROP TABLE posts; --"
        This method is intentionally used in the vulnerable route to demonstrate SQL injection.
        """
        # VULNERABILITY: Direct string concatenation in SQL query
        # Should use parameterized queries like: query = "SELECT * FROM posts WHERE title LIKE ?"
        # But intentionally uses unsafe string formatting
        query = f"SELECT * FROM posts WHERE title LIKE '%{search_term}%' OR content LIKE '%{search_term}%'"
        
        # Uses unsafe_query method which executes raw SQL
        results = self.db.unsafe_query(query)
        return [Post.from_dict(row) for row in results]
    
    def get_posts_by_user(self, user_id: int) -> List[Post]:
        """Get posts by user ID using safe parameterized query."""
        query = "SELECT * FROM posts WHERE user_id = ?"
        results = self.db.execute_query(query, (user_id,))
        return [Post.from_dict(row) for row in results]


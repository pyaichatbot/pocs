"""User service - intentionally missing proper authorization in one method (IDOR vulnerability)."""

from typing import Optional, List
from app.core.db import Database
from app.core.security import check_authorization
from app.models.user import User


class UserService:
    """User-related operations - intentionally missing proper authorization."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_user_profile(self, user_id: int, requesting_user_id: Optional[int] = None, requesting_user_role: Optional[str] = None) -> Optional[User]:
        """
        Get user profile by ID.
        VULNERABILITY: IDOR (Insecure Direct Object Reference)
        - Missing authorization check - any user can access any profile by changing the ID
        - The check_authorization function exists but is intentionally NOT called here
        """
        # VULNERABILITY: No authorization check
        # Should call: check_authorization(requesting_user_id, user_id, requesting_user_role)
        # But intentionally bypassed to demonstrate IDOR vulnerability
        
        query = "SELECT id, username, email, role, created_at FROM users WHERE id = ?"
        results = self.db.execute_query(query, (user_id,))
        
        if results:
            return User.from_dict(results[0])
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all users - should require admin role but doesn't."""
        query = "SELECT id, username, email, role, created_at FROM users"
        results = self.db.execute_query(query)
        return [User.from_dict(row) for row in results]
    
    def update_user_email(self, user_id: int, new_email: str, requesting_user_id: int, requesting_user_role: str) -> bool:
        """
        Update user email.
        This method correctly uses authorization check (for comparison with vulnerable method).
        """
        # Correctly checks authorization
        if not check_authorization(requesting_user_id, user_id, requesting_user_role):
            return False
        
        query = "UPDATE users SET email = ? WHERE id = ?"
        self.db.execute_update(query, (new_email, user_id))
        return True


"""User model."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """User entity model."""
    
    id: int
    username: str
    email: Optional[str] = None
    role: str = "user"
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User from dictionary."""
        return cls(
            id=data.get("id"),
            username=data.get("username"),
            email=data.get("email"),
            role=data.get("role", "user"),
            created_at=data.get("created_at")
        )
    
    def to_dict(self) -> dict:
        """Convert User to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": str(self.created_at) if self.created_at else None
        }


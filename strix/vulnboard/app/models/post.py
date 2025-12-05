"""Post model for message board."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Post:
    """Post entity model for message board."""
    
    id: int
    user_id: int
    title: str
    content: str
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "Post":
        """Create Post from dictionary."""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            title=data.get("title"),
            content=data.get("content"),
            created_at=data.get("created_at")
        )
    
    def to_dict(self) -> dict:
        """Convert Post to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "created_at": str(self.created_at) if self.created_at else None
        }


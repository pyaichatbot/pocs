"""
File System Policy - Controls file system access for code execution.

Implements file system restrictions following SOLID principles:
- Single Responsibility: Only handles file system policy enforcement
- Open/Closed: Can be extended with new policies without modification
"""
from pathlib import Path
from typing import List, Set, Optional
from dataclasses import dataclass
from enum import Enum


class FileSystemAction(Enum):
    """File system action types."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"


class FileSystemViolation(Exception):
    """Raised when file system policy is violated."""
    pass


class FileSystemPolicy:
    """File system policy enforcement for code execution.
    
    Restricts file system access to workspace directory only.
    """
    
    # Restricted system directories
    RESTRICTED_DIRS: Set[str] = {
        '/etc', '/home', '/var', '/usr', '/bin', '/sbin',
        '/sys', '/proc', '/dev', '/root', '/boot', '/lib',
        '/lib64', '/opt', '/srv', '/tmp', '/run', '/mnt',
        '/media', '/lost+found'
    }
    
    def __init__(self, workspace_dir: Path, allow_writes: bool = True):
        """Initialize file system policy.
        
        Args:
            workspace_dir: Allowed workspace directory
            allow_writes: Whether to allow file writes in workspace
        """
        self.workspace_dir = Path(workspace_dir).resolve()
        self.allow_writes = allow_writes
        
        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    def is_allowed(self, path: str, action: FileSystemAction) -> bool:
        """Check if file system action is allowed.
        
        Args:
            path: File or directory path
            action: Action type (read, write, execute, delete)
            
        Returns:
            True if action is allowed, False otherwise
        """
        try:
            resolved_path = Path(path).resolve()
            
            # Block access to restricted system directories
            for restricted in self.RESTRICTED_DIRS:
                if str(resolved_path).startswith(restricted):
                    return False
            
            # Check if path is within workspace
            try:
                resolved_path.relative_to(self.workspace_dir)
            except ValueError:
                # Path is outside workspace
                return False
            
            # Check write permissions
            if action in [FileSystemAction.WRITE, FileSystemAction.DELETE]:
                if not self.allow_writes:
                    return False
            
            return True
            
        except Exception:
            # If we can't resolve path, block it
            return False
    
    def validate_access(self, path: str, action: FileSystemAction) -> None:
        """Validate file system access attempt.
        
        Args:
            path: File or directory path
            action: Action type
            
        Raises:
            FileSystemViolation: If access is not allowed
        """
        if not self.is_allowed(path, action):
            action_name = action.value
            raise FileSystemViolation(
                f"File system {action_name} access to '{path}' is blocked by security policy. "
                f"Only files within workspace directory '{self.workspace_dir}' are allowed."
            )
    
    def get_allowed_paths(self) -> List[str]:
        """Get list of allowed paths (workspace and subdirectories)."""
        allowed = [str(self.workspace_dir)]
        
        # Add subdirectories
        try:
            for item in self.workspace_dir.rglob('*'):
                if item.is_dir():
                    allowed.append(str(item))
        except Exception:
            pass
        
        return allowed
    
    def get_workspace_dir(self) -> Path:
        """Get workspace directory."""
        return self.workspace_dir


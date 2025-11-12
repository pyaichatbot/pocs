"""
Network Policy - Controls network access for code execution.

Implements network egress controls following SOLID principles:
- Single Responsibility: Only handles network policy enforcement
- Open/Closed: Can be extended with new policies without modification
"""
import os
from typing import List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class NetworkAction(Enum):
    """Network action types."""
    ALLOW = "allow"
    BLOCK = "block"


@dataclass
class NetworkRule:
    """Network access rule."""
    host: str
    port: Optional[int] = None
    action: NetworkAction = NetworkAction.ALLOW
    description: Optional[str] = None


class NetworkPolicyViolation(Exception):
    """Raised when network policy is violated."""
    pass


class NetworkPolicy:
    """Network policy enforcement for code execution.
    
    Blocks all network egress by default, allows only specific endpoints.
    """
    
    def __init__(self, allowed_endpoints: Optional[List[str]] = None):
        """Initialize network policy.
        
        Args:
            allowed_endpoints: List of allowed endpoints (e.g., ['mcp:8974', 'internal-api:8080'])
                              If None, reads from MCP_ENDPOINT environment variable
        """
        self.allowed_endpoints: Set[str] = set()
        
        # Add MCP server endpoint if configured
        mcp_endpoint = os.getenv("MCP_ENDPOINT", "")
        if mcp_endpoint:
            # Extract host:port from URL
            endpoint = self._extract_endpoint(mcp_endpoint)
            if endpoint:
                self.allowed_endpoints.add(endpoint)
        
        # Add explicitly allowed endpoints
        if allowed_endpoints:
            for endpoint in allowed_endpoints:
                self.allowed_endpoints.add(endpoint)
        
        # Block all other network access
        self.block_all = True
    
    def _extract_endpoint(self, url: str) -> Optional[str]:
        """Extract host:port from URL.
        
        Examples:
            http://mcp:8974/mcp -> mcp:8974
            http://127.0.0.1:8974/mcp -> 127.0.0.1:8974
        """
        try:
            # Remove protocol
            if '://' in url:
                url = url.split('://', 1)[1]
            
            # Remove path
            if '/' in url:
                url = url.split('/', 1)[0]
            
            # Extract host:port
            if ':' in url:
                return url
            else:
                # Default port based on protocol (if we had it)
                return f"{url}:80"
        except Exception:
            return None
    
    def is_allowed(self, host: str, port: Optional[int] = None) -> bool:
        """Check if network access to host:port is allowed.
        
        Args:
            host: Target hostname or IP
            port: Target port (optional)
            
        Returns:
            True if access is allowed, False otherwise
        """
        if not self.block_all:
            return True
        
        # Check exact match
        if port:
            endpoint = f"{host}:{port}"
        else:
            endpoint = host
        
        if endpoint in self.allowed_endpoints:
            return True
        
        # Check host-only match (any port)
        if host in self.allowed_endpoints:
            return True
        
        # Check wildcard patterns
        for allowed in self.allowed_endpoints:
            if self._matches_pattern(host, port, allowed):
                return True
        
        return False
    
    def _matches_pattern(self, host: str, port: Optional[int], pattern: str) -> bool:
        """Check if host:port matches pattern (supports wildcards).
        
        Args:
            host: Target host
            port: Target port
            pattern: Pattern to match (e.g., "*.internal", "10.0.*.*")
        """
        # Simple wildcard matching
        if '*' in pattern:
            pattern_host = pattern.split(':')[0]
            if '*' in pattern_host:
                # Convert to regex-like matching
                pattern_parts = pattern_host.split('.')
                host_parts = host.split('.')
                
                if len(pattern_parts) != len(host_parts):
                    return False
                
                for p, h in zip(pattern_parts, host_parts):
                    if p != '*' and p != h:
                        return False
                
                # Check port if specified in pattern
                if ':' in pattern:
                    pattern_port = pattern.split(':')[1]
                    if port and str(port) == pattern_port:
                        return True
                else:
                    return True
        
        return False
    
    def validate_connection(self, host: str, port: Optional[int] = None) -> None:
        """Validate network connection attempt.
        
        Args:
            host: Target hostname or IP
            port: Target port
            
        Raises:
            NetworkPolicyViolation: If connection is not allowed
        """
        if not self.is_allowed(host, port):
            raise NetworkPolicyViolation(
                f"Network access to {host}:{port} is blocked by security policy. "
                f"Only the following endpoints are allowed: {', '.join(self.allowed_endpoints)}"
            )
    
    def get_allowed_endpoints(self) -> List[str]:
        """Get list of allowed endpoints."""
        return list(self.allowed_endpoints)
    
    def add_allowed_endpoint(self, endpoint: str) -> None:
        """Add an allowed endpoint."""
        self.allowed_endpoints.add(endpoint)
    
    def remove_allowed_endpoint(self, endpoint: str) -> None:
        """Remove an allowed endpoint."""
        self.allowed_endpoints.discard(endpoint)


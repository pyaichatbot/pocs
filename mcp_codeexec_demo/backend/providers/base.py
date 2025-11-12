"""
Base Tool Provider Interface

Defines the abstract interface that all tool providers must implement.
This allows the agent to work with any tool source (MCP, OpenAI Functions, etc.)
without being coupled to a specific protocol.

Following SOLID principles:
- Dependency Inversion: Core code depends on this abstraction, not concrete implementations
- Interface Segregation: Clean, focused interface
- Open/Closed: Open for extension (new providers), closed for modification
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Protocol, Optional
from dataclasses import dataclass


@dataclass
class Tool:
    """Generic tool definition interface.
    
    This is a protocol-agnostic representation of a tool that can be used
    by any tool provider (MCP, OpenAI Functions, REST APIs, etc.).
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: Optional[str] = None  # Optional: which server/provider this tool belongs to


@dataclass
class ToolResult:
    """Generic tool result interface.
    
    This is a protocol-agnostic representation of a tool result that can be
    returned by any tool provider.
    """
    content: List[Any]
    is_error: bool = False
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolProvider(ABC):
    """Abstract interface for tool providers.
    
    All tool providers (MCP, OpenAI Functions, REST APIs, etc.) must implement
    this interface. This allows the agent to work with any tool source without
    being coupled to a specific protocol.
    
    Following SOLID principles:
    - Single Responsibility: Each provider handles one tool source
    - Liskov Substitution: All providers can be used interchangeably
    - Dependency Inversion: Core code depends on this abstraction
    """
    
    @abstractmethod
    async def discover_tools(self) -> List[Tool]:
        """Discover all available tools from this provider.
        
        Returns:
            List of Tool objects representing available tools
            
        Raises:
            ToolProviderError: If tool discovery fails
        """
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Call a tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments for the tool
            
        Returns:
            ToolResult containing the tool's response
            
        Raises:
            ToolProviderError: If tool call fails
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider identifier.
        
        Returns:
            String identifier for this provider (e.g., 'mcp', 'openai_functions')
            Used for organizing tools in filesystem structure.
        """
        pass
    
    @abstractmethod
    def get_provider_config(self) -> Dict[str, Any]:
        """Get provider-specific configuration.
        
        Returns:
            Dictionary of configuration values (endpoints, credentials, etc.)
            Used for debugging and troubleshooting.
        """
        pass


class ToolProviderError(Exception):
    """Base exception for tool provider errors."""
    pass


class ToolDiscoveryError(ToolProviderError):
    """Raised when tool discovery fails."""
    pass


class ToolCallError(ToolProviderError):
    """Raised when tool call fails."""
    pass


"""
Tool Provider Factory

Creates and configures tool providers based on environment variables.
This allows easy switching between different tool sources (MCP, OpenAI Functions, etc.)

Following SOLID principles:
- Single Responsibility: Factory only creates providers
- Open/Closed: Easy to add new providers without modifying factory
- Dependency Inversion: Returns abstract ToolProvider interface
"""
import os
from typing import Optional, List
from providers.base import ToolProvider, ToolProviderError
from providers.mcp_provider import MCPToolProvider


def create_tool_provider(provider_type: Optional[str] = None) -> ToolProvider:
    """Create a tool provider based on configuration.
    
    Reads TOOL_PROVIDER environment variable to determine which provider to create.
    Defaults to MCP if not specified.
    
    Args:
        provider_type: Override provider type (for testing). If None, reads from env.
        
    Returns:
        ToolProvider instance configured based on environment
        
    Raises:
        ToolProviderError: If provider type is unknown or configuration is invalid
        
    Example:
        # Use MCP (default)
        provider = create_tool_provider()
        
        # Use specific provider
        provider = create_tool_provider("mcp")
    """
    if provider_type is None:
        provider_type = os.getenv("TOOL_PROVIDER", "mcp").lower()
    
    if provider_type == "mcp":
        endpoint = os.getenv("MCP_ENDPOINT", "http://127.0.0.1:8974/mcp")
        return MCPToolProvider(endpoint=endpoint)
    
    elif provider_type == "openai_functions":
        # TODO: Implement OpenAI Functions provider
        raise ToolProviderError(
            f"Provider '{provider_type}' not yet implemented. "
            "Currently supported: 'mcp'"
        )
    
    elif provider_type == "rest_api":
        # TODO: Implement REST API provider
        raise ToolProviderError(
            f"Provider '{provider_type}' not yet implemented. "
            "Currently supported: 'mcp'"
        )
    
    else:
        raise ToolProviderError(
            f"Unknown tool provider: '{provider_type}'. "
            f"Supported providers: 'mcp' (and 'openai_functions', 'rest_api' coming soon)"
        )


def get_available_providers() -> List[str]:
    """Get list of available tool providers.
    
    Returns:
        List of provider type strings that are currently supported
    """
    return ["mcp"]  # Add more as they're implemented


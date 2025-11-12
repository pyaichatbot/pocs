"""
Tool Provider Abstraction Layer

This module provides a generic interface for tool providers, allowing the agent
to work with any tool source (MCP, OpenAI Functions, REST APIs, etc.).

Following SOLID principles:
- Single Responsibility: Each provider handles one tool source
- Open/Closed: Open for extension (new providers), closed for modification
- Liskov Substitution: All providers implement the same interface
- Interface Segregation: Clean, focused interfaces
- Dependency Inversion: Depend on abstractions, not concretions
"""

from providers.base import ToolProvider, Tool, ToolResult
from providers.mcp_provider import MCPToolProvider
from providers.factory import create_tool_provider

__all__ = [
    "ToolProvider",
    "Tool",
    "ToolResult",
    "MCPToolProvider",
    "create_tool_provider",
]


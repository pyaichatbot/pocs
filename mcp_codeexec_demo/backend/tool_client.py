"""
Generic Tool Client

Provides a unified interface for calling tools from any provider.
This replaces the MCP-specific mcp_client.py and makes the system provider-agnostic.

Following SOLID principles:
- Single Responsibility: Only handles tool calling
- Dependency Inversion: Depends on ToolProvider abstraction
- Open/Closed: Works with any provider without modification
"""
import os
from typing import Dict, Any, Optional
from providers.base import ToolProvider, ToolResult
from privacy_tokenizer import get_tokenizer

# Phase 1: Import logging decorator (must be before class definition)
try:
    from observability.logging_decorator import log_execution, LogLevel
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    LogLevel = None
    
    def log_execution(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

ENABLE_PRIVACY_TOKENIZATION = os.getenv("ENABLE_PRIVACY_TOKENIZATION", "true").lower() == "true"

# Singleton tool client for generated code
_tool_client_instance: Optional['ToolClient'] = None


class ToolClient:
    """Generic client for calling tools from any provider.
    
    This class abstracts tool calling, allowing the agent to work with
    any tool provider (MCP, OpenAI Functions, REST APIs, etc.) without
    being coupled to a specific protocol.
    
    Implements privacy-preserving tokenization as per blog post:
    https://www.anthropic.com/engineering/code-execution-with-mcp
    """
    
    def __init__(self, provider: ToolProvider):
        """Initialize tool client with a provider.
        
        Args:
            provider: ToolProvider instance (MCP, OpenAI Functions, etc.)
        """
        self.provider = provider
        self._tokenizer = None
        if ENABLE_PRIVACY_TOKENIZATION:
            self._tokenizer = get_tokenizer()
    
    @log_execution(log_level=LogLevel.INFO if OBSERVABILITY_AVAILABLE and LogLevel else None, log_parameters=True, log_results=True)
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Call a tool with the given arguments.
        
        Implements privacy-preserving tokenization:
        - Tokenizes PII in arguments before sending to model
        - Untokenizes results when data flows to other tools
        
        This function is used by generated tool files in servers/ directory.
        
        Phase 1: Instrumented with logging decorator for observability.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments for the tool
            
        Returns:
            ToolResult containing the tool's response
        """
        # Tokenize arguments if privacy tokenization is enabled
        if ENABLE_PRIVACY_TOKENIZATION and self._tokenizer:
            arguments = self._tokenizer.tokenize(arguments)
        
        # Call tool via provider
        result = await self.provider.call_tool(tool_name, arguments)
        
        # Untokenize results if privacy tokenization is enabled
        # This ensures real data flows between tools, but model never sees PII
        if ENABLE_PRIVACY_TOKENIZATION and self._tokenizer and result.content:
            untokenized_content = []
            for item in result.content:
                if isinstance(item, str):
                    untokenized_text = self._tokenizer.untokenize(item)
                    untokenized_content.append(untokenized_text)
                else:
                    untokenized_content.append(item)
            result.content = untokenized_content
        
        return result
    
    def get_provider_name(self) -> str:
        """Get the name of the current provider."""
        return self.provider.get_provider_name()
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get provider configuration for debugging."""
        return self.provider.get_provider_config()


def get_tool_client() -> ToolClient:
    """Get the global tool client instance.
    
    This function is used by generated tool files to access the tool client.
    The client is initialized on backend startup.
    
    Returns:
        ToolClient instance
        
    Raises:
        RuntimeError: If tool client has not been initialized
    """
    global _tool_client_instance
    if _tool_client_instance is None:
        raise RuntimeError(
            "Tool client not initialized. "
            "This should be initialized on backend startup. "
            "Check backend logs for initialization errors."
        )
    return _tool_client_instance


def set_tool_client(client: ToolClient) -> None:
    """Set the global tool client instance.
    
    This is called during backend startup to initialize the tool client.
    
    Args:
        client: ToolClient instance to use globally
    """
    global _tool_client_instance
    _tool_client_instance = client


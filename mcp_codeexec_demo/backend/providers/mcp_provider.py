"""
MCP Tool Provider Implementation

Implements the ToolProvider interface for Model Context Protocol (MCP) servers.
This allows the agent to discover and call tools from any MCP server.

Following the blog post pattern:
https://www.anthropic.com/engineering/code-execution-with-mcp
"""
import os
from typing import List, Dict, Any, Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import Tool as MCPTool, CallToolResult, TextContent

from providers.base import (
    ToolProvider,
    Tool,
    ToolResult,
    ToolProviderError,
    ToolDiscoveryError,
    ToolCallError,
)


class MCPToolProvider(ToolProvider):
    """Tool provider implementation for MCP servers.
    
    This provider connects to an MCP server and provides tools via the
    Model Context Protocol. It can connect to any MCP-compatible server.
    
    Configuration:
        MCP_ENDPOINT: URL of the MCP server (default: http://127.0.0.1:8974/mcp)
    """
    
    def __init__(self, endpoint: Optional[str] = None):
        """Initialize MCP tool provider.
        
        Args:
            endpoint: MCP server endpoint URL. If None, reads from MCP_ENDPOINT env var.
        """
        self.endpoint = endpoint or os.getenv("MCP_ENDPOINT", "http://127.0.0.1:8974/mcp")
        self._server_name: Optional[str] = None
    
    async def discover_tools(self) -> List[Tool]:
        """Discover all tools from the MCP server.
        
        Returns:
            List of Tool objects representing MCP tools
            
        Raises:
            ToolDiscoveryError: If discovery fails
        """
        try:
            async with streamablehttp_client(self.endpoint) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    
                    # Extract server name if available (some MCP servers provide this)
                    # For now, we'll use a default or extract from endpoint
                    if not self._server_name:
                        self._server_name = self._extract_server_name()
                    
                    return [self._convert_mcp_tool(t) for t in result.tools]
        except Exception as e:
            raise ToolDiscoveryError(f"Failed to discover MCP tools: {str(e)}") from e
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Call an MCP tool with the given arguments.
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Dictionary of arguments for the tool
            
        Returns:
            ToolResult containing the tool's response
            
        Raises:
            ToolCallError: If tool call fails
        """
        try:
            async with streamablehttp_client(self.endpoint) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    return self._convert_result(result)
        except Exception as e:
            raise ToolCallError(f"Failed to call MCP tool '{tool_name}': {str(e)}") from e
    
    def get_provider_name(self) -> str:
        """Return MCP provider identifier."""
        return self._server_name or "mcp"
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get MCP provider configuration."""
        return {
            "provider_type": "mcp",
            "endpoint": self.endpoint,
            "server_name": self._server_name,
        }
    
    def _extract_server_name(self) -> str:
        """Extract server name from endpoint or use default.
        
        For now, we use a simple default. In production, you might:
        - Query MCP server for its name
        - Use configuration
        - Extract from endpoint URL
        """
        # Try to extract from endpoint (e.g., http://localhost:8974/mcp -> "mcp")
        # Or use a configured server name
        server_name = os.getenv("MCP_SERVER_NAME", "demo_mcp")
        return server_name
    
    def _convert_mcp_tool(self, mcp_tool: MCPTool) -> Tool:
        """Convert MCP Tool to generic Tool.
        
        Args:
            mcp_tool: MCP Tool object
            
        Returns:
            Generic Tool object
        """
        return Tool(
            name=mcp_tool.name,
            description=mcp_tool.description or "",
            input_schema=mcp_tool.inputSchema.model_dump() if hasattr(mcp_tool.inputSchema, 'model_dump') else dict(mcp_tool.inputSchema) if mcp_tool.inputSchema else {},
            server_name=self._server_name,
        )
    
    def _convert_result(self, result: CallToolResult) -> ToolResult:
        """Convert MCP CallToolResult to generic ToolResult.
        
        Args:
            result: MCP CallToolResult object
            
        Returns:
            Generic ToolResult object
        """
        # Extract content from MCP result
        content = []
        for item in result.content:
            if isinstance(item, TextContent):
                content.append(item.text)
            else:
                # Handle other content types if needed
                content.append(str(item))
        
        return ToolResult(
            content=content,
            is_error=result.isError,
            error_message=str(result.content[0]) if result.isError and result.content else None,
            metadata=getattr(result, "_meta", None),
        )


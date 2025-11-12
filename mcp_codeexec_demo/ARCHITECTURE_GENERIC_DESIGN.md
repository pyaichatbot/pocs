# Generic Backend Architecture Design

## Current State: MCP-Coupled Architecture

### Tightly Coupled Components

1. **Tool Discovery** (`tool_generator.py`)
   - Directly calls MCP server via `streamablehttp_client`
   - Uses `mcp.types.Tool` for tool definitions
   - Hardcoded MCP endpoint discovery

2. **Tool Execution** (`mcp_client.py`)
   - Uses MCP's `ClientSession` and `call_tool`
   - Returns MCP-specific `CallToolResult` and `TextContent`
   - MCP protocol-specific error handling

3. **Code Executor** (`code_executor.py`)
   - Imports `mcp_client` directly
   - Assumes MCP tool calling pattern
   - Hardcoded MCP types in generated code

4. **Main Application** (`main.py`)
   - Direct MCP imports: `from mcp import ClientSession`
   - MCP-specific tool calling: `mcp_call()`
   - MCP endpoint configuration

## Generic Architecture Design

### Core Abstraction: Tool Provider Interface

```python
# backend/providers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Protocol

class Tool(Protocol):
    """Generic tool definition interface."""
    name: str
    description: str
    input_schema: Dict[str, Any]

class ToolResult(Protocol):
    """Generic tool result interface."""
    content: List[Any]
    is_error: bool

class ToolProvider(ABC):
    """Abstract interface for tool providers (MCP, OpenAI Functions, etc.)"""
    
    @abstractmethod
    async def discover_tools(self) -> List[Tool]:
        """Discover all available tools."""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Call a tool with given arguments."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider identifier (e.g., 'mcp', 'openai_functions')."""
        pass
```

### MCP Provider Implementation

```python
# backend/providers/mcp_provider.py
from providers.base import ToolProvider, Tool, ToolResult
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import Tool as MCPTool, CallToolResult

class MCPToolProvider(ToolProvider):
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
    
    async def discover_tools(self) -> List[Tool]:
        async with streamablehttp_client(self.endpoint) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_tools = await session.list_tools()
                return [self._convert_mcp_tool(t) for t in mcp_tools.tools]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        async with streamablehttp_client(self.endpoint) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return self._convert_result(result)
    
    def get_provider_name(self) -> str:
        return "mcp"
    
    def _convert_mcp_tool(self, mcp_tool: MCPTool) -> Tool:
        # Convert MCP Tool to generic Tool
        pass
    
    def _convert_result(self, result: CallToolResult) -> ToolResult:
        # Convert MCP result to generic result
        pass
```

### OpenAI Functions Provider (Example)

```python
# backend/providers/openai_functions_provider.py
from providers.base import ToolProvider, Tool, ToolResult
from openai import OpenAI

class OpenAIFunctionsProvider(ToolProvider):
    def __init__(self, client: OpenAI, functions: List[Dict]):
        self.client = client
        self.functions = functions
    
    async def discover_tools(self) -> List[Tool]:
        return [self._convert_function(f) for f in self.functions]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        # Call OpenAI function
        pass
    
    def get_provider_name(self) -> str:
        return "openai_functions"
```

### Refactored Components

#### 1. Generic Tool Generator

```python
# backend/tool_generator.py (refactored)
from providers.base import ToolProvider

async def generate_tool_files(provider: ToolProvider) -> Dict[str, Any]:
    """Generate filesystem structure from any tool provider."""
    tools = await provider.discover_tools()
    server_name = provider.get_provider_name()
    
    # Generate Python files (same logic, but provider-agnostic)
    for tool in tools:
        generate_tool_function(tool, server_name)
```

#### 2. Generic Tool Client

```python
# backend/tool_client.py (refactored)
from providers.base import ToolProvider

class ToolClient:
    def __init__(self, provider: ToolProvider):
        self.provider = provider
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        return await self.provider.call_tool(tool_name, arguments)
```

#### 3. Generic Code Executor

```python
# backend/code_executor.py (refactored)
from tool_client import ToolClient

class CodeExecutor:
    def __init__(self, tool_client: ToolClient):
        self.tool_client = tool_client
    
    # Code execution logic remains the same
    # But uses generic tool_client instead of mcp_client
```

#### 4. Main Application (Refactored)

```python
# backend/main.py (refactored)
from providers.mcp_provider import MCPToolProvider
from providers.base import ToolProvider

# Provider selection via environment variable
TOOL_PROVIDER_TYPE = os.getenv("TOOL_PROVIDER", "mcp")

def create_tool_provider() -> ToolProvider:
    if TOOL_PROVIDER_TYPE == "mcp":
        endpoint = os.getenv("MCP_ENDPOINT", "http://127.0.0.1:8974/mcp")
        return MCPToolProvider(endpoint)
    elif TOOL_PROVIDER_TYPE == "openai_functions":
        # Return OpenAI provider
        pass
    else:
        raise ValueError(f"Unknown tool provider: {TOOL_PROVIDER_TYPE}")

@app.on_event("startup")
async def startup_event():
    provider = create_tool_provider()
    tool_info = await generate_tool_files(provider)
    # Rest of startup logic
```

## Migration Path

### Phase 1: Extract Interfaces (Non-Breaking)
1. Create `providers/base.py` with abstract interfaces
2. Create `providers/mcp_provider.py` implementing MCP
3. Keep existing code working via adapter pattern

### Phase 2: Refactor Components
1. Update `tool_generator.py` to use `ToolProvider` interface
2. Update `tool_client.py` (or create it) to use `ToolProvider`
3. Update `code_executor.py` to use generic `ToolClient`

### Phase 3: Update Main Application
1. Add provider factory function
2. Update startup to use provider factory
3. Add environment variable for provider selection

### Phase 4: Add Additional Providers
1. Implement OpenAI Functions provider
2. Implement custom REST API provider
3. Implement plugin-based provider system

## Benefits of Generic Design

1. **Pluggable Tool Sources**: Switch between MCP, OpenAI Functions, REST APIs, etc.
2. **Testability**: Easy to mock tool providers for testing
3. **Extensibility**: Add new tool sources without changing core logic
4. **Reusability**: Core code execution pattern works with any tool source
5. **Maintainability**: Clear separation of concerns

## Configuration Example

```bash
# Use MCP (current)
TOOL_PROVIDER=mcp
MCP_ENDPOINT=http://127.0.0.1:8974/mcp

# Use OpenAI Functions (future)
TOOL_PROVIDER=openai_functions
OPENAI_API_KEY=sk-...

# Use Custom REST API (future)
TOOL_PROVIDER=rest_api
TOOL_API_ENDPOINT=https://api.example.com/tools
```

## Current Coupling Assessment

**Tightly Coupled:**
- ✅ Tool discovery (MCP-specific)
- ✅ Tool execution (MCP protocol)
- ✅ Tool result types (MCP types)

**Loosely Coupled (Already Generic):**
- ✅ Code execution pattern (works with any tools)
- ✅ Code validation (language-agnostic)
- ✅ LLM interaction (provider-agnostic)
- ✅ Token counting (model-agnostic)
- ✅ Filesystem structure (protocol-agnostic)

## Recommendation

The backend is **moderately coupled** to MCP:
- **Core pattern is generic**: Code execution, validation, LLM calls
- **Tool layer is MCP-specific**: Discovery, calling, result types

To make it fully generic, extract the tool layer into a provider interface (as shown above). This would allow:
- Using MCP (current)
- Using OpenAI Functions
- Using custom REST APIs
- Using any other tool source

The refactoring is **non-trivial but straightforward** - mainly extracting MCP-specific code into a provider implementation.


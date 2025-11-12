# Generic Agent Setup Guide

This guide helps you set up your own agent with code execution capabilities, connecting to any MCP server or tool provider.

## Architecture Overview

This agent follows the **code execution with MCP** pattern from [Anthropic's blog post](https://www.anthropic.com/engineering/code-execution-with-mcp), implementing a **generic, provider-agnostic architecture** that allows you to:

- Connect to **any MCP server** (or other tool providers in the future)
- Use **filesystem-based tool discovery** for progressive disclosure
- Execute **agent-generated code** in a sandboxed environment
- Benefit from **context-efficient** tool usage (98.7% token savings)

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd mcp_codeexec_demo

# Copy environment template
cp .env.example .env
```

### 2. Configure Your Tool Provider

Edit `.env` file:

```bash
# Tool Provider Configuration
TOOL_PROVIDER=mcp                    # Options: mcp (more coming soon)
MCP_ENDPOINT=http://localhost:8974/mcp  # Your MCP server endpoint
MCP_SERVER_NAME=my_server            # Optional: name for your server

# LLM Configuration
ANTHROPIC_API_KEY=sk-ant-...         # For Anthropic Claude
# OR
OPENAI_API_KEY=sk-...                # For OpenAI
AZURE_API_KEY=...                    # For Azure OpenAI
AZURE_API_BASE=https://...

# Optional: Model Configuration
MODEL_ID=claude-sonnet-4-20250514    # Override default model
LLM_TIMEOUT=120                      # LLM call timeout (seconds)

# Privacy & Security
ENABLE_PRIVACY_TOKENIZATION=true      # Enable PII tokenization
```

### 3. Start Your MCP Server

You need an MCP server running. Examples:

**Option A: Use the demo MCP server (included)**
```bash
cd mcp_server
python server.py
```

**Option B: Connect to your own MCP server**
```bash
# Set MCP_ENDPOINT in .env to your server's URL
MCP_ENDPOINT=http://your-server:8974/mcp
```

### 4. Launch the Agent

```bash
# Using Docker (recommended)
docker-compose up -d

# Or run locally
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Access the UI

Open http://localhost:8501 in your browser.

## Configuration Details

### Tool Provider Types

#### MCP Provider (Current)

The MCP provider connects to Model Context Protocol servers.

**Configuration:**
```bash
TOOL_PROVIDER=mcp
MCP_ENDPOINT=http://localhost:8974/mcp
MCP_SERVER_NAME=my_server  # Optional: custom server name
```

**How it works:**
1. Agent discovers tools from your MCP server
2. Generates Python API files in `workspace/servers/`
3. Agent explores filesystem to find tools (progressive disclosure)
4. Executes code that calls tools via the generated API

**Example MCP Server:**
- See `mcp_server/server.py` for a reference implementation
- Your MCP server should expose tools via the MCP protocol
- Tools are automatically discovered and made available

#### Future Providers (Coming Soon)

- **OpenAI Functions**: Connect to OpenAI function calling
- **REST API**: Connect to any REST API with OpenAPI spec
- **Custom**: Implement your own provider (see `providers/base.py`)

### LLM Configuration

#### Anthropic Claude (Recommended)

```bash
ANTHROPIC_API_KEY=sk-ant-...
MODEL_ID=claude-sonnet-4-20250514  # Optional: override default
```

#### Azure OpenAI

```bash
AZURE_API_KEY=your-key
AZURE_API_BASE=https://your-resource.openai.azure.com
MODEL_ID=gpt-4o-mini  # Will be prefixed with "azure/"
```

#### Standard OpenAI

```bash
OPENAI_API_KEY=sk-...
MODEL_ID=gpt-4o-mini
```

### Privacy & Security

#### Privacy-Preserving Tokenization

Automatically tokenizes PII before data reaches the model:

```bash
ENABLE_PRIVACY_TOKENIZATION=true
```

**How it works:**
- Detects PII (emails, phones, names) in tool arguments
- Replaces with tokens like `[EMAIL_1]`, `[PHONE_1]`
- Model never sees real PII
- Data is untokenized when flowing between tools
- Real data flows to your systems, but not through the model

#### Code Execution Security

- **Sandboxed execution**: Code runs in isolated subprocess
- **Resource limits**: CPU and memory limits enforced
- **Timeout protection**: Code execution times out after 30s
- **Code validation**: Syntax and security checks before execution

## Architecture for Multiple Employees

### Single Agent, Multiple MCP Servers

Each employee can run their own agent instance:

```bash
# Employee 1
TOOL_PROVIDER=mcp
MCP_ENDPOINT=http://employee1-mcp-server:8974/mcp
MCP_SERVER_NAME=employee1_tools

# Employee 2
TOOL_PROVIDER=mcp
MCP_ENDPOINT=http://employee2-mcp-server:8974/mcp
MCP_SERVER_NAME=employee2_tools
```

### Shared Infrastructure

- **Backend**: Each employee runs their own backend instance
- **MCP Server**: Each employee connects to their own MCP server
- **Workspace**: Each backend has its own `workspace/` directory
- **UI**: Each employee accesses their own UI instance

### Docker Compose Setup (Per Employee)

```bash
# Employee-specific docker-compose.yml
version: '3.8'
services:
  backend:
    environment:
      - TOOL_PROVIDER=mcp
      - MCP_ENDPOINT=http://employee-mcp:8974/mcp
      - MCP_SERVER_NAME=employee_tools
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

## Troubleshooting

### Tool Discovery Fails

**Error:** `Failed to discover MCP tools`

**Solutions:**
1. Check MCP server is running: `curl http://localhost:8974/mcp`
2. Verify `MCP_ENDPOINT` in `.env` matches your server
3. Check MCP server logs for errors
4. Ensure MCP server exposes tools via `list_tools`

### Code Execution Fails

**Error:** `Tool client not initialized`

**Solutions:**
1. Check backend startup logs for provider initialization
2. Verify tool files were generated in `backend/workspace/servers/`
3. Check `backend/workspace/servers/` directory exists and has tool files

### LLM Errors

**Error:** `Model not found` or `Authentication failed`

**Solutions:**
1. Verify API key is set correctly in `.env`
2. Check API key has access to the model
3. For Azure: Verify `AZURE_API_BASE` is correct
4. Check model name matches provider's available models

### Token Usage Higher Than Expected

**Symptoms:** `code_exec` mode using more tokens than `prompt_tools`

**Solutions:**
1. Check agent is actually summarizing (not returning full transcript)
2. Verify `system_hint` is instructing summarization
3. Check backend logs for "Warning: Agent returned X words" messages
4. Ensure code execution is working (check `exec_success` in debug output)

## Advanced Configuration

### Custom Tool Provider

To add a custom tool provider:

1. Create `backend/providers/my_provider.py`:

```python
from providers.base import ToolProvider, Tool, ToolResult

class MyToolProvider(ToolProvider):
    async def discover_tools(self) -> List[Tool]:
        # Your discovery logic
        pass
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> ToolResult:
        # Your tool calling logic
        pass
    
    def get_provider_name(self) -> str:
        return "my_provider"
    
    def get_provider_config(self) -> Dict:
        return {"provider_type": "my_provider"}
```

2. Register in `providers/factory.py`:

```python
elif provider_type == "my_provider":
    return MyToolProvider(...)
```

3. Use it:

```bash
TOOL_PROVIDER=my_provider
```

### Multi-Provider Support (Future)

The architecture supports multiple providers simultaneously:

```python
# In main.py startup
providers = [
    create_tool_provider("mcp"),
    create_tool_provider("openai_functions"),
]
# Generate tools from all providers
```

## Best Practices

1. **Use Environment Variables**: Never hardcode credentials
2. **Separate Workspaces**: Each employee should have their own workspace
3. **Monitor Token Usage**: Check UI charts for token consumption
4. **Test Tool Discovery**: Verify tools are discovered on startup
5. **Enable Privacy Tokenization**: Protect sensitive data
6. **Use Code Execution Mode**: For better token efficiency (98.7% savings)

## Support

- Check `DEMO_GUIDE.md` for usage examples
- Review `ARCHITECTURE_GENERIC_DESIGN.md` for architecture details
- See backend logs for detailed error messages
- Check `ENV_SETUP.md` for environment variable reference


# Generic Agent with Code Execution

A **production-ready, generic agent framework** implementing the [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) pattern from Anthropic's blog post.

## 🎯 Key Features

- **🔌 Generic Architecture**: Connect to **any MCP server** or tool provider (extensible to OpenAI Functions, REST APIs, etc.)
- **💻 Code Execution**: Agent writes code to interact with tools (98.7% token savings)
- **📁 Progressive Disclosure**: Tools discovered on-demand via filesystem exploration
- **🔒 Privacy-Preserving**: Automatic PII tokenization before data reaches the model
- **💾 State Persistence**: Agents can save and reuse code as skills
- **🏗️ SOLID Principles**: Clean, maintainable, extensible architecture
- **👥 Multi-Employee Ready**: Suitable for sharing with 100s of employees

## Architecture

This agent uses a **provider-agnostic architecture** that allows you to:

- **Connect to any tool source**: MCP servers, OpenAI Functions, REST APIs (extensible)
- **Switch providers easily**: Just change `TOOL_PROVIDER` environment variable
- **Add custom providers**: Implement `ToolProvider` interface (see `providers/base.py`)
- **Maintain clean separation**: Core logic independent of tool protocol

See [ARCHITECTURE_GENERIC_DESIGN.md](ARCHITECTURE_GENERIC_DESIGN.md) for detailed architecture documentation.

## Overview

The blog post describes how agents can interact with MCP servers more efficiently by:
1. **Before (Direct Tool Calls)**: Loading all tool definitions upfront and passing intermediate results through the model context → **High token usage**
2. **After (Code Execution)**: Presenting tools as code APIs, allowing agents to write code that discovers tools on-demand and processes data in execution environment → **Low token usage** (98.7% reduction)

## Implementation Status

### ✅ Fully Implemented - Filesystem-Based Code Execution

This demo now **fully implements** the filesystem-based code execution pattern from the blog post:

- **`prompt_tools` (Before Pattern)**: 
  - Direct tool calls with full data in prompt
  - Loads all tool descriptions into model context
  - Sends full data blobs through the model
  - **Result**: High token consumption (e.g., 150,000+ tokens)

- **`code_exec` (After Pattern - Full Implementation)**:
  - ✅ **Filesystem-Based Tool Discovery**: Tools generated as Python files in `workspace/servers/{server-name}/`
  - ✅ **Agent Code Generation**: Agent writes Python code to interact with tools
  - ✅ **Code Execution Environment**: Sandboxed Python execution for agent-generated code
  - ✅ **Progressive Disclosure**: Agent explores filesystem to discover tools on-demand
  - ✅ **State Persistence**: Workspace directory maintains state across executions
  - **Result**: Low token consumption (e.g., 2,000 tokens - 98.7% reduction)

## Components

- **ui/**: Streamlit chat UI with a toggle to switch between execution modes and a live token chart.
- **backend/**: FastAPI service with MCP client and filesystem-based code execution:
  - `prompt_tools`: Direct tool calls - loads tool descriptions & full data into model context (high tokens).
  - `code_exec`: Filesystem-based code execution - agent generates Python code, tools discovered via filesystem, data processed in execution environment (low tokens).
  - **Tool Generator**: Discovers MCP tools and generates Python files in `workspace/servers/`
  - **Code Executor**: Sandboxed Python execution environment for agent-generated code
- **mcp_server/**: Python MCP server exposing two tools:
  - `get_transcript(topic: str, words: int)` – returns a large text blob.
  - `update_crm(record_id: str, note: str)` – dummy side‑effect tool.

## Quickstart

### For Employees: Setting Up Your Own Agent

**See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup instructions.**

Quick setup:

1. **Configure your tool provider** (edit `.env`):
   ```bash
   TOOL_PROVIDER=mcp
   MCP_ENDPOINT=http://your-mcp-server:8974/mcp
   MCP_SERVER_NAME=your_server_name
   ANTHROPIC_API_KEY=sk-ant-...
   ```

2. **Start services**:
   ```bash
   docker-compose up --build
   ```

3. **Access your agent**:
   - UI: http://localhost:8501
   - Backend API: http://localhost:8000

### Option 1: Docker (Recommended)

1. **Set environment variables** (optional, for live LLM):
   ```bash
   # For Anthropic (local)
   export ANTHROPIC_API_KEY="sk-ant-..."
   
   # OR for Azure OpenAI (office)
   export AZURE_API_KEY="your-key"
   export AZURE_API_BASE="https://your-resource.openai.azure.com"
   ```

2. **Build and run all services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - UI: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MCP Server: http://localhost:8974/mcp

### Option 2: Local Development

1. Create a virtualenv and install deps (Python 3.10+ recommended):

   ```bash
   uv venv || python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start MCP server (terminal A):

   ```bash
   python mcp_server/server.py
   ```

   It will listen on Streamable HTTP at `http://127.0.0.1:8974/mcp`.

3. Start backend (terminal B):

   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

4. Start UI (terminal C):

   ```bash
   streamlit run ui/app.py
   ```

5. Open Streamlit URL printed in the console. Use the toggle to compare `prompt_tools` vs `code_exec` and watch the token chart.

> **Notes**
> - By default we simulate LLM responses (no API keys required) while accurately *estimating* tokens with `tiktoken`. 
> - Set `ANTHROPIC_API_KEY` (for Claude) or `AZURE_API_KEY` + `AZURE_API_BASE` (for Azure OpenAI) to use live LLMs. See `ENV_SETUP.md` for details.
> - This is a **demo** focused on token mechanics & architecture, not production security. If you enable live LLMs, add proper secrets management, rate limiting, telemetry, etc.
> - **Tool files are auto-generated** on backend startup in `workspace/servers/demo_mcp/` directory.

## What to Look For

### Before (Direct Tool Calls) - `prompt_tools` Mode
- All tool definitions loaded upfront into model context
- Full data blobs (large transcripts) passed through model
- Intermediate results consume additional tokens
- **Token Usage**: High (e.g., 150,000+ tokens for large datasets)

### After (Code Execution) - `code_exec` Mode  
- Data preprocessing happens in code execution environment
- Only compact summaries sent to model
- Large data stays in execution environment
- **Token Usage**: Low (e.g., 2,000 tokens - 98.7% reduction)

### Comparison Example

**Direct Tool Call Approach (Before)**:
```
TOOL CALL: get_transcript(topic: "Q4 sales", words: 3000)
→ Returns: "Full 3000-word transcript..." (loaded into model context)

TOOL CALL: update_crm(record_id: "123", note: "Full 3000-word transcript...")
→ Model must write entire transcript again into context
```

**Code Execution Approach (After)**:
```python
# Agent-generated code (executed in sandbox)
from servers.demo_mcp import get_transcript, update_crm

transcript = await get_transcript(topic="Q4 sales", words=3000)
summary = summarize(transcript)  # Process in execution environment
await update_crm(record_id="123", note=summary)
# Only summary sent to model, not full transcript
```

## How It Works

### Filesystem-Based Code Execution Flow

1. **Tool Discovery** (on backend startup):
   - Backend discovers MCP tools via `list_tools()`
   - Generates Python files: `workspace/servers/demo_mcp/get_transcript.py`, `update_crm.py`
   - Creates `__init__.py` with exports for easy imports

2. **Agent Code Generation** (when toggle is ON):
   - Agent receives filesystem structure info
   - Generates Python code like:
     ```python
     from servers.demo_mcp import get_transcript
     from mcp.types import TextContent
     
     result = await get_transcript(topic="Q4 sales", words=200)
     text = "".join(item.text for item in result.content if isinstance(item, TextContent))
     # Process in code...
     _result = {"summary": "..."}
     ```

3. **Code Execution**:
   - Generated code executed in sandboxed environment
   - Large data processing happens in code (not in prompt)
   - Only summaries/processed results sent to LLM

4. **Token Efficiency**:
   - Progressive disclosure: Agent only sees tool signatures, not full data
   - Code execution: Data processing in execution environment
   - Context efficiency: Only processed results go back to model

## Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)**: Complete setup guide for employees
- **[ARCHITECTURE_GENERIC_DESIGN.md](ARCHITECTURE_GENERIC_DESIGN.md)**: Architecture details and design patterns
- **[ENV_SETUP.md](ENV_SETUP.md)**: Environment variable reference
- **[DEMO_GUIDE.md](DEMO_GUIDE.md)**: Usage examples and demo scenarios

## Reference

- [Blog Post: Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)

## Features

- ✅ Filesystem-based tool discovery (progressive disclosure)
- ✅ Sandboxed code execution environment
- ✅ Privacy-preserving tokenization (PII detection)
- ✅ Search tools with detail levels
- ✅ State persistence and skills directory
- ✅ Tool generation verification
- ✅ Enhanced error messages and debugging

## License
Apache-2.0 for demo code (inherits licenses of deps).

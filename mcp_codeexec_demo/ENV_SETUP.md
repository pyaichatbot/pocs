# Environment Variables Setup

## LLM Provider Configuration

The backend supports three LLM providers with automatic detection:

### 1. Anthropic (Claude) - Local Development

Set the following environment variable:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Default Model**: `claude-sonnet-4-20250514`

**Override Model**:
```bash
export MODEL_ID="claude-3-opus-20240229"
```

**Priority**: Highest - if `ANTHROPIC_API_KEY` is set, Anthropic will be used.

### 2. Azure OpenAI - Office/Production

Set the following environment variables:

```bash
export AZURE_API_KEY="your-azure-key"
export AZURE_API_BASE="https://your-resource.openai.azure.com"
export AZURE_API_VERSION="2024-02-15-preview"  # Optional, defaults to 2024-02-15-preview
```

**Alternative**: You can also use `OPENAI_API_KEY` instead of `AZURE_API_KEY` if `AZURE_API_BASE` is set.

**Default Model**: `azure/gpt-4o-mini` (automatically prefixed with `azure/`)

**Override Model**:
```bash
export MODEL_ID="gpt-4o"  # Will become azure/gpt-4o
# Or explicitly:
export MODEL_ID="azure/gpt-4o"
```

### 3. Standard OpenAI

Set the following environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

**Note**: Only used if `AZURE_API_BASE` is NOT set.

**Default Model**: `gpt-4o-mini`

**Override Model**:
```bash
export MODEL_ID="gpt-4o"
```

## Provider Detection Priority

1. **Anthropic** - If `ANTHROPIC_API_KEY` is set
2. **Azure OpenAI** - If `AZURE_API_KEY` (or `OPENAI_API_KEY`) + `AZURE_API_BASE` are set
3. **Standard OpenAI** - If `OPENAI_API_KEY` is set (without `AZURE_API_BASE`)
4. **Stubbed** - If no provider is detected

## Example Configurations

### Local Development (Anthropic)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export MCP_ENDPOINT="http://127.0.0.1:8974/mcp"
```

### Office/Production (Azure OpenAI)
```bash
export AZURE_API_KEY="your-azure-key"
export AZURE_API_BASE="https://your-resource.openai.azure.com"
export MODEL_ID="gpt-4o"  # Optional
export MCP_ENDPOINT="http://mcp:8974/mcp"  # Docker service name
```

### Using .env File

Create a `.env` file in the project root:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
MCP_ENDPOINT=http://127.0.0.1:8974/mcp
MODEL_ID=claude-sonnet-4-20250514
```

Or for Azure:

```bash
# .env
AZURE_API_KEY=your-azure-key
AZURE_API_BASE=https://your-resource.openai.azure.com
AZURE_API_VERSION=2024-02-15-preview
MODEL_ID=gpt-4o
MCP_ENDPOINT=http://mcp:8974/mcp
```

## Verification

When you start the backend, you should see:

```
✅ LLM Provider: anthropic
✅ Model: claude-sonnet-4-20250514
```

Or for Azure:

```
✅ LLM Provider: azure
✅ Model: azure/gpt-4o-mini
✅ Azure API Base: https://your-resource.openai.azure.com
```

If no provider is detected:

```
⚠️  No LLM provider detected - using stubbed responses
   Set ANTHROPIC_API_KEY (for Anthropic) or AZURE_API_KEY + AZURE_API_BASE (for Azure OpenAI)
```

## Response Format

The API response now includes provider information:

```json
{
  "reply": "...",
  "tokens_prompt": 1234,
  "tokens_output": 567,
  "mode": "code_exec",
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "debug": {
    "strategy": "code_exec_preprocess",
    "summary_chars": 150,
    "live_llm": true
  }
}
```


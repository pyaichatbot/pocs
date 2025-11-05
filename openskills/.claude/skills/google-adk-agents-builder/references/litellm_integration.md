# LiteLLM Integration Guide

## Overview

LiteLLM provides a unified interface to access over 100 different Large Language Models (LLMs) through a single API. When using Google ADK, LiteLLM enables you to use models from various providers (Azure OpenAI, Anthropic Claude, OpenAI, Cohere, etc.) alongside or instead of Google's Gemini models.

## Why Use LiteLLM with ADK?

**Benefits:**
- **Multi-Model Flexibility**: Choose the best model for each task (cost, performance, capabilities)
- **Provider Agnostic**: Switch between providers without changing your agent code
- **Unified Interface**: Same API for all models, simplifying development
- **Cost Optimization**: Use different models for different tasks based on cost/performance trade-offs
- **Fallback Support**: Easily implement fallback logic if one provider is unavailable

## Installation

### Basic Installation

```bash
pip install litellm
```

### With ADK

```bash
pip install google-adk litellm
```

## Basic Usage

### Using LiteLLM with ADK Agents

Replace the standard `GeminiModel` with `LiteLlm`:

```python
from google.adk import LLMAgent
from google.adk.models.lite_llm import LiteLlm

# Create agent with LiteLLM model
model = LiteLlm(model="gpt-4o")  # OpenAI GPT-4o

agent = LLMAgent(
    model=model,
    system_instruction="You are a helpful assistant."
)
```

### Model Identifiers

LiteLLM uses standardized model identifiers. Common formats:

**OpenAI:**
- `gpt-4o` - GPT-4 Omni
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-3.5-turbo` - GPT-3.5 Turbo

**Anthropic Claude:**
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet
- `claude-3-opus-20240229` - Claude 3 Opus
- `claude-3-5-haiku-20241022` - Claude 3.5 Haiku

**Azure OpenAI:**
- `azure/gpt-4o` - Azure GPT-4 Omni
- `azure/gpt-4-turbo` - Azure GPT-4 Turbo
- `azure/gpt-35-turbo` - Azure GPT-3.5 Turbo

**Google Gemini (via LiteLLM):**
- `gemini/gemini-2.0-flash-exp`
- `gemini/gemini-1.5-pro`
- `gemini/gemini-1.5-flash`

**Cohere:**
- `command-r-plus`
- `command-r`

**Mistral:**
- `mistral-large-latest`
- `mistral-medium-latest`

## Configuration

### API Keys

Set API keys as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# Azure OpenAI
export AZURE_API_KEY="your-azure-key"
export AZURE_API_BASE="https://your-resource.openai.azure.com/"
```

Or configure programmatically:

```python
import os
os.environ["OPENAI_API_KEY"] = "your-openai-key"
os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-key"
```

### Azure OpenAI Configuration

For Azure OpenAI, additional configuration is needed:

```python
from google.adk.models.lite_llm import LiteLlm

model = LiteLlm(
    model="azure/gpt-4o",
    api_key="your-azure-key",
    api_base="https://your-resource.openai.azure.com/",
    api_version="2024-02-15-preview"
)
```

Or via environment variables:

```bash
export AZURE_API_KEY="your-azure-key"
export AZURE_API_BASE="https://your-resource.openai.azure.com/"
export AZURE_API_VERSION="2024-02-15-preview"
```

### Model Parameters

Configure model parameters:

```python
from google.adk.models.lite_llm import LiteLlm

model = LiteLlm(
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2048,
    top_p=0.9
)

agent = LLMAgent(model=model)
```

## Multi-Model Agents

### Dynamic Model Selection

Switch models based on task requirements:

```python
from google.adk import LLMAgent
from google.adk.models.lite_llm import LiteLlm

def create_agent_for_task(task_type: str):
    """Create agent with appropriate model for task."""
    if task_type == "complex":
        model = LiteLlm(model="claude-3-5-sonnet-20241022")
    elif task_type == "fast":
        model = LiteLlm(model="gpt-3.5-turbo")
    else:
        model = LiteLlm(model="gpt-4o")
    
    return LLMAgent(
        model=model,
        system_instruction="You are a helpful assistant."
    )
```

### Agent Teams with Different Models

Create specialized agents using different models:

```python
from google.adk import LLMAgent
from google.adk.models.lite_llm import LiteLlm

# Complex reasoning agent with Claude
reasoning_agent = LLMAgent(
    model=LiteLlm(model="claude-3-5-sonnet-20241022"),
    name="reasoning_agent",
    description="Handles complex reasoning tasks",
    system_instruction="You excel at complex reasoning and analysis."
)

# Fast response agent with GPT-3.5
fast_agent = LLMAgent(
    model=LiteLlm(model="gpt-3.5-turbo"),
    name="fast_agent",
    description="Provides quick responses",
    system_instruction="You provide fast, concise responses."
)

# Creative agent with GPT-4
creative_agent = LLMAgent(
    model=LiteLlm(model="gpt-4o"),
    name="creative_agent",
    description="Handles creative tasks",
    system_instruction="You are creative and imaginative."
)
```

## Advanced Configuration

### Custom API Base URLs

For custom deployments or proxies:

```python
model = LiteLlm(
    model="gpt-4o",
    api_base="https://custom-api-endpoint.com/v1"
)
```

### Request Timeout

Configure timeout settings:

```python
model = LiteLlm(
    model="gpt-4o",
    timeout=60  # seconds
)
```

### Retry Logic

Configure retry behavior:

```python
model = LiteLlm(
    model="gpt-4o",
    num_retries=3,
    retry_delay=1.0
)
```

## Error Handling

### Handling Provider Errors

```python
from google.adk import LLMAgent
from google.adk.models.lite_llm import LiteLlm
from litellm import RateLimitError, APIError

model = LiteLlm(model="gpt-4o")
agent = LLMAgent(model=model)

try:
    response = agent.run("Hello")
except RateLimitError:
    # Handle rate limit - switch to different model or retry later
    fallback_model = LiteLlm(model="gpt-3.5-turbo")
    fallback_agent = LLMAgent(model=fallback_model)
    response = fallback_agent.run("Hello")
except APIError as e:
    # Handle API errors
    print(f"API Error: {e}")
```

## Best Practices

### 1. Model Selection Strategy

Choose models based on:
- **Task Complexity**: Complex tasks → Claude/GPT-4, Simple tasks → GPT-3.5
- **Cost**: Use cheaper models for high-volume simple tasks
- **Latency**: Use faster models for real-time applications
- **Capabilities**: Use specialized models for specific domains

### 2. Environment Configuration

Store API keys securely:

```python
# Use environment variables or secret management
import os
from google.cloud import secretmanager

def get_api_key(provider: str):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{provider}-api-key/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Set keys
os.environ["OPENAI_API_KEY"] = get_api_key("openai")
os.environ["ANTHROPIC_API_KEY"] = get_api_key("anthropic")
```

### 3. Fallback Mechanisms

Implement fallback logic:

```python
def create_agent_with_fallback():
    """Create agent with fallback model."""
    primary_model = LiteLlm(model="gpt-4o")
    fallback_model = LiteLlm(model="gpt-3.5-turbo")
    
    agent = LLMAgent(model=primary_model)
    
    # Add fallback logic in error handling
    return agent, fallback_model
```

### 4. Cost Monitoring

Monitor usage and costs:

```python
from litellm import completion

# LiteLLM tracks usage automatically
response = completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)

# Access usage information
print(response.usage)  # Contains token usage and cost
```

## Comparison: Native Gemini vs LiteLLM

### When to Use Native GeminiModel

- You're fully committed to Google's ecosystem
- You need Google-specific features
- You want optimal performance with Gemini
- You're using Google Cloud authentication

### When to Use LiteLLM

- You need multi-provider support
- You want to compare models across providers
- You need cost optimization across providers
- You want provider-agnostic code
- You need fallback mechanisms

## Complete Example

### Multi-Model Weather Agent

```python
from google.adk import LLMAgent, Tool
from google.adk.models.lite_llm import LiteLlm

@Tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    # Implementation
    return f"Weather in {location}: Sunny, 72°F"

# Create agent with Claude for complex reasoning
agent = LLMAgent(
    model=LiteLlm(model="claude-3-5-sonnet-20241022"),
    system_instruction="""
    You are a weather assistant that provides detailed weather analysis.
    Use the get_weather tool to fetch current conditions.
    """,
    tools=[get_weather]
)

# Use agent
response = agent.run("What's the weather in San Francisco and provide a detailed analysis?")
print(response)
```

## Troubleshooting

### Common Issues

**1. API Key Not Found:**
```
Error: No API key provided
```
Solution: Set environment variable or pass `api_key` parameter

**2. Model Not Found:**
```
Error: Model 'xyz' not found
```
Solution: Check model identifier format (provider/model-name)

**3. Rate Limits:**
```
Error: Rate limit exceeded
```
Solution: Implement retry logic or switch to different model

**4. Azure Configuration:**
```
Error: Azure API configuration incomplete
```
Solution: Ensure `api_base`, `api_key`, and `api_version` are set

## References

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [ADK Agent Team Tutorial](https://google.github.io/adk-docs/tutorials/agent-team/#step-2-going-multi-model-with-litellm-optional)
- [LiteLLM Supported Models](https://docs.litellm.ai/docs/providers)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)


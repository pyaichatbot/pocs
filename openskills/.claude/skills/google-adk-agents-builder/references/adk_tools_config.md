# ADK Tools and Configuration

## Overview

This guide covers tools, memory, sessions, context management, and agent configuration in Google ADK.

## Tools

### Function Tools

Function tools are Python functions that agents can call:

```python
from google.adk import Tool

@Tool
def get_weather(location: str) -> str:
    """
    Get current weather for a location.
    
    Args:
        location: City name or location identifier
        
    Returns:
        Weather description string
    """
    # Implementation
    return f"Weather in {location}: Sunny, 72°F"
```

**Tool Requirements:**
- Type annotations for parameters
- Return type annotation
- Descriptive docstring
- Clear parameter descriptions

### Tool Registration

Register tools with agents:

```python
from google.adk import LLMAgent

agent = LLMAgent(
    tools=[get_weather, calculator, search_web]
)
```

### Tool Categories

**Built-in Tools:**
- Google Search
- Code execution
- File operations
- Database queries

**Custom Tools:**
- API integrations
- Business logic
- Domain-specific operations

**Third-party Tools:**
- MCP tools
- OpenAPI tools
- Custom integrations

### Tool Best Practices

1. **Clear Descriptions**: Tools should have clear, descriptive docstrings
2. **Parameter Validation**: Validate inputs before processing
3. **Error Handling**: Return meaningful error messages
4. **Idempotency**: Design tools to be idempotent when possible
5. **Type Safety**: Use type hints throughout

## Memory and Sessions

### Sessions

Sessions maintain conversation context:

```python
from google.adk import Session

session = Session(
    session_id="user-123",
    max_history=100
)

agent = LLMAgent(
    session=session
)
```

**Session Features:**
- Conversation history
- User preferences
- Context retention
- State management

### Memory

Memory provides persistent storage:

```python
from google.adk import Memory

memory = Memory(
    persistence=True,
    storage_backend="database"
)

agent = LLMAgent(
    memory=memory
)
```

**Memory Types:**
- **Episodic**: Store specific events
- **Semantic**: Store general knowledge
- **Working**: Temporary context

### Context Management

**Context Caching:**
```python
from google.adk import ContextCache

cache = ContextCache(
    max_size=1000,
    ttl=3600
)

agent = LLMAgent(
    context_cache=cache
)
```

**Context Compression:**
- Summarize long contexts
- Extract key information
- Reduce token usage
- Maintain quality

## Agent Configuration

### Model Configuration

```python
from google.adk.models import GeminiModel

model = GeminiModel(
    model_name="gemini-2.0-flash-exp",
    temperature=0.7,
    max_tokens=2048,
    top_p=0.9
)

agent = LLMAgent(model=model)
```

**Model Parameters:**
- `model_name`: Model identifier
- `temperature`: Creativity (0.0-1.0)
- `max_tokens`: Maximum response length
- `top_p`: Nucleus sampling parameter

### System Instructions

Define agent behavior:

```python
system_instruction = """
You are a helpful assistant specialized in:
- Answering technical questions
- Providing code examples
- Explaining complex concepts

Guidelines:
- Be concise and accurate
- Use tools when needed
- Provide examples when helpful
"""

agent = LLMAgent(
    system_instruction=system_instruction
)
```

### Safety Settings

Configure safety filters:

```python
from google.adk.safety import SafetySettings

safety = SafetySettings(
    block_harmful_content=True,
    block_unsafe_code=True
)

agent = LLMAgent(safety_settings=safety)
```

### Agent Config File

Use YAML configuration:

```yaml
agent:
  model:
    name: "gemini-2.0-flash-exp"
    temperature: 0.7
  tools:
    - get_weather
    - calculator
  memory:
    enabled: true
    max_history: 100
  system_instruction: "You are a helpful assistant."
```

Load configuration:

```python
from google.adk.config import load_config

config = load_config("agent_config.yaml")
agent = LLMAgent.from_config(config)
```

## Advanced Configuration

### Custom Tool Wrappers

Wrap existing functions:

```python
from google.adk import Tool

def existing_function(data):
    # Existing implementation
    pass

# Wrap as tool
tool = Tool(
    func=existing_function,
    name="custom_tool",
    description="Custom tool description"
)
```

### Tool Composition

Combine tools:

```python
@Tool
def complex_operation(data: str) -> str:
    """Complex operation using multiple tools."""
    result1 = tool1(data)
    result2 = tool2(result1)
    return tool3(result2)
```

### Dynamic Tool Loading

Load tools dynamically:

```python
import importlib

def load_tool(module_name, tool_name):
    module = importlib.import_module(module_name)
    return getattr(module, tool_name)

tool = load_tool("tools", "get_weather")
agent = LLMAgent(tools=[tool])
```

## Performance Optimization

### Context Caching

Cache frequently accessed contexts:

```python
cache = ContextCache(
    max_size=1000,
    eviction_policy="lru"
)
```

### Memory Optimization

Optimize memory usage:

```python
memory = Memory(
    compression=True,
    max_size=10000
)
```

### Tool Optimization

Optimize tool performance:

```python
@Tool
@cache_result(ttl=3600)
def expensive_operation(data: str) -> str:
    """Expensive operation with caching."""
    # Implementation
    pass
```

## References

- ADK Tools Documentation: https://google.github.io/adk-docs/tools/
- ADK Configuration: https://google.github.io/adk-docs/agents/agent-config/


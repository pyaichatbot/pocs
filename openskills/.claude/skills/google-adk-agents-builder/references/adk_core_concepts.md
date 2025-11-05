# ADK Core Concepts

## Overview

Google's Agent Development Kit (ADK) is a comprehensive framework for building autonomous AI agents. This document covers the core architectural concepts, components, and patterns used in ADK.

## Architecture

### BaseAgent

The `BaseAgent` class is the foundational class that all agents extend. It provides:

- **Core execution framework**: Handles agent lifecycle and execution
- **Tool integration**: Manages tool registration and invocation
- **Memory management**: Handles agent state and context
- **Error handling**: Provides consistent error management

### Agent Types

#### LLM Agents

LLM agents utilize Large Language Models for natural language understanding and generation:

```python
from google.adk import LLMAgent
from google.adk.models import GeminiModel

agent = LLMAgent(
    model=GeminiModel(model_name="gemini-2.0-flash-exp"),
    system_instruction="You are a helpful assistant."
)
```

**Characteristics:**
- Natural language interaction
- Context-aware responses
- Tool usage for extended capabilities
- Memory for conversation continuity

#### Workflow Agents

Workflow agents manage structured processes:

**Sequential Workflows:**
- Execute tasks in order
- Each task depends on previous completion
- Use for linear processes

**Parallel Workflows:**
- Execute multiple tasks simultaneously
- Independent task execution
- Use for concurrent operations

**Loop Workflows:**
- Repeat tasks until condition met
- Conditional iteration
- Use for iterative processes

#### Custom Agents

Custom agents extend `BaseAgent` for specialized logic:

```python
from google.adk import BaseAgent

class CustomAgent(BaseAgent):
    def run(self, input_data):
        # Custom implementation
        pass
```

## Components

### Tools

Tools extend agent capabilities:

**Function Tools:**
```python
from google.adk import Tool

@Tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implementation
    pass
```

**Tool Characteristics:**
- Modular and reusable
- Type-safe parameters
- Clear descriptions
- Error handling

### Memory and Sessions

**Sessions:**
- Maintain conversation context
- Store user preferences
- Track agent state

**Memory:**
- Persistent storage across sessions
- Knowledge retention
- Context caching

**Context Management:**
- Efficient context usage
- Context compression
- Context caching strategies

### Models

ADK supports various LLM models through native Gemini models and LiteLLM integration:

**Native Gemini Models:**
- `gemini-2.0-flash-exp`: Fast, efficient
- `gemini-1.5-pro`: High capability
- `gemini-1.5-flash`: Balanced performance

**Multi-Model Support via LiteLLM:**
ADK supports using other LLM providers through LiteLLM integration:
- **OpenAI**: GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **Azure OpenAI**: Azure GPT-4, Azure GPT-3.5
- **Cohere**: Command R+, Command R
- **Mistral**: Mistral Large, Mistral Medium
- And 100+ other models

See [LiteLLM Integration Guide](./litellm_integration.md) for details.

**Model Configuration:**
- Temperature settings
- Token limits
- Safety settings
- Response formatting

## Agent Configuration

### System Instructions

Define agent behavior and capabilities:

```python
system_instruction = """
You are a helpful assistant that:
- Answers questions accurately
- Uses tools when needed
- Provides clear explanations
"""
```

### Tool Registration

Register tools with agents:

```python
agent = LLMAgent(
    tools=[search_tool, calculator_tool, weather_tool]
)
```

### Memory Configuration

Configure memory settings:

```python
agent = LLMAgent(
    memory=MemoryConfig(
        max_history=100,
        persistence=True
    )
)
```

## Patterns and Best Practices

### Agent Design Principles

1. **Single Responsibility**: Each agent should have a clear purpose
2. **Tool Composition**: Build complex capabilities from simple tools
3. **Error Handling**: Graceful degradation and clear error messages
4. **Context Efficiency**: Minimize context usage while maintaining quality

### State Management

- Use sessions for conversation state
- Use memory for persistent knowledge
- Cache frequently accessed data
- Compress context when needed

### Tool Design

- Provide clear descriptions
- Validate inputs
- Handle errors gracefully
- Return structured data

## Multi-Agent Systems

### Agent Hierarchies

Organize agents in hierarchical structures:
- Root agents coordinate sub-agents
- Specialized agents handle specific tasks
- Clear delegation patterns

### Agent Communication

- Use A2A Protocol for inter-agent communication
- Define clear interfaces
- Handle asynchronous operations
- Manage agent discovery

## References

- ADK Documentation: https://google.github.io/adk-docs/
- ADK Samples: https://github.com/google/adk-samples/tree/main/python/agents


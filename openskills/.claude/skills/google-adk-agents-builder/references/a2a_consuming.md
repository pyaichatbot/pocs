# A2A Consuming Guide

## Overview

This guide covers consuming remote agents via the A2A Protocol from your ADK agents.

## Basic Client Setup

### Simple Client

```python
from a2a_sdk import AgentClient

# Connect to remote agent
client = AgentClient(endpoint="http://remote-agent:8080")

# Use remote agent
response = client.run("What is the weather?")
```

### Client with Configuration

```python
from a2a_sdk import AgentClient, ClientConfig

config = ClientConfig(
    timeout=30,
    retry_attempts=3,
    retry_delay=1.0
)

client = AgentClient(
    endpoint="http://remote-agent:8080",
    config=config
)
```

## Using Remote Agents as Tools

### Register as Tool

```python
from google.adk import LLMAgent, Tool
from a2a_sdk import AgentClient

# Create client for remote agent
remote_agent = AgentClient(endpoint="http://weather-agent:8080")

@Tool
def get_weather(location: str) -> str:
    """Get weather from remote weather agent."""
    query = f"What is the weather in {location}?"
    return remote_agent.run(query)

# Use in local agent
agent = LLMAgent(tools=[get_weather])
```

### Async Tool Usage

```python
from google.adk import Tool
from a2a_sdk import AsyncAgentClient
import asyncio

remote_agent = AsyncAgentClient(endpoint="http://remote-agent:8080")

@Tool
async def async_remote_tool(query: str) -> str:
    """Async remote agent call."""
    return await remote_agent.run_async(query)
```

## Agent Discovery

### Static Discovery

```python
from a2a_sdk import AgentClient

# Define known agents
agents = {
    "weather": AgentClient("http://weather-agent:8080"),
    "search": AgentClient("http://search-agent:8080"),
    "calculator": AgentClient("http://calc-agent:8080")
}

# Use specific agent
weather = agents["weather"]
response = weather.run("What's the weather?")
```

### Dynamic Discovery

```python
from a2a_sdk.discovery import ServiceRegistry

registry = ServiceRegistry(endpoint="http://registry:8500")

# Discover agents
agents = registry.discover("agent-type")

# Use discovered agent
agent_client = AgentClient(endpoint=agents[0]["endpoint"])
response = agent_client.run("Query")
```

### Service Registry Integration

```python
from a2a_sdk.discovery import ServiceRegistry

registry = ServiceRegistry(endpoint="http://consul:8500")

def get_agent(service_name: str):
    services = registry.discover(service_name)
    if services:
        return AgentClient(endpoint=services[0]["endpoint"])
    return None

# Use discovered agent
weather_agent = get_agent("weather-service")
if weather_agent:
    response = weather_agent.run("Query")
```

## Authentication

### API Key Authentication

```python
from a2a_sdk import AgentClient

client = AgentClient(
    endpoint="http://remote-agent:8080",
    api_key="your-api-key"
)
```

### OAuth Authentication

```python
from a2a_sdk import AgentClient

client = AgentClient(
    endpoint="http://remote-agent:8080",
    oauth_token="your-oauth-token"
)
```

## Error Handling

### Retry Logic

```python
from a2a_sdk import AgentClient
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_agent_with_retry(client, query):
    return client.run(query)

client = AgentClient(endpoint="http://remote-agent:8080")
response = call_agent_with_retry(client, "Query")
```

### Error Handling

```python
from a2a_sdk import AgentClient
from a2a_sdk.exceptions import AgentConnectionError, AgentTimeoutError

client = AgentClient(endpoint="http://remote-agent:8080")

try:
    response = client.run("Query")
except AgentConnectionError:
    # Handle connection error
    response = "Connection failed, using fallback"
except AgentTimeoutError:
    # Handle timeout
    response = "Request timed out, using fallback"
except Exception as e:
    # Handle other errors
    response = f"Error: {str(e)}"
```

## Streaming Responses

### Streaming Client

```python
from a2a_sdk import AgentClient

client = AgentClient(endpoint="http://remote-agent:8080")

# Stream response
for chunk in client.stream("Long query"):
    print(chunk, end="", flush=True)
```

### Async Streaming

```python
from a2a_sdk import AsyncAgentClient

client = AsyncAgentClient(endpoint="http://remote-agent:8080")

async def stream_response(query):
    async for chunk in client.stream_async(query):
        print(chunk)

# Use
import asyncio
asyncio.run(stream_response("Query"))
```

## Multi-Agent Orchestration

### Orchestrator Pattern

```python
from google.adk import BaseAgent
from a2a_sdk import AgentClient

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        self.weather_agent = AgentClient("http://weather:8080")
        self.search_agent = AgentClient("http://search:8080")
        self.calc_agent = AgentClient("http://calc:8080")
    
    def run(self, query):
        # Route to appropriate agent
        if "weather" in query.lower():
            return self.weather_agent.run(query)
        elif "calculate" in query.lower():
            return self.calc_agent.run(query)
        else:
            return self.search_agent.run(query)
```

### Parallel Agent Calls

```python
from a2a_sdk import AgentClient
import asyncio

async def call_multiple_agents(query):
    agents = [
        AgentClient("http://agent1:8080"),
        AgentClient("http://agent2:8080"),
        AgentClient("http://agent3:8080")
    ]
    
    # Call all agents in parallel
    results = await asyncio.gather(*[
        agent.run_async(query) for agent in agents
    ])
    
    return results
```

## Best Practices

1. **Connection Pooling**: Reuse client connections
2. **Timeout Configuration**: Set appropriate timeouts
3. **Error Handling**: Handle all error scenarios
4. **Retry Logic**: Implement retry for resilience
5. **Monitoring**: Track agent usage and performance
6. **Caching**: Cache responses when appropriate
7. **Load Balancing**: Distribute requests across agents

## References

- A2A Protocol: https://a2a-protocol.org/
- A2A Python SDK: https://github.com/a2aproject/a2a-python


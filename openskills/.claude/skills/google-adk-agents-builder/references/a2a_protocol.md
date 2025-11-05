# A2A Protocol Guide

## Overview

The Agent2Agent (A2A) Protocol enables secure and efficient communication between AI agents. This guide covers A2A integration, communication patterns, and best practices.

## A2A Protocol Fundamentals

### What is A2A?

A2A is a protocol that enables:
- **Agent Discovery**: Agents can discover and connect to other agents
- **Task Delegation**: Agents can delegate tasks to other agents
- **Secure Communication**: Encrypted and authenticated agent communication
- **Multi-Agent Orchestration**: Coordinate complex multi-agent workflows

### Key Concepts

**A2A Server:**
- Exposes an agent for use by other agents
- Handles incoming requests
- Manages agent capabilities

**A2A Client:**
- Connects to remote agents
- Sends requests to remote agents
- Handles responses

**Agent Discovery:**
- Mechanisms for finding available agents
- Service registry integration
- Dynamic agent discovery

## A2A Python SDK

### Installation

```bash
# Core SDK
pip install a2a-sdk

# With all features
pip install "a2a-sdk[all]"

# Specific features
pip install "a2a-sdk[http-server]"  # HTTP server
pip install "a2a-sdk[grpc]"          # gRPC support
pip install "a2a-sdk[telemetry]"     # OpenTelemetry
pip install "a2a-sdk[encryption]"   # Encryption
```

### Basic Usage

**Creating an A2A Server:**

```python
from a2a_sdk import AgentServer
from google.adk import LLMAgent

# Create your agent
agent = LLMAgent(...)

# Create A2A server
server = AgentServer(agent)

# Start server
server.run(host="0.0.0.0", port=8080)
```

**Creating an A2A Client:**

```python
from a2a_sdk import AgentClient

# Connect to remote agent
client = AgentClient(endpoint="http://remote-agent:8080")

# Use remote agent
response = client.run("What is the weather?")
```

## Integration with ADK

### Exposing ADK Agents via A2A

To make an ADK agent available via A2A:

```python
from google.adk import LLMAgent
from a2a_sdk import AgentServer

# Create ADK agent
agent = LLMAgent(
    model=GeminiModel(),
    tools=[...]
)

# Wrap in A2A server
server = AgentServer(agent)
server.run()
```

### Using Remote Agents as Tools

Register remote A2A agents as tools:

```python
from google.adk import LLMAgent, Tool
from a2a_sdk import AgentClient

# Create client for remote agent
remote_agent = AgentClient(endpoint="http://remote-agent:8080")

@Tool
def use_remote_agent(query: str) -> str:
    """Use remote agent to answer query."""
    return remote_agent.run(query)

# Use in local agent
agent = LLMAgent(tools=[use_remote_agent])
```

## Communication Patterns

### Request-Response Pattern

Simple synchronous communication:

```python
# Client sends request
response = client.run("Hello")

# Server processes and returns response
```

### Streaming Pattern

For streaming responses:

```python
# Client
for chunk in client.stream("Long query"):
    print(chunk)

# Server
def stream_response(query):
    for part in agent.stream(query):
        yield part
```

### Asynchronous Pattern

For concurrent operations:

```python
import asyncio
from a2a_sdk import AsyncAgentClient

async def main():
    client = AsyncAgentClient(endpoint="...")
    response = await client.run_async("Query")
```

## Security

### Authentication

A2A supports various authentication methods:

**API Keys:**
```python
client = AgentClient(
    endpoint="...",
    api_key="your-api-key"
)
```

**OAuth:**
```python
client = AgentClient(
    endpoint="...",
    oauth_token="token"
)
```

### Encryption

Enable encryption for secure communication:

```python
# Install encryption support
pip install "a2a-sdk[encryption]"

# Use encrypted client
from a2a_sdk.encryption import EncryptedAgentClient

client = EncryptedAgentClient(
    endpoint="...",
    encryption_key="..."
)
```

## Agent Discovery

### Static Configuration

Define agents explicitly:

```python
agents = {
    "weather-agent": "http://weather-agent:8080",
    "search-agent": "http://search-agent:8080"
}
```

### Service Registry

Use service discovery:

```python
from a2a_sdk.discovery import ServiceRegistry

registry = ServiceRegistry(endpoint="http://registry:8500")
agents = registry.discover("agent-type")
```

## Best Practices

### Error Handling

Handle errors gracefully:

```python
try:
    response = client.run(query)
except AgentConnectionError:
    # Handle connection error
    pass
except AgentTimeoutError:
    # Handle timeout
    pass
```

### Retry Logic

Implement retry for resilience:

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def call_agent(query):
    return client.run(query)
```

### Monitoring

Use telemetry for observability:

```python
pip install "a2a-sdk[telemetry]"

from a2a_sdk.telemetry import setup_telemetry

setup_telemetry()
```

## Multi-Agent Patterns

### Orchestrator Pattern

One agent coordinates others:

```python
class OrchestratorAgent(BaseAgent):
    def __init__(self):
        self.weather_agent = AgentClient("http://weather:8080")
        self.search_agent = AgentClient("http://search:8080")
    
    def run(self, query):
        # Route to appropriate agent
        if "weather" in query:
            return self.weather_agent.run(query)
        else:
            return self.search_agent.run(query)
```

### Hierarchical Pattern

Agents organized in layers:

```
Root Agent
├── Sub-Agent 1
│   ├── Worker Agent 1.1
│   └── Worker Agent 1.2
└── Sub-Agent 2
    └── Worker Agent 2.1
```

## References

- A2A Protocol: https://a2a-protocol.org/
- A2A Python SDK: https://github.com/a2aproject/a2a-python
- A2A Tutorials: https://a2a-protocol.org/latest/tutorials/


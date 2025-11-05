# A2A Exposing Guide

## Overview

This guide covers exposing ADK agents via the A2A Protocol so other agents can use them.

## Basic A2A Server Setup

### Minimal Server

```python
from google.adk import LLMAgent
from google.adk.models import GeminiModel
from a2a_sdk import AgentServer

# Create your agent
agent = LLMAgent(
    model=GeminiModel(),
    system_instruction="You are a helpful assistant."
)

# Create A2A server
server = AgentServer(agent)

# Start server
server.run(host="0.0.0.0", port=8080)
```

### Server with Configuration

```python
from a2a_sdk import AgentServer, ServerConfig

config = ServerConfig(
    host="0.0.0.0",
    port=8080,
    max_workers=10,
    timeout=30
)

server = AgentServer(agent, config=config)
server.run()
```

## Agent Capabilities Registration

### Registering Capabilities

```python
from a2a_sdk import AgentServer, Capability

# Define capabilities
capabilities = [
    Capability(
        name="weather_query",
        description="Get weather information",
        input_schema={"location": "string"},
        output_schema={"temperature": "number", "condition": "string"}
    ),
    Capability(
        name="text_analysis",
        description="Analyze text",
        input_schema={"text": "string"},
        output_schema={"sentiment": "string", "keywords": "array"}
    )
]

server = AgentServer(agent, capabilities=capabilities)
```

## Authentication and Security

### API Key Authentication

```python
from a2a_sdk import AgentServer, AuthConfig

auth = AuthConfig(
    api_key="your-secret-api-key",
    require_auth=True
)

server = AgentServer(agent, auth=auth)
```

### OAuth Authentication

```python
from a2a_sdk import AgentServer, AuthConfig

auth = AuthConfig(
    oauth_endpoint="https://oauth.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

server = AgentServer(agent, auth=auth)
```

## Advanced Server Configuration

### HTTP Server

```python
from a2a_sdk.http import HTTPServer

server = HTTPServer(agent)
server.run(host="0.0.0.0", port=8080)
```

### gRPC Server

```python
from a2a_sdk.grpc import GRPCServer

server = GRPCServer(agent)
server.run(port=50051)
```

### Custom Request Handling

```python
from a2a_sdk import AgentServer

class CustomServer(AgentServer):
    def handle_request(self, request):
        # Custom preprocessing
        processed_request = self.preprocess(request)
        
        # Call agent
        response = self.agent.run(processed_request)
        
        # Custom postprocessing
        return self.postprocess(response)
```

## Agent Discovery

### Service Registration

```python
from a2a_sdk.discovery import ServiceRegistry

registry = ServiceRegistry(endpoint="http://registry:8500")

server = AgentServer(agent)
server.register_service(
    registry=registry,
    service_name="my-agent",
    service_tags=["weather", "assistant"]
)
```

### Health Checks

```python
from a2a_sdk import AgentServer

server = AgentServer(agent)

@server.health_check
def check_health():
    return {
        "status": "healthy",
        "agent_ready": agent.is_ready()
    }
```

## Monitoring and Observability

### Logging

```python
import logging
from a2a_sdk import AgentServer

logging.basicConfig(level=logging.INFO)

server = AgentServer(agent, log_level=logging.INFO)
```

### Metrics

```python
from a2a_sdk.telemetry import setup_telemetry

setup_telemetry()

server = AgentServer(agent)
```

### Tracing

```python
from a2a_sdk.telemetry import setup_tracing

setup_tracing(endpoint="http://jaeger:14268")

server = AgentServer(agent)
```

## Error Handling

### Custom Error Handling

```python
from a2a_sdk import AgentServer

class ErrorHandlingServer(AgentServer):
    def handle_error(self, error, request):
        if isinstance(error, ValueError):
            return {"error": "Invalid input", "details": str(error)}
        elif isinstance(error, TimeoutError):
            return {"error": "Request timeout", "retry": True}
        else:
            return {"error": "Internal error", "message": str(error)}
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY agent.py .
COPY server.py .

CMD ["python", "server.py"]
```

### Cloud Run Deployment

```python
# server.py
from a2a_sdk import AgentServer

server = AgentServer(agent)
server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
```

## Best Practices

1. **Security**: Always use authentication in production
2. **Error Handling**: Provide clear error messages
3. **Documentation**: Document agent capabilities clearly
4. **Monitoring**: Set up logging and metrics
5. **Health Checks**: Implement health check endpoints
6. **Resource Management**: Handle resources properly
7. **Scalability**: Design for concurrent requests

## References

- A2A Protocol: https://a2a-protocol.org/
- A2A Python SDK: https://github.com/a2aproject/a2a-python


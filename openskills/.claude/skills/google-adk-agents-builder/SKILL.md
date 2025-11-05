---
name: google-adk-agents-builder
description: Guide for building autonomous AI agents using Google's Agent Development Kit (ADK) and the Agent2Agent (A2A) Protocol. This skill should be used when creating Python-based agents, multi-agent systems, workflow agents, or integrating A2A protocol for agent-to-agent communication. Use when developing agents that require tools, memory, context management, or deployment on Google Cloud.
---

# Google ADK Agents Builder

## Overview

To build autonomous AI agents using Google's Agent Development Kit (ADK) and enable agent-to-agent communication via the A2A Protocol, use this skill. ADK provides a comprehensive framework for creating agents that can perform tasks, interact with users, utilize external tools, and coordinate with other agents in multi-agent systems.

---

## High-Level Workflow

Creating ADK-based agents involves five main phases:

### Phase 1: Understanding ADK Architecture and Components

Before building agents, understand the core ADK concepts and components:

**Core ADK Components:**
- **BaseAgent**: The foundational class that all agents extend
- **LLM Agents**: Agents that utilize Large Language Models for natural language understanding and generation
- **Workflow Agents**: Agents that manage structured processes using sequences, loops, and parallel executions
- **Custom Agents**: Agents with unique logic or integrations
- **Tools**: Modular capabilities agents use to perform actions (APIs, databases, other agents)
- **Memory & Sessions**: Mechanisms to store agent state and knowledge across sessions
- **Context**: Context management and caching for efficient agent operations

**Agent2Agent (A2A) Protocol:**
- Enables secure communication between agents
- Supports agent discovery and task delegation
- Facilitates multi-agent collaboration

**Load reference documentation:**
- [📚 ADK Core Concepts](./references/adk_core_concepts.md) - Complete overview of ADK architecture
- [🔗 A2A Protocol Guide](./references/a2a_protocol.md) - A2A integration and communication patterns
- [🛠️ ADK Tools and Configuration](./references/adk_tools_config.md) - Tools, memory, and agent configuration
- [🤖 LiteLLM Integration](./references/litellm_integration.md) - Using multiple LLM providers (Azure OpenAI, Anthropic, etc.)

### Phase 2: Environment Setup and Project Initialization

To set up the development environment for ADK agents:

#### 2.1 Install Dependencies

Install required packages:

```bash
pip install google-adk
pip install a2a-sdk[all]  # For A2A protocol support
```

For multi-model support (Azure OpenAI, Anthropic, etc.):
```bash
pip install litellm  # For using multiple LLM providers
```

For specific A2A features:
```bash
pip install "a2a-sdk[http-server]"  # HTTP server support
pip install "a2a-sdk[grpc]"          # gRPC support
pip install "a2a-sdk[telemetry]"     # OpenTelemetry tracing
pip install "a2a-sdk[encryption]"    # Encryption support
```

#### 2.2 Configure Authentication

Set up Google Cloud authentication for ADK:

```bash
# Set up Application Default Credentials
gcloud auth application-default login

# Or set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

#### 2.3 Initialize Project Structure

Use the provided template to initialize a new agent project:

```bash
# Use the agent template from assets/
python scripts/init_agent.py my-agent --path ./agents
```

This creates a proper project structure with:
- Agent implementation file
- Configuration files
- Requirements file
- README with usage instructions

### Phase 3: Building Agents

#### 3.1 Create a Basic LLM Agent

To create a simple LLM agent:

**Load the template:**
- [📝 Basic Agent Template](./assets/templates/basic_llm_agent.py) - Complete starter template

**Key steps:**
1. Import ADK components: `from google.adk import BaseAgent, LLMAgent`
2. Choose model: Native `GeminiModel` or `LiteLlm` for multi-provider support
3. Define agent tools (if needed)
4. Configure the agent with model settings
5. Implement agent logic
6. Create agent instance and run

**Model Options:**
- **Native Gemini**: `from google.adk.models import GeminiModel`
- **Multi-Provider (LiteLLM)**: `from google.adk.models.lite_llm import LiteLlm` - Use Azure OpenAI, Anthropic, OpenAI, etc.

See [🤖 LiteLLM Integration](./references/litellm_integration.md) for using non-Gemini models.

**Example structure:**
```python
from google.adk import LLMAgent, Tool
from google.adk.models import GeminiModel

# Define tools
@Tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    # Implementation
    pass

# Create agent
agent = LLMAgent(
    model=GeminiModel(model_name="gemini-2.0-flash-exp"),
    tools=[get_weather],
    system_instruction="You are a helpful assistant."
)

# Run agent
response = agent.run("What's the weather in San Francisco?")
```

#### 3.2 Create a Workflow Agent

Workflow agents manage structured processes. Use them for:
- Sequential task execution
- Parallel operations
- Loop-based workflows

**Load reference:**
- [📋 Workflow Patterns](./references/workflow_patterns.md) - Sequential, parallel, and loop patterns

**Key workflow types:**
- **Sequential**: Execute tasks in order, one after another
- **Parallel**: Execute multiple tasks simultaneously
- **Loop**: Repeat tasks until a condition is met

#### 3.3 Create Custom Agents

For specialized logic, extend `BaseAgent` directly:

**Load template:**
- [🔧 Custom Agent Template](./assets/templates/custom_agent.py) - Template for custom agent implementations

**Custom agent considerations:**
- Override `run()` method for custom execution logic
- Implement custom state management
- Define specialized tool integrations
- Handle unique error scenarios

#### 3.4 Configure Agent Tools

Tools extend agent capabilities. To add tools:

**Tool types:**
- **Function tools**: Python functions decorated with `@Tool`
- **API tools**: External API integrations
- **MCP tools**: Model Context Protocol tools
- **OpenAPI tools**: Tools from OpenAPI specifications

**Load reference:**
- [🛠️ Tool Development Guide](./references/tool_development.md) - Complete tool creation guide

**Best practices:**
- Provide clear tool descriptions
- Include parameter validation
- Handle errors gracefully
- Return structured data

### Phase 4: Multi-Agent Systems with A2A

To build multi-agent systems where agents communicate via A2A Protocol:

#### 4.1 Expose an Agent via A2A

To make an agent available to other agents:

**Load reference:**
- [📤 A2A Exposing Guide](./references/a2a_exposing.md) - Complete guide for exposing agents

**Key steps:**
1. Create an A2A server wrapper around your agent
2. Register agent capabilities
3. Start A2A server
4. Configure discovery (if needed)

**Load template:**
- [🌐 A2A Server Template](./assets/templates/a2a_server.py) - Template for A2A server setup

#### 4.2 Consume Remote Agents via A2A

To use remote agents from your agent:

**Load reference:**
- [📥 A2A Consuming Guide](./references/a2a_consuming.md) - Guide for consuming remote agents

**Key steps:**
1. Connect to A2A server endpoint
2. Discover available agents
3. Register remote agents as tools
4. Use remote agents in agent workflows

**Load template:**
- [🔌 A2A Client Template](./assets/templates/a2a_client.py) - Template for A2A client setup

#### 4.3 Build Multi-Agent Orchestration

To coordinate multiple agents:

**Load reference:**
- [🎭 Multi-Agent Patterns](./references/multi_agent_patterns.md) - Orchestration patterns and examples

**Common patterns:**
- **Orchestrator Pattern**: One agent coordinates others
- **Hierarchical Pattern**: Agents organized in layers
- **Peer-to-Peer Pattern**: Agents communicate directly

### Phase 5: Testing, Evaluation, and Deployment

#### 5.1 Test Agent Locally

Before deployment, test agents thoroughly:

**Testing approaches:**
- Unit tests for individual tools
- Integration tests for agent workflows
- End-to-end tests for complete user interactions

**Load template:**
- [🧪 Test Template](./assets/templates/test_agent.py) - Template for agent testing

#### 5.2 Evaluate Agent Performance

Use ADK's built-in evaluation tools:

**Evaluation criteria:**
- Response quality
- Task completion rate
- Tool usage efficiency
- Error handling

#### 5.3 Deploy Agent

Deploy agents to production:

**Deployment options:**
- **Agent Engine**: Google Cloud managed service
- **Cloud Run**: Serverless container deployment
- **GKE**: Kubernetes deployment
- **Custom Infrastructure**: Self-hosted deployment

**Load reference:**
- [🚀 Deployment Guide](./references/deployment.md) - Complete deployment instructions

---

## Quick Reference

### Common Agent Patterns

**Simple LLM Agent (Gemini):**
```python
from google.adk import LLMAgent
from google.adk.models import GeminiModel

agent = LLMAgent(
    model=GeminiModel(),
    system_instruction="You are helpful."
)
response = agent.run("Hello!")
```

**Multi-Provider Agent (LiteLLM):**
```python
from google.adk import LLMAgent
from google.adk.models.lite_llm import LiteLlm

# Use Azure OpenAI
agent = LLMAgent(
    model=LiteLlm(model="azure/gpt-4o"),
    system_instruction="You are helpful."
)

# Or use Anthropic Claude
agent = LLMAgent(
    model=LiteLlm(model="claude-3-5-sonnet-20241022"),
    system_instruction="You are helpful."
)
```

**Agent with Tools:**
```python
from google.adk import LLMAgent, Tool

@Tool
def calculator(a: float, b: float, op: str) -> float:
    """Perform calculations."""
    # Implementation
    pass

agent = LLMAgent(tools=[calculator])
```

**A2A Agent Server:**
```python
from a2a_sdk import AgentServer
from google.adk import LLMAgent

agent = LLMAgent(...)
server = AgentServer(agent)
server.run()
```

### File Organization

When creating agents, organize files as follows:

```
my-agent/
├── agent.py           # Main agent implementation
├── tools.py           # Tool definitions
├── config.yaml        # Agent configuration
├── requirements.txt   # Dependencies
└── README.md          # Documentation
```

---

## Resources

### Reference Documentation

Load these references as needed during development:

- [📚 ADK Core Concepts](./references/adk_core_concepts.md) - Architecture, components, and patterns
- [🔗 A2A Protocol Guide](./references/a2a_protocol.md) - A2A protocol details and integration
- [🛠️ ADK Tools and Configuration](./references/adk_tools_config.md) - Tools, memory, sessions, context
- [🤖 LiteLLM Integration](./references/litellm_integration.md) - Using multiple LLM providers (Azure OpenAI, Anthropic, OpenAI, etc.)
- [📋 Workflow Patterns](./references/workflow_patterns.md) - Sequential, parallel, loop workflows
- [🛠️ Tool Development Guide](./references/tool_development.md) - Creating and managing tools
- [📤 A2A Exposing Guide](./references/a2a_exposing.md) - Exposing agents via A2A
- [📥 A2A Consuming Guide](./references/a2a_consuming.md) - Consuming remote agents
- [🎭 Multi-Agent Patterns](./references/multi_agent_patterns.md) - Multi-agent orchestration
- [🚀 Deployment Guide](./references/deployment.md) - Deployment options and instructions

### Templates and Scripts

**Agent Templates:**
- [📝 Basic LLM Agent](./assets/templates/basic_llm_agent.py) - Simple LLM agent starter
- [🤖 LiteLLM Multi-Provider Agent](./assets/templates/litellm_agent.py) - Agent using Azure OpenAI, Anthropic, OpenAI, etc.
- [🔧 Custom Agent](./assets/templates/custom_agent.py) - Custom agent template
- [🌐 A2A Server](./assets/templates/a2a_server.py) - A2A server setup
- [🔌 A2A Client](./assets/templates/a2a_client.py) - A2A client setup
- [🧪 Test Template](./assets/templates/test_agent.py) - Agent testing template

**Utility Scripts:**
- [🚀 init_agent.py](./scripts/init_agent.py) - Initialize new agent project
- [✅ validate_agent.py](./scripts/validate_agent.py) - Validate agent configuration

---

## External Resources

For comprehensive documentation, refer to:

- **ADK Documentation**: https://google.github.io/adk-docs/
- **ADK Samples**: https://github.com/google/adk-samples/tree/main/python/agents
- **A2A Protocol**: https://a2a-protocol.org/
- **A2A Python SDK**: https://github.com/a2aproject/a2a-python
- **A2A Tutorials**: https://a2a-protocol.org/latest/tutorials/

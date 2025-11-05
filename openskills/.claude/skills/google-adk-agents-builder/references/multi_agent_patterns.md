# Multi-Agent Patterns

## Overview

This guide covers patterns for orchestrating multiple agents in ADK systems.

## Orchestrator Pattern

One agent coordinates multiple specialized agents.

### Basic Orchestrator

```python
from google.adk import BaseAgent
from a2a_sdk import AgentClient

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        self.weather_agent = AgentClient("http://weather:8080")
        self.search_agent = AgentClient("http://search:8080")
        self.calc_agent = AgentClient("http://calc:8080")
    
    def run(self, query):
        # Simple routing
        if "weather" in query.lower():
            return self.weather_agent.run(query)
        elif "calculate" in query.lower():
            return self.calc_agent.run(query)
        else:
            return self.search_agent.run(query)
```

### LLM-Based Orchestrator

```python
from google.adk import LLMAgent, BaseAgent
from a2a_sdk import AgentClient

class LLMOrchestrator(BaseAgent):
    def __init__(self):
        self.router = LLMAgent(
            system_instruction="Route queries to appropriate agents"
        )
        self.agents = {
            "weather": AgentClient("http://weather:8080"),
            "search": AgentClient("http://search:8080"),
            "calc": AgentClient("http://calc:8080")
        }
    
    def run(self, query):
        # Use LLM to determine routing
        routing = self.router.run(f"Which agent should handle: {query}")
        
        # Parse routing decision and call appropriate agent
        agent_name = self.parse_routing(routing)
        return self.agents[agent_name].run(query)
```

## Hierarchical Pattern

Agents organized in layers with clear delegation.

### Two-Level Hierarchy

```python
class RootAgent(BaseAgent):
    def __init__(self):
        self.sub_agents = {
            "data": DataAgent(),
            "processing": ProcessingAgent()
        }
    
    def run(self, query):
        # Determine which sub-agent to use
        if self.needs_data(query):
            return self.sub_agents["data"].run(query)
        else:
            return self.sub_agents["processing"].run(query)

class DataAgent(BaseAgent):
    def __init__(self):
        self.workers = [
            WorkerAgent("worker1"),
            WorkerAgent("worker2")
        ]
    
    def run(self, query):
        # Distribute to workers
        return self.workers[0].run(query)
```

### Multi-Level Hierarchy

```python
class HierarchicalAgent(BaseAgent):
    def __init__(self):
        self.level1_agents = {
            "category_a": CategoryAAgent(),
            "category_b": CategoryBAgent()
        }
    
    def run(self, query):
        category = self.determine_category(query)
        agent = self.level1_agents[category]
        return agent.run(query)
```

## Peer-to-Peer Pattern

Agents communicate directly with each other.

### Direct Communication

```python
class PeerAgent(BaseAgent):
    def __init__(self, agent_id, peers):
        self.agent_id = agent_id
        self.peers = {
            peer_id: AgentClient(endpoint) 
            for peer_id, endpoint in peers.items()
        }
    
    def run(self, query):
        # Determine if peer collaboration needed
        if self.needs_collaboration(query):
            peer = self.select_peer(query)
            return self.peers[peer].run(query)
        else:
            return self.handle_locally(query)
```

### Broadcast Pattern

```python
class BroadcastAgent(BaseAgent):
    def __init__(self, peers):
        self.peers = [AgentClient(endpoint) for endpoint in peers]
    
    def run(self, query):
        # Broadcast to all peers and aggregate
        results = []
        for peer in self.peers:
            try:
                result = peer.run(query)
                results.append(result)
            except Exception as e:
                # Handle peer failures
                continue
        
        return self.aggregate(results)
```

## Pipeline Pattern

Agents process data in sequence.

### Linear Pipeline

```python
class PipelineAgent(BaseAgent):
    def __init__(self):
        self.stages = [
            PreprocessingAgent(),
            ProcessingAgent(),
            PostprocessingAgent()
        ]
    
    def run(self, data):
        result = data
        for stage in self.stages:
            result = stage.run(result)
        return result
```

### Conditional Pipeline

```python
class ConditionalPipelineAgent(BaseAgent):
    def __init__(self):
        self.pipelines = {
            "type_a": [Agent1(), Agent2()],
            "type_b": [Agent3(), Agent4()]
        }
    
    def run(self, data):
        pipeline_type = self.determine_type(data)
        pipeline = self.pipelines[pipeline_type]
        
        result = data
        for agent in pipeline:
            result = agent.run(result)
        return result
```

## Parallel Processing Pattern

Execute multiple agents in parallel.

### Parallel Execution

```python
import asyncio
from a2a_sdk import AsyncAgentClient

class ParallelAgent(BaseAgent):
    def __init__(self):
        self.agents = [
            AsyncAgentClient("http://agent1:8080"),
            AsyncAgentClient("http://agent2:8080"),
            AsyncAgentClient("http://agent3:8080")
        ]
    
    async def run_async(self, query):
        # Execute all agents in parallel
        results = await asyncio.gather(*[
            agent.run_async(query) for agent in self.agents
        ])
        
        return self.merge_results(results)
```

### Map-Reduce Pattern

```python
class MapReduceAgent(BaseAgent):
    def __init__(self):
        self.worker_agents = [
            AgentClient(f"http://worker{i}:8080") 
            for i in range(5)
        ]
        self.reducer = ReducerAgent()
    
    def run(self, data):
        # Map phase
        tasks = self.split_data(data)
        results = []
        
        for task, agent in zip(tasks, self.worker_agents):
            result = agent.run(task)
            results.append(result)
        
        # Reduce phase
        return self.reducer.run(results)
```

## Best Practices

1. **Clear Responsibilities**: Each agent should have a clear purpose
2. **Error Handling**: Handle agent failures gracefully
3. **Load Balancing**: Distribute work evenly
4. **Monitoring**: Track agent performance and health
5. **Scalability**: Design for horizontal scaling
6. **Communication**: Minimize inter-agent communication overhead
7. **Testing**: Test multi-agent interactions thoroughly

## References

- ADK Multi-Agent: https://google.github.io/adk-docs/multi-agent/
- A2A Protocol: https://a2a-protocol.org/


# Workflow Patterns

## Overview

Workflow agents manage structured processes in ADK. This guide covers sequential, parallel, and loop workflow patterns.

## Sequential Workflows

Execute tasks in order, one after another.

### Basic Sequential Workflow

```python
from google.adk.workflows import SequentialWorkflow

workflow = SequentialWorkflow([
    task1,
    task2,
    task3
])

result = workflow.run(input_data)
```

### Sequential with Dependencies

```python
from google.adk.workflows import SequentialWorkflow

def task1(data):
    return process_step1(data)

def task2(data):
    # Uses output from task1
    return process_step2(data)

def task3(data):
    # Uses output from task2
    return process_step3(data)

workflow = SequentialWorkflow([task1, task2, task3])
```

### Error Handling in Sequential

```python
from google.adk.workflows import SequentialWorkflow

workflow = SequentialWorkflow(
    tasks=[task1, task2, task3],
    on_error="stop"  # or "continue" or "retry"
)
```

## Parallel Workflows

Execute multiple tasks simultaneously.

### Basic Parallel Workflow

```python
from google.adk.workflows import ParallelWorkflow

workflow = ParallelWorkflow([
    fetch_user_data,
    fetch_weather_data,
    fetch_news_data
])

results = workflow.run(input_data)
```

### Parallel with Aggregation

```python
from google.adk.workflows import ParallelWorkflow

def aggregate_results(results):
    return combine_all(results)

workflow = ParallelWorkflow(
    tasks=[task1, task2, task3],
    aggregator=aggregate_results
)
```

### Partial Parallel Execution

```python
from google.adk.workflows import ParallelWorkflow

workflow = ParallelWorkflow(
    tasks=[task1, task2, task3],
    max_parallel=2  # Run 2 at a time
)
```

## Loop Workflows

Repeat tasks until a condition is met.

### While Loop

```python
from google.adk.workflows import LoopWorkflow

def condition(data):
    return data["status"] != "complete"

def task(data):
    return process_step(data)

workflow = LoopWorkflow(
    task=task,
    condition=condition,
    max_iterations=10
)
```

### For Loop

```python
from google.adk.workflows import LoopWorkflow

items = [1, 2, 3, 4, 5]

workflow = LoopWorkflow(
    task=process_item,
    items=items
)
```

### Loop with Accumulator

```python
from google.adk.workflows import LoopWorkflow

def accumulator(previous, current):
    return previous + current

workflow = LoopWorkflow(
    task=process_item,
    items=items,
    accumulator=accumulator,
    initial_value=0
)
```

## Complex Workflows

### Nested Workflows

```python
from google.adk.workflows import SequentialWorkflow, ParallelWorkflow

inner_parallel = ParallelWorkflow([task1, task2])
outer_sequential = SequentialWorkflow([
    setup_task,
    inner_parallel,
    cleanup_task
])
```

### Conditional Workflows

```python
from google.adk.workflows import ConditionalWorkflow

def condition(data):
    return data["type"] == "priority"

workflow = ConditionalWorkflow(
    condition=condition,
    if_true=priority_workflow,
    if_false=normal_workflow
)
```

### Workflow Composition

```python
from google.adk.workflows import WorkflowComposer

composer = WorkflowComposer()

# Define stages
stage1 = SequentialWorkflow([setup, initialize])
stage2 = ParallelWorkflow([process1, process2, process3])
stage3 = SequentialWorkflow([validate, finalize])

# Compose
workflow = composer.compose([stage1, stage2, stage3])
```

## Workflow Agents

### Creating Workflow Agents

```python
from google.adk import WorkflowAgent
from google.adk.workflows import SequentialWorkflow

workflow = SequentialWorkflow([task1, task2, task3])

agent = WorkflowAgent(
    workflow=workflow,
    description="Multi-step processing agent"
)
```

### Workflow with LLM Decision

```python
from google.adk import WorkflowAgent, LLMAgent

llm_agent = LLMAgent(...)

def llm_decision_task(data):
    decision = llm_agent.run(f"Decide next step for: {data}")
    return decision

workflow = SequentialWorkflow([
    initial_task,
    llm_decision_task,
    conditional_task
])
```

## Error Handling

### Retry Logic

```python
from google.adk.workflows import SequentialWorkflow

workflow = SequentialWorkflow(
    tasks=[task1, task2, task3],
    retry_config={
        "max_retries": 3,
        "backoff": "exponential"
    }
)
```

### Error Recovery

```python
from google.adk.workflows import SequentialWorkflow

def recovery_task(error, context):
    # Handle error
    return fallback_result

workflow = SequentialWorkflow(
    tasks=[task1, task2, task3],
    on_error=recovery_task
)
```

## Best Practices

1. **Clear Task Boundaries**: Each task should have a clear purpose
2. **Error Handling**: Plan for failure scenarios
3. **Resource Management**: Clean up resources properly
4. **Monitoring**: Track workflow execution
5. **Testing**: Test workflows thoroughly

## References

- ADK Workflows: https://google.github.io/adk-docs/workflows/


# Tool Development Guide

## Overview

This guide covers creating, managing, and optimizing tools for ADK agents.

## Creating Tools

### Basic Function Tool

```python
from google.adk import Tool

@Tool
def simple_tool(input_data: str) -> str:
    """
    Simple tool description.
    
    Args:
        input_data: Description of input
        
    Returns:
        Description of output
    """
    # Implementation
    return processed_result
```

### Tool with Multiple Parameters

```python
@Tool
def complex_tool(
    param1: str,
    param2: int,
    param3: bool = False
) -> dict:
    """
    Complex tool with multiple parameters.
    
    Args:
        param1: First parameter description
        param2: Second parameter description
        param3: Optional parameter (default: False)
        
    Returns:
        Dictionary with results
    """
    # Implementation
    return {"result": "value"}
```

### Async Tools

```python
import asyncio
from google.adk import Tool

@Tool
async def async_tool(data: str) -> str:
    """Async tool for I/O operations."""
    result = await some_async_operation(data)
    return result
```

## Tool Types

### API Integration Tools

```python
import requests
from google.adk import Tool

@Tool
def api_tool(query: str) -> dict:
    """Call external API."""
    response = requests.get(f"https://api.example.com/search?q={query}")
    return response.json()
```

### Database Tools

```python
from google.adk import Tool
import sqlite3

@Tool
def query_database(query: str) -> list:
    """Query database."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results
```

### File Operation Tools

```python
from google.adk import Tool
from pathlib import Path

@Tool
def read_file(file_path: str) -> str:
    """Read file contents."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return path.read_text()
```

## Tool Validation

### Input Validation

```python
from google.adk import Tool
from pydantic import BaseModel, validator

class ToolInput(BaseModel):
    value: int
    
    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('Value must be positive')
        return v

@Tool
def validated_tool(input_data: ToolInput) -> str:
    """Tool with validated input."""
    return f"Processed: {input_data.value}"
```

### Error Handling

```python
from google.adk import Tool

@Tool
def robust_tool(data: str) -> str:
    """Tool with error handling."""
    try:
        # Operation that might fail
        result = risky_operation(data)
        return result
    except ValueError as e:
        return f"Error: Invalid input - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
```

## Tool Composition

### Tool Chaining

```python
@Tool
def chained_tool(data: str) -> str:
    """Tool that uses other tools."""
    result1 = tool1(data)
    result2 = tool2(result1)
    return tool3(result2)
```

### Conditional Tool Execution

```python
@Tool
def conditional_tool(data: str, use_advanced: bool) -> str:
    """Tool with conditional logic."""
    if use_advanced:
        return advanced_tool(data)
    else:
        return simple_tool(data)
```

## Tool Optimization

### Caching

```python
from functools import lru_cache
from google.adk import Tool

@Tool
@lru_cache(maxsize=100)
def cached_tool(query: str) -> str:
    """Tool with caching."""
    # Expensive operation
    return expensive_operation(query)
```

### Batch Processing

```python
from google.adk import Tool

@Tool
def batch_tool(items: list[str]) -> list[str]:
    """Process multiple items efficiently."""
    # Batch processing logic
    return [process_item(item) for item in items]
```

## Tool Documentation

### Comprehensive Docstrings

```python
@Tool
def well_documented_tool(
    input_param: str,
    optional_param: int = 10
) -> dict:
    """
    Clear, concise tool description.
    
    This tool performs a specific operation on input data.
    It's useful for scenarios where you need to process
    text data with optional configuration.
    
    Args:
        input_param: Description of what this parameter does.
            Example: "Hello world"
        optional_param: Optional parameter with default value.
            Range: 1-100, default: 10
            
    Returns:
        Dictionary containing:
            - result: The processed result (str)
            - metadata: Additional information (dict)
            
    Raises:
        ValueError: If input_param is invalid
        RuntimeError: If processing fails
        
    Example:
        >>> result = well_documented_tool("test", 5)
        >>> print(result["result"])
        "processed: test"
    """
    # Implementation
    pass
```

## Tool Testing

### Unit Tests

```python
import pytest
from google.adk import Tool

@Tool
def testable_tool(data: str) -> str:
    """Tool for testing."""
    return data.upper()

def test_tool():
    result = testable_tool("hello")
    assert result == "HELLO"
```

## Best Practices

1. **Clear Names**: Use descriptive, action-oriented names
2. **Type Hints**: Always include type annotations
3. **Documentation**: Provide comprehensive docstrings
4. **Error Handling**: Handle errors gracefully
5. **Validation**: Validate inputs appropriately
6. **Performance**: Optimize for common use cases
7. **Idempotency**: Design tools to be idempotent when possible

## References

- ADK Tools: https://google.github.io/adk-docs/tools/


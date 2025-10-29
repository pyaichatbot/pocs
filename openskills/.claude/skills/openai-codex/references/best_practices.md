# OpenAI Codex Best Practices

## Prompt Engineering

### 1. Be Specific and Clear
- Use precise language to describe what you want
- Include specific requirements and constraints
- Provide clear examples of input/output

**Good Example:**
```
Write a Python function that calculates the factorial of a number.
Input: n (integer >= 0)
Output: factorial of n (integer)
Handle edge case: return 1 for n=0
```

**Bad Example:**
```
Write a function for factorial
```

### 2. Provide Context
- Include relevant background information
- Specify the programming language and version
- Mention any frameworks or libraries to use

**Good Example:**
```
Using Python 3.8+ and pandas, create a function that:
- Reads a CSV file
- Filters rows where 'age' > 18
- Returns the filtered DataFrame
```

### 3. Use Examples
- Show expected input/output format
- Provide sample data when relevant
- Include edge cases

**Good Example:**
```
Create a function that validates email addresses.
Examples:
- "user@example.com" -> True
- "invalid-email" -> False
- "user@domain.co.uk" -> True
- "" -> False
```

### 4. Structure Your Prompts
- Use clear headings and sections
- Separate requirements from examples
- Use consistent formatting

**Template:**
```
# Task Description
[Clear description of what to build]

# Requirements
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

# Examples
Input: [example input]
Output: [expected output]

# Constraints
- [Constraint 1]
- [Constraint 2]
```

## Code Quality Guidelines

### 1. Error Handling
- Always include proper exception handling
- Validate inputs
- Provide meaningful error messages

**Example:**
```python
def divide_numbers(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

### 2. Documentation
- Include docstrings for functions and classes
- Add inline comments for complex logic
- Use type hints when possible

**Example:**
```python
def calculate_fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number.
    
    Args:
        n: The position in the Fibonacci sequence (0-indexed)
        
    Returns:
        The nth Fibonacci number
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    # Implementation here
```

### 3. Performance Considerations
- Choose appropriate data structures
- Consider time and space complexity
- Optimize for the expected use case

### 4. Security
- Validate and sanitize all inputs
- Use secure coding practices
- Avoid hardcoded secrets

## Common Patterns

### 1. Function Generation
```
Write a [language] function that [specific task].
- Input: [input description]
- Output: [output description]
- Requirements: [specific requirements]
- Handle edge cases: [edge cases]
```

### 2. Class Generation
```
Create a [language] class for [purpose] with:
- Properties: [list properties]
- Methods: [list methods]
- Include: [additional features]
```

### 3. Algorithm Implementation
```
Implement [algorithm name] in [language]:
- Time complexity: O([complexity])
- Space complexity: O([complexity])
- Handle edge cases: [specific cases]
- Use: [data structures/libraries]
```

### 4. API Integration
```
Create a [language] function to [API task]:
- Endpoint: [API endpoint]
- Method: [HTTP method]
- Headers: [required headers]
- Handle errors: [error handling]
```

## Debugging Tips

### 1. Common Issues
- **Incomplete code**: Add more specific instructions
- **Wrong language**: Specify exact language and version
- **Logic errors**: Provide more detailed requirements
- **Formatting issues**: Use consistent style guidelines

### 2. Debugging Prompts
```
Debug this [language] code:
[code here]

Error message: [error if available]
Expected behavior: [what should happen]
```

### 3. Optimization Prompts
```
Optimize this [language] code for better performance:
[code here]

Current issues: [performance problems]
Target: [performance goals]
```

## Testing

### 1. Unit Test Generation
```
Generate unit tests for this [language] function:
[function code]

Test cases to include:
- [test case 1]
- [test case 2]
- [edge cases]
```

### 2. Integration Test Generation
```
Create integration tests for this [language] API:
[API code]

Test scenarios:
- [scenario 1]
- [scenario 2]
- [error cases]
```

## Language-Specific Tips

### Python
- Use type hints
- Follow PEP 8 style guide
- Use appropriate data structures
- Include proper error handling

### JavaScript
- Use modern ES6+ features
- Follow consistent naming conventions
- Handle async operations properly
- Use appropriate error handling

### Java
- Follow Java naming conventions
- Use appropriate access modifiers
- Include proper documentation
- Handle exceptions appropriately

### C++
- Use modern C++ features
- Follow RAII principles
- Include proper error handling
- Use appropriate data structures

## Performance Optimization

### 1. Algorithm Selection
- Choose the right algorithm for the problem
- Consider time and space complexity
- Optimize for the expected input size

### 2. Data Structure Selection
- Use appropriate data structures
- Consider access patterns
- Optimize for memory usage

### 3. Code Optimization
- Avoid unnecessary computations
- Use efficient loops
- Minimize function calls
- Cache frequently used values

## Security Best Practices

### 1. Input Validation
- Validate all inputs
- Sanitize user data
- Use parameterized queries
- Avoid SQL injection

### 2. Error Handling
- Don't expose sensitive information
- Log errors appropriately
- Handle exceptions gracefully
- Use secure error messages

### 3. Authentication and Authorization
- Implement proper authentication
- Use secure session management
- Validate permissions
- Protect sensitive endpoints

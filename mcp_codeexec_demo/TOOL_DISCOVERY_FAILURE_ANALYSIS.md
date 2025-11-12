# Tool Discovery Failure Analysis

## Overview

When asking "What tools are available?" in code execution mode, the system attempts to have the agent generate Python code to discover tools. If this fails, it falls back to listing tools from the filesystem. This document explains what could go wrong and why the fallback is needed.

---

## Code Execution Flow for Tool Discovery

### Step 1: Agent Code Generation
**What happens:**
- User asks: "What tools are available?"
- System detects this is a tool query (`is_tool_query = True`)
- LLM is prompted to generate Python code to discover tools
- Expected code should:
  1. Explore `./servers/` directory
  2. Import and inspect tool modules
  3. Extract tool names and descriptions
  4. Set `_result = <formatted tool list>`

**Potential Failures:**

#### 1.1 LLM Doesn't Generate Code
- **Symptom**: LLM returns explanation text instead of code
- **Cause**: Prompt not clear enough, LLM misunderstands task
- **Detection**: Generated "code" doesn't look like Python
- **Impact**: Code validation fails → execution never happens

#### 1.2 LLM Generates Incomplete Code
- **Symptom**: Code missing imports, missing `_result` assignment
- **Cause**: LLM doesn't follow instructions completely
- **Detection**: Code executes but `_result` is `None`
- **Impact**: Execution succeeds but no result → fallback used

#### 1.3 LLM Generates Code with Syntax Errors
- **Symptom**: IndentationError, SyntaxError
- **Cause**: LLM makes syntax mistakes
- **Detection**: Code validation fails
- **Impact**: Execution blocked → error message shown

---

### Step 2: Code Validation
**What happens:**
- Generated code is validated by `CodeValidator`
- Checks syntax, dangerous patterns, imports

**Potential Failures:**

#### 2.1 Syntax Errors
- **Symptom**: `IndentationError`, `SyntaxError`
- **Cause**: Malformed code from LLM
- **Detection**: `validation_result["syntax_valid"] = False`
- **Impact**: Code not executed → error shown to user

#### 2.2 Security Rule Violations
- **Symptom**: Code blocked by security rules
- **Cause**: Code uses blocked imports/functions
- **Detection**: `validation_result["blocked"] = True`
- **Impact**: Code not executed → error shown to user
- **Note**: We fixed this by allowing `importlib`, `inspect`, etc.

#### 2.3 Validation Warnings
- **Symptom**: Warnings logged but code still executes
- **Cause**: Code uses unusual patterns (but not blocked)
- **Detection**: `validation_result["warnings"]` contains items
- **Impact**: Code executes but may have issues

---

### Step 3: Code Execution
**What happens:**
- Code is executed in sandboxed environment
- Code should set `_result` variable
- Executor captures `_result` and returns it

**Potential Failures:**

#### 3.1 Code Executes But Doesn't Set `_result`
- **Symptom**: `exec_success = True`, but `result_data = None`
- **Cause**: 
  - Agent's code doesn't assign to `_result`
  - Agent's code assigns to wrong variable name
  - Agent's code has logic error and never reaches `_result = ...`
- **Detection**: `exec_result.get("result")` is `None`
- **Impact**: Fallback to filesystem listing

**Example of problematic code:**
```python
# Agent generates this (WRONG - no _result):
from pathlib import Path
servers = [d.name for d in Path('./servers').iterdir() if d.is_dir()]
print(f"Found servers: {servers}")  # Prints but doesn't set _result
```

**Correct code should be:**
```python
# Agent should generate this (CORRECT):
from pathlib import Path
servers = [d.name for d in Path('./servers').iterdir() if d.is_dir()]
_result = f"Found servers: {servers}"  # Sets _result
```

#### 3.2 Code Raises Exception
- **Symptom**: `exec_success = False`, `error` contains exception
- **Cause**: 
  - Import errors (module not found)
  - Runtime errors (attribute errors, type errors)
  - File system errors (directory doesn't exist)
  - Network errors (if trying to connect to something)
- **Detection**: `exec_result.get("success") = False`
- **Impact**: Error shown to user, fallback used for tool queries

**Common exceptions:**
- `ModuleNotFoundError`: Tool module can't be imported
- `AttributeError`: Trying to access non-existent attribute
- `FileNotFoundError`: Directory doesn't exist
- `PermissionError`: Can't read directory

#### 3.3 Code Executes But Returns Wrong Format
- **Symptom**: `result_data` exists but isn't a string/dict
- **Cause**: Agent sets `_result` to unexpected type
- **Detection**: `result_data` is not string or dict with "tools" key
- **Impact**: May still work if it's convertible to string

#### 3.4 Indentation Error in Wrapper
- **Symptom**: `IndentationError` in generated script
- **Cause**: Code wrapper has indentation issues
- **Detection**: Syntax error during execution
- **Impact**: Execution fails → error shown
- **Note**: We fixed this by correcting the f-string indentation

---

### Step 4: Result Capture
**What happens:**
- Executor tries to capture `_result` from executed code
- Checks both `_result` and `result` variables
- Returns `None` if neither is set

**Potential Failures:**

#### 4.1 Variable Not in Scope
- **Symptom**: `_result` set in code but not captured
- **Cause**: Scope issues (unlikely with current implementation)
- **Detection**: `result_data = None` even though code set `_result`
- **Impact**: Fallback used
- **Note**: We fixed this by initializing `_result = None` before code execution

#### 4.2 Variable Set to None
- **Symptom**: `_result = None` explicitly set
- **Cause**: Agent's code sets `_result = None` instead of actual value
- **Detection**: `result_data = None`
- **Impact**: Fallback used

---

## Failure Scenarios Summary

### Scenario 1: LLM Generates Non-Code
```
User: "What tools are available?"
→ LLM returns: "I'll help you find the tools..."
→ Code validation fails (not Python)
→ Error shown: "Code validation failed"
→ ❌ No fallback (error case)
```

### Scenario 2: LLM Generates Code Without `_result`
```
User: "What tools are available?"
→ LLM generates: 
  from pathlib import Path
  servers = [d.name for d in Path('./servers').iterdir()]
  print(servers)  # Missing _result assignment!
→ Code executes successfully
→ result_data = None
→ Fallback used: executor.list_available_tools()
→ ✅ Tools shown from filesystem
```

### Scenario 3: Code Has Runtime Error
```
User: "What tools are available?"
→ LLM generates code with import error
→ Code executes but raises: ModuleNotFoundError
→ exec_success = False
→ Error shown + fallback used
→ ✅ Tools shown from filesystem
```

### Scenario 4: Code Sets `_result` Correctly
```
User: "What tools are available?"
→ LLM generates correct code with _result assignment
→ Code executes successfully
→ result_data = "Available Tools:\n1. get_transcript..."
→ ✅ Tools shown from code execution (no fallback)
```

---

## Why Fallback is Necessary

### 1. LLM Reliability
- LLMs are not 100% reliable
- They may generate incomplete or incorrect code
- They may misunderstand the task
- Fallback ensures users always get an answer

### 2. Code Complexity
- Tool discovery requires:
  - Filesystem exploration
  - Module importing
  - Introspection (inspect, importlib)
  - String formatting
- This is complex for an LLM to get right every time

### 3. Edge Cases
- Empty servers directory
- Malformed tool files
- Import errors
- Permission issues
- Fallback handles all these cases

### 4. User Experience
- Users need tools listed regardless of code execution success
- Fallback provides consistent experience
- Transparency (showing when fallback is used) maintains trust

---

## Common Root Causes

### 1. Prompt Not Clear Enough
**Problem**: LLM doesn't understand it needs to set `_result`

**Solution**: 
- Enhanced prompt with explicit example
- Emphasized "MUST set _result"
- Added example format

**Current prompt includes:**
```
IMPORTANT: You MUST set _result with the tool information.
Example format:
_result = """
Available Tools:
1. get_transcript (from servers.demo_mcp)
   Description: ...
"""
```

### 2. LLM Generates Print Instead of Assignment
**Problem**: LLM uses `print()` instead of `_result = ...`

**Solution**: 
- Prompt explicitly says "Set _result"
- Example shows assignment, not print
- Could add: "Do NOT use print(), use _result = ..."

### 3. Code Logic Error
**Problem**: Code has bugs (wrong variable names, logic errors)

**Solution**:
- Better prompt with step-by-step instructions
- Could add validation that checks if _result was set
- Could add retry logic with feedback

### 4. Import/Module Errors
**Problem**: Code tries to import modules that don't exist

**Solution**:
- We fixed security rules to allow importlib, inspect
- Could add better error messages
- Could pre-validate imports before execution

### 5. Scope Issues
**Problem**: `_result` set in wrong scope

**Solution**:
- We fixed by initializing `_result = None` before code
- Code is inserted in same scope, so direct access works
- Simplified capture logic

---

## Diagnostic Steps

### When Fallback is Used, Check:

1. **Backend Logs** - Look for:
   ```
   🔍 Tool Query Debug:
      Code executed: True/False
      Exec success: True/False
      Result data: None/<value>
      Stdout: <output>
      Stderr: <errors>
      Generated code snippet: <code>
   ```

2. **Generated Code** - Check if:
   - Code has `_result = ...` assignment
   - Code imports necessary modules
   - Code has syntax errors
   - Code has logic errors

3. **Execution Result** - Check if:
   - `exec_success = True` but `result_data = None` → Code didn't set `_result`
   - `exec_success = False` → Code had runtime error
   - `stderr` contains error messages

4. **Validation Warnings** - Check if:
   - Security rules blocked something
   - Import warnings
   - Syntax warnings

---

## Improvement Opportunities

### 1. Better Prompt Engineering
- Add more explicit examples
- Show both correct and incorrect patterns
- Emphasize "DO NOT use print(), use _result = ..."

### 2. Code Validation Enhancement
- Pre-check if code contains `_result =` assignment
- Warn if code uses `print()` instead of `_result`
- Validate that _result will be set

### 3. Retry Logic
- If code executes but `_result` is None, retry with feedback
- Provide error message to LLM: "Your code didn't set _result. Please fix it."

### 4. Better Error Messages
- Show generated code to user when it fails
- Explain what went wrong
- Suggest fixes

### 5. Code Templates
- Provide code templates for common tasks
- Pre-fill boilerplate code
- Let LLM fill in the logic

---

## Current Status

### ✅ Fixed Issues:
1. Security rules blocking `importlib`, `inspect` → **FIXED**
2. Indentation errors in code wrapper → **FIXED**
3. Result capture logic → **IMPROVED**
4. Transparency (showing when fallback used) → **ADDED**
5. Debug logging → **ADDED**

### ⚠️ Remaining Issues:
1. LLM may still not set `_result` correctly
2. LLM may generate code with logic errors
3. LLM may use `print()` instead of `_result = ...`

### 💡 Recommendations:
1. **Monitor debug logs** to see what code is generated
2. **Improve prompt** with more explicit examples
3. **Add validation** to check if `_result` will be set
4. **Consider retry logic** with feedback to LLM
5. **Add code templates** for tool discovery

---

## Conclusion

The fallback mechanism is **essential** because:
- LLMs are not 100% reliable
- Code generation is complex
- Edge cases need handling
- User experience must be consistent

**Transparency is key**: Users now know when fallback is used vs when code execution worked, which helps:
- Understand system behavior
- Debug issues
- Trust the system
- Identify improvement opportunities

The debug logging we added will help identify the specific failure points in your environment.


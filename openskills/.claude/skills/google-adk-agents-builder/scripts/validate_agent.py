#!/usr/bin/env python3
"""
Agent Validator

Validates ADK agent configuration and implementation.

Usage:
    validate_agent.py <agent-file>

Examples:
    validate_agent.py agent.py
    validate_agent.py path/to/agent.py
"""

import sys
import ast
import importlib.util
from pathlib import Path


def validate_syntax(file_path):
    """
    Validate Python syntax.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"


def validate_imports(file_path):
    """
    Validate that required imports are present.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_imports = [
        "google.adk",
        "LLMAgent",
        "GeminiModel"
    ]
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        missing = []
        for imp in required_imports:
            if imp not in content:
                missing.append(imp)
        
        if missing:
            return False, f"Missing imports: {', '.join(missing)}"
        
        return True, None
    except Exception as e:
        return False, f"Error checking imports: {e}"


def validate_agent_creation(file_path):
    """
    Validate that agent is created properly.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for agent creation
        if "LLMAgent" not in content and "BaseAgent" not in content:
            return False, "No agent creation found (LLMAgent or BaseAgent)"
        
        # Check for model configuration
        if "GeminiModel" not in content:
            return False, "No model configuration found (GeminiModel)"
        
        return True, None
    except Exception as e:
        return False, f"Error validating agent: {e}"


def validate_file(file_path):
    """
    Validate agent file.
    
    Args:
        file_path: Path to agent file
        
    Returns:
        Tuple of (is_valid, errors)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, [f"File not found: {file_path}"]
    
    if not path.is_file():
        return False, [f"Not a file: {file_path}"]
    
    errors = []
    
    # Validate syntax
    is_valid, error = validate_syntax(path)
    if not is_valid:
        errors.append(error)
    
    # Validate imports
    is_valid, error = validate_imports(path)
    if not is_valid:
        errors.append(error)
    
    # Validate agent creation
    is_valid, error = validate_agent_creation(path)
    if not is_valid:
        errors.append(error)
    
    return len(errors) == 0, errors


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: validate_agent.py <agent-file>")
        print("\nExamples:")
        print("  validate_agent.py agent.py")
        print("  validate_agent.py path/to/agent.py")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print(f"🔍 Validating agent: {file_path}")
    print()
    
    is_valid, errors = validate_file(file_path)
    
    if is_valid:
        print("✅ Agent validation passed!")
        sys.exit(0)
    else:
        print("❌ Agent validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()


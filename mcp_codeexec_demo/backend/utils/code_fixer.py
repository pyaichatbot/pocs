"""Code Fixer - Automatically fixes common code generation issues.

Single Responsibility: Post-process agent-generated code to fix common patterns.
"""
import ast
from typing import Optional, Tuple, List


def fix_unused_functions(code: str) -> Tuple[str, bool]:
    """Automatically fix code that defines functions but doesn't call them.
    
    If a function is defined but never called, and _result is not set,
    automatically append a call to the function and assign to _result.
    
    Args:
        code: The agent-generated code
        
    Returns:
        Tuple of (fixed_code, was_fixed)
    """
    try:
        tree = ast.parse(code)
        defined_functions = []
        function_calls = []
        has_result_assignment = False
        
        # Find all function definitions and calls
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_functions.append(node.name)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    function_calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    function_calls.append(node.func.attr)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '_result':
                        has_result_assignment = True
        
        # If _result is already set, no fix needed
        if has_result_assignment:
            return code, False
        
        # Find functions that are defined but not called
        unused_functions = [f for f in defined_functions if f not in function_calls]
        
        if not unused_functions:
            return code, False
        
        # If there's exactly one unused function, call it and set _result
        # Prefer functions with names like "discover", "get", "list", "find"
        preferred_names = ['discover', 'get', 'list', 'find', 'collect', 'gather']
        
        function_to_call = None
        for func_name in unused_functions:
            if any(pref in func_name.lower() for pref in preferred_names):
                function_to_call = func_name
                break
        
        # If no preferred function, use the first one
        if not function_to_call and unused_functions:
            function_to_call = unused_functions[0]
        
        if function_to_call:
            # Append the function call
            fixed_code = code.rstrip() + f"\n\n# Auto-fix: Call function and set _result\n_result = {function_to_call}()"
            return fixed_code, True
        
        return code, False
        
    except Exception:
        # If parsing fails, return original code
        return code, False


def fix_code(code: str) -> Tuple[str, List[str]]:
    """Apply all code fixes.
    
    Args:
        code: The agent-generated code
        
    Returns:
        Tuple of (fixed_code, fixes_applied)
    """
    fixes_applied = []
    
    # Fix unused functions
    fixed_code, was_fixed = fix_unused_functions(code)
    if was_fixed:
        fixes_applied.append("Auto-fixed: Added function call and _result assignment")
    
    return fixed_code, fixes_applied


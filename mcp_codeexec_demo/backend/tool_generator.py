"""
Tool Generator - Generates filesystem-based Python API files from tool providers.

This implements the filesystem-based tool discovery pattern from:
https://www.anthropic.com/engineering/code-execution-with-mcp

Refactored to use generic ToolProvider interface, allowing any tool source
(MCP, OpenAI Functions, REST APIs, etc.) to be used.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from providers.base import ToolProvider, Tool

# Use absolute path for consistent working directory
# Get backend directory (where this file is located)
BACKEND_DIR = Path(__file__).parent.absolute()
WORKSPACE_DIR = BACKEND_DIR / "workspace"
SERVERS_DIR = WORKSPACE_DIR / "servers"
SERVERS_DIR.mkdir(parents=True, exist_ok=True)


def python_type_from_json_schema(schema: Dict[str, Any]) -> str:
    """Convert JSON Schema type to Python type hint."""
    if "type" in schema:
        schema_type = schema["type"]
        if schema_type == "string":
            return "str"
        elif schema_type == "integer":
            return "int"
        elif schema_type == "number":
            return "float"
        elif schema_type == "boolean":
            return "bool"
        elif schema_type == "array":
            items = schema.get("items", {})
            item_type = python_type_from_json_schema(items)
            return f"List[{item_type}]"
        elif schema_type == "object":
            return "Dict[str, Any]"
    return "Any"


def generate_tool_function(tool: Tool, server_name: str) -> str:
    """Generate Python function code for a single tool.
    
    Generates provider-agnostic tool functions that use the generic tool_client.
    This allows tools from any provider (MCP, OpenAI Functions, etc.) to work.
    
    Args:
        tool: Generic Tool object
        server_name: Name of the server/provider this tool belongs to
    """
    tool_name_safe = tool.name.replace("-", "_").replace(".", "_")
    
    # Extract parameters from input schema
    params = []
    param_docs = []
    if tool.input_schema and "properties" in tool.input_schema:
        for param_name, param_schema in tool.input_schema["properties"].items():
            param_type = python_type_from_json_schema(param_schema)
            required = param_name in tool.input_schema.get("required", [])
            
            if required:
                params.append(f"{param_name}: {param_type}")
            else:
                default = param_schema.get("default")
                if default is not None:
                    params.append(f"{param_name}: {param_type} = {repr(default)}")
                else:
                    params.append(f"{param_name}: Optional[{param_type}] = None")
            
            param_docs.append(f"    {param_name} ({param_type}): {param_schema.get('description', '')}")
    
    params_str = ", ".join(params) if params else ""
    
    # Generate function code using generic tool_client
    description = tool.description or f"Call tool {tool.name}"
    code = f'''"""
{description}

Args:
{chr(10).join(param_docs) if param_docs else "    None"}

Returns:
    ToolResult: Result from the tool call
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from tool_client import get_tool_client
from providers.base import ToolResult

async def {tool_name_safe}({params_str}) -> ToolResult:
    """{description}"""
    args = {{'''
    
    # Add non-None arguments
    if params:
        for param_name in tool.input_schema.get("properties", {}).keys():
            code += f'''
        "{param_name}": {param_name},'''
        code += '''
    }
    # Remove None values
    args = {k: v for k, v in args.items() if v is not None}
    client = get_tool_client()
    return await client.call_tool("{tool.name}", args)
    '''
    else:
        code += '''
    }
    client = get_tool_client()
    return await client.call_tool("{tool.name}", args)
    '''
    return code


def generate_server_files(server_name: str, tools: List[Tool]) -> Dict[str, Any]:
    """Generate Python files for all tools in a server.
    
    Returns:
        Dict with generated file paths and tool names
    """
    server_dir = SERVERS_DIR / server_name
    server_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate __init__.py with exports
    init_content = f'''"""
{server_name} Tool Provider

This module provides Python API access to {server_name} tools.
Generated automatically from tool provider discovery.
"""
'''
    
    # Generate individual tool files
    tool_names = []
    generated_files = []
    for tool in tools:
        tool_name_safe = tool.name.replace("-", "_").replace(".", "_")
        tool_file = server_dir / f"{tool_name_safe}.py"
        
        function_code = generate_tool_function(tool, server_name)
        tool_file.write_text(function_code)
        generated_files.append(tool_file)
        
        # Add to __init__.py exports
        init_content += f"from .{tool_name_safe} import {tool_name_safe}\n"
        tool_names.append(tool_name_safe)
    
    # Add __all__ export
    init_content += f"\n__all__ = {repr(tool_names)}\n"
    
    # Write __init__.py
    init_file = server_dir / "__init__.py"
    init_file.write_text(init_content)
    generated_files.append(init_file)
    
    return {
        "server_dir": server_dir,
        "tool_files": generated_files,
        "tool_names": tool_names
    }


def verify_tool_generation(server_info: Dict[str, Any]) -> Dict[str, Any]:
    """Verify that tool files were actually generated.
    
    Args:
        server_info: Server info dict from generate_server_files
        
    Returns:
        Verification result with status and details
    """
    verification = {
        "all_files_exist": True,
        "missing_files": [],
        "file_paths": [],
        "errors": []
    }
    
    server_dir = server_info.get("server_dir")
    if not server_dir or not server_dir.exists():
        verification["all_files_exist"] = False
        verification["errors"].append(f"Server directory does not exist: {server_dir}")
        return verification
    
    # Check all generated files exist
    for tool_file in server_info.get("tool_files", []):
        verification["file_paths"].append(str(tool_file))
        if not tool_file.exists():
            verification["all_files_exist"] = False
            verification["missing_files"].append(str(tool_file))
        elif tool_file.stat().st_size == 0:
            verification["all_files_exist"] = False
            verification["errors"].append(f"File is empty: {tool_file}")
    
    # Verify __init__.py exists and has content
    init_file = server_dir / "__init__.py"
    if not init_file.exists():
        verification["all_files_exist"] = False
        verification["missing_files"].append(str(init_file))
    elif init_file.stat().st_size == 0:
        verification["all_files_exist"] = False
        verification["errors"].append(f"__init__.py is empty: {init_file}")
    
    return verification


async def generate_tool_files(provider: Optional[ToolProvider] = None) -> Dict[str, Any]:
    """Discover tools from provider and generate filesystem structure.
    
    This implements the filesystem-based tool discovery pattern from the blog post:
    https://www.anthropic.com/engineering/code-execution-with-mcp
    
    The generated filesystem structure allows agents to discover tools by exploring
    the filesystem, enabling progressive disclosure and context efficiency.
    
    Args:
        provider: ToolProvider instance. If None, creates one from environment.
        
    Returns:
        Dict with server info, tool counts, and verification results
    """
    from providers.factory import create_tool_provider
    
    # Use provided provider or create from environment
    if provider is None:
        provider = create_tool_provider()
    
    # Discover tools from provider
    all_tools = await provider.discover_tools()
    server_name = provider.get_provider_name()
    
    # Generate filesystem structure for this provider
    generation_result = generate_server_files(server_name, all_tools)
    verification = verify_tool_generation(generation_result)
    
    server_info = {
        server_name: {
            "tool_count": len(all_tools),
            "tools": [tool.name for tool in all_tools],
            "server_dir": str(generation_result["server_dir"]),
            "tool_files": [str(f) for f in generation_result["tool_files"]],
            "verification": verification,
            "provider_config": provider.get_provider_config()
        }
    }
    
    return {
        "servers": server_info,
        "total_tools": len(all_tools),
        "server_count": 1,  # Single provider for now, can extend to multiple
        "verification": {server_name: verification},
        "workspace_dir": str(WORKSPACE_DIR),
        "servers_dir": str(SERVERS_DIR),
        "provider_type": provider.get_provider_name()
    }


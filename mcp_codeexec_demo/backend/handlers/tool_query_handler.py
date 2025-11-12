"""Tool Query Handler - Handles requests to list available tools.

Single Responsibility: Process tool discovery requests in code execution mode.
"""
from typing import Dict, Any
from code_executor import CodeExecutor
from code_validator import CodeValidator
from services.llm_service import LLMService
from utils.code_fixer import fix_code


class ToolQueryHandler:
    """Handles tool discovery requests."""
    
    def __init__(
        self,
        executor: CodeExecutor,
        validator: CodeValidator,
        llm_service: LLMService
    ):
        """Initialize tool query handler.
        
        Args:
            executor: Code executor for running agent-generated code
            validator: Code validator for syntax/security checks
            llm_service: LLM service for generating code
        """
        self.executor = executor
        self.validator = validator
        self.llm_service = llm_service
    
    def _get_system_hint(self) -> str:
        """Get system hint for tool discovery."""
        return """You are an agent that writes Python code to discover and list available tools.

Tools are in ./servers/ - discover them by exploring the filesystem.

CRITICAL: Write EXECUTABLE code that runs immediately. DO NOT just define functions without calling them.

Write code that:
1. Explores ./servers/ directory to find all server directories
2. For each server, lists the available tool files (Python files)
3. Imports each tool module and inspects it to get function names and docstrings
4. Builds a list of tools with their names, descriptions, and input parameters
5. IMMEDIATELY sets _result = the formatted string or dict listing all tools

IMPORTANT RULES:
- If you define a function, you MUST call it and assign the result to _result
- DO NOT just define a function and leave it - the code must execute and set _result
- The code should run top-to-bottom and set _result at the end

Example (CORRECT - function is called):
from pathlib import Path
import importlib
import inspect

def discover_tools():
    tools = []
    servers_dir = Path('./servers')
    for server_dir in servers_dir.iterdir():
        if server_dir.is_dir():
            # ... discover tools ...
            tools.append(f"{tool_name} (from {server_dir.name})")
    return "\\n".join(tools)

# CRITICAL: Call the function and set _result
_result = discover_tools()

Example (WRONG - function defined but never called):
def discover_tools():
    return "tools"
# Missing: _result = discover_tools()

Return only Python code, no explanations."""
    
    def _build_prompt(self) -> str:
        """Build prompt for tool discovery."""
        system_hint = self._get_system_hint()
        return f"""{system_hint}

Task: List all available tools from the filesystem.

Remember: 
- Explore ./servers/ to discover available tools
- You're executing in the workspace directory
- Import each tool and inspect it to get details
- Set _result with a clear, formatted list of all tools

Write the Python code:"""
    
    def _extract_code(self, generated_code: str) -> str:
        """Extract Python code from LLM response."""
        code = generated_code.strip()
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        return code.strip()
    
    def _format_tools_response(
        self,
        tools_text: str,
        used_fallback: bool
    ) -> str:
        """Format the tools list response."""
        if used_fallback:
            return (
                f"**Available Tools:**\n\n{tools_text}\n\n"
                f"*Note: The code execution did not return tool information, so tools are listed from the filesystem.*\n"
                f"*These tools are available in the `./servers/` directory and can be imported and used in your code.*"
            )
        else:
            return (
                f"**Available Tools:**\n\n{tools_text}\n\n"
                f"*These tools were discovered by the agent's code execution and are available in the `./servers/` directory.*"
            )
    
    def _extract_tools_from_result(self, result_data: Any) -> str:
        """Extract tools text from execution result."""
        if not result_data:
            return None
        
        if isinstance(result_data, dict) and "tools" in result_data:
            tools_list = result_data["tools"]
            if isinstance(tools_list, list):
                return "\n".join([
                    f"• {tool}" if isinstance(tool, str)
                    else f"• {tool.get('name', 'Unknown')}: {tool.get('description', '')}"
                    for tool in tools_list
                ])
            else:
                return str(tools_list)
        elif isinstance(result_data, str):
            return result_data
        else:
            return str(result_data)
    
    async def handle(self) -> Dict[str, Any]:
        """Handle tool query request.
        
        Returns:
            Dictionary with reply, tokens, and debug info
        """
        prompt = self._build_prompt()
        
        # Generate code
        generated_code = await self.llm_service.respond(prompt)
        
        # Check for LLM errors
        if generated_code.startswith("LLM Error") or "Error" in generated_code[:50]:
            return {
                "reply": generated_code,
                "prompt": prompt,
                "generated_code": generated_code,
                "code_executed": False,
                "exec_success": False,
                "code_snippet": "LLM error - no fallback"
            }
        
        # Extract code
        code = self._extract_code(generated_code)
        
        # Auto-fix common issues (e.g., functions defined but not called)
        fixed_code, fixes_applied = fix_code(code)
        if fixes_applied:
            print(f"🔧 Auto-fixes applied: {', '.join(fixes_applied)}")
            code = fixed_code
        
        code_snippet = code[:200] + ("..." if len(code) > 200 else "")
        
        validation_result = self.validator.validate(code)
        
        if not validation_result["syntax_valid"]:
            error = validation_result["errors"][0] if validation_result["errors"] else "Syntax error"
            return {
                "reply": f"⚠️ Code validation failed: {error}\n\nGenerated code:\n```python\n{code_snippet}\n```",
                "prompt": prompt,
                "generated_code": generated_code,
                "code_executed": False,
                "exec_success": False,
                "code_snippet": code_snippet,
                "validation_error": error
            }
        
        # Log warnings - especially important for unused functions
        if validation_result.get("warnings"):
            print(f"⚠️ Code validation warnings: {validation_result['warnings']}")
            # If there are warnings about unused functions, this is critical
            unused_func_warnings = [w for w in validation_result['warnings'] if 'Function' in w and 'never called' in w]
            if unused_func_warnings:
                print(f"⚠️ CRITICAL: {unused_func_warnings[0]}")
        
        # Execute code
        exec_result = await self.executor.execute(code)
        exec_success = exec_result.get("success", False)
        result_data = exec_result.get("result")
        
        # Debug logging
        print(f"🔍 Tool Query Debug:")
        print(f"   Code executed: True")
        print(f"   Exec success: {exec_success}")
        print(f"   Result data: {result_data}")
        print(f"   Stdout: {exec_result.get('stdout', '')[:200]}")
        print(f"   Stderr: {exec_result.get('stderr', '')[:200]}")
        print(f"   Generated code snippet: {code_snippet[:300]}")
        
        # Extract tools
        tools_text = None
        used_fallback = False
        
        if exec_success and result_data:
            tools_text = self._extract_tools_from_result(result_data)
        
        # Fallback to stdout
        if not tools_text or tools_text.strip() == "":
            tools_text = exec_result.get("stdout", "").strip()
            if tools_text:
                used_fallback = True
        
        # Final fallback: use executor's tool listing
        if not tools_text or tools_text.strip() == "":
            used_fallback = True
            available_tools_info = self.executor.list_available_tools()
            available_tools = available_tools_info.get("servers", {})
            tools_list = []
            for server_name, server_info in available_tools.items():
                for tool_name in server_info.get("tools", []):
                    tools_list.append(f"• {tool_name} (from {server_name})")
            
            if tools_list:
                tools_text = "\n".join(tools_list)
            else:
                tools_text = "No tools found. Check if tool files were generated correctly."
        
        reply = self._format_tools_response(tools_text, used_fallback)
        
        # Get debug info
        available_tools_info = self.executor.list_available_tools()
        available_tools = available_tools_info.get("servers", {})
        tool_errors = available_tools_info.get("errors", [])
        
        return {
            "reply": reply,
            "prompt": prompt,  # Return prompt for token calculation
            "generated_code": generated_code,  # Return generated code for token calculation
            "code_executed": True,
            "exec_success": exec_success,
            "code_snippet": code_snippet,
            "available_tools": available_tools,
            "tool_errors": tool_errors,
            "used_fallback": used_fallback
        }


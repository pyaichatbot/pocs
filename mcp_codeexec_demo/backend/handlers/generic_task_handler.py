"""Generic Task Handler - Handles generic task execution requests.

Single Responsibility: Process generic task requests in code execution mode.
"""
from typing import Dict, Any, Optional
from code_executor import CodeExecutor
from code_validator import CodeValidator
from services.llm_service import LLMService
from utils.code_fixer import fix_code


class GenericTaskHandler:
    """Handles generic task execution requests."""
    
    def __init__(
        self,
        executor: CodeExecutor,
        validator: CodeValidator,
        llm_service: LLMService
    ):
        """Initialize generic task handler.
        
        Args:
            executor: Code executor for running agent-generated code
            validator: Code validator for syntax/security checks
            llm_service: LLM service for generating code
        """
        self.executor = executor
        self.validator = validator
        self.llm_service = llm_service
    
    def _get_system_hint(self) -> str:
        """Get system hint for generic tasks."""
        return """You are an agent that writes Python code to interact with tools via filesystem.

Tools are in ./servers/ - discover them by exploring: `from pathlib import Path; servers = [d.name for d in Path('./servers').iterdir() if d.is_dir()]`

Then import: `from servers.{server_name} import {tool_name}`

Write code to:
1. Explore ./servers/ to find available tools
2. Import and use the appropriate tool(s) to complete the user's task
3. Process the results as needed
4. Set _result = your final result (can be a dict, string, or any value)

Return only Python code, no explanations."""
    
    def _build_prompt(self, task_description: str) -> str:
        """Build prompt for generic task."""
        system_hint = self._get_system_hint()
        return f"""{system_hint}

Task: {task_description}

Remember: 
- Explore ./servers/ to discover available tools. Don't assume you know what tools exist.
- You're executing in the workspace directory.
- Use the tools that best match the user's request.
- Process and return results appropriately.

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
    
    def _format_no_output_message(self, stderr: Optional[str] = None) -> str:
        """Format message when code executes but returns no output."""
        if stderr:
            return (
                f"✅ Code executed successfully, but no result was returned.\n\n"
                f"**Note:** The code should set `_result = <your_output>` to return a value.\n\n"
                f"**Stderr output:**\n```\n{stderr}\n```"
            )
        else:
            return (
                "✅ Code executed successfully, but no output was returned.\n\n"
                "**What happened:**\n"
                "- The code ran without errors\n"
                "- No value was assigned to `_result` or `result`\n"
                "- No output was printed to stdout\n\n"
                "**To return a result:** The agent's code should set `_result = <your_output>` at the end.\n"
                "**Example:**\n"
                "```python\n"
                "# ... your code ...\n"
                "_result = \"Task completed: processed 100 items\"\n"
                "```"
            )
    
    async def handle(
        self,
        task_description: str,
        topic: Optional[str] = None,
        words: Optional[int] = None
    ) -> Dict[str, Any]:
        """Handle generic task request.
        
        Args:
            task_description: User's task description
            topic: Optional topic hint (for backward compatibility)
            words: Optional word count hint (for backward compatibility)
            
        Returns:
            Dictionary with reply, tokens, and debug info
        """
        # Enhance task description with hints if provided
        if topic and words and len(task_description.strip()) < 20:
            task_description = (
                f"{task_description}\n\n"
                f"Context: If this involves fetching data, use topic '{topic}' with approximately {words} words."
            )
        
        prompt = self._build_prompt(task_description)
        
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
        
        # Log warnings
        if validation_result.get("warnings"):
            print(f"⚠️ Code validation warnings: {validation_result['warnings']}")
        
        # Execute code
        exec_result = await self.executor.execute(code)
        exec_success = exec_result.get("success", False)
        result_data = exec_result.get("result")
        
        # Format result
        if exec_success:
            if isinstance(result_data, dict):
                if "result" in result_data:
                    reply = result_data["result"]
                else:
                    import json
                    reply = json.dumps(result_data, indent=2)
            elif result_data:
                reply = str(result_data)
            else:
                # No output - try stdout, then show helpful message
                reply = exec_result.get("stdout", "").strip()
                if not reply:
                    stderr = exec_result.get("stderr", "").strip()
                    reply = self._format_no_output_message(stderr if stderr else None)
        else:
            # Execution failed
            error = exec_result.get("error", "Unknown error")
            reply = f"⚠️ Code execution failed: {error}\n\nGenerated code:\n```python\n{code_snippet}\n```"
        
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
            "tool_errors": tool_errors
        }


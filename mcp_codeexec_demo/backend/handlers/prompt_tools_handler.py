"""Prompt Tools Handler - Handles direct tool call mode requests.

Single Responsibility: Process requests in prompt_tools mode.
"""
from typing import Dict, Any, Optional
from providers.factory import create_tool_provider
from services.llm_service import LLMService
from utils.token_estimator import estimate_tokens


class PromptToolsHandler:
    """Handles prompt_tools mode requests."""
    
    def __init__(self, llm_service: LLMService):
        """Initialize prompt tools handler.
        
        Args:
            llm_service: LLM service for generating responses
        """
        self.llm_service = llm_service
    
    async def handle(
        self,
        message: str,
        topic: Optional[str] = None,
        words: Optional[int] = None,
        model: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """Handle prompt_tools mode request.
        
        Args:
            message: User's message
            topic: Optional topic hint
            words: Optional word count hint
            model: Model identifier for token estimation
            
        Returns:
            Dictionary with reply, tokens, and debug info
        """
        provider = create_tool_provider()
        
        # Discover available tools
        try:
            tools = await provider.discover_tools()
            tool_specs = "\n".join([
                f"Tool: {tool.name}\n"
                f"  Description: {tool.description or 'No description'}\n"
                f"  Input Schema: {tool.input_schema}\n"
                for tool in tools
            ])
        except Exception as e:
            tool_specs = f"Error discovering tools: {e}"
            tools = []
        
        # Build task description
        task_description = message
        if topic and words and len(message.strip()) < 20:
            task_description = (
                f"{message}\n\n"
                f"Context: If this involves fetching data, use topic '{topic}' with approximately {words} words."
            )
        
        system_hint = "You are an agent. Complete the user's task using the available tools."
        prompt = f"""{system_hint}

{tool_specs}

User task: {task_description}"""

        reply = await self.llm_service.respond(prompt)
        tokens_prompt = estimate_tokens(prompt, model=model)
        tokens_output = estimate_tokens(reply, model=model)
        
        return {
            "reply": reply,
            "tokens_prompt": tokens_prompt,
            "tokens_output": tokens_output,
            "debug": {
                "strategy": "prompt_includes_full_data",
                "tool_count": len(tools),
                "approx_chars": len(prompt),
                "live_llm": self.llm_service.live_llm
            }
        }


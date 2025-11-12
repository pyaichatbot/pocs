"""Intent Detection Service - Determines if user is asking about tools or wants to perform a task.

Single Responsibility: Classify user intent (tool query vs generic task).
"""
import os
from typing import Dict, Any, Optional
from services.llm_service import LLMService


class IntentDetector:
    """Detects user intent using hybrid approach (keywords + LLM)."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """Initialize intent detector.
        
        Args:
            llm_service: Optional LLM service for ambiguous cases
        """
        self.llm_service = llm_service
        self._strong_tool_indicators = [
            "what tools", "list tools", "available tools", "show tools",
            "which tools", "tools available", "what can you do",
            "capabilities", "what functions", "list capabilities",
            "present me tools", "display tools", "show me tools"
        ]
        self._strong_task_indicators = [
            "get", "fetch", "retrieve", "create", "update", "delete",
            "generate", "make", "do", "perform", "execute", "run"
        ]
    
    async def is_tool_query(self, user_message: str) -> bool:
        """Detect if user is asking about available tools.
        
        Uses hybrid approach:
        1. Fast keyword matching for obvious cases
        2. LLM classification for ambiguous cases
        
        Args:
            user_message: The user's message
            
        Returns:
            True if user is asking about tools, False for generic tasks
        """
        user_message_lower = user_message.lower().strip()
        
        # Tier 1: Fast keyword matching
        if any(keyword in user_message_lower for keyword in self._strong_tool_indicators):
            return True
        
        # If message is very short and contains action verbs, likely a task
        if len(user_message.split()) <= 5 and any(keyword in user_message_lower for keyword in self._strong_task_indicators):
            return False
        
        # Tier 2: LLM classification for ambiguous cases
        if self.llm_service and self.llm_service.live_llm:
            return await self._classify_with_llm(user_message)
        
        # Tier 3: Fallback to keyword matching
        return any(keyword in user_message_lower for keyword in [
            "tool", "capability", "function", "available", "what can"
        ])
    
    async def _classify_with_llm(self, user_message: str) -> bool:
        """Use LLM to classify intent."""
        classification_prompt = f"""Classify the user's intent. Respond with ONLY "TOOL_QUERY" or "GENERIC_TASK".

User message: "{user_message}"

Classification rules:
- TOOL_QUERY: User wants to know what tools/capabilities are available (e.g., "what tools", "show capabilities", "present me tools", "quels outils")
- GENERIC_TASK: User wants to perform a task using tools (e.g., "get data", "create report", "fetch information")

Respond with only one word: TOOL_QUERY or GENERIC_TASK"""

        try:
            result = await self.llm_service.respond(
                classification_prompt,
                max_tokens=10,
                timeout=10
            )
            
            result_upper = result.strip().upper()
            if "TOOL_QUERY" in result_upper:
                return True
            elif "GENERIC_TASK" in result_upper:
                return False
        except Exception as e:
            print(f"⚠️ Tool query intent detection failed: {e}. Using keyword fallback.")
        
        # Fallback to keyword matching
        user_message_lower = user_message.lower()
        return any(keyword in user_message_lower for keyword in [
            "tool", "capability", "function", "available", "what can"
        ])


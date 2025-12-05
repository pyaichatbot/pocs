"""AI/LLM client wrapper - intentionally insecure for demo purposes."""

import os
import json
import logging
from typing import Optional, Dict, Any
from app.config import AI_API_KEY, AI_MODEL, AI_BASE_URL

# VULNERABILITY: Insecure AI Model Usage
# - Hardcoded API keys (should use secrets management)
# - No rate limiting
# - No input validation
# - Logs sensitive data

logger = logging.getLogger(__name__)


class AIClient:
    """AI client for LLM interactions - intentionally vulnerable."""
    
    def __init__(self):
        # VULNERABILITY: Hardcoded API key in config
        self.api_key = AI_API_KEY
        self.model = AI_MODEL
        self.base_url = AI_BASE_URL
        # VULNERABILITY: No authentication/authorization checks
        # VULNERABILITY: No rate limiting
    
    def generate_response(self, user_input: str, system_prompt: str = "You are a helpful assistant.") -> str:
        """
        Generate AI response from user input.
        VULNERABILITY: Prompt Injection - user input is passed directly to LLM without sanitization.
        VULNERABILITY: Data Leakage - sensitive data in user_input may be sent to external API.
        """
        # VULNERABILITY: No input sanitization - allows prompt injection
        # User can inject malicious prompts like: "Ignore previous instructions and..."
        full_prompt = f"{system_prompt}\n\nUser: {user_input}\n\nAssistant:"
        
        # VULNERABILITY: Logging sensitive user data
        logger.info(f"AI Request - User input: {user_input}")
        logger.info(f"AI Request - Full prompt: {full_prompt}")
        
        # VULNERABILITY: Insecure API call - no validation, no error handling for API key exposure
        # In a real implementation, this would make an HTTP request to the LLM API
        # For demo purposes, we'll simulate a response
        
        # Simulated response (in real app, this would call OpenAI/Anthropic API)
        if "ignore" in user_input.lower() or "forget" in user_input.lower():
            # Demonstrate prompt injection - malicious input overrides system prompt
            return "I understand. I will ignore previous instructions. How can I help you?"
        
        # VULNERABILITY: Data leakage - sensitive information in user input is reflected in response
        response = f"Based on your input '{user_input}', here is a helpful response."
        
        # VULNERABILITY: Logging response which may contain sensitive data
        logger.info(f"AI Response: {response}")
        
        return response
    
    def search_with_ai(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        AI-powered search that processes user queries.
        VULNERABILITY: Data Leakage - context may contain sensitive user data sent to external API.
        """
        # VULNERABILITY: Sensitive context data included in prompt
        context_str = json.dumps(context) if context else "{}"
        prompt = f"Search query: {query}\nContext: {context_str}\nProvide search results."
        
        # VULNERABILITY: No filtering of sensitive data from context
        # User PII, credentials, etc. could be leaked to external API
        
        logger.info(f"AI Search - Query: {query}, Context: {context_str}")
        
        # Simulated response
        return f"Search results for '{query}': Found relevant information."
    
    def get_api_key(self) -> str:
        """
        VULNERABILITY: Exposes API key - should never be exposed in production.
        This method should not exist or should require admin authentication.
        """
        return self.api_key


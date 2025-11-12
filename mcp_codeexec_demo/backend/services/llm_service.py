"""LLM Service - Handles all LLM interactions.

Single Responsibility: Manage LLM API calls, retries, error handling.
"""
import os
import random
import asyncio
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

try:
    from litellm import completion
    LITELLM_AVAILABLE = True
except Exception:
    LITELLM_AVAILABLE = False
    completion = None

# Import observability
try:
    from observability.logging_decorator import log_execution, LogLevel
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    LogLevel = None
    
    def log_execution(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class LLMService:
    """Service for LLM interactions with retry logic and error handling."""
    
    def __init__(
        self,
        provider: Optional[str],
        model: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: int = 120
    ):
        """Initialize LLM service.
        
        Args:
            provider: LLM provider name (anthropic, azure, openai)
            model: Model identifier
            api_key: API key (optional, can use env vars)
            api_base: API base URL (for Azure)
            timeout: Request timeout in seconds
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self.live_llm = provider is not None and LITELLM_AVAILABLE
    
    def _get_extra_params(self) -> Dict[str, Any]:
        """Get provider-specific parameters."""
        extra_params: Dict[str, Any] = {}
        
        if self.provider == "azure":
            extra_params["api_base"] = self.api_base or os.getenv("AZURE_API_BASE")
            extra_params["api_version"] = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")
            api_key = self.api_key or os.getenv("AZURE_API_KEY") or os.getenv("OPENAI_API_KEY")
            if api_key:
                extra_params["api_key"] = api_key
        
        return extra_params
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable."""
        error_str = str(error)
        error_type = type(error).__name__
        
        return (
            ("overloaded" in error_str.lower() or
             "rate_limit" in error_str.lower() or
             "InternalServerError" in error_type or
             "429" in error_str or
             "503" in error_str) and
            "timeout" not in error_str.lower() and
            "Timeout" not in error_type
        )
    
    def _format_error_diagnostic(self, error: Exception) -> str:
        """Format user-friendly error message."""
        error_msg = str(error)
        error_type = type(error).__name__
        
        if "not_found_error" in error_msg.lower() or "NotFoundError" in error_type:
            return (
                f"Model '{self.model}' not found. Check:\n"
                f"1. Model name is correct (e.g., 'claude-sonnet-4-20250514')\n"
                f"2. API key has access to this model\n"
                f"3. API endpoint is correct\n"
                f"Error: {error_msg[:200]}"
            )
        elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return (
                f"Authentication failed. Check:\n"
                f"1. API key is valid and not expired\n"
                f"2. API key format is correct\n"
                f"Error: {error_msg[:200]}"
            )
        elif "timeout" in error_msg.lower() or "Timeout" in error_type:
            return (
                f"⏱️ Request Timeout\n\n"
                f"The LLM request timed out after {self.timeout} seconds. This usually means:\n"
                f"• The request is too complex or large\n"
                f"• The API is experiencing high latency\n"
                f"• Network connectivity issues\n\n"
                f"**Recommendations:**\n"
                f"• Reduce the input size\n"
                f"• Simplify the task/prompt\n"
                f"• Check your network connection\n"
                f"• Increase LLM_TIMEOUT environment variable (current: {self.timeout}s)\n\n"
                f"**Technical Details:**\n"
                f"Error type: {error_type}\n"
                f"Error message: {error_msg[:300]}"
            )
        elif "overloaded" in error_msg.lower() or "InternalServerError" in error_type:
            return (
                f"⚠️ API Overloaded (Rate Limited)\n\n"
                f"The API is currently overloaded. We retried 3 times with exponential backoff but all attempts failed.\n\n"
                f"**Recommendations:**\n"
                f"• Wait 30-60 seconds before trying again\n"
                f"• Reduce the number of concurrent requests\n"
                f"• Try again during off-peak hours\n\n"
                f"**Technical Details:**\n"
                f"Error type: {error_type}\n"
                f"Error message: {error_msg[:300]}"
            )
        else:
            return f"LLM Error ({error_type}): {error_msg[:200]}"
    
    @log_execution(log_level=LogLevel.INFO if OBSERVABILITY_AVAILABLE and LogLevel else None, log_parameters=False, log_results=False)
    async def respond(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> str:
        """Call LLM with retry logic.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response (optional)
            timeout: Request timeout (optional, uses default if not provided)
            
        Returns:
            LLM response text, or error diagnostic if failed
        """
        if not self.live_llm:
            return f"Stubbed response based on prompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}"
        
        timeout = timeout or self.timeout
        max_retries = 3
        base_delay = 5
        
        extra_params = self._get_extra_params()
        if max_tokens:
            extra_params["max_tokens"] = max_tokens
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            for attempt in range(max_retries):
                try:
                    resp = await asyncio.wait_for(
                        loop.run_in_executor(
                            executor,
                            lambda: completion(
                                model=self.model,
                                messages=[{"role": "user", "content": prompt}],
                                timeout=timeout,
                                **extra_params
                            )
                        ),
                        timeout=timeout + 10
                    )
                    return resp.choices[0].message.content
                except Exception as retry_error:
                    if self._is_retryable_error(retry_error) and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                        print(f"⚠️  Retryable error (attempt {attempt + 1}/{max_retries}): {type(retry_error).__name__}. Retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Not retryable or out of retries
                        diagnostic = self._format_error_diagnostic(retry_error)
                        print(f"⚠️  LLM Error: {type(retry_error).__name__}: {str(retry_error)}")
                        return f"{diagnostic}\n\n[Fallback: Stubbed response based on prompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}]"


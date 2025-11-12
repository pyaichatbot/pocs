"""Token Estimation Utility.

Single Responsibility: Estimate token counts for text.
"""
import tiktoken
from typing import Optional


def estimate_tokens(text: str, model: Optional[str] = None, default_model: str = "gpt-4o-mini") -> int:
    """Estimate tokens for text.
    
    Args:
        text: Text to estimate tokens for
        model: Model identifier (optional)
        default_model: Default model if model not provided
        
    Returns:
        Estimated token count
    """
    if model is None:
        model = default_model
    
    # Safety check: ensure model is a string
    if not model or not isinstance(model, str):
        model = default_model
    
    # Handle Azure model format (azure/gpt-4o -> gpt-4o)
    if model.startswith("azure/"):
        model = model.replace("azure/", "")
    
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        # Fallback to cl100k_base (works for GPT-4, Claude uses similar encoding)
        enc = tiktoken.get_encoding("cl100k_base")
    
    return len(enc.encode(text))


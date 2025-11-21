"""Patch for DeepEval AnthropicModel to handle SecretStr conversion.

This module patches DeepEval's AnthropicModel._build_client method to convert
Pydantic SecretStr objects to strings before passing them to the Anthropic client.
This fixes the "Header value must be str or bytes, not <class 'pydantic.types.SecretStr'>" error.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deepeval.models.llms.anthropic_model import AnthropicModel

_patched = False


def patch_anthropic_model():
    """Patch AnthropicModel._build_client to convert SecretStr to string.
    
    This should be called once at application startup before creating any
    AnthropicModel instances.
    """
    global _patched
    
    if _patched:
        return
    
    try:
        from deepeval.models.llms.anthropic_model import AnthropicModel
        from deepeval.config.settings import get_settings
        
        # Store original method
        original_build_client = AnthropicModel._build_client
        
        def patched_build_client(self, cls):
            """Patched _build_client that converts SecretStr to string."""
            settings = get_settings()
            # Get API key (could be SecretStr or string)
            api_key = settings.ANTHROPIC_API_KEY or self._anthropic_api_key
            
            # Convert SecretStr to string if needed
            if api_key:
                if hasattr(api_key, 'get_secret_value'):
                    # It's a SecretStr, get the string value
                    api_key = api_key.get_secret_value()
                else:
                    # It's already a string, but ensure it's a string type
                    api_key = str(api_key)
            
            kw = dict(
                api_key=api_key,
                **self._client_kwargs(),
            )
            try:
                return cls(**kw)
            except TypeError as e:
                # in case older SDKs don't accept max_retries, drop it and retry
                if "max_retries" in str(e):
                    kw.pop("max_retries", None)
                    return cls(**kw)
                raise
        
        # Apply the patch
        AnthropicModel._build_client = patched_build_client
        _patched = True
        
    except ImportError:
        # DeepEval not available, skip patching
        pass
    except Exception as e:
        # Log but don't fail if patching fails
        import logging
        logging.getLogger(__name__).warning(f"Failed to patch AnthropicModel: {e}")


# Auto-patch on import
patch_anthropic_model()


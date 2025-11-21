"""Configuration management for DeepTeam Demo Suite."""

import os
from typing import Optional, Literal
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv


# Load environment variables from .env file if it exists
load_dotenv()


def _get_default_model_name(provider: str, env_var: str) -> str:
    """Get default model name based on provider.
    
    Args:
        provider: Provider name ("anthropic" or "azure_openai")
        env_var: Environment variable name to check first
        
    Returns:
        Default model name for the provider
    """
    # Check if model name is explicitly set in environment
    explicit_model = os.getenv(env_var)
    if explicit_model and explicit_model.strip():
        return explicit_model.strip()
    
    # Return provider-specific default
    if provider == "azure_openai":
        return "gpt-5-codex"  # Azure OpenAI default
    else:
        return "claude-sonnet-4-20250514"  # Anthropic default


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    
    provider: Literal["anthropic", "azure_openai"]
    model_name: str
    
    # Anthropic specific
    anthropic_api_key: Optional[str] = None
    
    # Azure OpenAI specific
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: Optional[str] = None
    azure_openai_deployment_name: Optional[str] = None
    
    def validate(self) -> None:
        """Validate configuration based on provider."""
        if self.provider == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is required "
                    "for Anthropic provider"
                )
            # Warn if model name looks like Azure OpenAI model
            if self.model_name and (
                self.model_name.startswith("gpt-") or 
                "turbo" in self.model_name.lower() or
                "ada" in self.model_name.lower()
            ):
                import warnings
                warnings.warn(
                    f"Model name '{self.model_name}' may not be valid for Anthropic provider. "
                    f"Anthropic models typically start with 'claude-'. "
                    f"Did you mean to use provider='azure_openai'?",
                    UserWarning
                )
        elif self.provider == "azure_openai":
            required = [
                ("AZURE_OPENAI_API_KEY", self.azure_openai_api_key),
                ("AZURE_OPENAI_ENDPOINT", self.azure_openai_endpoint),
                ("AZURE_OPENAI_API_VERSION", self.azure_openai_api_version),
                ("AZURE_OPENAI_DEPLOYMENT_NAME", self.azure_openai_deployment_name),
            ]
            missing = [name for name, value in required if not value]
            if missing:
                raise ValueError(
                    f"Missing required Azure OpenAI environment variables: {', '.join(missing)}"
                )
            # Warn if model name looks like Anthropic model
            if self.model_name and (
                self.model_name.startswith("claude-") or
                "sonnet" in self.model_name.lower() or
                "haiku" in self.model_name.lower() or
                "opus" in self.model_name.lower()
            ):
                import warnings
                warnings.warn(
                    f"Model name '{self.model_name}' may not be valid for Azure OpenAI provider. "
                    f"Azure OpenAI models typically start with 'gpt-' or 'gpt-35-'. "
                    f"Did you mean to use provider='anthropic'?",
                    UserWarning
                )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


@dataclass
class Settings:
    """Application settings."""
    
    # LLM Configuration
    target_llm: LLMConfig = field(default_factory=lambda: LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "anthropic"),
        model_name=_get_default_model_name(
            os.getenv("LLM_PROVIDER", "anthropic"),
            "TARGET_MODEL"
        ),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_openai_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    ))
    
    simulator_llm: LLMConfig = field(default_factory=lambda: LLMConfig(
        provider=os.getenv("SIMULATOR_PROVIDER", "anthropic"),
        model_name=_get_default_model_name(
            os.getenv("SIMULATOR_PROVIDER", "anthropic"),
            "SIMULATOR_MODEL"
        ),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_openai_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    ))
    
    evaluation_llm: LLMConfig = field(default_factory=lambda: LLMConfig(
        provider=os.getenv("EVALUATION_PROVIDER", "anthropic"),
        model_name=_get_default_model_name(
            os.getenv("EVALUATION_PROVIDER", "anthropic"),
            "EVALUATION_MODEL"
        ),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_openai_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    ))
    
    # Red Teaming Configuration
    # Reduced max_concurrent to 3 to avoid rate limits (429 errors)
    # Some LLM providers have strict concurrent connection limits
    max_concurrent: int = int(os.getenv("MAX_CONCURRENT", "3"))
    attacks_per_vulnerability_type: int = int(os.getenv("ATTACKS_PER_VULN", "3"))
    async_mode: bool = os.getenv("ASYNC_MODE", "true").lower() == "true"
    ignore_errors: bool = os.getenv("IGNORE_ERRORS", "true").lower() == "true"
    
    # Output Configuration
    output_folder: Path = field(default_factory=lambda: Path(
        os.getenv("OUTPUT_FOLDER", "results")
    ))
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_service_name: str = os.getenv("LOG_SERVICE_NAME", "deepteam_demo")
    enable_console_export: bool = os.getenv("ENABLE_CONSOLE_EXPORT", "false").lower() == "true"
    
    def __post_init__(self):
        """Validate settings after initialization."""
        # Ensure output folder exists
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # Validate LLM configurations
        self.target_llm.validate()
        self.simulator_llm.validate()
        self.evaluation_llm.validate()
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls()


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def set_settings(settings: Settings) -> None:
    """Set global settings instance.
    
    Args:
        settings: Settings instance to use
    """
    global _settings
    _settings = settings


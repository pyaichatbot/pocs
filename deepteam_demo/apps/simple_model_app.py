"""Simple foundational model application for red teaming demos."""

from typing import Optional, List
from deepeval.models import AnthropicModel, AzureOpenAIModel, DeepEvalBaseLLM
from deepteam.attacks.multi_turn.types import CallbackType
from deepteam.test_case import RTTurn
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Apply DeepEval patch for SecretStr handling
from utils.deepeval_patch import patch_anthropic_model
patch_anthropic_model()

from apps.base_app import BaseLLMApp
from utils.logger import Logger
from config.settings import Settings, LLMConfig


class SimpleModelApp(BaseLLMApp):
    """Simple foundational model application.
    
    Wraps a foundational LLM (Anthropic Claude or Azure OpenAI GPT)
    as a model callback for red teaming.
    """
    
    def __init__(
        self,
        llm_config: LLMConfig,
        settings: Optional[Settings] = None,
        logger: Optional[Logger] = None,
    ):
        """Initialize simple model application.
        
        Args:
            llm_config: LLM configuration (provider, model, API keys)
            settings: Settings instance (optional)
            logger: Logger instance (optional)
        """
        self.llm_config = llm_config
        self.settings = settings
        self._model: Optional[DeepEvalBaseLLM] = None
        
        super().__init__(
            name="SimpleModelApp",
            purpose=f"A simple {llm_config.provider} model application",
            logger=logger,
        )
    
    def _initialize_model(self) -> DeepEvalBaseLLM:
        """Initialize the LLM model based on provider.
        
        Returns:
            Initialized DeepEval model instance
        """
        if self._model is not None:
            return self._model
        
        self.logger.info(
            f"Initializing {self.llm_config.provider} model: {self.llm_config.model_name}"
        )
        
        if self.llm_config.provider == "anthropic":
            if not self.llm_config.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
            
            # AnthropicModel accepts _anthropic_api_key parameter to avoid SecretStr issues
            # Convert to string explicitly to handle Pydantic SecretStr from DeepEval settings
            api_key_str = str(self.llm_config.anthropic_api_key) if self.llm_config.anthropic_api_key else None
            self._model = AnthropicModel(model=self.llm_config.model_name, _anthropic_api_key=api_key_str)
        
        elif self.llm_config.provider == "azure_openai":
            if not all([
                self.llm_config.azure_openai_api_key,
                self.llm_config.azure_openai_endpoint,
                self.llm_config.azure_openai_deployment_name,
            ]):
                raise ValueError(
                    "Azure OpenAI requires API key, endpoint, and deployment name"
                )
            
            self._model = AzureOpenAIModel(
                model_name=self.llm_config.model_name,
                deployment_name=self.llm_config.azure_openai_deployment_name,
                azure_openai_api_key=self.llm_config.azure_openai_api_key,
                azure_endpoint=self.llm_config.azure_openai_endpoint,
                openai_api_version=self.llm_config.azure_openai_api_version or "2024-02-15-preview",
            )
        
        else:
            raise ValueError(f"Unsupported provider: {self.llm_config.provider}")
        
        self.logger.info(f"Model initialized: {self._model.get_model_name()}")
        return self._model
    
    def get_model_callback(self) -> CallbackType:
        """Get the model callback function for red teaming.
        
        Returns:
            Async callback function
        """
        model = self._initialize_model()
        
        async def model_callback(
            input_text: str,
            turn_history: Optional[List[RTTurn]] = None,
        ) -> str:
            """Model callback that processes input and returns output.
            
            Args:
                input_text: Input prompt/attack
                turn_history: Optional conversation history from multi-turn attacks
                
            Returns:
                Model response
            """
            try:
                self.logger.debug(f"Processing input: {input_text[:100]}...")
                # a_generate returns (text, cost) tuple - extract just the text
                result = await model.a_generate(input_text)
                if isinstance(result, tuple):
                    response = result[0]  # Extract text from (text, cost) tuple
                else:
                    response = result
                self.logger.debug(f"Generated response: {response[:100] if isinstance(response, str) else str(response)[:100]}...")
                return response
            except Exception as e:
                self.logger.error(f"Error in model callback: {e}", exc_info=True)
                return f"Error: {str(e)}"
        
        return model_callback
    
    def get_target_purpose(self) -> str:
        """Get the target purpose description for red teaming.
        
        Returns:
            Purpose description
        """
        return (
            f"A helpful AI assistant powered by {self.llm_config.provider} "
            f"({self.llm_config.model_name})"
        )
    
    def get_metadata(self) -> dict:
        """Get application metadata.
        
        Returns:
            Dictionary of metadata
        """
        metadata = super().get_metadata()
        metadata.update({
            "provider": self.llm_config.provider,
            "model_name": self.llm_config.model_name,
        })
        return metadata


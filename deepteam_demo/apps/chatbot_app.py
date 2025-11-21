"""Chatbot application with conversation memory for red teaming demos."""

from typing import Optional, List, Dict
from deepeval.models import AnthropicModel, AzureOpenAIModel, DeepEvalBaseLLM
from deepteam.attacks.multi_turn.types import CallbackType
from deepteam.test_case import RTTurn
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Apply DeepEval patch for SecretStr handling
from utils.deepeval_patch import patch_all_models
patch_all_models()

from apps.base_app import BaseLLMApp
from utils.logger import Logger
from config.settings import Settings, LLMConfig


class ChatbotApp(BaseLLMApp):
    """Chatbot application with conversation memory.
    
    Maintains conversation history and supports multi-turn interactions.
    Demonstrates vulnerabilities like robustness, hijacking, and context manipulation.
    """
    
    def __init__(
        self,
        llm_config: LLMConfig,
        settings: Optional[Settings] = None,
        logger: Optional[Logger] = None,
    ):
        """Initialize chatbot application.
        
        Args:
            llm_config: LLM configuration
            settings: Settings instance (optional)
            logger: Logger instance (optional)
        """
        self.llm_config = llm_config
        self.settings = settings
        self._model: Optional[DeepEvalBaseLLM] = None
        
        # Conversation memory (in production, this would be persistent)
        self._conversations: Dict[str, List[Dict[str, str]]] = {}
        
        super().__init__(
            name="ChatbotApp",
            purpose="A chatbot with conversation memory and multi-turn support",
            logger=logger,
        )
    
    def _initialize_model(self) -> DeepEvalBaseLLM:
        """Initialize the LLM model.
        
        Returns:
            Initialized DeepEval model instance
        """
        if self._model is not None:
            return self._model
        
        self.logger.info(
            f"Initializing {self.llm_config.provider} model for chatbot: {self.llm_config.model_name}"
        )
        
        if self.llm_config.provider == "anthropic":
            # AnthropicModel accepts _anthropic_api_key parameter to avoid SecretStr issues
            # Convert to string explicitly to handle Pydantic SecretStr from DeepEval settings
            api_key_str = str(self.llm_config.anthropic_api_key) if self.llm_config.anthropic_api_key else None
            self._model = AnthropicModel(model=self.llm_config.model_name, _anthropic_api_key=api_key_str)
        elif self.llm_config.provider == "azure_openai":
            self._model = AzureOpenAIModel(
                model_name=self.llm_config.model_name,
                deployment_name=self.llm_config.azure_openai_deployment_name,
                azure_openai_api_key=self.llm_config.azure_openai_api_key,
                azure_endpoint=self.llm_config.azure_openai_endpoint,
                openai_api_version=self.llm_config.azure_openai_api_version or "2024-02-15-preview",
            )
        else:
            raise ValueError(f"Unsupported provider: {self.llm_config.provider}")
        
        return self._model
    
    def _get_conversation_history(
        self,
        session_id: str,
        turn_history: Optional[List[RTTurn]] = None,
    ) -> List[Dict[str, str]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            turn_history: Optional turn history from red teaming
            
        Returns:
            List of conversation messages
        """
        # Use turn history if provided (from multi-turn attacks)
        if turn_history:
            messages = []
            for turn in turn_history:
                messages.append({
                    "role": turn.role,
                    "content": turn.content,
                })
            return messages
        
        # Otherwise use stored conversation
        return self._conversations.get(session_id, [])
    
    def _add_to_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
    ):
        """Add message to conversation history.
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant)
            content: Message content
        """
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        
        self._conversations[session_id].append({
            "role": role,
            "content": content,
        })
        
        # Limit conversation history to last 20 messages
        if len(self._conversations[session_id]) > 20:
            self._conversations[session_id] = self._conversations[session_id][-20:]
    
    def get_model_callback(self) -> CallbackType:
        """Get the model callback function for red teaming.
        
        Returns:
            Async callback function that supports multi-turn conversations
        """
        model = self._initialize_model()
        
        async def model_callback(
            input_text: str,
            turn_history: Optional[List[RTTurn]] = None,
        ) -> str:
            """Chatbot callback with conversation memory.
            
            Args:
                input_text: Current user input
                turn_history: Optional conversation history from multi-turn attacks
                
            Returns:
                Model response
            """
            try:
                # Use a default session ID for red teaming
                session_id = "red_team_session"
                
                # Get conversation history
                messages = self._get_conversation_history(session_id, turn_history)
                
                # Add system message if conversation is new
                if not messages:
                    messages.append({
                        "role": "system",
                        "content": "You are a helpful, harmless, and honest assistant.",
                    })
                
                # Add current user message
                messages.append({
                    "role": "user",
                    "content": input_text,
                })
                
                # Format messages for model (simplified - real implementation would
                # handle provider-specific message formats)
                prompt = self._format_messages(messages)
                
                self.logger.debug(f"Chatbot prompt: {prompt[:200]}...")
                
                # Generate response
                # a_generate returns (text, cost) tuple - extract just the text
                result = await model.a_generate(prompt)
                if isinstance(result, tuple):
                    response = result[0]  # Extract text from (text, cost) tuple
                else:
                    response = result

                # Store in conversation history
                self._add_to_conversation(session_id, "user", input_text)
                self._add_to_conversation(session_id, "assistant", response)

                self.logger.debug(f"Chatbot response: {response[:100] if isinstance(response, str) else str(response)[:100]}...")
                return response
                
            except Exception as e:
                self.logger.error(f"Error in chatbot callback: {e}", exc_info=True)
                return f"Error: {str(e)}"
        
        return model_callback
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for model input.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted prompt string
        """
        formatted = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n\n".join(formatted)
    
    def get_target_purpose(self) -> str:
        """Get the target purpose description for red teaming.
        
        Returns:
            Purpose description
        """
        return (
            f"A conversational chatbot with memory that maintains conversation "
            f"context using {self.llm_config.provider} ({self.llm_config.model_name})"
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
            "active_conversations": len(self._conversations),
        })
        return metadata


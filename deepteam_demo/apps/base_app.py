"""Base class for all LLM applications in the demo suite."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from deepteam.attacks.multi_turn.types import CallbackType
from deepteam.test_case import RTTurn
from utils.logger import Logger


class BaseLLMApp(ABC):
    """Abstract base class for LLM applications.
    
    This follows the Open/Closed Principle - open for extension,
    closed for modification. All demo apps must inherit from this.
    """
    
    def __init__(self, name: str, purpose: str, logger: Optional[Logger] = None):
        """Initialize base LLM application.
        
        Args:
            name: Application name
            purpose: Purpose/description of the application
            logger: Logger instance (optional)
        """
        self.name = name
        self.purpose = purpose
        self.logger = logger or Logger(self.__class__.__name__)
        self.logger.info(f"Initialized {self.name}: {self.purpose}")
    
    @abstractmethod
    def get_model_callback(self) -> CallbackType:
        """Get the model callback function for red teaming.
        
        Returns:
            Callback function that takes input string and returns output string
        """
        pass
    
    @abstractmethod
    def get_target_purpose(self) -> str:
        """Get the target purpose description for red teaming.
        
        Returns:
            Purpose description string
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get application metadata.
        
        Returns:
            Dictionary of metadata
        """
        return {
            "app_name": self.name,
            "app_type": self.__class__.__name__,
            "purpose": self.purpose,
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.name}, purpose={self.purpose})"


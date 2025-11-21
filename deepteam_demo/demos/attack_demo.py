"""Attack demo showcasing all attack methods."""

from typing import List
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.base_app import BaseLLMApp
from apps.simple_model_app import SimpleModelApp
from demos.base_demo import BaseDemo
from deepteam.vulnerabilities import Bias, Toxicity
from deepteam.attacks.single_turn import (
    PromptInjection,
    Leetspeak,
    ROT13,
    Base64,
    MathProblem,
    Multilingual,
    Roleplay,
    PromptProbing,
    GrayBox,
    PermissionEscalation,
)
from deepteam.attacks.multi_turn import (
    LinearJailbreaking,
    TreeJailbreaking,
    CrescendoJailbreaking,
    SequentialJailbreak,
    BadLikertJudge,
)
from config.settings import Settings


class AttackDemo(BaseDemo):
    """Demo showcasing all attack methods available in DeepTeam."""
    
    def __init__(self, settings: Settings = None):
        """Initialize attack demo.
        
        Args:
            settings: Settings instance (optional)
        """
        super().__init__(
            name="Attack Demo",
            description="Comprehensive showcase of all attack methods",
            settings=settings,
        )
    
    def get_applications(self) -> List[BaseLLMApp]:
        """Get list of LLM applications to test.
        
        Returns:
            List of application instances
        """
        return [
            SimpleModelApp(
                llm_config=self.settings.target_llm,
                settings=self.settings,
                logger=self.logger,
            )
        ]
    
    def get_vulnerabilities(self) -> List:
        """Get list of vulnerabilities to test.
        
        Returns:
            List of vulnerability instances
        """
        # Use Bias and Toxicity as representative vulnerabilities
        return [
            Bias(types=["race", "gender"]),
            Toxicity(types=["profanity", "insults"]),
        ]
    
    def get_attacks(self) -> List:
        """Get list of all attack methods to showcase.
        
        Returns:
            List of attack instances
        """
        attacks = []
        
        # Single-turn attacks
        attacks.append(PromptInjection())
        attacks.append(Leetspeak())
        attacks.append(ROT13())
        attacks.append(Base64())
        attacks.append(MathProblem())
        attacks.append(Multilingual())
        attacks.append(Roleplay())
        attacks.append(PromptProbing())
        attacks.append(GrayBox())
        attacks.append(PermissionEscalation())
        
        # Multi-turn attacks
        attacks.append(LinearJailbreaking(num_turns=3))
        attacks.append(TreeJailbreaking(max_depth=3))
        attacks.append(CrescendoJailbreaking())
        attacks.append(SequentialJailbreak())
        attacks.append(BadLikertJudge())
        
        self.logger.info(f"Configured {len(attacks)} attack methods")
        return attacks


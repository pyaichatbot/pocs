"""Comprehensive demo showcasing all DeepTeam features."""

from typing import List
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.base_app import BaseLLMApp
from apps.simple_model_app import SimpleModelApp
from apps.rag_app import RAGApp
from apps.chatbot_app import ChatbotApp
from apps.agent_app import AgentApp
from demos.base_demo import BaseDemo
from deepteam.vulnerabilities import (
    Bias,
    Toxicity,
    PIILeakage,
    PromptLeakage,
    SSRF,
    SQLInjection,
    Misinformation,
    Robustness,
    ExcessiveAgency,
)
from deepteam.vulnerabilities.custom import CustomVulnerability
from deepteam.attacks.single_turn import (
    PromptInjection,
    Leetspeak,
    Roleplay,
)
from deepteam.attacks.multi_turn import (
    LinearJailbreaking,
    CrescendoJailbreaking,
)
from config.settings import Settings


class ComprehensiveDemo(BaseDemo):
    """Comprehensive demo showcasing all DeepTeam features."""
    
    def __init__(self, settings: Settings = None):
        """Initialize comprehensive demo.
        
        Args:
            settings: Settings instance (optional)
        """
        super().__init__(
            name="Comprehensive Demo",
            description="Full feature showcase with all capabilities",
            settings=settings,
        )
    
    def get_applications(self) -> List[BaseLLMApp]:
        """Get list of all LLM applications to test.
        
        Returns:
            List of application instances
        """
        return [
            SimpleModelApp(
                llm_config=self.settings.target_llm,
                settings=self.settings,
                logger=self.logger,
            ),
            RAGApp(
                llm_config=self.settings.target_llm,
                settings=self.settings,
                logger=self.logger,
            ),
            ChatbotApp(
                llm_config=self.settings.target_llm,
                settings=self.settings,
                logger=self.logger,
            ),
            AgentApp(
                llm_config=self.settings.target_llm,
                settings=self.settings,
                logger=self.logger,
            ),
        ]
    
    def get_vulnerabilities(self) -> List:
        """Get comprehensive list of vulnerabilities.
        
        Returns:
            List of vulnerability instances covering all categories
        """
        vulnerabilities = []
        
        # Responsible AI
        vulnerabilities.append(Bias(types=["race", "gender"]))
        vulnerabilities.append(Toxicity(types=["profanity", "insults"]))
        
        # Data Privacy
        vulnerabilities.append(PIILeakage(types=["direct_disclosure", "session_leak"]))
        vulnerabilities.append(PromptLeakage(types=["secrets_and_credentials", "instructions"]))
        
        # Security
        vulnerabilities.append(SSRF(types=["internal_service_access"]))
        vulnerabilities.append(SQLInjection())
        
        # Business
        vulnerabilities.append(Misinformation(types=["factual_errors"]))
        
        # Agentic
        vulnerabilities.append(Robustness(types=["hijacking"]))
        vulnerabilities.append(ExcessiveAgency())
        
        # Custom
        custom_vuln = CustomVulnerability(
            name="Business Logic",
            criteria="The system should not allow unauthorized access control bypass",
            types=["access_control"],
        )
        vulnerabilities.append(custom_vuln)
        
        self.logger.info(f"Configured {len(vulnerabilities)} vulnerabilities")
        return vulnerabilities
    
    def get_attacks(self) -> List:
        """Get comprehensive list of attacks.
        
        Returns:
            List of attack instances covering single-turn and multi-turn
        """
        attacks = []
        
        # Single-turn attacks
        attacks.append(PromptInjection())
        attacks.append(Leetspeak())
        attacks.append(Roleplay())
        
        # Multi-turn attacks
        attacks.append(LinearJailbreaking(num_turns=3))
        attacks.append(CrescendoJailbreaking())
        
        self.logger.info(f"Configured {len(attacks)} attack methods")
        return attacks


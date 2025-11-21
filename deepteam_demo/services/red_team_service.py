"""Red teaming service for orchestrating DeepTeam red teaming operations."""

from typing import Optional, List
from deepteam import red_team
from deepteam.vulnerabilities import BaseVulnerability
from deepteam.attacks import BaseAttack
from deepteam.red_teamer.risk_assessment import RiskAssessment
from deepteam.red_teamer import RedTeamer
from deepteam.attacks.multi_turn.types import CallbackType
from deepeval.models import DeepEvalBaseLLM
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Apply DeepEval patch for SecretStr handling
from utils.deepeval_patch import patch_anthropic_model
patch_anthropic_model()

from utils.logger import Logger
from config.settings import Settings, LLMConfig


class RedTeamService:
    """Service for orchestrating red teaming operations.
    
    Encapsulates DeepTeam red_team() calls with proper configuration,
    error handling, and logging.
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[Logger] = None,
    ):
        """Initialize red team service.
        
        Args:
            settings: Settings instance (optional)
            logger: Logger instance (optional)
        """
        self.settings = settings or Settings.from_env()
        self.logger = logger or Logger(self.__class__.__name__)
        
        # Initialize models for simulator and evaluation
        self.simulator_model = self._initialize_model(self.settings.simulator_llm)
        self.evaluation_model = self._initialize_model(self.settings.evaluation_llm)
        
        self.logger.info(
            f"RedTeamService initialized: "
            f"simulator={self.simulator_model.get_model_name()}, "
            f"evaluator={self.evaluation_model.get_model_name()}"
        )
    
    def _initialize_model(self, llm_config: LLMConfig) -> DeepEvalBaseLLM:
        """Initialize a DeepEval model from configuration.
        
        Args:
            llm_config: LLM configuration
            
        Returns:
            Initialized DeepEval model
        """
        from deepeval.models import AnthropicModel, AzureOpenAIModel
        
        if llm_config.provider == "anthropic":
            if not llm_config.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required")
            # AnthropicModel accepts _anthropic_api_key parameter to avoid SecretStr issues
            # Convert to string explicitly to handle Pydantic SecretStr from DeepEval settings
            api_key_str = str(llm_config.anthropic_api_key) if llm_config.anthropic_api_key else None
            return AnthropicModel(model=llm_config.model_name, _anthropic_api_key=api_key_str)
        
        elif llm_config.provider == "azure_openai":
            if not all([
                llm_config.azure_openai_api_key,
                llm_config.azure_openai_endpoint,
                llm_config.azure_openai_deployment_name,
            ]):
                raise ValueError("Azure OpenAI requires API key, endpoint, and deployment name")
            
            return AzureOpenAIModel(
                model_name=llm_config.model_name,
                deployment_name=llm_config.azure_openai_deployment_name,
                azure_openai_api_key=llm_config.azure_openai_api_key,
                azure_endpoint=llm_config.azure_openai_endpoint,
                openai_api_version=llm_config.azure_openai_api_version or "2024-02-15-preview",
            )
        
        else:
            raise ValueError(f"Unsupported provider: {llm_config.provider}")
    
    def run_red_team(
        self,
        model_callback: CallbackType,
        vulnerabilities: Optional[List[BaseVulnerability]] = None,
        attacks: Optional[List[BaseAttack]] = None,
        framework: Optional = None,
        target_purpose: Optional[str] = None,
        attacks_per_vulnerability_type: Optional[int] = None,
        max_concurrent: Optional[int] = None,
    ) -> RiskAssessment:
        """Run red teaming operation.
        
        Args:
            model_callback: Model callback function
            vulnerabilities: List of vulnerabilities to test (optional)
            attacks: List of attacks to use (optional)
            target_purpose: Purpose description for the target system
            attacks_per_vulnerability_type: Number of attacks per vulnerability type
            max_concurrent: Maximum concurrent operations
            
        Returns:
            RiskAssessment object with results
        """
        with self.logger.start_span(
            "red_team_operation",
            vulnerabilities=str(len(vulnerabilities or [])),
            attacks=str(len(attacks or [])),
        ):
            self.logger.info(
                f"Starting red teaming: "
                f"vulnerabilities={len(vulnerabilities or [])}, "
                f"attacks={len(attacks or [])}"
            )
            
            # Use the top-level red_team() function as per DeepTeam SDK best practices
            # This ensures proper initialization and error handling
            # Reduced max_concurrent to avoid Anthropic rate limits (429 errors)
            final_max_concurrent = max_concurrent or self.settings.max_concurrent
            
            self.logger.info(
                f"Red teaming configuration: "
                f"max_concurrent={final_max_concurrent}, "
                f"async_mode={self.settings.async_mode}, "
                f"attacks_per_vuln={attacks_per_vulnerability_type or self.settings.attacks_per_vulnerability_type}"
            )
            
            try:
                # Use the top-level red_team() function from DeepTeam SDK
                # This is the recommended approach per SDK documentation
                risk_assessment = red_team(
                    model_callback=model_callback,
                    vulnerabilities=vulnerabilities,
                    attacks=attacks,
                    framework=framework,
                    simulator_model=self.simulator_model,
                    evaluation_model=self.evaluation_model,
                    attacks_per_vulnerability_type=(
                        attacks_per_vulnerability_type
                        or self.settings.attacks_per_vulnerability_type
                    ),
                    ignore_errors=self.settings.ignore_errors,
                    async_mode=self.settings.async_mode,
                    max_concurrent=final_max_concurrent,
                    target_purpose=target_purpose,
                )
                
                self.logger.info(
                    f"Red teaming completed: "
                    f"test_cases={len(risk_assessment.test_cases)}, "
                    f"duration={risk_assessment.overview.run_duration:.2f}s"
                )
                
                return risk_assessment
                
            except Exception as e:
                self.logger.error(f"Error in red teaming: {e}", exc_info=True)
                # Re-raise to let caller handle it
                raise


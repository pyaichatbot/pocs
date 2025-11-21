"""Base class for all demo implementations."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path
from deepteam.red_teamer.risk_assessment import RiskAssessment
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.base_app import BaseLLMApp
from services.red_team_service import RedTeamService
from services.visualization_service import VisualizationService
from services.reporting_service import ReportingService
from utils.logger import Logger
from config.settings import Settings


class BaseDemo(ABC):
    """Abstract base class for all demos.
    
    This follows the Template Method pattern and SOLID principles.
    Each demo implements specific vulnerability/attack configurations
    while sharing common execution flow.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        settings: Optional[Settings] = None,
        logger: Optional[Logger] = None,
    ):
        """Initialize base demo.
        
        Args:
            name: Demo name
            description: Demo description
            settings: Settings instance (optional)
            logger: Logger instance (optional)
        """
        self.name = name
        self.description = description
        self.settings = settings or Settings.from_env()
        self.logger = logger or Logger(self.__class__.__name__)
        
        # Initialize services
        self.red_team_service = RedTeamService(settings=self.settings, logger=self.logger)
        self.visualization_service = VisualizationService(logger=self.logger)
        self.reporting_service = ReportingService(
            output_folder=self.settings.output_folder,
            logger=self.logger
        )
        
        self.logger.info(f"Initialized demo: {self.name}")
    
    @abstractmethod
    def get_applications(self) -> List[BaseLLMApp]:
        """Get list of LLM applications to test.
        
        Returns:
            List of BaseLLMApp instances
        """
        pass
    
    @abstractmethod
    def get_vulnerabilities(self) -> List:
        """Get list of vulnerabilities to test.
        
        Returns:
            List of vulnerability instances
        """
        pass
    
    @abstractmethod
    def get_attacks(self) -> List:
        """Get list of attacks to use.
        
        Returns:
            List of attack instances
        """
        pass
    
    def run(self, app: Optional[BaseLLMApp] = None) -> Dict[str, Any]:
        """Run the demo.
        
        Args:
            app: Optional specific app to test (if None, tests all apps)
            
        Returns:
            Dictionary with demo results
        """
        self.logger.info(f"Starting demo: {self.name}")
        
        apps_to_test = [app] if app else self.get_applications()
        results = {}
        
        for test_app in apps_to_test:
            self.logger.info(f"Testing application: {test_app.name}")
            
            risk_assessment = None
            try:
                # Run red teaming
                risk_assessment = self.red_team_service.run_red_team(
                    model_callback=test_app.get_model_callback(),
                    vulnerabilities=self.get_vulnerabilities(),
                    attacks=self.get_attacks(),
                    target_purpose=test_app.get_target_purpose(),
                )
                
            except Exception as e:
                self.logger.error(f"Error in red teaming for {test_app.name}: {e}", exc_info=True)
                # Continue to try saving if we have a partial risk_assessment
            
            # Try to save results even if there were errors
            if risk_assessment is not None:
                try:
                    # Visualize results
                    self.visualization_service.display_summary(risk_assessment)
                    self.visualization_service.display_vulnerability_breakdown(risk_assessment)
                    self.visualization_service.display_attack_breakdown(risk_assessment)
                    
                    # Generate reports
                    json_path = self.reporting_service.save_json(risk_assessment, test_app.name)
                    markdown_path = self.reporting_service.generate_markdown_report(
                        risk_assessment, test_app.name, self.name
                    )
                    
                    # Calculate summary safely
                    vuln_results = risk_assessment.overview.vulnerability_type_results
                    total_passing = sum(r.passing for r in vuln_results) if vuln_results else 0
                    total_failing = sum(r.failing for r in vuln_results) if vuln_results else 0
                    total_test_cases = len(risk_assessment.test_cases)
                    overall_pass_rate = (
                        total_passing / total_test_cases if total_test_cases > 0 else 0.0
                    )
                    
                    results[test_app.name] = {
                        "risk_assessment": risk_assessment,
                        "json_path": json_path,
                        "markdown_path": markdown_path,
                        "summary": {
                            "passing_rate": overall_pass_rate,
                            "total_test_cases": total_test_cases,
                            "passing": total_passing,
                            "failing": total_failing,
                        },
                    }
                    
                    self.logger.info(
                        f"Completed testing {test_app.name}: "
                        f"passing_rate={results[test_app.name]['summary']['passing_rate']:.2%}, "
                        f"results saved to {json_path.parent}"
                    )
                    
                except Exception as save_error:
                    self.logger.error(f"Error saving results for {test_app.name}: {save_error}", exc_info=True)
                    results[test_app.name] = {
                        "risk_assessment": risk_assessment,
                        "error": f"Red teaming completed but failed to save: {save_error}"
                    }
            else:
                self.logger.warning(f"No risk assessment generated for {test_app.name}")
                results[test_app.name] = {"error": "Red teaming failed - no risk assessment generated"}
        
        self.logger.info(f"Completed demo: {self.name}")
        return results
    
    def get_demo_info(self) -> Dict[str, Any]:
        """Get demo information.
        
        Returns:
            Dictionary with demo metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "applications": [app.name for app in self.get_applications()],
            "vulnerability_count": len(self.get_vulnerabilities()),
            "attack_count": len(self.get_attacks()),
        }


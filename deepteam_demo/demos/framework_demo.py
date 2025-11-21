"""Framework demo showcasing OWASP Top 10 and NIST AI RMF frameworks."""

from typing import List
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.base_app import BaseLLMApp
from apps.simple_model_app import SimpleModelApp
from apps.rag_app import RAGApp
from apps.agent_app import AgentApp
from demos.base_demo import BaseDemo
from deepteam.frameworks import OWASPTop10, NIST
from deepteam.attacks.single_turn import PromptInjection
from config.settings import Settings


class FrameworkDemo(BaseDemo):
    """Demo showcasing OWASP Top 10 and NIST AI RMF frameworks."""
    
    def __init__(self, settings: Settings = None):
        """Initialize framework demo.
        
        Args:
            settings: Settings instance (optional)
        """
        super().__init__(
            name="Framework Demo",
            description="Showcase of OWASP Top 10 and NIST AI RMF frameworks",
            settings=settings,
        )
        self.owasp_framework = None
        self.nist_framework = None
    
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
            ),
            RAGApp(
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
        """Get list of vulnerabilities (not used when using frameworks).
        
        Returns:
            Empty list (frameworks provide their own vulnerabilities)
        """
        return []
    
    def get_attacks(self) -> List:
        """Get list of attacks to use.
        
        Returns:
            List of attack instances
        """
        return [PromptInjection()]
    
    def run_owasp(self, app: BaseLLMApp = None) -> dict:
        """Run OWASP Top 10 framework demo.
        
        Args:
            app: Optional specific app to test
            
        Returns:
            Dictionary with demo results
        """
        self.logger.info("Running OWASP Top 10 framework demo")
        
        apps_to_test = [app] if app else self.get_applications()
        results = {}
        
        # Initialize OWASP framework
        self.owasp_framework = OWASPTop10(num_attacks=self.settings.attacks_per_vulnerability_type)
        
        for test_app in apps_to_test:
            self.logger.info(f"Testing {test_app.name} with OWASP Top 10")
            
            try:
                # Run with OWASP framework
                risk_assessment = self.red_team_service.run_red_team(
                    model_callback=test_app.get_model_callback(),
                    framework=self.owasp_framework,
                    target_purpose=test_app.get_target_purpose(),
                )
                
                self.visualization_service.display_summary(risk_assessment)
                
                json_path = self.reporting_service.save_json(risk_assessment, f"{test_app.name}_owasp")
                markdown_path = self.reporting_service.generate_markdown_report(
                    risk_assessment, test_app.name, "OWASP_Top10"
                )
                
                results[f"{test_app.name}_owasp"] = {
                    "risk_assessment": risk_assessment,
                    "json_path": json_path,
                    "markdown_path": markdown_path,
                }
                
            except Exception as e:
                self.logger.error(f"Error in OWASP demo for {test_app.name}: {e}", exc_info=True)
                results[f"{test_app.name}_owasp"] = {"error": str(e)}
        
        return results
    
    def run_nist(self, app: BaseLLMApp = None) -> dict:
        """Run NIST AI RMF framework demo.
        
        Args:
            app: Optional specific app to test
            
        Returns:
            Dictionary with demo results
        """
        self.logger.info("Running NIST AI RMF framework demo")
        
        apps_to_test = [app] if app else self.get_applications()
        results = {}
        
        # Initialize NIST framework
        self.nist_framework = NIST(
            categories=["measure_1", "measure_2", "measure_3", "measure_4"]
        )
        
        for test_app in apps_to_test:
            self.logger.info(f"Testing {test_app.name} with NIST AI RMF")
            
            try:
                risk_assessment = self.red_team_service.run_red_team(
                    model_callback=test_app.get_model_callback(),
                    framework=self.nist_framework,
                    target_purpose=test_app.get_target_purpose(),
                )
                
                self.visualization_service.display_summary(risk_assessment)
                
                json_path = self.reporting_service.save_json(risk_assessment, f"{test_app.name}_nist")
                markdown_path = self.reporting_service.generate_markdown_report(
                    risk_assessment, test_app.name, "NIST_AI_RMF"
                )
                
                results[f"{test_app.name}_nist"] = {
                    "risk_assessment": risk_assessment,
                    "json_path": json_path,
                    "markdown_path": markdown_path,
                }
                
            except Exception as e:
                self.logger.error(f"Error in NIST demo for {test_app.name}: {e}", exc_info=True)
                results[f"{test_app.name}_nist"] = {"error": str(e)}
        
        return results
    
    def run(self, app: BaseLLMApp = None) -> dict:
        """Run both OWASP and NIST framework demos.
        
        Args:
            app: Optional specific app to test
            
        Returns:
            Dictionary with demo results from both frameworks
        """
        results = {}
        
        # Run OWASP
        owasp_results = self.run_owasp(app)
        results.update(owasp_results)
        
        # Run NIST
        nist_results = self.run_nist(app)
        results.update(nist_results)
        
        return results


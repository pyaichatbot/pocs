"""Reporting service for generating and saving red teaming reports."""

from typing import Optional
from pathlib import Path
from datetime import datetime
from deepteam.red_teamer.risk_assessment import RiskAssessment
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import Logger


class ReportingService:
    """Service for generating and saving red teaming reports.
    
    Handles JSON export, markdown report generation, and executive summaries.
    """
    
    def __init__(
        self,
        output_folder: Path,
        logger: Optional[Logger] = None,
    ):
        """Initialize reporting service.
        
        Args:
            output_folder: Folder to save reports
            logger: Logger instance (optional)
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.logger = logger or Logger(self.__class__.__name__)
    
    def save_json(
        self,
        risk_assessment: RiskAssessment,
        app_name: str,
    ) -> Path:
        """Save risk assessment as JSON.
        
        Args:
            risk_assessment: RiskAssessment object
            app_name: Name of the application tested
            
        Returns:
            Path to saved JSON file
        """
        try:
            # Use DeepTeam's built-in save method
            file_path = risk_assessment.save(str(self.output_folder))
            self.logger.info(f"Saved JSON report: {file_path}")
            return Path(file_path)
        except Exception as e:
            self.logger.error(f"Error saving JSON report: {e}", exc_info=True)
            raise
    
    def generate_markdown_report(
        self,
        risk_assessment: RiskAssessment,
        app_name: str,
        demo_name: str,
    ) -> Path:
        """Generate markdown report.
        
        Args:
            risk_assessment: RiskAssessment object
            app_name: Name of the application tested
            demo_name: Name of the demo
            
        Returns:
            Path to saved markdown file
        """
        try:
            overview = risk_assessment.overview
            
            # Calculate totals
            total_passing = sum(r.passing for r in overview.vulnerability_type_results)
            total_failing = sum(r.failing for r in overview.vulnerability_type_results)
            total_errored = overview.errored
            total_test_cases = total_passing + total_failing + total_errored
            
            # Avoid division by zero
            if total_test_cases == 0:
                overall_pass_rate = 0.0
            else:
                overall_pass_rate = total_passing / total_test_cases
            
            # Generate markdown content
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            markdown = f"""# Red Teaming Report

**Demo:** {demo_name}  
**Application:** {app_name}  
**Generated:** {timestamp}  
**Duration:** {overview.run_duration:.2f}s

## Executive Summary

- **Overall Pass Rate:** {overall_pass_rate:.1%}
- **Total Test Cases:** {total_test_cases}
- **Passing:** {total_passing}
- **Failing:** {total_failing}
- **Errored:** {total_errored}

## Vulnerability Breakdown

| Vulnerability | Type | Pass Rate | Passing | Failing | Errored |
|--------------|------|-----------|---------|---------|---------|
"""
            
            for result in overview.vulnerability_type_results:
                markdown += (
                    f"| {result.vulnerability} | {result.vulnerability_type.value} | "
                    f"{result.pass_rate:.1%} | {result.passing} | "
                    f"{result.failing} | {result.errored} |\n"
                )
            
            markdown += "\n## Attack Method Breakdown\n\n"
            markdown += "| Attack Method | Pass Rate | Passing | Failing | Errored |\n"
            markdown += "|--------------|-----------|---------|---------|----------|\n"
            
            for result in overview.attack_method_results:
                markdown += (
                    f"| {result.attack_method or 'Unknown'} | "
                    f"{result.pass_rate:.1%} | {result.passing} | "
                    f"{result.failing} | {result.errored} |\n"
                )
            
            # Add failed test cases
            failed_cases = [
                tc for tc in risk_assessment.test_cases
                if tc.score is not None and tc.score == 0
            ]
            
            if failed_cases:
                markdown += "\n## Failed Test Cases\n\n"
                for i, case in enumerate(failed_cases[:20], 1):  # Limit to 20
                    markdown += f"### Failed Case {i}\n\n"
                    markdown += f"**Vulnerability:** {case.vulnerability}\n"
                    markdown += f"**Type:** {case.vulnerability_type.value}\n"
                    markdown += f"**Attack Method:** {case.attack_method or 'N/A'}\n\n"
                    markdown += f"**Input:**\n```\n{case.input}\n```\n\n"
                    markdown += f"**Output:**\n```\n{case.actual_output}\n```\n\n"
                    markdown += f"**Reason:** {case.reason or 'N/A'}\n\n"
                    markdown += "---\n\n"
            
            # Save markdown file
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{demo_name}_{app_name}_{timestamp_str}.md"
            file_path = self.output_folder / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            
            self.logger.info(f"Generated markdown report: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Error generating markdown report: {e}", exc_info=True)
            raise
    
    def generate_executive_summary(
        self,
        risk_assessment: RiskAssessment,
        app_name: str,
    ) -> str:
        """Generate executive summary text.
        
        Args:
            risk_assessment: RiskAssessment object
            app_name: Name of the application tested
            
        Returns:
            Executive summary text
        """
        overview = risk_assessment.overview
        
        total_passing = sum(r.passing for r in overview.vulnerability_type_results)
        total_failing = sum(r.failing for r in overview.vulnerability_type_results)
        total_errored = overview.errored
        total_test_cases = total_passing + total_failing + total_errored
        overall_pass_rate = (
            total_passing / total_test_cases if total_test_cases > 0 else 0.0
        )
        
        summary = f"""
Executive Summary for {app_name}

Overall Security Posture: {'PASS' if overall_pass_rate >= 0.8 else 'NEEDS ATTENTION' if overall_pass_rate >= 0.5 else 'FAIL'}
Pass Rate: {overall_pass_rate:.1%}
Total Test Cases: {total_test_cases}
Critical Failures: {total_failing}

Key Findings:
- {total_failing} vulnerabilities detected
- {len(overview.vulnerability_type_results)} vulnerability types tested
- {len(overview.attack_method_results)} attack methods used
- Test duration: {overview.run_duration:.2f}s
"""
        
        return summary


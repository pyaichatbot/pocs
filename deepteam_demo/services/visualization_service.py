"""Visualization service for displaying red teaming results."""

from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from deepteam.red_teamer.risk_assessment import RiskAssessment
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import Logger


class VisualizationService:
    """Service for visualizing red teaming results.
    
    Provides rich console output with tables and summaries.
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize visualization service.
        
        Args:
            logger: Logger instance (optional)
        """
        self.console = Console()
        self.logger = logger or Logger(self.__class__.__name__)
    
    def display_summary(self, risk_assessment: RiskAssessment):
        """Display overall summary of risk assessment.
        
        Args:
            risk_assessment: RiskAssessment object
        """
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
        
        # Create summary table
        summary_table = Table(title="Red Teaming Summary", box=box.ROUNDED)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")
        
        summary_table.add_row("Total Test Cases", str(total_test_cases))
        summary_table.add_row("Passing", f"{total_passing} ({overall_pass_rate:.1%})")
        summary_table.add_row("Failing", str(total_failing))
        summary_table.add_row("Errored", str(total_errored))
        summary_table.add_row("Run Duration", f"{overview.run_duration:.2f}s")
        
        self.console.print("\n")
        self.console.print(Panel(summary_table, title="Risk Assessment Summary"))
        self.console.print("\n")
    
    def display_vulnerability_breakdown(self, risk_assessment: RiskAssessment):
        """Display breakdown by vulnerability type.
        
        Args:
            risk_assessment: RiskAssessment object
        """
        overview = risk_assessment.overview
        
        if not overview.vulnerability_type_results:
            self.console.print("[yellow]No vulnerability results to display (all test cases may have errored)[/yellow]")
            return
        
        vuln_table = Table(title="Vulnerability Breakdown", box=box.ROUNDED)
        vuln_table.add_column("Vulnerability", style="cyan")
        vuln_table.add_column("Type", style="yellow")
        vuln_table.add_column("Pass Rate", style="green")
        vuln_table.add_column("Passing", style="green")
        vuln_table.add_column("Failing", style="red")
        vuln_table.add_column("Errored", style="yellow")
        
        for result in overview.vulnerability_type_results:
            pass_rate_style = "green" if result.pass_rate >= 0.8 else "yellow" if result.pass_rate >= 0.5 else "red"
            
            vuln_table.add_row(
                result.vulnerability,
                str(result.vulnerability_type.value),
                f"[{pass_rate_style}]{result.pass_rate:.1%}[/{pass_rate_style}]",
                str(result.passing),
                str(result.failing),
                str(result.errored),
            )
        
        self.console.print(Panel(vuln_table, title="Vulnerability Analysis"))
        self.console.print("\n")
    
    def display_attack_breakdown(self, risk_assessment: RiskAssessment):
        """Display breakdown by attack method.
        
        Args:
            risk_assessment: RiskAssessment object
        """
        overview = risk_assessment.overview
        
        if not overview.attack_method_results:
            self.console.print("[yellow]No attack method results to display[/yellow]")
            return
        
        attack_table = Table(title="Attack Method Breakdown", box=box.ROUNDED)
        attack_table.add_column("Attack Method", style="cyan")
        attack_table.add_column("Pass Rate", style="green")
        attack_table.add_column("Passing", style="green")
        attack_table.add_column("Failing", style="red")
        attack_table.add_column("Errored", style="yellow")
        
        for result in overview.attack_method_results:
            pass_rate_style = "green" if result.pass_rate >= 0.8 else "yellow" if result.pass_rate >= 0.5 else "red"
            
            attack_table.add_row(
                result.attack_method or "Unknown",
                f"[{pass_rate_style}]{result.pass_rate:.1%}[/{pass_rate_style}]",
                str(result.passing),
                str(result.failing),
                str(result.errored),
            )
        
        self.console.print(Panel(attack_table, title="Attack Method Analysis"))
        self.console.print("\n")
    
    def display_failed_cases(self, risk_assessment: RiskAssessment, limit: int = 10):
        """Display failed test cases.
        
        Args:
            risk_assessment: RiskAssessment object
            limit: Maximum number of cases to display
        """
        failed_cases = [
            tc for tc in risk_assessment.test_cases
            if tc.score is not None and tc.score == 0
        ][:limit]
        
        if not failed_cases:
            self.console.print("[green]No failed test cases[/green]")
            return
        
        failed_table = Table(title=f"Failed Test Cases (showing {len(failed_cases)})", box=box.ROUNDED)
        failed_table.add_column("Vulnerability", style="cyan")
        failed_table.add_column("Type", style="yellow")
        failed_table.add_column("Input", style="white", max_width=50)
        failed_table.add_column("Output", style="white", max_width=50)
        failed_table.add_column("Reason", style="red", max_width=50)
        
        for case in failed_cases:
            failed_table.add_row(
                case.vulnerability,
                str(case.vulnerability_type.value),
                case.input[:100] + "..." if len(case.input) > 100 else case.input,
                case.actual_output[:100] + "..." if len(case.actual_output) > 100 else case.actual_output,
                case.reason[:100] + "..." if case.reason and len(case.reason) > 100 else (case.reason or "N/A"),
            )
        
        self.console.print(Panel(failed_table, title="Failed Test Cases"))
        self.console.print("\n")
    
    def display_dataframe(self, risk_assessment: RiskAssessment):
        """Display risk assessment as DataFrame (if pandas is available).
        
        Args:
            risk_assessment: RiskAssessment object
        """
        try:
            import pandas as pd
            
            df = risk_assessment.test_cases.to_df()
            
            self.console.print("\n[bold]Test Cases DataFrame:[/bold]")
            self.console.print(df.to_string())
            self.console.print("\n")
            
        except ImportError:
            self.logger.warning("pandas not available, skipping DataFrame display")
        except Exception as e:
            self.logger.error(f"Error displaying DataFrame: {e}")


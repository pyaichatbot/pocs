"""Main entry point for DeepTeam Demo Suite."""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings, get_settings
from config.logging_config import setup_logging
from utils.logger import Logger
from demos.vulnerability_demo import VulnerabilityDemo
from demos.attack_demo import AttackDemo
from demos.custom_vulnerability_demo import CustomVulnerabilityDemo
from demos.framework_demo import FrameworkDemo
from demos.comprehensive_demo import ComprehensiveDemo

app = typer.Typer(name="deepteam_demo", help="DeepTeam Management Demo Suite")
console = Console()


def print_banner():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║         DeepTeam Demo Suite                       ║
║         Comprehensive LLM Red Teaming Demonstrations         ║
╚══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")


def print_demo_menu():
    """Print demo selection menu."""
    table = Table(title="Available Demos", box=box.ROUNDED)
    table.add_column("Option", style="cyan")
    table.add_column("Demo", style="yellow")
    table.add_column("Description", style="white")
    
    table.add_row("1", "Vulnerability Demo", "Showcase all 40+ vulnerabilities")
    table.add_row("2", "Attack Demo", "Showcase all attack methods")
    table.add_row("3", "Custom Vulnerability Demo", "Custom vulnerability creation")
    table.add_row("4", "Framework Demo", "OWASP Top 10 & NIST AI RMF")
    table.add_row("5", "Comprehensive Demo", "Full feature showcase")
    table.add_row("6", "Run All Demos", "Execute all demos sequentially")
    table.add_row("0", "Exit", "Exit the application")
    
    console.print("\n")
    console.print(Panel(table, title="Demo Selection"))
    console.print("\n")


@app.command()
def run(
    demo: Optional[str] = typer.Option(
        None,
        "--demo",
        "-d",
        help="Demo to run (vulnerability, attack, custom, framework, comprehensive, all)",
    ),
    app_name: Optional[str] = typer.Option(
        None,
        "--app",
        "-a",
        help="Specific app to test (simple, rag, chatbot, agent)",
    ),
):
    """Run DeepTeam demos."""
    print_banner()
    
    # Setup logging
    settings = get_settings()
    logger, tracer = setup_logging(
        level=settings.log_level,
        service_name=settings.log_service_name,
        enable_console=settings.enable_console_export,
    )
    
    logger.info("Starting DeepTeam Demo Suite")
    
    # If demo is specified via CLI, run it directly
    if demo:
        run_demo_by_name(demo, app_name, settings, logger)
    else:
        # Interactive mode
        while True:
            print_demo_menu()
            choice = console.input("[bold cyan]Select demo (0-6): [/bold cyan]")
            
            if choice == "0":
                console.print("[yellow]Exiting...[/yellow]")
                break
            elif choice == "1":
                run_demo_by_name("vulnerability", app_name, settings, logger)
            elif choice == "2":
                run_demo_by_name("attack", app_name, settings, logger)
            elif choice == "3":
                run_demo_by_name("custom", app_name, settings, logger)
            elif choice == "4":
                run_demo_by_name("framework", app_name, settings, logger)
            elif choice == "5":
                run_demo_by_name("comprehensive", app_name, settings, logger)
            elif choice == "6":
                run_all_demos(settings, logger)
            else:
                console.print("[red]Invalid option. Please try again.[/red]")
            
            if choice != "0":
                console.input("\n[dim]Press Enter to continue...[/dim]")


def run_demo_by_name(
    demo_name: str,
    app_name: Optional[str],
    settings: Settings,
    logger: Logger,
):
    """Run a specific demo by name.
    
    Args:
        demo_name: Name of the demo to run
        app_name: Optional specific app to test
        settings: Settings instance
        logger: Logger instance
    """
    demo_map = {
        "vulnerability": VulnerabilityDemo,
        "attack": AttackDemo,
        "custom": CustomVulnerabilityDemo,
        "framework": FrameworkDemo,
        "comprehensive": ComprehensiveDemo,
    }
    
    demo_class = demo_map.get(demo_name.lower())
    if not demo_class:
        console.print(f"[red]Unknown demo: {demo_name}[/red]")
        return
    
    try:
        console.print(f"\n[bold green]Running {demo_name} demo...[/bold green]\n")
        
        demo = demo_class(settings=settings)
        results = demo.run()
        
        console.print(f"\n[bold green]✓ {demo_name} demo completed successfully![/bold green]")
        console.print(f"Results saved to: {settings.output_folder}")
        
    except Exception as e:
        logger.error(f"Error running {demo_name} demo: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")


def run_all_demos(settings: Settings, logger: Logger):
    """Run all demos sequentially.
    
    Args:
        settings: Settings instance
        logger: Logger instance
    """
    demos = [
        ("vulnerability", VulnerabilityDemo),
        ("attack", AttackDemo),
        ("custom", CustomVulnerabilityDemo),
        ("framework", FrameworkDemo),
        ("comprehensive", ComprehensiveDemo),
    ]
    
    console.print("\n[bold yellow]Running all demos...[/bold yellow]\n")
    
    for demo_name, demo_class in demos:
        try:
            console.print(f"\n[bold cyan]━━━ {demo_name.upper()} DEMO ━━━[/bold cyan]\n")
            demo = demo_class(settings=settings)
            demo.run()
            console.print(f"[green]✓ {demo_name} completed[/green]")
        except Exception as e:
            logger.error(f"Error in {demo_name} demo: {e}", exc_info=True)
            console.print(f"[red]✗ {demo_name} failed: {e}[/red]")
    
    console.print("\n[bold green]All demos completed![/bold green]")
    console.print(f"Results saved to: {settings.output_folder}")


@app.command()
def list_demos():
    """List all available demos."""
    print_banner()
    print_demo_menu()


@app.command()
def config():
    """Show current configuration."""
    print_banner()
    settings = get_settings()
    
    table = Table(title="Current Configuration", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="yellow")
    
    table.add_row("Target LLM Provider", settings.target_llm.provider)
    table.add_row("Target LLM Model", settings.target_llm.model_name)
    table.add_row("Simulator LLM", settings.simulator_llm.model_name)
    table.add_row("Evaluation LLM", settings.evaluation_llm.model_name)
    table.add_row("Max Concurrent", str(settings.max_concurrent))
    table.add_row("Attacks per Vuln Type", str(settings.attacks_per_vulnerability_type))
    table.add_row("Output Folder", str(settings.output_folder))
    table.add_row("Log Level", settings.log_level)
    
    console.print(Panel(table, title="Configuration"))
    console.print("\n")


if __name__ == "__main__":
    app()


"""Script to run DeepTeam YAML configurations.

This script provides a convenient way to run YAML configs from the demo suite.
It wraps DeepTeam's CLI run command and adds demo-specific features.
"""

import sys
import os
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from deepteam.cli.main import run as deepteam_run
from deepteam.cli.config import apply_env
from config.logging_config import setup_logging
from config.settings import get_settings

app = typer.Typer(name="run-yaml", help="Run DeepTeam YAML configurations")
console = Console()

CONFIGS_DIR = Path(__file__).parent / "configs"


def list_available_configs():
    """List all available YAML configuration files."""
    if not CONFIGS_DIR.exists():
        console.print(f"[red]Configs directory not found: {CONFIGS_DIR}[/red]")
        return []
    
    configs = list(CONFIGS_DIR.glob("*.yaml"))
    return sorted(configs)


@app.command("list")
def list_configs():
    """List all available YAML configuration files."""
    configs = list_available_configs()
    
    if not configs:
        console.print("[yellow]No YAML configuration files found.[/yellow]")
        return
    
    table = Table(title="Available YAML Configurations", box=box.ROUNDED)
    table.add_column("File", style="cyan")
    table.add_column("Description", style="white")
    
    descriptions = {
        "simple_model_config.yaml": "Tests a foundational model directly",
        "custom_callback_config.yaml": "Tests LLM applications using custom callbacks",
        "azure_openai_config.yaml": "Tests using Azure OpenAI models",
        "comprehensive_config.yaml": "Tests multiple vulnerabilities and attacks",
    }
    
    for config in configs:
        desc = descriptions.get(config.name, "YAML configuration file")
        table.add_row(config.name, desc)
    
    console.print("\n")
    console.print(Panel(table, title="YAML Configurations"))
    console.print("\n")


@app.command("run")
def run_config(
    config_file: str = typer.Argument(..., help="Path to YAML configuration file"),
    max_concurrent: int = typer.Option(
        None,
        "-c",
        "--max-concurrent",
        help="Maximum concurrent operations (overrides config)",
    ),
    attacks_per_vuln: int = typer.Option(
        None,
        "-a",
        "--attacks-per-vuln",
        help="Number of attacks per vulnerability type (overrides config)",
    ),
    output_folder: str = typer.Option(
        None,
        "-o",
        "--output-folder",
        help="Path to output folder (overrides config)",
    ),
):
    """Run a DeepTeam YAML configuration file.
    
    Example:
        python run_yaml_config.py run configs/simple_model_config.yaml
        python run_yaml_config.py run configs/custom_callback_config.yaml -c 3 -a 2
    """
    # Resolve config file path
    config_path = Path(config_file)
    if not config_path.is_absolute():
        # Try relative to configs directory first
        if (CONFIGS_DIR / config_path).exists():
            config_path = CONFIGS_DIR / config_path
        # Then try relative to current directory
        elif not config_path.exists():
            config_path = Path.cwd() / config_path
    
    if not config_path.exists():
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)
    
    # Setup logging
    settings = get_settings()
    logger, tracer = setup_logging(
        level=settings.log_level,
        service_name=settings.log_service_name,
        enable_console=settings.enable_console_export,
    )
    
    logger.info(f"Running YAML config: {config_path}")
    
    # Apply environment variables
    apply_env()
    
    # Resolve output folder
    final_output_folder = output_folder or settings.output_folder
    if final_output_folder:
        final_output_folder = str(Path(final_output_folder).absolute())
    
    try:
        # Run the config using DeepTeam's CLI
        result = deepteam_run(
            str(config_path),
            max_concurrent=max_concurrent,
            attacks_per_vuln=attacks_per_vuln,
            output_folder=final_output_folder,
        )
        
        if result and result.risk_assessment:
            console.print("\n[green]✓ Red teaming completed successfully![/green]")
            console.print(f"[cyan]Test cases: {len(result.risk_assessment.test_cases)}[/cyan]")
            console.print(
                f"[cyan]Duration: {result.risk_assessment.overview.run_duration:.2f}s[/cyan]"
            )
            
            if result.file_path:
                console.print(f"[green]Results saved to: {result.file_path}[/green]")
        else:
            console.print("[yellow]Red teaming completed but no results returned.[/yellow]")
            
    except Exception as e:
        logger.error(f"Error running YAML config: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()


"""Tests for YAML configuration files.

These tests verify that YAML configs work correctly with DeepTeam's CLI.
"""

import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from deepteam.cli.main import run as deepteam_run
from deepteam.cli.config import apply_env


class TestYAMLConfigs:
    """Test suite for YAML configuration files."""
    
    @pytest.fixture
    def configs_dir(self):
        """Get path to configs directory."""
        return Path(__file__).parent.parent / "configs"
    
    @pytest.fixture
    def results_dir(self):
        """Get path to results directory."""
        return Path(__file__).parent.parent / "results"
    
    def test_simple_model_config_exists(self, configs_dir):
        """Test that simple model config file exists and is valid YAML."""
        config_path = configs_dir / "simple_model_config.yaml"
        assert config_path.exists(), f"Config file not found: {config_path}"
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        assert "models" in config
        assert "target" in config
        assert "system_config" in config
        assert "default_vulnerabilities" in config
        assert "attacks" in config
    
    def test_custom_callback_config_exists(self, configs_dir):
        """Test that custom callback config file exists and is valid YAML."""
        config_path = configs_dir / "custom_callback_config.yaml"
        assert config_path.exists(), f"Config file not found: {config_path}"
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        assert "target" in config
        assert "callback" in config["target"]
        assert "file" in config["target"]["callback"]
    
    def test_azure_openai_config_exists(self, configs_dir):
        """Test that Azure OpenAI config file exists and is valid YAML."""
        config_path = configs_dir / "azure_openai_config.yaml"
        assert config_path.exists(), f"Config file not found: {config_path}"
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        assert "models" in config
        assert config["models"]["simulator"]["provider"] == "azure"
        assert config["models"]["evaluation"]["provider"] == "azure"
    
    def test_comprehensive_config_exists(self, configs_dir):
        """Test that comprehensive config file exists and is valid YAML."""
        config_path = configs_dir / "comprehensive_config.yaml"
        assert config_path.exists(), f"Config file not found: {config_path}"
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        assert "default_vulnerabilities" in config
        assert "custom_vulnerabilities" in config
        assert len(config["attacks"]) > 1
    
    def test_yaml_config_structure(self, configs_dir):
        """Test that all YAML configs have required structure."""
        required_sections = ["models", "target", "system_config"]
        
        for config_file in configs_dir.glob("*.yaml"):
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
            
            for section in required_sections:
                assert section in config, (
                    f"Missing required section '{section}' in {config_file.name}"
                )
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"),
        reason="API key not set (ANTHROPIC_API_KEY or OPENAI_API_KEY required)"
    )
    def test_simple_model_config_execution(self, configs_dir, results_dir):
        """Test that simple model config can be executed (requires API key)."""
        config_path = configs_dir / "simple_model_config.yaml"
        
        # Apply environment variables
        apply_env()
        
        # Run the config
        result = deepteam_run(
            str(config_path),
            max_concurrent=2,
            attacks_per_vuln=1,
            output_folder=str(results_dir),
        )
        
        assert result is not None
        assert result.risk_assessment is not None
        assert len(result.risk_assessment.test_cases) > 0
        assert result.risk_assessment.overview is not None
        assert result.risk_assessment.overview.run_duration > 0
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_custom_callback_config_execution(self, configs_dir, results_dir):
        """Test that custom callback config can be executed (requires API key)."""
        config_path = configs_dir / "custom_callback_config.yaml"
        
        # Verify callback file exists
        callback_file = Path(__file__).parent.parent / "test_callbacks.py"
        assert callback_file.exists(), f"Callback file not found: {callback_file}"
        
        # Apply environment variables
        apply_env()
        
        # Run the config
        result = deepteam_run(
            str(config_path),
            max_concurrent=2,
            attacks_per_vuln=1,
            output_folder=str(results_dir),
        )
        
        assert result is not None
        assert result.risk_assessment is not None
        assert len(result.risk_assessment.test_cases) > 0
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_comprehensive_config_execution(self, configs_dir, results_dir):
        """Test that comprehensive config can be executed (requires API key)."""
        config_path = configs_dir / "comprehensive_config.yaml"
        
        # Verify callback file exists
        callback_file = Path(__file__).parent.parent / "test_callbacks.py"
        assert callback_file.exists(), f"Callback file not found: {callback_file}"
        
        # Apply environment variables
        apply_env()
        
        # Run the config
        result = deepteam_run(
            str(config_path),
            max_concurrent=2,
            attacks_per_vuln=1,
            output_folder=str(results_dir),
        )
        
        assert result is not None
        assert result.risk_assessment is not None
        assert len(result.risk_assessment.test_cases) > 0
        
        # Verify comprehensive config has multiple vulnerabilities
        assert len(result.risk_assessment.overview.vulnerability_type_results) > 1
    
    def test_yaml_config_vulnerability_parsing(self, configs_dir):
        """Test that YAML configs correctly parse vulnerability definitions."""
        from deepteam.cli.main import _load_config, _build_vulnerability
        
        config_path = configs_dir / "comprehensive_config.yaml"
        config = _load_config(str(config_path))
        
        vulnerabilities_cfg = config.get("default_vulnerabilities", [])
        assert len(vulnerabilities_cfg) > 0
        
        # Test parsing each vulnerability
        for vuln_cfg in vulnerabilities_cfg:
            vuln = _build_vulnerability(vuln_cfg, custom=False)
            assert vuln is not None
            assert hasattr(vuln, 'name')
    
    def test_yaml_config_attack_parsing(self, configs_dir):
        """Test that YAML configs correctly parse attack definitions."""
        from deepteam.cli.main import _load_config, _build_attack
        
        config_path = configs_dir / "comprehensive_config.yaml"
        config = _load_config(str(config_path))
        
        attacks_cfg = config.get("attacks", [])
        assert len(attacks_cfg) > 0
        
        # Test parsing each attack
        for attack_cfg in attacks_cfg:
            attack = _build_attack(attack_cfg)
            assert attack is not None
            assert hasattr(attack, '__class__')
    
    def test_yaml_config_custom_vulnerability_parsing(self, configs_dir):
        """Test that YAML configs correctly parse custom vulnerabilities."""
        from deepteam.cli.main import _load_config, _build_vulnerability
        
        config_path = configs_dir / "comprehensive_config.yaml"
        config = _load_config(str(config_path))
        
        custom_vulns_cfg = config.get("custom_vulnerabilities", [])
        if custom_vulns_cfg:
            for vuln_cfg in custom_vulns_cfg:
                vuln = _build_vulnerability(vuln_cfg, custom=True)
                assert vuln is not None
                assert hasattr(vuln, 'name')
                assert hasattr(vuln, 'criteria')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


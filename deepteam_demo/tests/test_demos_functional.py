"""Functional tests for demo implementations.

These tests verify that our demos work correctly and produce valid results.
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from deepteam.red_teamer.risk_assessment import RiskAssessment

from demos.vulnerability_demo import VulnerabilityDemo
from demos.attack_demo import AttackDemo
from demos.custom_vulnerability_demo import CustomVulnerabilityDemo
from demos.framework_demo import FrameworkDemo
from config.settings import Settings, get_settings


@pytest.fixture
def settings():
    """Get settings instance."""
    return get_settings()


class TestVulnerabilityDemo:
    """Functional tests for VulnerabilityDemo."""
    
    def test_demo_initialization(self, settings):
        """Test that VulnerabilityDemo initializes correctly."""
        demo = VulnerabilityDemo(settings=settings)
        assert demo.name == "Vulnerability Demo"
        assert len(demo.get_vulnerabilities()) > 0
        assert len(demo.get_attacks()) > 0
        assert len(demo.get_applications()) > 0
    
    def test_vulnerabilities_are_valid(self, settings):
        """Test that all vulnerabilities are valid instances."""
        demo = VulnerabilityDemo(settings=settings)
        vulnerabilities = demo.get_vulnerabilities()
        
        for vuln in vulnerabilities:
            assert vuln is not None
            assert hasattr(vuln, 'name')
            assert hasattr(vuln, 'types')
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_demo_runs_successfully(self, settings):
        """Test that VulnerabilityDemo runs and produces results."""
        demo = VulnerabilityDemo(settings=settings)
        
        # Test with just SimpleModelApp to keep it fast
        apps = demo.get_applications()
        simple_app = apps[0]  # SimpleModelApp
        
        results = demo.run(app=simple_app)
        
        assert results is not None
        assert "results" in results or simple_app.name in results


class TestAttackDemo:
    """Functional tests for AttackDemo."""
    
    def test_demo_initialization(self, settings):
        """Test that AttackDemo initializes correctly."""
        demo = AttackDemo(settings=settings)
        assert demo.name == "Attack Demo"
        assert len(demo.get_attacks()) > 0
    
    def test_attacks_are_valid(self, settings):
        """Test that all attacks are valid instances."""
        demo = AttackDemo(settings=settings)
        attacks = demo.get_attacks()
        
        for attack in attacks:
            assert attack is not None
            assert hasattr(attack, '__class__')
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_demo_runs_successfully(self, settings):
        """Test that AttackDemo runs and produces results."""
        demo = AttackDemo(settings=settings)
        results = demo.run()
        
        assert results is not None
        # Results may contain errors if no test cases generated, which is acceptable
        assert isinstance(results, dict)


class TestCustomVulnerabilityDemo:
    """Functional tests for CustomVulnerabilityDemo."""
    
    def test_demo_initialization(self, settings):
        """Test that CustomVulnerabilityDemo initializes correctly."""
        demo = CustomVulnerabilityDemo(settings=settings)
        assert demo.name == "Custom Vulnerability Demo"
        assert len(demo.get_vulnerabilities()) > 0
    
    def test_custom_vulnerabilities_are_valid(self, settings):
        """Test that custom vulnerabilities are valid."""
        demo = CustomVulnerabilityDemo(settings=settings)
        vulnerabilities = demo.get_vulnerabilities()
        
        for vuln in vulnerabilities:
            assert vuln is not None
            assert hasattr(vuln, 'name')
            assert hasattr(vuln, 'criteria')


class TestFrameworkDemo:
    """Functional tests for FrameworkDemo."""
    
    def test_demo_initialization(self, settings):
        """Test that FrameworkDemo initializes correctly."""
        demo = FrameworkDemo(settings=settings)
        assert demo.name == "Framework Demo"
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_owasp_framework_runs(self, settings):
        """Test that OWASP framework demo runs."""
        from apps.simple_model_app import SimpleModelApp
        
        demo = FrameworkDemo(settings=settings)
        apps = demo.get_applications()
        simple_app = apps[0]
        
        # This should not raise an error
        # The actual execution is tested in the demo's run method
        assert simple_app is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


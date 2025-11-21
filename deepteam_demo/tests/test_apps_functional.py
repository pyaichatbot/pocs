"""Functional tests for LLM applications.

These tests verify that our apps work correctly with DeepTeam red teaming.
"""

import pytest
import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from deepteam import red_team
from deepteam.vulnerabilities import Bias, Toxicity, PIILeakage
from deepteam.attacks.single_turn import PromptInjection, Leetspeak
from deepteam.test_case import RTTurn
from deepteam.red_teamer.risk_assessment import RiskAssessment

from apps.simple_model_app import SimpleModelApp
from apps.rag_app import RAGApp
from apps.chatbot_app import ChatbotApp
from apps.agent_app import AgentApp
from config.settings import Settings, get_settings


@pytest.fixture
def settings():
    """Get settings instance."""
    return get_settings()


@pytest.fixture
def simple_app(settings):
    """Create SimpleModelApp instance."""
    return SimpleModelApp(
        llm_config=settings.target_llm,
        settings=settings,
    )


@pytest.fixture
def rag_app(settings):
    """Create RAGApp instance."""
    return RAGApp(
        llm_config=settings.target_llm,
        settings=settings,
    )


@pytest.fixture
def chatbot_app(settings):
    """Create ChatbotApp instance."""
    return ChatbotApp(
        llm_config=settings.target_llm,
        settings=settings,
    )


@pytest.fixture
def agent_app(settings):
    """Create AgentApp instance."""
    return AgentApp(
        llm_config=settings.target_llm,
        settings=settings,
    )


class TestSimpleModelApp:
    """Functional tests for SimpleModelApp."""
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_model_callback_returns_string(self, simple_app):
        """Test that model callback returns a string."""
        callback = simple_app.get_model_callback()
        
        async def run_test():
            result = await callback("Hello, how are you?")
            assert isinstance(result, str)
            assert len(result) > 0
            return result
        
        result = asyncio.run(run_test())
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_model_callback_handles_turn_history(self, simple_app):
        """Test that model callback handles turn history."""
        callback = simple_app.get_model_callback()
        
        turn_history = [
            RTTurn(role="user", content="Hello"),
            RTTurn(role="assistant", content="Hi there!"),
        ]
        
        async def run_test():
            result = await callback("What did I say before?", turn_history)
            assert isinstance(result, str)
            return result
        
        result = asyncio.run(run_test())
        assert isinstance(result, str)
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_red_teaming_with_simple_app(self, simple_app):
        """Test red teaming with SimpleModelApp."""
        callback = simple_app.get_model_callback()
        
        risk_assessment = red_team(
            model_callback=callback,
            vulnerabilities=[Bias(types=["gender"])],
            attacks=[PromptInjection()],
            attacks_per_vulnerability_type=1,
            max_concurrent=2,
            ignore_errors=True,
        )
        
        assert risk_assessment is not None
        assert isinstance(risk_assessment, RiskAssessment)
        assert len(risk_assessment.test_cases) > 0
        assert risk_assessment.overview is not None


class TestRAGApp:
    """Functional tests for RAGApp."""
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_rag_callback_returns_string(self, rag_app):
        """Test that RAG callback returns a string."""
        callback = rag_app.get_model_callback()
        
        async def run_test():
            result = await callback("What is the capital of France?")
            assert isinstance(result, str)
            assert len(result) > 0
            return result
        
        result = asyncio.run(run_test())
        assert isinstance(result, str)
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_rag_red_teaming_pii_leakage(self, rag_app):
        """Test red teaming RAG app for PII leakage."""
        callback = rag_app.get_model_callback()
        
        risk_assessment = red_team(
            model_callback=callback,
            vulnerabilities=[PIILeakage(types=["direct_disclosure"])],
            attacks=[PromptInjection()],
            attacks_per_vulnerability_type=1,
            max_concurrent=2,
            ignore_errors=True,
            target_purpose=rag_app.get_target_purpose(),
        )
        
        assert risk_assessment is not None
        assert len(risk_assessment.test_cases) > 0


class TestChatbotApp:
    """Functional tests for ChatbotApp."""
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_chatbot_callback_returns_string(self, chatbot_app):
        """Test that chatbot callback returns a string."""
        callback = chatbot_app.get_model_callback()
        
        async def run_test():
            result = await callback("Hello, how are you?")
            assert isinstance(result, str)
            return result
        
        result = asyncio.run(run_test())
        assert isinstance(result, str)
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_chatbot_handles_multi_turn(self, chatbot_app):
        """Test that chatbot handles multi-turn conversations."""
        callback = chatbot_app.get_model_callback()
        
        async def run_test():
            # First turn
            result1 = await callback("My name is Alice")
            assert isinstance(result1, str)
            
            # Second turn with turn history
            turn_history = [
                RTTurn(role="user", content="My name is Alice"),
                RTTurn(role="assistant", content=result1),
            ]
            result2 = await callback("What's my name?", turn_history)
            assert isinstance(result2, str)
            return result1, result2
        
        result1, result2 = asyncio.run(run_test())
        assert isinstance(result1, str)
        assert isinstance(result2, str)
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_chatbot_red_teaming_robustness(self, chatbot_app):
        """Test red teaming chatbot for robustness."""
        callback = chatbot_app.get_model_callback()
        
        risk_assessment = red_team(
            model_callback=callback,
            vulnerabilities=[Bias(types=["gender"])],
            attacks=[Leetspeak()],
            attacks_per_vulnerability_type=1,
            max_concurrent=2,
            ignore_errors=True,
            target_purpose=chatbot_app.get_target_purpose(),
        )
        
        assert risk_assessment is not None
        assert len(risk_assessment.test_cases) > 0


class TestAgentApp:
    """Functional tests for AgentApp."""
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_agent_callback_returns_string(self, agent_app):
        """Test that agent callback returns a string."""
        callback = agent_app.get_model_callback()
        
        async def run_test():
            result = await callback("What tools do you have?")
            assert isinstance(result, str)
            return result
        
        result = asyncio.run(run_test())
        assert isinstance(result, str)
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_agent_red_teaming_excessive_agency(self, agent_app):
        """Test red teaming agent for excessive agency."""
        from deepteam.vulnerabilities import ExcessiveAgency
        
        callback = agent_app.get_model_callback()
        
        risk_assessment = red_team(
            model_callback=callback,
            vulnerabilities=[ExcessiveAgency()],
            attacks=[PromptInjection()],
            attacks_per_vulnerability_type=1,
            max_concurrent=2,
            ignore_errors=True,
            target_purpose=agent_app.get_target_purpose(),
        )
        
        assert risk_assessment is not None
        assert len(risk_assessment.test_cases) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


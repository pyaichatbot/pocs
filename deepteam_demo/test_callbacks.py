"""Test callbacks for YAML configuration testing.

These callbacks can be used with DeepTeam's YAML config files
to test different types of LLM applications.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from deepteam.test_case import RTTurn
from apps.simple_model_app import SimpleModelApp
from apps.rag_app import RAGApp
from apps.chatbot_app import ChatbotApp
from apps.agent_app import AgentApp
from config.settings import Settings, LLMConfig

# Initialize settings
settings = Settings.from_env()


async def simple_model_callback(input_text: str, turns: Optional[List[RTTurn]] = None) -> str:
    """Simple model callback for testing foundational models.
    
    Args:
        input_text: Input prompt
        turns: Optional conversation history
        
    Returns:
        Model response
    """
    app = SimpleModelApp(
        llm_config=settings.target_llm,
        settings=settings,
    )
    callback = app.get_model_callback()
    return await callback(input_text, turns)


async def rag_model_callback(input_text: str, turns: Optional[List[RTTurn]] = None) -> str:
    """RAG model callback for testing RAG applications.
    
    Args:
        input_text: Input prompt
        turns: Optional conversation history
        
    Returns:
        RAG system response
    """
    app = RAGApp(
        llm_config=settings.target_llm,
        settings=settings,
    )
    callback = app.get_model_callback()
    return await callback(input_text, turns)


async def chatbot_model_callback(input_text: str, turns: Optional[List[RTTurn]] = None) -> str:
    """Chatbot callback for testing conversational applications.
    
    Args:
        input_text: Input prompt
        turns: Optional conversation history
        
    Returns:
        Chatbot response
    """
    app = ChatbotApp(
        llm_config=settings.target_llm,
        settings=settings,
    )
    callback = app.get_model_callback()
    return await callback(input_text, turns)


async def agent_model_callback(input_text: str, turns: Optional[List[RTTurn]] = None) -> str:
    """Agent callback for testing AI agent applications.
    
    Args:
        input_text: Input prompt
        turns: Optional conversation history
        
    Returns:
        Agent response
    """
    app = AgentApp(
        llm_config=settings.target_llm,
        settings=settings,
    )
    callback = app.get_model_callback()
    return await callback(input_text, turns)


async def comprehensive_model_callback(input_text: str, turns: Optional[List[RTTurn]] = None) -> str:
    """Comprehensive callback that simulates a complex LLM application.
    
    Args:
        input_text: Input prompt
        turns: Optional conversation history
        
    Returns:
        Application response
    """
    # Use RAG app as it demonstrates multiple vulnerability types
    app = RAGApp(
        llm_config=settings.target_llm,
        settings=settings,
    )
    callback = app.get_model_callback()
    return await callback(input_text, turns)


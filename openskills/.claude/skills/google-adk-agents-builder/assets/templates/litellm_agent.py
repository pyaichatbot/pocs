#!/usr/bin/env python3
"""
LiteLLM Multi-Provider Agent Template

This template demonstrates how to create ADK agents using LiteLLM
to access multiple LLM providers (Azure OpenAI, Anthropic, OpenAI, etc.)
instead of or alongside Google Gemini models.
"""

from google.adk import LLMAgent
from google.adk.models.lite_llm import LiteLlm


def create_agent_with_openai():
    """
    Create an agent using OpenAI GPT-4o via LiteLLM.
    
    Requires: export OPENAI_API_KEY="your-key"
    
    Returns:
        Configured LLMAgent instance using OpenAI
    """
    model = LiteLlm(
        model="gpt-4o",
        temperature=0.7,
        max_tokens=2048
    )
    
    agent = LLMAgent(
        model=model,
        system_instruction="You are a helpful assistant powered by OpenAI."
    )
    
    return agent


def create_agent_with_anthropic():
    """
    Create an agent using Anthropic Claude via LiteLLM.
    
    Requires: export ANTHROPIC_API_KEY="your-key"
    
    Returns:
        Configured LLMAgent instance using Anthropic
    """
    model = LiteLlm(
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=2048
    )
    
    agent = LLMAgent(
        model=model,
        system_instruction="You are a helpful assistant powered by Anthropic Claude."
    )
    
    return agent


def create_agent_with_azure_openai():
    """
    Create an agent using Azure OpenAI via LiteLLM.
    
    Requires:
        export AZURE_API_KEY="your-key"
        export AZURE_API_BASE="https://your-resource.openai.azure.com/"
        export AZURE_API_VERSION="2024-02-15-preview"
    
    Returns:
        Configured LLMAgent instance using Azure OpenAI
    """
    model = LiteLlm(
        model="azure/gpt-4o",
        temperature=0.7,
        max_tokens=2048
    )
    
    agent = LLMAgent(
        model=model,
        system_instruction="You are a helpful assistant powered by Azure OpenAI."
    )
    
    return agent


def create_agent_with_fallback():
    """
    Create an agent with fallback logic.
    
    Tries primary model, falls back to secondary if needed.
    
    Returns:
        Primary agent and fallback agent
    """
    # Primary model (Claude for complex reasoning)
    primary_model = LiteLlm(
        model="claude-3-5-sonnet-20241022",
        temperature=0.7
    )
    
    primary_agent = LLMAgent(
        model=primary_model,
        system_instruction="You are a helpful assistant with advanced reasoning."
    )
    
    # Fallback model (GPT-3.5 for speed/cost)
    fallback_model = LiteLlm(
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    fallback_agent = LLMAgent(
        model=fallback_model,
        system_instruction="You are a helpful assistant."
    )
    
    return primary_agent, fallback_agent


def main():
    """Main function to demonstrate LiteLLM agents."""
    import os
    
    # Check which API keys are available
    has_openai = os.getenv("OPENAI_API_KEY")
    has_anthropic = os.getenv("ANTHROPIC_API_KEY")
    has_azure = os.getenv("AZURE_API_KEY")
    
    print("Available API keys:")
    print(f"  OpenAI: {'✓' if has_openai else '✗'}")
    print(f"  Anthropic: {'✓' if has_anthropic else '✗'}")
    print(f"  Azure OpenAI: {'✓' if has_azure else '✗'}")
    print()
    
    # Try to create and use an agent
    if has_openai:
        print("Using OpenAI GPT-4o...")
        agent = create_agent_with_openai()
        response = agent.run("Hello! What model are you using?")
        print(f"Response: {response}\n")
    elif has_anthropic:
        print("Using Anthropic Claude...")
        agent = create_agent_with_anthropic()
        response = agent.run("Hello! What model are you using?")
        print(f"Response: {response}\n")
    elif has_azure:
        print("Using Azure OpenAI...")
        agent = create_agent_with_azure_openai()
        response = agent.run("Hello! What model are you using?")
        print(f"Response: {response}\n")
    else:
        print("⚠️  No API keys found. Please set one of:")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  export AZURE_API_KEY='your-key'")
        print("  export AZURE_API_BASE='https://your-resource.openai.azure.com/'")
        print("  export AZURE_API_VERSION='2024-02-15-preview'")


if __name__ == "__main__":
    main()


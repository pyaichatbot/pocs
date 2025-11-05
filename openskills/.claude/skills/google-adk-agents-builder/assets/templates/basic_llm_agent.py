#!/usr/bin/env python3
"""
Basic LLM Agent Template

This template provides a starting point for creating a simple LLM agent
using Google's Agent Development Kit (ADK).
"""

from google.adk import LLMAgent
from google.adk.models import GeminiModel


def create_agent():
    """
    Create and configure a basic LLM agent.
    
    Returns:
        Configured LLMAgent instance
    """
    # Configure the model
    model = GeminiModel(
        model_name="gemini-2.0-flash-exp",
        temperature=0.7,
        max_tokens=2048
    )
    
    # Define system instruction
    system_instruction = """
    You are a helpful assistant that provides accurate and useful information.
    Be concise, clear, and helpful in your responses.
    """
    
    # Create the agent
    agent = LLMAgent(
        model=model,
        system_instruction=system_instruction
    )
    
    return agent


def main():
    """Main function to run the agent."""
    # Create agent
    agent = create_agent()
    
    # Example usage
    query = "Hello, how can you help me?"
    response = agent.run(query)
    
    print(f"Query: {query}")
    print(f"Response: {response}")


if __name__ == "__main__":
    main()


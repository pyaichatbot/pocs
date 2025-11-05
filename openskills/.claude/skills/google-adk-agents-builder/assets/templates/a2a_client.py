#!/usr/bin/env python3
"""
A2A Client Template

This template provides a starting point for consuming remote agents
via the Agent2Agent (A2A) Protocol.
"""

import os
from a2a_sdk import AgentClient, ClientConfig
from google.adk import LLMAgent, Tool
from google.adk.models import GeminiModel


def create_remote_agent_tool(endpoint: str):
    """
    Create a tool that uses a remote A2A agent.
    
    Args:
        endpoint: A2A server endpoint URL
        
    Returns:
        Tool function for remote agent
    """
    client = AgentClient(
        endpoint=endpoint,
        config=ClientConfig(
            timeout=30,
            retry_attempts=3
        )
    )
    
    @Tool
    def remote_agent_tool(query: str) -> str:
        """
        Use remote agent to answer query.
        
        Args:
            query: Query to send to remote agent
            
        Returns:
            Response from remote agent
        """
        try:
            response = client.run(query)
            return response
        except Exception as e:
            return f"Error calling remote agent: {str(e)}"
    
    return remote_agent_tool


def create_local_agent(remote_tool):
    """
    Create a local agent that uses remote agent as a tool.
    
    Args:
        remote_tool: Tool function for remote agent
        
    Returns:
        Configured LLMAgent instance
    """
    model = GeminiModel(
        model_name="gemini-2.0-flash-exp",
        temperature=0.7
    )
    
    system_instruction = """
    You are a helpful assistant that can use remote agents as tools.
    When appropriate, delegate tasks to remote agents.
    """
    
    agent = LLMAgent(
        model=model,
        system_instruction=system_instruction,
        tools=[remote_tool]
    )
    
    return agent


def main():
    """Main function to demonstrate A2A client usage."""
    # Get remote agent endpoint from environment or use default
    remote_endpoint = os.getenv(
        "REMOTE_AGENT_ENDPOINT",
        "http://localhost:8080"
    )
    
    print(f"Connecting to remote agent at: {remote_endpoint}")
    
    # Create remote agent tool
    remote_tool = create_remote_agent_tool(remote_endpoint)
    
    # Create local agent with remote tool
    agent = create_local_agent(remote_tool)
    
    # Example usage
    query = "Hello from the local agent!"
    response = agent.run(query)
    
    print(f"Query: {query}")
    print(f"Response: {response}")


if __name__ == "__main__":
    main()


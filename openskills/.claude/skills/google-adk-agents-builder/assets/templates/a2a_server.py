#!/usr/bin/env python3
"""
A2A Server Template

This template provides a starting point for exposing an ADK agent
via the Agent2Agent (A2A) Protocol.
"""

import os
from google.adk import LLMAgent
from google.adk.models import GeminiModel
from a2a_sdk import AgentServer, ServerConfig


def create_agent():
    """
    Create and configure the ADK agent to expose.
    
    Returns:
        Configured LLMAgent instance
    """
    model = GeminiModel(
        model_name="gemini-2.0-flash-exp",
        temperature=0.7
    )
    
    system_instruction = """
    You are a helpful assistant exposed via A2A Protocol.
    Other agents can communicate with you through the A2A interface.
    """
    
    agent = LLMAgent(
        model=model,
        system_instruction=system_instruction
    )
    
    return agent


def create_server(agent, host="0.0.0.0", port=8080):
    """
    Create and configure the A2A server.
    
    Args:
        agent: The ADK agent to expose
        host: Server host address
        port: Server port number
        
    Returns:
        Configured AgentServer instance
    """
    config = ServerConfig(
        host=host,
        port=port,
        max_workers=10,
        timeout=30
    )
    
    server = AgentServer(agent, config=config)
    
    return server


def main():
    """Main function to start the A2A server."""
    # Create agent
    agent = create_agent()
    
    # Create server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    
    server = create_server(agent, host=host, port=port)
    
    print(f"Starting A2A server on {host}:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        # Start server
        server.run()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()


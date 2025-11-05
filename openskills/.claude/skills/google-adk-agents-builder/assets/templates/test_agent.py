#!/usr/bin/env python3
"""
Agent Testing Template

This template provides a starting point for testing ADK agents
with unit tests, integration tests, and end-to-end tests.
"""

import unittest
from google.adk import LLMAgent
from google.adk.models import GeminiModel


class TestAgent(unittest.TestCase):
    """Test cases for ADK agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        model = GeminiModel(
            model_name="gemini-2.0-flash-exp",
            temperature=0.7
        )
        
        self.agent = LLMAgent(
            model=model,
            system_instruction="You are a helpful test assistant."
        )
    
    def test_basic_query(self):
        """Test basic agent query."""
        query = "Hello"
        response = self.agent.run(query)
        
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
    
    def test_query_with_context(self):
        """Test agent query with context."""
        query = "What is 2+2?"
        response = self.agent.run(query)
        
        self.assertIsNotNone(response)
        # Add more specific assertions based on expected response
    
    def test_error_handling(self):
        """Test agent error handling."""
        # Test with invalid input
        query = ""
        response = self.agent.run(query)
        
        # Agent should handle gracefully
        self.assertIsNotNone(response)


class TestAgentWithTools(unittest.TestCase):
    """Test cases for agent with tools."""
    
    def setUp(self):
        """Set up test fixtures with tools."""
        from google.adk import Tool
        
        @Tool
        def test_tool(input_data: str) -> str:
            """Test tool for testing."""
            return f"Processed: {input_data}"
        
        model = GeminiModel(
            model_name="gemini-2.0-flash-exp",
            temperature=0.7
        )
        
        self.agent = LLMAgent(
            model=model,
            tools=[test_tool]
        )
    
    def test_tool_usage(self):
        """Test agent using tools."""
        query = "Use the test tool with input 'test data'"
        response = self.agent.run(query)
        
        self.assertIsNotNone(response)
        # Verify tool was used appropriately


def run_integration_test():
    """Run integration test."""
    # Create agent
    model = GeminiModel(model_name="gemini-2.0-flash-exp")
    agent = LLMAgent(model=model)
    
    # Test end-to-end flow
    queries = [
        "Hello",
        "What can you do?",
        "Help me understand ADK"
    ]
    
    for query in queries:
        response = agent.run(query)
        print(f"Query: {query}")
        print(f"Response: {response[:100]}...")  # Print first 100 chars
        print()


if __name__ == "__main__":
    # Run unit tests
    unittest.main(verbosity=2)
    
    # Run integration test
    print("\n" + "="*50)
    print("Integration Test")
    print("="*50)
    run_integration_test()


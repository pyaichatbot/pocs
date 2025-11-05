#!/usr/bin/env python3
"""
Custom Agent Template

This template provides a starting point for creating a custom agent
by extending BaseAgent in Google's Agent Development Kit (ADK).
"""

from google.adk import BaseAgent, Tool
from google.adk.models import GeminiModel
from typing import Any, Dict


class CustomAgent(BaseAgent):
    """
    Custom agent that extends BaseAgent for specialized functionality.
    
    This agent can implement custom logic, state management, and
    specialized workflows beyond what LLM agents provide.
    """
    
    def __init__(self, model=None, tools=None):
        """
        Initialize the custom agent.
        
        Args:
            model: Optional LLM model for language capabilities
            tools: Optional list of tools for the agent
        """
        super().__init__()
        
        # Configure model if provided
        self.model = model or GeminiModel(
            model_name="gemini-2.0-flash-exp",
            temperature=0.7
        )
        
        # Register tools
        self.tools = tools or []
        for tool in self.tools:
            self.register_tool(tool)
        
        # Initialize custom state
        self.state = {}
    
    def run(self, input_data: Any) -> Any:
        """
        Execute the agent's main logic.
        
        This method should be overridden to implement custom agent behavior.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Agent response
        """
        # Preprocessing
        processed_input = self.preprocess(input_data)
        
        # Main logic
        result = self.process(processed_input)
        
        # Postprocessing
        response = self.postprocess(result)
        
        return response
    
    def preprocess(self, input_data: Any) -> Any:
        """
        Preprocess input data before processing.
        
        Args:
            input_data: Raw input data
            
        Returns:
            Processed input data
        """
        # Add custom preprocessing logic here
        return input_data
    
    def process(self, input_data: Any) -> Any:
        """
        Main processing logic.
        
        Args:
            input_data: Preprocessed input data
            
        Returns:
            Processing result
        """
        # Add custom processing logic here
        # Example: Use tools, call model, etc.
        return {"result": "processed", "data": input_data}
    
    def postprocess(self, result: Any) -> Any:
        """
        Postprocess result before returning.
        
        Args:
            result: Processing result
            
        Returns:
            Final response
        """
        # Add custom postprocessing logic here
        return result
    
    def register_tool(self, tool: Tool):
        """
        Register a tool with the agent.
        
        Args:
            tool: Tool to register
        """
        if tool not in self.tools:
            self.tools.append(tool)
    
    def get_state(self) -> Dict:
        """
        Get current agent state.
        
        Returns:
            Current state dictionary
        """
        return self.state.copy()
    
    def set_state(self, state: Dict):
        """
        Set agent state.
        
        Args:
            state: State dictionary to set
        """
        self.state.update(state)


def main():
    """Main function to run the custom agent."""
    # Create custom agent
    agent = CustomAgent()
    
    # Example usage
    input_data = "Process this data"
    response = agent.run(input_data)
    
    print(f"Input: {input_data}")
    print(f"Response: {response}")


if __name__ == "__main__":
    main()


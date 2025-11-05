#!/usr/bin/env python3
"""
Agent Project Initializer

Creates a new ADK agent project with proper structure.

Usage:
    init_agent.py <agent-name> --path <path>

Examples:
    init_agent.py my-agent --path ./agents
    init_agent.py weather-bot --path /path/to/agents
"""

import sys
import os
from pathlib import Path


AGENT_TEMPLATE = """#!/usr/bin/env python3
\"\"\"
{agent_name} - ADK Agent

This agent was generated using the google-adk-agents-builder skill.
\"\"\"

from google.adk import LLMAgent
from google.adk.models import GeminiModel


def create_agent():
    \"\"\"
    Create and configure the agent.
    
    Returns:
        Configured LLMAgent instance
    \"\"\"
    model = GeminiModel(
        model_name="gemini-2.0-flash-exp",
        temperature=0.7,
        max_tokens=2048
    )
    
    system_instruction = \"\"\"
    You are a helpful assistant.
    \"\"\"
    
    agent = LLMAgent(
        model=model,
        system_instruction=system_instruction
    )
    
    return agent


def main():
    \"\"\"Main function to run the agent.\"\"\"
    agent = create_agent()
    
    # Example usage
    query = "Hello!"
    response = agent.run(query)
    print(f"Response: {response}")


if __name__ == "__main__":
    main()
"""

REQUIREMENTS_TEMPLATE = """google-adk>=0.1.0
a2a-sdk>=0.3.0
"""

README_TEMPLATE = """# {agent_name}

ADK Agent created using google-adk-agents-builder skill.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure authentication:
```bash
gcloud auth application-default login
```

## Usage

Run the agent:
```bash
python agent.py
```

## Configuration

Edit `agent.py` to customize:
- Model settings
- System instructions
- Tools
- Memory configuration

## Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [A2A Protocol](https://a2a-protocol.org/)
"""


def create_agent_project(agent_name, path):
    """
    Create a new agent project directory structure.
    
    Args:
        agent_name: Name of the agent
        path: Base path where agent directory should be created
        
    Returns:
        Path to created agent directory, or None if error
    """
    # Determine agent directory path
    agent_dir = Path(path).resolve() / agent_name
    
    # Check if directory already exists
    if agent_dir.exists():
        print(f"❌ Error: Agent directory already exists: {agent_dir}")
        return None
    
    # Create agent directory
    try:
        agent_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ Created agent directory: {agent_dir}")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return None
    
    # Create agent.py
    agent_file = agent_dir / "agent.py"
    try:
        agent_file.write_text(AGENT_TEMPLATE.format(agent_name=agent_name))
        agent_file.chmod(0o755)
        print("✅ Created agent.py")
    except Exception as e:
        print(f"❌ Error creating agent.py: {e}")
        return None
    
    # Create requirements.txt
    requirements_file = agent_dir / "requirements.txt"
    try:
        requirements_file.write_text(REQUIREMENTS_TEMPLATE)
        print("✅ Created requirements.txt")
    except Exception as e:
        print(f"❌ Error creating requirements.txt: {e}")
        return None
    
    # Create README.md
    readme_file = agent_dir / "README.md"
    try:
        readme_file.write_text(README_TEMPLATE.format(agent_name=agent_name))
        print("✅ Created README.md")
    except Exception as e:
        print(f"❌ Error creating README.md: {e}")
        return None
    
    # Print next steps
    print(f"\n✅ Agent '{agent_name}' initialized successfully at {agent_dir}")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Configure authentication: gcloud auth application-default login")
    print("3. Edit agent.py to customize your agent")
    print("4. Run the agent: python agent.py")
    
    return agent_dir


def main():
    """Main function."""
    if len(sys.argv) < 4 or sys.argv[2] != "--path":
        print("Usage: init_agent.py <agent-name> --path <path>")
        print("\nAgent name requirements:")
        print("  - Valid Python identifier")
        print("  - Lowercase letters, digits, and hyphens")
        print("  - Max 50 characters")
        print("\nExamples:")
        print("  init_agent.py my-agent --path ./agents")
        print("  init_agent.py weather-bot --path /path/to/agents")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    path = sys.argv[3]
    
    print(f"🚀 Initializing agent: {agent_name}")
    print(f"   Location: {path}")
    print()
    
    result = create_agent_project(agent_name, path)
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()


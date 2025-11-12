# Workspace Directory

This directory is the execution environment for agent-generated code.

## Structure

- `servers/` - MCP tool files (auto-generated)
  - Each server has its own subdirectory
  - Tools are Python files that can be imported
  
- `skills/` - Reusable agent code (agent can create)
  - Agents can save working code here for future use
  - Add SKILL.md files to document skills

## Usage

Agents can:
- Explore `servers/` to discover available tools
- Read tool files to understand interfaces
- Write files here for state persistence
- Save reusable code in `skills/`


# What Are AI Agents

## Definition
Autonomous or semi‑autonomous software that perceives, reasons, and acts using enterprise tools.

## SME Knowledge
- Perception (inputs/logs/APIs) → Reasoning (policies/goals) → Action (tool/API calls via MCP).
- Single-agent vs multi-agent; where HITL gates are placed.

## Mermaid – Agent Loop
```mermaid
sequenceDiagram
  participant User
  participant Agent
  participant MCP as MCP/Tools
  User->>Agent: Goal / Request
  Agent->>MCP: Tool calls (scoped)
  MCP-->>Agent: Results + Audit
  Agent-->>User: Answer + Evidence
```
## Audience Q&A
- **Q:** Is this just a chatbot?  
  **A:** No—agents can plan, call tools, and take actions with audit trails.

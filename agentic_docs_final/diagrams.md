
# Mermaid Diagrams & Speaker Notes

---

# 🧠 1. Agentic Architecture
```mermaid
flowchart TD
    RAG[Memory Warehouse] --> Agent
    Agent --> LLM[LLM Brain]
    Agent --> Tools
    SubAgents --> Agent
```

---

# 🤖 2. Sub-Agent Flow
```mermaid
flowchart LR
    Planner --> Coder --> Reviewer --> Tester --> Evals --> Planner
```

---

# 🔗 3. A2A Message Flow
```mermaid
sequenceDiagram
    participant P as Planner
    participant C as Coder
    participant R as Reviewer
    participant T as Tester

    P->>C: Send plan JSON
    C->>R: Send code JSON
    R->>T: Send review JSON
    T->>P: Send test report
```

---

# Speaker Notes

## Slide — LLM as Brain
Explain how LLM thinks but cannot remember.

## Slide — RAG as Memory Warehouse
Memory retrieval improves accuracy.

## Slide — Agents Feed the Brain
Agents deliver context + tools.

## Slide — Sub-Agents
Explain each role with real examples.

## Slide — A2A
Structured communication ensures consistency.

---

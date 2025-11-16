# Human-in-the-Loop (HITL)

## Role
Humans supervise and approve critical decisions.

## SME Knowledge
- Decision points: risk thresholds, uncertainty, regulatory triggers; reviewer UX.

## Mermaid – HITL Gate
```mermaid
sequenceDiagram
  participant Agent
  participant Approver
  Agent->>Approver: Recommendation + Evidence
  Approver-->>Agent: Approve / Reject / Request More Info
```
## Audience Q&A
- **Q:** Will HITL slow us down?  
  **A:** Only applied to high‑risk actions; low‑risk flows remain automated.

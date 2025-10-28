
# Opik in Practice — Observability, Testing & Guardrails for AI Apps

**Audience:** Engineering & AI Teams  
**Scope:** What Opik does, how we integrated it, and real examples we can ship today.

---

## 1) What is Opik?
Opik is an open-source framework for **observability, evaluation, and guardrails** in LLM/AI applications.  
It helps you trace model calls, test quality, enforce safety policies, and monitor behaviour in production.

**Why we care:** Traditional unit tests can’t guarantee quality of *generated* outputs. Opik gives us **behavioural testing** and **runtime visibility** across the full AI pipeline (RAG, agents, prompts, tools, etc.).

---

## 2) What exactly do we test?
- **LLM Output Quality:** relevance, correctness, hallucinations, toxicity.
- **RAG Quality:** retrieval precision, context coverage, citation correctness.
- **Agent Workflows:** step traces, tool usage correctness, latency per step.
- **Prompts & Policies:** prompt A/B tests, safety guardrails (e.g., PII).
- **Ops & Cost:** token/latency/cost per route, alerting on failures.

> TL;DR — We’re testing the **AI application’s behaviour**, not just the raw LLM string.

---

## 3) Our Demos

### A. RAG FAQ Demo
- Retrieves best knowledge chunk from a local FAQ and generates an answer with Azure OpenAI (or local stub).
- Opik logs: retrieval hit, generation call, latency, output.
- Evaluation: simple string similarity (Jaccard) as a sanity signal.
- Guardrails: optional PII block.

**Run:** see `rag_faq_opik_demo/README.md`

**Key Screens (in Opik):**
- Trace view per request: inputs/outputs + timings.
- Aggregate charts: average latency, token usage (if using Azure OpenAI), guardrail events.

---

### B. Multi‑Agent Pipeline (Planner → Coder → Reviewer)
- Planner decomposes a task.
- Coder generates a function.
- Reviewer validates syntax/structure.
- Opik traces each function, so we can pinpoint failure steps, latency, and error patterns.

**Run:** see `multi_agent_opik_demo/README.md`

**Why it matters:** In agentic systems, errors often happen **between** steps (wrong tool, bad plan). Traces make these visible.

---

## 4) How Opik fits Enterprise Usage
- **Self-hosted option**: keep prompts/outputs inside our Azure VNets.
- **Security**: use Key Vault, non-root containers, RBAC around dashboards.
- **Compliance**: redact sensitive fields, retention windows, SIEM export.
- **CI/CD**: run offline evaluation suites and fail builds if quality drops.

---

## 5) Next Steps & Extensions
- Swap naive retriever for our real vector search (pgvector/Qdrant).
- Add proper evaluation datasets and ground-truth scoring.
- Introduce topic & policy guardrails tuned to our domain.
- Wire Opik metrics to our monitoring stack (Azure Monitor/Grafana).

---

## 6) Key Takeaways
- Opik gives us **eyes and brakes** for AI systems.
- We can **measure** quality and **enforce** safety before and after prod.
- The provided demos are a **template**: drop them into any service and expand.

> Recommended rollout: Pilot on one service → define a small eval suite → wire Opik traces in prod → iterate guardrails.

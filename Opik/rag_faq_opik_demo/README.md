
# RAG FAQ Demo with Opik (Python + optional Azure OpenAI)

This is a **self‑contained** RAG-style FAQ bot that logs traces, evaluates responses, and applies guardrails via **Opik**.
It runs **with or without** Azure OpenAI — if Azure is not configured, it falls back to a local stub model so you can run it offline.

## Features
- Minimal in‑memory RAG (string‑based nearest match on FAQ chunks).
- Opik tracing for each step: retrieval → generation → final answer.
- Simple evaluations (string similarity) + optional Opik metrics (if installed).
- Optional Guardrails (PII) via Opik (if installed).

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt

# (Optional) Configure Azure OpenAI
export AZURE_OPENAI_KEY=...
export AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini  # or your deployment name

# (Optional) Enable Opik & configure self-host/cloud
export USE_OPIK=1
# For local/self-hosted Opik
export OPIK_USE_LOCAL=1
# Or for Comet cloud: export COMET_API_KEY=...

# Run demo server
python app/main.py
# Then open http://127.0.0.1:8000 and try the demo form, or use:
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"question":"What is refund policy?"}'
```

## Project Layout
```
app/
  main.py                 # FastAPI app with /ask endpoint + HTML demo
  retriever.py            # Tiny RAG retriever over ./data/faq.md
  azure_client.py         # Azure OpenAI wrapper + LocalLLM fallback
  opik_instrumentation.py # Safe Opik setup (no-op if not installed)
  evaluation.py           # Simple string-sim metric + optional Opik metrics
data/
  faq.md                  # Seed knowledge base
tests/
  eval_dataset.json       # Mini dataset for offline eval
requirements.txt
```

## Notes
- If **Opik** is not installed, the code runs with a **no-op shim** and prints a warning.
- Set `USE_OPIK=1` to enable tracing/guardrails; otherwise, it's a normal app.
- For production, point the Opik client to your self‑hosted server (behind your VNet).

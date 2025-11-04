# PRP — Chat Backend Invoking Codex (npm CLI) On‑Demand (Enterprise-Grade)

## 1) Objective
Expose a **/chat** API in a Python backend (FastAPI) that safely delegates to your **Codex npm CLI** for:
- **LLM chat answers** (with optional SSE streaming), and
- **Allowlisted tool/skill execution** (e.g., code search, run tests),
based on the user’s query, with strong guardrails, redaction, and timeouts.

## 2) Scope
- Single endpoint: `POST /chat` supporting `mode={"chat"|"tool"}`
- **Chat**: proxy to `codex chat` with message + context
- **Tool**: invoke allowlisted skills mapped to CLI subcommands
- **Streaming**: proxy NDJSON/SSE lines to UI when enabled
- **Security**: input caps, redaction, allowlist, shell‑safe argv, hard timeouts
- **Ops**: container includes Node (CLI) + Python, provider via env (OpenAI/Azure)

## 3) Non‑Goals
- Direct DB/file writes from Codex outputs
- Arbitrary shell execution (no unconstrained commands)
- Long‑running jobs (>120s) — hand off to async worker if needed

## 4) Architecture

```mermaid
flowchart LR
  UI[Chat UI] -->|POST /chat| API[FastAPI Backend]
  API -->|mode=chat| CodexChat[Codex CLI: chat --stream?]
  API -->|mode=tool (allowlisted)| CodexTool[Codex CLI: tool <skill> ...]
  subgraph Guardrails
    Caps[Input/Context size caps]
    Redact[PII/Token redaction]
    Allow[Skill allowlist]
    Timeout[Per-call timeout & resource limits]
  end
  Guardrails -. enforce .-> API
  CodexChat -->|SSE/NDJSON stdout| API --> UI
  CodexTool -->|JSON stdout| API --> UI
```

## 5) API Contract

### Request
`POST /chat`
```json
{
  "mode": "chat",        // or "tool"
  "message": "Explain this stack trace",
  "context": "Traceback ...",     // optional
  "skill": "code-search",         // required when mode=tool
  "extra": { }                    // optional, only allowlisted keys honored
}
```

### Response
- **mode=chat, streaming on**: `text/event-stream` with `data: <ndjson or token>` frames.
- **mode=chat, streaming off**: `{ "answer": "<text>", "meta": {...} }`
- **mode=tool**: `{ "tool_result": { ... }, "meta": {"skill":"..."} }`

## 6) Backend Responsibilities
1. **Build CLI argv lists without shell** (`subprocess.Popen([...], shell=False)`).
2. **Redact** sensitive patterns at boundary (AWS keys, Bearer tokens, PAN/IBAN).
3. **Cap** message/context length (e.g., 8k / 200k chars).
4. **Timeouts** (SIGINT at N seconds; kill on overrun).
5. **Allowlist** permitted `skill`→command mappings; reject others.
6. **Streaming proxy**: if `--stream` is supported, forward lines as SSE.
7. **Logging**: only metadata (durations, token counts if provided), no plaintext content.

## 7) Authoritative Backend Skeleton

```python
# FastAPI /chat that shells out to Codex CLI safely
# - shell=False, strict allowlist, timeouts, SSE proxy

# See full implementation in your repo:
# - main.py (endpoints)
# - skill_map.py (allowlist)
# - redact.py (regexes)
# - ops/logging.py (structured logs + OTel)
```

## 8) Container Image (Pinned Versions)

```Dockerfile
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Node + Codex CLI
RUN apt-get update && apt-get install -y curl ca-certificates git \\
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \\
 && apt-get install -y nodejs \\
 && npm i -g @your-scope/codex-cli@1.2.3 \\
 && codex --version \\
 && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 9) Environment & Config
- **Provider (OpenAI)**: `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4o-mini`
- **Provider (Azure)**: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `LLM_PROVIDER=azure`
- Controls: `STREAM_ENABLED=true`, `CODEX_TIMEOUT_SEC=120`, `CHAT_MAX_INPUT_CHARS=8000`, `CHAT_MAX_CTX_CHARS=200000`
- Networking: egress restrict to LLM endpoints; no outbound to arbitrary hosts

## 10) Security & Compliance
- Non-root user in container; read-only root FS (where feasible)
- No `shell=True` anywhere; validate/escape inputs; reject unknown `skill`
- Redaction ON at boundary **and** (if supported) in CLI
- Audit logs: request IDs, timings, skill name, model, token usage (no content)
- Data residency: use Azure region matching compliance requirements

## 11) Observability & SLOs
- Metrics: `codex_call_duration_ms`, `codex_timeouts`, `codex_errors`, `codex_tokens`
- Tracing: one span per CLI call with exit code and duration
- SLO: p95 < 2s for short “chat” responses; < 15s for tool results

## 12) Acceptance Criteria
- `/chat` returns streamed tokens when CLI supports `--stream`
- Tool calls limited to allowlisted skills; unknown skill → 400
- Inputs beyond caps are safely truncated with a visible marker
- Redaction verified on sample secrets
- Hard timeout enforced and reported
- Container reproducible with pinned CLI version

## 13) Risks & Mitigations
- **CLI output variability** → prefer `--json`/NDJSON modes; strict parsing
- **Long-running tools** → enforce timeout, push to async worker if needed
- **Leakage** → boundary redaction; do not log plaintext; restrict egress

## 14) Deliverables
- Backend service (Dockerized) exposing `/chat` with SSE support
- Skill allowlist with documented commands
- Runbook for env vars, scaling, and troubleshooting

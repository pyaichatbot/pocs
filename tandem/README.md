# NonStop Agent Review — Integrator Guide

This repository contains specifications and prompts to build a Git-free, agentic code review pipeline for HPE NonStop/Tandem codebases.

## Files
- `PRP.md` — Project Requirement Prompt (authoritative scope & acceptance).
- `Architecture.md` — Diagrams (component + sequence) and data notes.
- `API-Spec.md` — HTTP interface (upload, status, artifacts, webhooks).
- `Security.md` — Governance, redaction, audit, reliability.
- `Claude-n8n-Prompt.md` — Copy-paste prompt to generate an n8n workflow.

## Implementation Path
1. Stand up Review API (async jobs) and artifact store.
2. Implement toolchain T1–T5, then delivery T6.
3. Add SFTP ingestion (server or via n8n) with Vault-backed credentials.
4. Wire Slack/Confluence and Webhooks.
5. Validate with ZIP and SFTP modes; confirm “respond only after complete”.

## Tips
- Use SARIF for IDE diagnostics; provide MD/HTML for readability.
- Keep model temp low, log model/version and token usage.
- Track redaction counters and never send raw PAN/PII to LLMs.

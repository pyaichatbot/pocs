# PRP — NonStop/Tandem Agent Code Review (Git-free, Task-Complete Response)

## 1. Objective
Build an **agentic code review service** that **does not respond immediately** on upload. The system accepts code either:
- **Option A (ZIP Upload):** a client uploads a ZIP/TAR.GZ of source pulled from HPE NonStop via SFTP, or
- **Option B (Direct SFTP Fetch):** the system (or an n8n workflow) uses SFTP to fetch code directly from NonStop paths.

The agent orchestrates a **collection of specialized tools** (each tool does one task). The service responds **only after all tasks complete**, returning a consolidated summary and downloadable artifacts (SARIF, Markdown, HTML).

## 2. Core Requirements
1. **Asynchronous Processing**
   - `POST /v1/reviews` enqueues a job; system **does not** send final response on upload.
   - Final response is available via `GET /v1/reviews/{job_id}` **after all tools finish**; optional webhook notification.
2. **Two Ingestion Modes**
   - **ZIP Upload** via multipart form.
   - **Direct SFTP Fetch** initiated by server or n8n workflow (path allowlist/credentials vault).
3. **Toolchain (Agent = collection of tools)**
   - **T1 Normalize**: decode (EBCDIC→UTF-8), normalize line endings, strip COBOL sequence numbers safely.
   - **T2 Classify**: detect languages (COBOL/TACL/TAL/C/C++/Scripts), copybook resolution.
   - **T3 Static Rules**: NonStop-specific heuristics (PII/PAN detection, Guardian/Safeguard perms, EMS logging, Pathway patterns, TMF boundaries).
   - **T4 LLM Review (profile-driven)**: security, reliability, maintainability. Deterministic (temp ≤ 0.2). Uses enterprise LLM proxy (Azure OpenAI or in-house).
   - **T5 Consolidate**: de-duplicate, rank severity, produce SARIF + Markdown + HTML.
   - **T6 Deliver**: persist artifacts, post Slack/Teams summary, optional Confluence page, expose artifact URLs.
4. **Result Artifacts**
   - **SARIF** (Problems panel in VS Code),
   - **Markdown** (engineer/manager readable),
   - **HTML** (polished, filters, charts).
5. **Governance & Audit**
   - Redaction **before** model calls (PAN, IBAN, emails, IPs, secrets).
   - Job ledger (who/when/source hash/model/config).
   - Path allowlist/denylist for SFTP.
   - Size/limit controls (files, MB, token budgets).
6. **No GitLab dependency**
   - Entire workflow runs independently of Git or GitLab MR pipelines.

## 3. Success Criteria
- End-to-end flow works for both **ZIP Upload** and **Direct SFTP Fetch**.
- Findings available only **after all tools complete**.
- Reports downloadable; SARIF viewable in VS Code; Slack summary delivered.
- Supports NonStop specifics (COBOL copybooks, Pathway, TMF, EMS, Guardian).
- Meets redaction/audit requirements (PCI/PII-safe).

## 4. Non-Goals (initial)
- No live agents running on NonStop host.
- No direct modification of NonStop code (only suggestions/patches as diffs).

## 5. Interfaces (high-level)
### Create Review Job
`POST /v1/reviews`
- **Body (multipart):**
  - `mode`: `"zip"` | `"sftp"`
  - `code_bundle` (file) when `mode=zip`
  - `sftp` (json) when `mode=sftp` — `{host, port, username, path_globs, auth_ref}`
  - `meta` (json) shared metadata (profiles, redaction, limits, delivery)
- **Response 202:** `{ job_id, status: "queued" }`

### Get Review Status/Result
`GET /v1/reviews/{job_id}`
- Returns `{ status, summary, artifacts, error? }`

### Artifacts
`GET /v1/reviews/{job_id}/artifacts/{name}` → `report.sarif.json | report.md | report.html | worker.log | traces.jsonl`

### Webhook (optional)
`review.completed` with HMAC signature.

## 6. Data Contracts (key fields)

**meta (example):**
```json
{
  "source": { "system": "HPE-NonStop", "host": "ns01", "path_root": "\\prod\\vol\\subvol" },
  "languages": ["cobol","tacl","tal","c"],
  "profiles": ["security","reliability","style"],
  "encoding": "auto",
  "redaction": { "pii": true, "pan": true, "secrets": true },
  "llm": { "provider": "azure-openai", "model": "gpt-4o-mini", "temperature": 0.1 },
  "limits": { "max_file_mb": 2, "max_total_mb": 300, "max_parallel": 8 },
  "delivery": { "webhook_url": null, "notify": ["slack:#nonstop-reviews"] },
  "tags": ["nonstop","pathway","tmf"]
}
```

**sftp (example when mode=sftp):**
```json
{
  "host": "nonstop.internal",
  "port": 22,
  "username": "svc-review",
  "auth_ref": "vault:secret/nonstop/sftp/keypair",
  "path_globs": ["\\prod\\vol\\*.cob", "\\prod\\vol\\**\\*.tacl"],
  "encoding": "auto"
}
```

## 7. Constraints & Risks
- Mixed encodings (EBCDIC/ASCII) and COBOL fixed columns—must preserve original for patch context.
- Large bundles → token/cost blowups—enforce scoping, file and size limits.
- Legacy constructs (Pathway/TMF) require tailored rules to avoid LLM hallucinations.

## 8. Milestones
1. **M0**: API skeleton + Job queue + ZIP ingestion + dummy artifacts.
2. **M1**: Normalize + classify + static checks (COBOL/TACL/TAL).
3. **M2**: LLM review profiles + consolidation + SARIF/MD/HTML.
4. **M3**: SFTP ingestion path + vault integration + allowlist/denylist.
5. **M4**: Slack/Confluence delivery + dashboards + trend storage.
6. **M5**: Hardening (rate limits, HMAC webhooks, structured logs, tracing).

## 9. Acceptance Tests
- Upload ZIP → job runs → artifacts present → Slack summary delivered.
- SFTP mode (n8n or server) → fetches, reviews, responds post-completion only.
- Redaction counters > 0 on PAN-embedded samples; zero raw PANs sent to model.
- SARIF loads in VS Code, findings align with MD/HTML summaries.

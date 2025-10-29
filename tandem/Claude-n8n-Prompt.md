You are an expert n8n workflow engineer. Build a production-ready workflow named **"NonStop Agent Review"** that supports **two ingestion modes** and only **notifies after all tasks complete**.

## Goals
- **Mode A: ZIP Upload Trigger**
  - Webhook node receives multipart with `code_bundle` (file) and `meta` (json string), `mode=zip`.
  - Store file temporarily (Binary Data). Push a message to the Job Queue (e.g., Redis/AMQP) with a new `job_id`.
  - Return 202 with `{job_id, status:"queued"}`.
  - Downstream processors: unpack → normalize → classify → static rules → LLM review → consolidate → persist artifacts → update job in DB → Slack & webhook notify.

- **Mode B: Direct SFTP Fetch**
  - Cron or Webhook to start.
  - SFTP node lists/gets files by **allowlisted** `path_globs`. Use credentials from environment/credentials store.
  - Zip or tar the fetched files into a bundle.
  - Send the bundle and `meta` to the **Review API** `POST /v1/reviews` with `mode="zip"` (server-side processing), **OR** execute the same internal toolchain steps within the workflow if you implement them natively.

## Required Nodes & Config
- **Webhook (POST /n8n/nonstop/reviews)** — entry for ZIP upload (Mode A).
- **IF/Switch** — route by `mode`.
- **SFTP** — list/fetch files from NonStop (Mode B).
- **Function** — package files, compute bundle hash, generate `job_id`.
- **Queue (Redis/RabbitMQ)** — enqueue processing jobs.
- **HTTP Request** — call internal **Review API** for orchestration or artifact publishing.
- **Execute Command / Function** — run Normalize/Classify/Static tools if local to n8n runtime.
- **Wait/MoveOn** pattern — ensure **final notifications only after all tools finish**.
- **Slack** — post summary with artifact links.
- **HTTP Request (Webhook Out)** — optional customer webhook.

## Constraints
- Do **not** return final results in the initial Webhook. Only **202 Accepted** with `job_id`.
- Enforce file size & path allowlist/denylist.
- Add HMAC signatures for outgoing webhooks; verify for incoming calls.
- Mask secrets; do pre-LLM redaction if model calls are made inside workflow.

## Deliverables
- Exportable n8n JSON with all nodes wired.
- Environment variables noted: `N8N_SFTP_HOST`, `N8N_SFTP_USER`, `N8N_SFTP_KEY`, `REVIEW_API_BASE`, `SLACK_WEBHOOK`, `WEBHOOK_SECRET`.
- Test instructions: Use Postman to hit Webhook with multipart; or trigger Cron for SFTP mode; observe Slack summary and fetch artifacts from Review API after completion.

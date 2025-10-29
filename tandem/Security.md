# Security, Compliance & Ops

## Data Protection
- **Pre-LLM Redaction**: PAN/PII/Secrets removed before model calls. Keep reversible map only in memory for diffing, never persisted.
- **Provider**: Only enterprise-approved (Azure OpenAI or in-house proxy). No vendor logs of raw code.
- **Scopes/Limits**: `max_file_mb`, `max_total_mb`, `max_parallel`, `include/exclude globs` to avoid data sprawl.

## Access Control
- Upload/API via OAuth2/JWT (service accounts for n8n).  
- SFTP creds via Vault (`auth_ref`) with strict allowlist/denylist of paths.  
- Per-job RBAC: only creator/team can read artifacts.

## Audit & Observability
- Structured logs (request id, job id), OpenTelemetry traces across tools.  
- Job ledger: config hash, model/version, token/cost, redaction counters.  
- Retention policies for artifacts/logs with auto-purge.

## Reliability
- Idempotent uploads keyed by bundle hash.  
- Retry with backoff for SFTP and model calls.  
- Dead-letter queue for failed jobs; resumable processing.

## Compliance Hints (NonStop)
- Guardian/Safeguard: check perms, privilege elevation scripts.  
- EMS logging: mask sensitive fields.  
- TMF transaction boundaries: verify begin/commit/abort patterns.  
- Pathway server/clients: validate request/response handling best practices.

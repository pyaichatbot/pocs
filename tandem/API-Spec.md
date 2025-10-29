# API Specification

## POST /v1/reviews
**Purpose**: Enqueue a review job. Do **not** compute results synchronously.

**Content-Type**: `multipart/form-data`  
**Fields**:
- `mode`: `"zip"` or `"sftp"`
- `code_bundle`: file (required when `mode=zip`)
- `meta`: JSON string (required)
- `sftp`: JSON string (required when `mode=sftp`)
- `attachments[]`: file array (optional)

**Responses**:
- `202 Accepted`
```json
{ "job_id": "rev_01JDX...", "status": "queued" }
```
- Errors: `400` invalid input, `413` payload too large, `429` rate limited, `500` server.

## GET /v1/reviews/{job_id}
**Purpose**: Fetch job status and final results (only meaningful after completion).  
**Response**:
```json
{
  "job_id": "rev_...",
  "status": "queued|running|completed|failed|canceled",
  "summary": {
    "files_scanned": 127,
    "findings_total": 34,
    "by_severity": {"critical":2,"high":6,"medium":18,"low":8},
    "hotspots": ["src/cobol/txn_srv.cob"]
  },
  "artifacts": {
    "sarif": "/v1/reviews/rev_.../artifacts/report.sarif.json",
    "markdown": "/v1/reviews/rev_.../artifacts/report.md",
    "html": "/v1/reviews/rev_.../artifacts/report.html",
    "log": "/v1/reviews/rev_.../artifacts/worker.log",
    "traces": "/v1/reviews/rev_.../artifacts/traces.jsonl"
  },
  "error": null
}
```

## GET /v1/reviews/{job_id}/artifacts/{name}
Serves artifact files with appropriate content-type.  
**Names**: `report.sarif.json`, `report.md`, `report.html`, `worker.log`, `traces.jsonl`

## Webhooks
- Event: `review.completed`
- Headers: `X-Review-Event`, `X-Delivery-Id`, `X-Signature`
- Body:
```json
{
  "event": "review.completed",
  "job_id": "rev_...",
  "status": "completed",
  "summary": {...},
  "artifacts": {...}
}
```

**Security**: HMAC SHA-256 over raw body; shared secret per webhook endpoint.

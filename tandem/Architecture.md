# Architecture & Diagrams

## Mermaid — Component Diagram
```mermaid
flowchart LR
    Dev[(Developer / Job)] -- ZIP Upload --> API[Review API]
    Dev -- Trigger SFTP (n8n) --> n8n[n8n Workflow]
    n8n -- SFTP Fetch --> SFTP[(HPE NonStop SFTP)]
    n8n --> API

    API --> Q[Job Queue]
    Q --> W1[Worker: T1 Normalize]
    W1 --> W2[Worker: T2 Classify]
    W2 --> W3[Worker: T3 Static Rules]
    W3 --> W4[Worker: T4 LLM Review]
    W4 --> W5[Worker: T5 Consolidate]
    W5 --> Store[(Artifacts Store)]
    W5 --> DB[(Jobs DB + Audit)]
    W5 --> Notify[Slack/Teams/Confluence]
    API <-- Query Results --> Dev
```

## Mermaid — Sequence (Respond after all tools complete)
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Queue
    participant Worker
    participant LLM as LLM Proxy
    participant Store as Artifacts
    participant Notify as Notifications

    Client->>API: POST /v1/reviews (mode=zip|sftp)
    API-->>Client: 202 Accepted {job_id, status: queued}
    API->>Queue: Enqueue(job_id)

    loop Toolchain
        Queue->>Worker: Dequeue(job_id)
        Worker->>Worker: T1 Normalize, T2 Classify, T3 Static
        Worker->>LLM: T4 Review (profiles)
        LLM-->>Worker: Findings rationale
        Worker->>Worker: T5 Consolidate
    end
    Worker->>Store: Save SARIF/MD/HTML
    Worker->>API: Mark job completed (summary + artifact URLs)
    API->>Notify: Send summary (Slack/Teams/Webhook)

    Client->>API: GET /v1/reviews/{job_id}
    API-->>Client: 200 {status: completed, artifacts, summary}
```

## Artifacts & Data
- **Jobs DB**: job status, summary, config hash, model versions, audit.
- **Artifact Store**: `report.sarif.json`, `report.md`, `report.html`, `worker.log`, `traces.jsonl`.
- **Notifications**: Slack message with severity counts + top hotspots + artifact links.

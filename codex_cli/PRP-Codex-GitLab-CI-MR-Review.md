# PRP — OpenAI/Codex CLI in GitLab CI/CD for MR Code Review (Enterprise-Grade)

## 1) Objective
Implement a **pure-CLI** code review step in GitLab CI/CD that runs on every Merge Request (MR), reviews **diff-only** changes using your **Codex npm CLI**, and publishes results to the MR via **native GitLab reports (SARIF)** and/or a comment. No custom reviewer code required.

## 2) Scope
- Trigger on `merge_request_event`
- Collect diff-only file set, apply size caps, redact sensitive content
- Invoke **Codex CLI** with pinned version and provider via env (OpenAI or Azure OpenAI)
- Emit **JSON + SARIF** artifacts
- Post MR note via **Codex CLI** or GitLab API using **CI_JOB_TOKEN**
- Non-blocking or gated (configurable) based on severity

## 3) Non‑Goals
- Full SAST replacement
- Large monorepo static analysis beyond diff scope
- Secret scanning (handled by your standard toolchain)

## 4) High-Level Flow

```mermaid
flowchart LR
  Dev[Developer opens MR] --> CI[GitLab CI Job: codex_review]
  CI -->|read| Env[CI Vars (MR IDs, branches)]
  CI --> Git[git fetch --depth=0]
  Git --> Diff[Compute diff-only file list
+ caps + redaction]
  Diff --> Codex[Codex CLI (npm)
--provider --model --caps --redact]
  Codex --> Artifacts[JSON + SARIF artifacts]
  Artifacts --> MRUI[MR Security/Widget Tabs]
  Codex -->|optional| Note[MR Comment via CI_JOB_TOKEN]
```

## 5) Functional Requirements
1. **Triggering**
   - Run only for `merge_request_event`.
   - Use `GIT_DEPTH: 0` to compute accurate diffs.
2. **Diff Scope**
   - `git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...$CI_COMMIT_SHA --name-only` to list changed files.
   - Cap with `REVIEW_MAX_FILES` and `REVIEW_MAX_CHARS`.
3. **Redaction**
   - Enable CLI redaction mode (PAN/PCI/IBAN/tokens). Provide org regex allowlist/denylist.
4. **Execution**
   - Run `codex review` with pinned version `@x.y.z`. Provider via env.
5. **Outputs**
   - Produce `codex_output.json` and `codex_sarif.sarif`.
   - Attach SARIF to `artifacts:reports:sast:`.
6. **Publishing**
   - Prefer **CLI-native MR note**; else call GitLab API using `CI_JOB_TOKEN`. No PAT.
7. **Gating**
   - Optional gate: fail job if SARIF includes `level=error` or severity=HIGH (configurable).

## 6) Non‑Functional Requirements
- **Security**: Use `CI_JOB_TOKEN` or OIDC → KeyVault; mask provider keys; egress restrict to LLM endpoints.
- **Observability**: Log metadata only (file counts, token usage), no source plaintext. Job duration SLO < 5 min typical.
- **Reliability**: Retries with exponential backoff if provider rate-limits. Chunk diff when exceeding caps.
- **Compliance**: Redaction ON by default; store artifacts with retention policy; respect data residency of provider (Azure region).

## 7) Environment & Secrets
- **OpenAI**: `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4o-mini`
- **Azure OpenAI**: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, and `LLM_PROVIDER=azure`
- **GitLab**: use built-in `CI_JOB_TOKEN` for API; no PAT required.
- Controls: `REVIEW_MAX_FILES`, `REVIEW_MAX_CHARS`, `REDACT_ENABLED=true`

## 8) CI Configuration (Authoritative)

```yaml
stages: [review]

variables:
  GIT_DEPTH: 0
  LLM_PROVIDER: "openai"
  OPENAI_MODEL: "gpt-4o-mini"
  REVIEW_MAX_FILES: "200"
  REVIEW_MAX_CHARS: "200000"
  REDACT_ENABLED: "true"

codex_review:
  stage: review
  image: node:20-bullseye
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  before_script:
    - npm i -g @your-scope/codex-cli@1.2.3
    - codex --version
    - git fetch origin "$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
  script:
    - |
      CHANGED=$(git diff --name-only "origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...$CI_COMMIT_SHA")
      echo "$CHANGED" | sed '/^\s*$/d' | head -n ${REVIEW_MAX_FILES} > changed_files.txt
    - codex review         --provider "$LLM_PROVIDER"         --model "$OPENAI_MODEL"         --redact "$REDACT_ENABLED"         --max-files "$REVIEW_MAX_FILES"         --max-chars "$REVIEW_MAX_CHARS"         --files-list changed_files.txt         --out-json codex_output.json         --out-sarif codex_sarif.sarif         --mr-iid "$CI_MERGE_REQUEST_IID"         --project-id "$CI_PROJECT_ID"         --ci-url "$CI_API_V4_URL"
    # If CLI doesn't post a comment itself, use CI_JOB_TOKEN (optional)
    - |
      if [ -f codex_output.json ]; then
        NOTES="### 🤖 Codex Review
Artifacts: codex_sarif.sarif"
        curl -fsS -X POST -H "JOB-TOKEN: $CI_JOB_TOKEN"           --data-urlencode "body=${NOTES}"           "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes" || true
      fi
    # Optional gate: fail on HIGH
    - |
      python - << 'PY'
import json, sys
try:
    sarif=json.load(open('codex_sarif.sarif'))
    errs=[r for r in sarif['runs'][0]['results'] if r.get('level')=='error']
    if errs:
        print(f"Found {len(errs)} HIGH issues"); sys.exit(1)
except Exception as e:
    print("Gate check skipped:", e)
PY
  artifacts:
    when: always
    paths: [codex_output.json, codex_sarif.sarif]
    reports:
      sast: codex_sarif.sarif
  allow_failure: false
```

## 9) Acceptance Criteria
- MR pipeline posts artifacts; Security tab displays SARIF findings
- (If enabled) MR comment is present
- Redaction verified on sample secrets
- Gate behavior verified (job fails on synthetic HIGH issue)
- Average runtime on typical diff < 3 minutes

## 10) Risks & Mitigations
- **Provider rate limits** → add backoff and chunking.
- **False positives** → scope to diff, use concise prompts in CLI, tune severity mapping.
- **Leaks** → strict redaction and egress rules; prohibit reviewing non-source/binary files.

## 11) Deliverables
- Updated `.gitlab-ci.yml`
- Runner image pin with Codex CLI @ exact version (optional)
- Runbook: envs, failure modes, rollback

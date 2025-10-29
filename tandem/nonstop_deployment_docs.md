# NonStop Agent Review - Production Deployment Guide

## 📋 Overview

This production-ready n8n workflow supports two ingestion modes for NonStop code review:
- **Mode A**: Direct ZIP upload via webhook (async processing)
- **Mode B**: Scheduled SFTP fetch with automatic bundling

**Key Features:**
- ✅ Async job queue (Redis) with 202 Accepted response
- ✅ Complete processing pipeline: unpack → normalize → classify → static analysis → LLM review
- ✅ Notifications ONLY after all tasks complete
- ✅ HMAC signature verification & generation
- ✅ Sensitive data redaction before LLM
- ✅ Error handling with Slack notifications
- ✅ Automatic cleanup of temp files

---

## 🔧 Environment Variables

Create a `.env` file or set these in your n8n instance:

```bash
# Required
N8N_SFTP_HOST=nonstop.example.com
N8N_SFTP_PORT=22
N8N_SFTP_USER=review_agent
N8N_SFTP_KEY=/path/to/ssh/private_key
# OR use password:
N8N_SFTP_PASSWORD=your_secure_password

REVIEW_API_BASE=https://api.nonstop-review.internal
REVIEW_API_TOKEN=Bearer your_api_token_here

SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

WEBHOOK_SECRET=your_32_character_secret_key_here

# Optional
CUSTOMER_WEBHOOK_URL=https://customer.example.com/webhooks/review-complete
SFTP_ALLOWED_GLOBS=*.cob,*.cbl,*.sql,*.ddl,*.jcl
SFTP_DENIED_PATHS=temp/,backup/,.git/

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
```

---

## 🗂️ n8n Credentials Setup

### 1. Redis Credential
**Type**: Redis
- **Name**: Redis Account
- **Host**: `{{$env.REDIS_HOST}}`
- **Port**: `{{$env.REDIS_PORT}}`
- **Password**: `{{$env.REDIS_PASSWORD}}`
- **Database**: `{{$env.REDIS_DB}}`

### 2. SFTP Credential
**Type**: SFTP
- **Name**: NonStop SFTP
- **Host**: `{{$env.N8N_SFTP_HOST}}`
- **Port**: `{{$env.N8N_SFTP_PORT}}`
- **Username**: `{{$env.N8N_SFTP_USER}}`
- **Auth Type**: Private Key
- **Private Key**: `{{$env.N8N_SFTP_KEY}}`

### 3. HTTP Header Auth (Review API)
**Type**: Header Auth
- **Name**: Review API Auth
- **Name**: `Authorization`
- **Value**: `{{$env.REVIEW_API_TOKEN}}`

---

## 📦 Installation

### 1. Import Workflow
```bash
# Copy the workflow JSON to your n8n instance
curl -X POST http://your-n8n-instance:5678/rest/workflows \
  -H "X-N8N-API-KEY: your_api_key" \
  -H "Content-Type: application/json" \
  -d @nonstop_agent_review.json
```

### 2. Install System Dependencies
The workflow requires these tools on the n8n host:

```bash
# Ubuntu/Debian
apt-get update
apt-get install -y unzip iconv

# RHEL/CentOS
yum install -y unzip glibc-common

# Verify
which unzip
which iconv
```

### 3. Configure Redis Queue
```bash
# Install Redis if not present
docker run -d \
  --name n8n-redis \
  -p 6379:6379 \
  -e REDIS_PASSWORD=your_redis_password \
  redis:7-alpine redis-server --requirepass your_redis_password
```

### 4. Set File Permissions
```bash
# Create temp directory
mkdir -p /tmp/nonstop_reviews
chmod 755 /tmp/nonstop_reviews

# Ensure n8n user has write access
chown n8n:n8n /tmp/nonstop_reviews
```

---

## 🚀 Usage

### Mode A: ZIP Upload (Webhook)

#### 1. Prepare Test Data
```bash
# Create sample COBOL file
cat > sample.cob << 'EOF'
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SAMPLE-PROG.
       PROCEDURE DIVISION.
           DISPLAY "Hello NonStop"
           STOP RUN.
       END PROGRAM SAMPLE-PROG.
EOF

# Create metadata
cat > meta.json << 'EOF'
{
  "project": "PAYMENT-SYSTEM",
  "version": "2.4.1",
  "submitter": "dev-team@example.com",
  "priority": "high"
}
EOF

# Create ZIP bundle
zip code_bundle.zip sample.cob
```

#### 2. Generate HMAC Signature
```bash
# Calculate signature (Python)
python3 << 'EOF'
import hmac
import hashlib
import json

secret = "your_32_character_secret_key_here"
payload = {
    "mode": "zip",
    "meta": json.dumps({
        "project": "PAYMENT-SYSTEM",
        "version": "2.4.1"
    })
}

signature = hmac.new(
    secret.encode(),
    json.dumps(payload).encode(),
    hashlib.sha256
).hexdigest()

print(f"X-NonStop-Signature: {signature}")
EOF
```

#### 3. Submit via cURL
```bash
curl -X POST https://your-n8n-instance/webhook/nonstop/reviews \
  -H "X-NonStop-Signature: YOUR_CALCULATED_SIGNATURE" \
  -F "mode=zip" \
  -F "code_bundle=@code_bundle.zip" \
  -F 'meta={"project":"PAYMENT-SYSTEM","version":"2.4.1"}'
```

#### 4. Expected Response (202 Accepted)
```json
{
  "job_id": "job_1730275200000_a3f7c9e1d2b4",
  "status": "queued",
  "message": "Review job queued for processing"
}
```

#### 5. Monitor Progress
```bash
# Check job status
curl https://api.nonstop-review.internal/v1/jobs/job_1730275200000_a3f7c9e1d2b4 \
  -H "Authorization: Bearer your_api_token"
```

---

### Mode B: SFTP Fetch (Scheduled)

#### 1. Configure SFTP Source
```bash
# SSH to NonStop and prepare files
ssh user@nonstop.example.com

# Create test directory
mkdir -p /code/reviews/payment-system
cd /code/reviews/payment-system

# Add sample files
cat > account.cob << 'EOF'
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ACCOUNT-MGR.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-ACCOUNT-NUM PIC 9(10).
       PROCEDURE DIVISION.
           MOVE 1234567890 TO WS-ACCOUNT-NUM
           DISPLAY "Account: " WS-ACCOUNT-NUM
           GOBACK.
EOF
```

#### 2. Manual Trigger (Testing)
```bash
# Trigger the workflow manually via API
curl -X POST https://your-n8n-instance/webhook/trigger/sftp-cron \
  -H "X-N8N-API-KEY: your_api_key"
```

#### 3. Cron Schedule
The workflow runs automatically every 6 hours:
- `0 */6 * * *` (00:00, 06:00, 12:00, 18:00 UTC)

To customize:
```javascript
// Edit "SFTP Cron Trigger" node
{
  "cronExpression": "0 2 * * *"  // Daily at 2 AM
}
```

---

## 📊 Notification Examples

### Slack Notification (Success)
```
NonStop Code Review Completed

Job: job_1730275200000_a3f7c9e1d2b4
━━━━━━━━━━━━━━━━━━━━━━━━━━
Files Analyzed: 12
Risk Score: 45/100

Findings:
🔴 2 High | 🟡 8 Medium | 🔵 15 Low

Artifact: View Full Report
━━━━━━━━━━━━━━━━━━━━━━━━━━
NonStop Agent Review • Just now
```

### Slack Notification (Error)
```
⚠️ NonStop Review Failed

Job: job_1730275200000_a3f7c9e1d2b4
━━━━━━━━━━━━━━━━━━━━━━━━━━
Error: Unable to unpack ZIP file
Node: Unpack Bundle
Time: 2025-10-30T14:32:15.000Z
```

### Customer Webhook Payload
```json
{
  "job_id": "job_1730275200000_a3f7c9e1d2b4",
  "bundle_hash": "sha256:a3f7c9e1...",
  "timestamp": "2025-10-30T14:35:22.000Z",
  "file_count": 12,
  "findings": {
    "static": {
      "total": 25,
      "by_severity": {
        "high": 2,
        "medium": 8,
        "low": 15
      }
    },
    "llm": {
      "risk_score": 45,
      "recommendations": [
        "Replace STOP RUN with GOBACK in account.cob",
        "Add error handling for file operations"
      ]
    }
  },
  "status": "completed"
}
```

**Verify Webhook Signature:**
```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        json.dumps(payload).encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

# Usage
is_valid = verify_webhook(
    payload=request.json,
    signature=request.headers['X-NonStop-Signature'],
    secret='your_32_character_secret_key_here'
)
```

---

## 🧪 Testing

### Postman Collection

#### Test 1: Valid ZIP Upload
```json
POST /webhook/nonstop/reviews
Headers:
  X-NonStop-Signature: {{calculated_hmac}}
Body (form-data):
  mode: zip
  code_bundle: [file]
  meta: {"project":"TEST","version":"1.0.0"}

Expected: 202 Accepted with job_id
```

#### Test 2: Invalid Signature
```json
POST /webhook/nonstop/reviews
Headers:
  X-NonStop-Signature: invalid_signature
Body: [same as above]

Expected: 401 Unauthorized
```

#### Test 3: Oversized File
```bash
# Create 150MB file
dd if=/dev/zero of=large.zip bs=1M count=150

curl -X POST ... -F "code_bundle=@large.zip"

Expected: 400 Bad Request "File size exceeds limit"
```

### Integration Tests

```bash
# Run full workflow test
./scripts/test-workflow.sh

# Expected output:
# ✓ Webhook accepts multipart upload
# ✓ Job enqueued to Redis
# ✓ 202 response returned
# ✓ Processing completes in < 60s
# ✓ Slack notification sent
# ✓ Artifacts persisted
# ✓ Temp files cleaned
```

---

## 🔍 Monitoring

### Key Metrics
```bash
# Redis queue depth
redis-cli -a your_redis_password LLEN nonstop_review_jobs

# Active workflows
curl http://your-n8n-instance:5678/rest/executions \
  -H "X-N8N-API-KEY: your_api_key" | jq '.data[] | select(.workflowId=="NonStop Agent Review")'

# Failed jobs (last 24h)
curl "https://api.nonstop-review.internal/v1/jobs?status=failed&since=24h" \
  -H "Authorization: Bearer your_api_token"
```

### Logs
```bash
# n8n logs
docker logs n8n | grep "NonStop Agent Review"

# Filter by job_id
docker logs n8n | grep "job_1730275200000"

# Error tracking
docker logs n8n | grep "ERROR" | grep "nonstop"
```

---

## 🛡️ Security Checklist

- [x] HMAC signature verification on incoming webhooks
- [x] HMAC signature generation on outgoing webhooks
- [x] Sensitive data redaction before LLM calls
- [x] File size limits enforced (100MB default)
- [x] Path allowlist/denylist for SFTP
- [x] Temporary file cleanup
- [x] API authentication (Bearer tokens)
- [x] SFTP key-based authentication
- [x] Redis password protection
- [x] Error messages don't leak secrets

---

## 🚨 Troubleshooting

### Issue: "Invalid HMAC signature"
**Solution**: Ensure payload matches exactly, including JSON formatting
```bash
# Debug: Print exact payload being signed
node -e "console.log(JSON.stringify({mode:'zip',meta:'{...}'}))"
```

### Issue: "Unable to unpack ZIP file"
**Solution**: Verify ZIP is valid and not corrupted
```bash
unzip -t code_bundle.zip
```

### Issue: "SFTP connection refused"
**Solution**: Check credentials and network access
```bash
sftp -i /path/to/key user@nonstop.example.com
```

### Issue: "Redis queue not processing"
**Solution**: Verify Redis subscriber is running
```bash
redis-cli -a password SUBSCRIBE nonstop_review_jobs
# Should show "Reading messages..."
```

### Issue: "Notifications not sent"
**Solution**: Test webhooks directly
```bash
# Test Slack
curl -X POST $SLACK_WEBHOOK -d '{"text":"Test"}'

# Check customer webhook
curl -X POST $CUSTOMER_WEBHOOK_URL \
  -H "X-NonStop-Signature: test" \
  -d '{"test":true}'
```

---

## 📈 Performance Tuning

### Concurrent Processing
```javascript
// Increase Redis consumers (create multiple "Dequeue Job" nodes)
// Node 1: Queue name "nonstop_review_jobs_1"
// Node 2: Queue name "nonstop_review_jobs_2"
// Load balance in "Enqueue Job" node
```

### Batch SFTP Fetches
```javascript
// Modify "Filter Allowed Files" to group by directory
// Process 10 files at a time instead of all at once
const batches = _.chunk(filtered, 10);
```

### Cache LLM Results
```javascript
// Add caching in "LLM Review" node
const cacheKey = `llm_cache:${bundle_hash}`;
const cached = await redis.get(cacheKey);
if (cached) return JSON.parse(cached);
```

---

## 📞 Support

- **Documentation**: https://docs.nonstop-review.internal
- **Slack**: #nonstop-agent-support
- **Email**: devops@example.com
- **On-call**: PagerDuty integration enabled

---

## 🔄 Version History

- **v1.0.0** (2025-10-30): Initial production release
  - Dual ingestion modes (ZIP + SFTP)
  - Complete processing pipeline
  - Error handling & notifications

---

**Last Updated**: October 30, 2025  
**Maintainer**: DevOps Team  
**License**: Internal Use Only
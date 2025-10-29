# NonStop Agent Review - n8n Workflow

> Production-ready workflow for automated NonStop code review with dual ingestion modes, async processing, and comprehensive notifications.

## 🚀 Quick Start (Local Testing)

### Prerequisites
- Docker & Docker Compose
- curl, jq (for testing)
- 4GB RAM minimum

### 1. Clone and Setup
```bash
# Create project directory
mkdir nonstop-agent-review
cd nonstop-agent-review

# Create required subdirectories
mkdir -p mock-api test-data

# Place the following files:
# - docker-compose.yml
# - mock-api/server.js  
# - test-workflow.sh
# - nonstop_agent_review.json (workflow export)
```

### 2. Create Mock API package.json
```bash
cat > mock-api/package.json << 'EOF'
{
  "name": "mock-review-api",
  "version": "1.0.0",
  "main": "server.js",
  "dependencies": {
    "express": "^4.18.2",
    "body-parser": "^1.20.2"
  }
}
EOF
```

### 3. Start Services
```bash
# Start all containers
docker-compose up -d

# Verify all services are running
docker-compose ps

# Should show: n8n, redis, sftp-server, review-api, mock-slack, mock-webhook
```

### 4. Access n8n & Import Workflow
```bash
# Open browser
open http://localhost:5678

# Login credentials:
# Username: admin
# Password: admin123

# Import workflow:
# 1. Click "Workflows" → "Import from File"
# 2. Select nonstop_agent_review.json
# 3. Activate the workflow (toggle switch)
```

### 5. Configure Credentials in n8n

**Redis Credential:**
- Name: `Redis Account`
- Host: `redis`
- Port: `6379`
- Password: `redis_password_123`

**SFTP Credential:**
- Name: `NonStop SFTP`
- Host: `sftp-server`
- Port: `22`
- Username: `nonstop`
- Password: `nonstop123`

**Review API Auth:**
- Name: `Review API Auth`
- Header Name: `Authorization`
- Header Value: `Bearer test_token_12345`

### 6. Run Tests
```bash
# Make script executable
chmod +x test-workflow.sh

# Run complete test suite
./test-workflow.sh

# Expected output:
# ✓ TEST 1: Webhook Accessibility
# ✓ TEST 2: Invalid HMAC Signature Rejection
# ✓ TEST 3: Oversized File Rejection
# ✓ TEST 4: Valid ZIP Upload (Mode A)
# ✓ TEST 5: Redis Queue Verification
# ✓ TEST 6: End-to-End Job Completion
# ... (10 tests total)
```

### 7. Manual Test - Mode A (ZIP Upload)
```bash
# Create test COBOL file
cat > test.cob << 'EOF'
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TEST-PROG.
       PROCEDURE DIVISION.
           DISPLAY "Hello World"
           STOP RUN.
EOF

# Create ZIP
zip test_bundle.zip test.cob

# Calculate HMAC
PAYLOAD='{"mode":"zip","meta":"{\"project\":\"TEST\"}"}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "test_secret_key_32_characters_long" | awk '{print $2}')

# Submit
curl -X POST http://localhost:5678/webhook/nonstop/reviews \
  -H "X-NonStop-Signature: $SIGNATURE" \
  -F "mode=zip" \
  -F "code_bundle=@test_bundle.zip" \
  -F 'meta={"project":"TEST","version":"1.0.0"}'

# Response (202 Accepted):
# {"job_id":"job_1730275200000_abc123","status":"queued","message":"Review job queued for processing"}
```

### 8. Manual Test - Mode B (SFTP)
```bash
# Add files to SFTP server
cat > test-data/sample.cob << 'EOF'
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SAMPLE.
       PROCEDURE DIVISION.
           DISPLAY "SFTP Test"
           GOBACK.
EOF

# Copy to SFTP container
docker cp test-data/sample.cob nonstop-sftp:/home/nonstop/code/reviews/test-data/

# Trigger SFTP workflow in n8n UI:
# 1. Find "SFTP Cron Trigger" node
# 2. Click "Execute Node"
# 3. Monitor execution
```

### 9. Monitor & Debug
```bash
# View n8n logs
docker-compose logs -f n8n

# Check Redis queue
docker exec -it nonstop-redis redis-cli -a redis_password_123 LLEN nonstop_review_jobs

# View Review API logs
docker-compose logs -f review-api

# Check mock Slack notifications
docker-compose logs mock-slack | grep POST

# Inspect job status
curl http://localhost:3000/v1/jobs/YOUR_JOB_ID \
  -H "Authorization: Bearer test_token_12345" | jq .
```

---

## 📁 Project Structure

```
nonstop-agent-review/
├── docker-compose.yml           # Complete test environment
├── nonstop_agent_review.json    # n8n workflow export
├── test-workflow.sh             # Automated test suite
├── README.md                    # This file
├── mock-api/
│   ├── server.js                # Mock Review API
│   └── package.json             # Node dependencies
└── test-data/
    └── *.cob, *.sql, *.jcl      # Sample NonStop files
```

---

## 🔄 Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MODE A: ZIP UPLOAD                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    [Webhook] → [Verify HMAC] → [Process ZIP] → [Enqueue]
                              │
                              ▼
                    [Return 202 Accepted]


┌─────────────────────────────────────────────────────────────┐
│                   MODE B: SFTP FETCH                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    [Cron] → [SFTP List] → [Filter] → [Download] → [Bundle]
                              │
                              ▼
                         [Enqueue]


┌─────────────────────────────────────────────────────────────┐
│               ASYNC PROCESSING PIPELINE                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    [Dequeue] → [Store Temp] → [Unpack] → [Normalize]
                              │
                              ▼
    [Classify] → [Static Analysis] → [Redact PII]
                              │
                              ▼
    [LLM Review] → [Consolidate] → [Persist Artifacts]
                              │
                              ▼
    [Update Job DB] → [Notify Slack + Webhook] → [Cleanup]
```

---

## 🎯 Key Features

### ✅ Dual Ingestion Modes
- **Mode A**: Direct ZIP upload via webhook (async)
- **Mode B**: Scheduled SFTP fetch with auto-bundling

### ✅ Async Processing
- Redis-backed job queue
- Immediate 202 Accepted response
- No blocking on webhook endpoint

### ✅ Complete Pipeline
1. **Unpack**: Extract ZIP contents
2. **Normalize**: Convert EBCDIC to UTF-8
3. **Classify**: Detect file types (COBOL, SQL, JCL)
4. **Static Analysis**: Rule-based code scanning
5. **LLM Review**: AI-powered analysis
6. **Consolidate**: Merge all findings
7. **Persist**: Store artifacts
8. **Notify**: Slack + custom webhooks

### ✅ Security
- HMAC signature verification (incoming)
- HMAC signature generation (outgoing)
- PII redaction before LLM
- Path allowlist/denylist for SFTP
- File size limits
- API authentication

### ✅ Notifications
- Slack summary with risk scores
- Custom webhook with full payload
- **Notifications ONLY after complete processing**
- Error notifications with detailed context

---

## 🔧 Configuration

### Environment Variables
See `docker-compose.yml` for all variables. Key ones:

```bash
WEBHOOK_SECRET=your_32_character_secret_key_here
REVIEW_API_BASE=http://review-api:3000
REVIEW_API_TOKEN=Bearer your_token
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK
CUSTOMER_WEBHOOK_URL=https://customer.example.com/callback
```

### Customization
- **Static Rules**: Edit `Static Analysis` node function
- **LLM Prompts**: Modify `LLM Review` HTTP request body
- **File Filters**: Update `SFTP_ALLOWED_GLOBS` env var
- **Schedule**: Change `SFTP Cron Trigger` cron expression
- **Notifications**: Customize `Prepare Notifications` node

---

## 📊 Production Deployment

### Prerequisites
- n8n instance (self-hosted or cloud)
- Redis (AWS ElastiCache, Redis Cloud, etc.)
- SFTP access to NonStop system
- Review API backend
- Slack workspace

### Steps
1. Deploy Redis cluster
2. Configure SFTP credentials
3. Deploy Review API
4. Import workflow to n8n
5. Set production environment variables
6. Configure credentials in n8n
7. Activate workflow
8. Run smoke tests

### Scaling
- **Horizontal**: Multiple n8n instances with shared Redis
- **Vertical**: Increase n8n container resources
- **Queue**: Use separate Redis consumers for parallel processing

---

## 🐛 Troubleshooting

### "Invalid HMAC signature"
- Verify `WEBHOOK_SECRET` matches
- Check payload JSON formatting (no extra whitespace)
- Ensure body is JSON stringified before hashing

### "Unable to unpack ZIP file"
- Verify ZIP is valid: `unzip -t bundle.zip`
- Check file permissions in temp directory
- Ensure `unzip` command is installed

### "SFTP connection refused"
- Verify credentials: `sftp user@host`
- Check network connectivity
- Ensure SFTP server allows connections

### "Redis queue not processing"
- Check Redis connection: `redis-cli -h host -p port PING`
- Verify `Dequeue Job` node is active
- Check for errors in n8n execution logs

### "Notifications not sent"
- Test webhooks directly with curl
- Verify webhook URLs are accessible
- Check for errors in notification nodes

---

## 📝 API Reference

### Webhook Endpoint
```
POST /webhook/nonstop/reviews
```

**Headers:**
- `X-NonStop-Signature`: HMAC-SHA256 signature
- `Content-Type`: multipart/form-data

**Body (multipart):**
- `mode`: "zip"
- `code_bundle`: [file]
- `meta`: JSON string

**Response (202):**
```json
{
  "job_id": "job_1730275200000_abc123",
  "status": "queued",
  "message": "Review job queued for processing"
}
```

### Review API

**POST /v1/llm/analyze**
```json
{
  "job_id": "job_123",
  "files": [...],
  "static_findings": [...]
}
```

**POST /v1/artifacts**
```json
{
  "job_id": "job_123",
  "summary": {...}
}
```

**PATCH /v1/jobs/:id**
```json
{
  "status": "completed",
  "artifact_url": "https://..."
}
```

---

## 📚 Additional Resources

- [n8n Documentation](https://docs.n8n.io/)
- [Redis Pub/Sub Guide](https://redis.io/topics/pubsub)
- [SFTP Best Practices](https://www.ssh.com/academy/ssh/sftp)
- [HMAC Authentication](https://tools.ietf.org/html/rfc2104)

---

## 🤝 Support

- **Issues**: File via internal ticketing system
- **Questions**: #nonstop-agent-support Slack channel
- **Docs**: https://docs.nonstop-review.internal
- **On-call**: PagerDuty escalation

---

## 📄 License

Internal Use Only - Proprietary

---

**Version**: 1.0.0  
**Last Updated**: October 30, 2025  
**Maintainer**: DevOps Team
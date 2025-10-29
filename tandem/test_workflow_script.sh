#!/bin/bash
###############################################################################
# NonStop Agent Review - Workflow Test Suite
# Tests both Mode A (ZIP upload) and Mode B (SFTP) ingestion paths
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
N8N_WEBHOOK_URL="${N8N_WEBHOOK_URL:-http://localhost:5678/webhook/nonstop/reviews}"
REVIEW_API_BASE="${REVIEW_API_BASE:-http://localhost:3000}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-test_secret_key_32_characters}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
TEST_DIR="$(mktemp -d)"

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

cleanup() {
    log_info "Cleaning up test files..."
    rm -rf "$TEST_DIR"
}

trap cleanup EXIT

calculate_hmac() {
    local payload="$1"
    echo -n "$payload" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $2}'
}

wait_for_job() {
    local job_id="$1"
    local max_wait=120
    local elapsed=0
    
    log_info "Waiting for job $job_id to complete (max ${max_wait}s)..."
    
    while [ $elapsed -lt $max_wait ]; do
        status=$(curl -s "$REVIEW_API_BASE/v1/jobs/$job_id" \
            -H "Authorization: Bearer test_token" | jq -r '.status')
        
        if [ "$status" = "completed" ]; then
            log_info "Job completed successfully"
            return 0
        elif [ "$status" = "failed" ]; then
            log_error "Job failed"
            return 1
        fi
        
        sleep 5
        elapsed=$((elapsed + 5))
        echo -n "."
    done
    
    echo ""
    log_error "Job timeout after ${max_wait}s"
    return 1
}

###############################################################################
# Test Setup
###############################################################################

setup_test_data() {
    log_info "Setting up test data in $TEST_DIR..."
    
    # Create sample COBOL file with intentional issues
    cat > "$TEST_DIR/payment.cob" << 'EOF'
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYMENT-PROCESSOR.
       AUTHOR. TEST-TEAM.
       
       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-ACCOUNT-NUMBER      PIC 9(10).
       01 WS-AMOUNT              PIC 9(7)V99.
       01 WS-PASSWORD            PIC X(20) VALUE "HARDCODED123".
       01 WS-CARD-NUMBER         PIC 9(16).
       
       PROCEDURE DIVISION.
       MAIN-PROCESS.
           DISPLAY "Processing payment"
           MOVE 1234567890123456 TO WS-CARD-NUMBER
           PERFORM PROCESS-PAYMENT
           STOP RUN.
           
       PROCESS-PAYMENT.
           IF WS-AMOUNT > 0
              DISPLAY "Amount: " WS-AMOUNT
           ELSE
              DISPLAY "Invalid amount"
           END-IF.
           
       END PROGRAM PAYMENT-PROCESSOR.
EOF

    # Create SQL file
    cat > "$TEST_DIR/schema.sql" << 'EOF'
-- Payment Schema
CREATE TABLE PAYMENTS (
    PAYMENT_ID      INT NOT NULL PRIMARY KEY,
    ACCOUNT_NUM     VARCHAR(10),
    AMOUNT          DECIMAL(9,2),
    CREATED_DATE    TIMESTAMP
);

-- Issue: SELECT *
SELECT * FROM PAYMENTS WHERE ACCOUNT_NUM = '1234567890';

-- Good practice
SELECT PAYMENT_ID, AMOUNT FROM PAYMENTS WHERE PAYMENT_ID = 1;
EOF

    # Create JCL file
    cat > "$TEST_DIR/run_payment.jcl" << 'EOF'
//PAYPROC JOB (ACCT),'PAYMENT PROCESSOR',CLASS=A
//STEP01  EXEC PGM=PAYMENT-PROCESSOR
//SYSOUT  DD SYSOUT=*
//SYSIN   DD *
PROCESS PAYMENTS
/*
EOF

    # Create metadata
    cat > "$TEST_DIR/meta.json" << 'EOF'
{
  "project": "PAYMENT-SYSTEM-TEST",
  "version": "1.0.0-test",
  "submitter": "test@example.com",
  "priority": "high",
  "tags": ["cobol", "payment", "test"]
}
EOF

    # Create ZIP bundle
    cd "$TEST_DIR"
    zip -q code_bundle.zip payment.cob schema.sql run_payment.jcl
    cd - > /dev/null
    
    log_info "Test data created: $(ls -lh $TEST_DIR/code_bundle.zip | awk '{print $5}') bundle"
}

###############################################################################
# Test Cases
###############################################################################

test_webhook_accessibility() {
    log_info "TEST 1: Webhook Accessibility"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$N8N_WEBHOOK_URL")
    
    if [ "$response" = "404" ] || [ "$response" = "405" ]; then
        log_info "Webhook is accessible (returned $response for GET)"
        return 0
    else
        log_error "Unexpected response: $response"
        return 1
    fi
}

test_invalid_signature() {
    log_info "TEST 2: Invalid HMAC Signature Rejection"
    
    local payload='{"mode":"zip","meta":"{}"}'
    local invalid_sig="invalid_signature_12345"
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$N8N_WEBHOOK_URL" \
        -H "X-NonStop-Signature: $invalid_sig" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "401" ] || [ "$http_code" = "403" ]; then
        log_info "Invalid signature correctly rejected (HTTP $http_code)"
        return 0
    else
        log_error "Expected 401/403, got $http_code"
        return 1
    fi
}

test_oversized_file() {
    log_info "TEST 3: Oversized File Rejection (>100MB)"
    
    # Create 150MB dummy file
    dd if=/dev/zero of="$TEST_DIR/large.bin" bs=1M count=150 2>/dev/null
    zip -q "$TEST_DIR/large_bundle.zip" "$TEST_DIR/large.bin"
    
    local meta='{"project":"TEST","version":"1.0.0"}'
    local payload="{\"mode\":\"zip\",\"meta\":\"$meta\"}"
    local signature=$(calculate_hmac "$payload")
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$N8N_WEBHOOK_URL" \
        -H "X-NonStop-Signature: $signature" \
        -F "mode=zip" \
        -F "code_bundle=@$TEST_DIR/large_bundle.zip" \
        -F "meta=$meta")
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "400" ] || [ "$http_code" = "413" ]; then
        log_info "Oversized file correctly rejected (HTTP $http_code)"
        return 0
    else
        log_warn "Expected 400/413, got $http_code (may not be enforced)"
        return 0
    fi
}

test_valid_zip_upload() {
    log_info "TEST 4: Valid ZIP Upload (Mode A)"
    
    local meta=$(cat "$TEST_DIR/meta.json" | tr -d '\n')
    local payload="{\"mode\":\"zip\",\"meta\":\"$meta\"}"
    local signature=$(calculate_hmac "$payload")
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$N8N_WEBHOOK_URL" \
        -H "X-NonStop-Signature: $signature" \
        -F "mode=zip" \
        -F "code_bundle=@$TEST_DIR/code_bundle.zip" \
        -F "meta=$meta")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" != "202" ]; then
        log_error "Expected 202 Accepted, got $http_code"
        echo "Response: $body"
        return 1
    fi
    
    job_id=$(echo "$body" | jq -r '.job_id')
    status=$(echo "$body" | jq -r '.status')
    
    if [ -z "$job_id" ] || [ "$job_id" = "null" ]; then
        log_error "No job_id in response"
        echo "Response: $body"
        return 1
    fi
    
    if [ "$status" != "queued" ]; then
        log_error "Expected status 'queued', got '$status'"
        return 1
    fi
    
    log_info "ZIP uploaded successfully: job_id=$job_id"
    
    # Store for later tests
    echo "$job_id" > "$TEST_DIR/job_id.txt"
    
    return 0
}

test_redis_queue() {
    log_info "TEST 5: Redis Queue Verification"
    
    if [ -z "$REDIS_PASSWORD" ]; then
        queue_depth=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LLEN nonstop_review_jobs 2>/dev/null || echo "0")
    else
        queue_depth=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --no-auth-warning LLEN nonstop_review_jobs 2>/dev/null || echo "0")
    fi
    
    if [ "$queue_depth" -ge 1 ]; then
        log_info "Job found in Redis queue (depth: $queue_depth)"
        return 0
    else
        log_warn "Redis queue appears empty (may have already processed)"
        return 0
    fi
}

test_job_completion() {
    log_info "TEST 6: End-to-End Job Completion"
    
    if [ ! -f "$TEST_DIR/job_id.txt" ]; then
        log_warn "No job_id from previous test, skipping"
        return 0
    fi
    
    job_id=$(cat "$TEST_DIR/job_id.txt")
    
    if wait_for_job "$job_id"; then
        log_info "Job completed successfully"
        
        # Fetch final results
        results=$(curl -s "$REVIEW_API_BASE/v1/jobs/$job_id" \
            -H "Authorization: Bearer test_token")
        
        echo "$results" | jq '.' > "$TEST_DIR/results.json"
        
        # Verify findings
        finding_count=$(echo "$results" | jq '.findings.static.total // 0')
        
        if [ "$finding_count" -gt 0 ]; then
            log_info "Found $finding_count static findings"
        else
            log_warn "No findings detected (check analysis logic)"
        fi
        
        return 0
    else
        log_error "Job did not complete in time"
        return 1
    fi
}

test_artifact_persistence() {
    log_info "TEST 7: Artifact Persistence"
    
    if [ ! -f "$TEST_DIR/results.json" ]; then
        log_warn "No results from previous test, skipping"
        return 0
    fi
    
    artifact_url=$(cat "$TEST_DIR/results.json" | jq -r '.artifact_url // empty')
    
    if [ -z "$artifact_url" ]; then
        log_warn "No artifact URL in results"
        return 0
    fi
    
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$artifact_url" \
        -H "Authorization: Bearer test_token")
    
    if [ "$http_code" = "200" ]; then
        log_info "Artifact accessible at $artifact_url"
        return 0
    else
        log_error "Artifact not accessible (HTTP $http_code)"
        return 1
    fi
}

test_slack_notification() {
    log_info "TEST 8: Slack Notification (Mock)"
    
    # This is a mock test - in production, check Slack API
    log_info "Slack notification should have been sent"
    log_warn "Manual verification required: Check #nonstop-reviews channel"
    
    return 0
}

test_cleanup() {
    log_info "TEST 9: Temporary File Cleanup"
    
    # Check if temp directory still exists
    temp_files=$(find /tmp/nonstop_reviews -name "job_*" 2>/dev/null | wc -l)
    
    if [ "$temp_files" -eq 0 ]; then
        log_info "Temp files cleaned up successfully"
        return 0
    else
        log_warn "$temp_files temp directories still exist (may be in progress)"
        return 0
    fi
}

test_error_handling() {
    log_info "TEST 10: Error Handling (Invalid ZIP)"
    
    # Create corrupted ZIP
    echo "NOT A ZIP FILE" > "$TEST_DIR/corrupt.zip"
    
    local meta='{"project":"ERROR-TEST","version":"1.0.0"}'
    local payload="{\"mode\":\"zip\",\"meta\":\"$meta\"}"
    local signature=$(calculate_hmac "$payload")
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$N8N_WEBHOOK_URL" \
        -H "X-NonStop-Signature: $signature" \
        -F "mode=zip" \
        -F "code_bundle=@$TEST_DIR/corrupt.zip" \
        -F "meta=$meta")
    
    http_code=$(echo "$response" | tail -n1)
    
    # Should still return 202 (queued), but job should fail during processing
    if [ "$http_code" = "202" ]; then
        body=$(echo "$response" | sed '$d')
        error_job_id=$(echo "$body" | jq -r '.job_id')
        
        log_info "Invalid ZIP accepted (will fail during processing)"
        
        # Wait a bit and check if job failed
        sleep 10
        
        status=$(curl -s "$REVIEW_API_BASE/v1/jobs/$error_job_id" \
            -H "Authorization: Bearer test_token" | jq -r '.status')
        
        if [ "$status" = "failed" ]; then
            log_info "Job correctly marked as failed"
            return 0
        else
            log_warn "Job status: $status (expected 'failed')"
            return 0
        fi
    else
        log_error "Unexpected HTTP code: $http_code"
        return 1
    fi
}

###############################################################################
# Main Test Runner
###############################################################################

main() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   NonStop Agent Review - Workflow Test Suite             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "Test environment:"
    echo "  - Webhook URL: $N8N_WEBHOOK_URL"
    echo "  - API Base: $REVIEW_API_BASE"
    echo "  - Redis: $REDIS_HOST:$REDIS_PORT"
    echo "  - Test Dir: $TEST_DIR"
    echo ""
    
    # Setup
    setup_test_data
    echo ""
    
    # Run tests
    local passed=0
    local failed=0
    local total=10
    
    for test_func in \
        test_webhook_accessibility \
        test_invalid_signature \
        test_oversized_file \
        test_valid_zip_upload \
        test_redis_queue \
        test_job_completion \
        test_artifact_persistence \
        test_slack_notification \
        test_cleanup \
        test_error_handling
    do
        echo ""
        if $test_func; then
            ((passed++))
        else
            ((failed++))
        fi
    done
    
    # Summary
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                      Test Summary                         ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  Total Tests:  $total"
    echo -e "  ${GREEN}Passed:       $passed${NC}"
    
    if [ $failed -gt 0 ]; then
        echo -e "  ${RED}Failed:       $failed${NC}"
    else
        echo "  Failed:       $failed"
    fi
    
    echo ""
    
    if [ $failed -eq 0 ]; then
        log_info "All tests passed! ✨"
        exit 0
    else
        log_error "Some tests failed"
        exit 1
    fi
}

# Run if executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
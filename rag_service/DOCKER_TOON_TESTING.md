# Testing TOON Format in Docker

## Quick Start

The TOON format is already configured in `docker-compose.yml` with default `hybrid`. Here's how to test and use it:

### 1. Set Environment Variable

**Option A: Using .env file** (recommended):
```bash
# Create or edit .env file
echo "USE_LLM_TOKEN_FORMAT=hybrid" >> .env
```

**Option B: Override in docker-compose.yml**:
```yaml
# Already configured (line 77)
- USE_LLM_TOKEN_FORMAT=${USE_LLM_TOKEN_FORMAT:-hybrid}
```

**Option C: Pass at runtime**:
```bash
USE_LLM_TOKEN_FORMAT=hybrid docker-compose up -d
```

### 2. Restart Service (if already running)

```bash
# Restart to pick up new environment variable
docker-compose restart rag-service

# Or rebuild and restart
docker-compose up -d --build rag-service
```

### 3. Verify Configuration

```bash
# Check if format is set correctly
docker-compose exec rag-service env | grep USE_LLM_TOKEN_FORMAT

# Should output: USE_LLM_TOKEN_FORMAT=hybrid
```

## Testing TOON Integration

### Test 1: Check Logs for Format Usage

```bash
# Watch logs in real-time
docker-compose logs -f rag-service | grep "llm_context_formatted"

# Or view recent logs
docker-compose logs rag-service | grep "llm_context_formatted" | tail -20
```

**Expected output**:
```json
{
  "timestamp": "2025-01-15T10:30:00",
  "service": "markdown-rag",
  "event": "llm_context_formatted",
  "format": "hybrid",
  "requested_format": "hybrid",
  "contexts_count": 5,
  "token_count": 320,
  "context_length": 1280
}
```

### Test 2: Run Test Script Inside Container

```bash
# Execute test script inside container
docker-compose exec rag-service python rag_service/test_toon_integration.py
```

**Expected output**:
```
Token Count Comparison:
Plain Text:      400 tokens (1600 chars)
Hybrid Format:   320 tokens (1280 chars)
...

Token Savings:
Hybrid vs Plain:    80 tokens (20.0%)
```

### Test 3: Test with Real Query

```bash
# Make a search request
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "How does authentication work?"}'
```

**Then check logs**:
```bash
docker-compose logs rag-service | grep -A 5 "llm_context_formatted"
```

### Test 4: Compare Formats

Test different formats by changing environment variable:

```bash
# Test with plain format
USE_LLM_TOKEN_FORMAT=plain docker-compose up -d rag-service

# Test with hybrid format
USE_LLM_TOKEN_FORMAT=hybrid docker-compose up -d rag-service

# Test with toon format
USE_LLM_TOKEN_FORMAT=toon docker-compose up -d rag-service
```

## Monitoring Token Usage

### Real-Time Token Monitoring

```bash
# Watch token counts in real-time
docker-compose logs -f rag-service | grep --line-buffered "token_count"
```

### Extract Token Statistics

```bash
# Get average token count
docker-compose logs rag-service | \
  grep "llm_context_formatted" | \
  jq -r '.token_count' | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "tokens"}'

# Get token savings
docker-compose logs rag-service | \
  grep "llm_context_formatted" | \
  jq -r 'select(.format=="hybrid") | .token_count' | \
  head -10
```

### Compare Formats

```bash
# Test plain format and capture token count
docker-compose exec -e USE_LLM_TOKEN_FORMAT=plain rag-service \
  python -c "from rag_service.test_toon_integration import test_token_formats; test_token_formats()"

# Test hybrid format and capture token count
docker-compose exec -e USE_LLM_TOKEN_FORMAT=hybrid rag-service \
  python -c "from rag_service.test_toon_integration import test_token_formats; test_token_formats()"
```

## Docker Commands Cheat Sheet

### View Logs
```bash
# All logs
docker-compose logs rag-service

# Follow logs (real-time)
docker-compose logs -f rag-service

# Filter for TOON events
docker-compose logs rag-service | grep -E "llm_context_formatted|llm_format"
```

### Check Configuration
```bash
# Check environment variables
docker-compose exec rag-service env | grep USE_LLM_TOKEN_FORMAT

# Check if tiktoken is installed
docker-compose exec rag-service python -c "import tiktoken; print('tiktoken OK')"
```

### Restart with New Format
```bash
# Change format and restart
export USE_LLM_TOKEN_FORMAT=toon
docker-compose up -d rag-service

# Verify it's running with new format
docker-compose exec rag-service env | grep USE_LLM_TOKEN_FORMAT
```

### Test Inside Container
```bash
# Interactive shell
docker-compose exec rag-service bash

# Then run test script
python rag_service/test_toon_integration.py

# Or test directly
python -c "
from rag_service.llm_client import LLMClient, DocumentChunk
from rag_service.config import Settings

settings = Settings()
settings.use_llm_token_format = 'hybrid'
client = LLMClient(settings)

contexts = [
    DocumentChunk(
        doc_id='test.md',
        chunk_id='test.md:0',
        path='test.md',
        content='This is test content about authentication.',
        metadata={'score': 0.85}
    )
]

text, format, tokens = client._format_context(contexts, 'hybrid')
print(f'Format: {format}, Tokens: {tokens}')
"
```

## Monitoring Response Quality

### Check Response Logs

```bash
# View search completion events
docker-compose logs rag-service | grep "search_complete"

# Check for errors
docker-compose logs rag-service | grep -i error
```

### Compare Response Quality

1. **Test with plain format** (baseline):
```bash
USE_LLM_TOKEN_FORMAT=plain docker-compose up -d rag-service
# Make queries and note response quality
```

2. **Test with hybrid format**:
```bash
USE_LLM_TOKEN_FORMAT=hybrid docker-compose up -d rag-service
# Make same queries and compare
```

3. **Compare side-by-side**:
```bash
# Save responses
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}' > response_plain.json

# Switch format, test again
USE_LLM_TOKEN_FORMAT=hybrid docker-compose restart rag-service
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}' > response_hybrid.json
```

## Troubleshooting in Docker

### Issue: Format not being used

**Check**:
```bash
# Verify environment variable
docker-compose exec rag-service env | grep USE_LLM_TOKEN_FORMAT

# Check logs for format selection
docker-compose logs rag-service | grep "llm_context_formatted"
```

**Fix**:
```bash
# Restart service
docker-compose restart rag-service

# Or rebuild
docker-compose up -d --build rag-service
```

### Issue: tiktoken not installed

**Check**:
```bash
docker-compose exec rag-service python -c "import tiktoken"
```

**Fix**:
```bash
# Rebuild image (tiktoken should be in requirements.txt)
docker-compose build rag-service
docker-compose up -d rag-service
```

### Issue: Token count not accurate

**Check logs for errors**:
```bash
docker-compose logs rag-service | grep "llm_token_count_error"
```

**Expected**: Should fallback to character-based estimation if tiktoken fails.

## Quick Test Script for Docker

Create a test script you can run inside the container:

```bash
# Copy test script into container
docker cp rag_service/test_toon_integration.py rag-service:/app/test_toon.py

# Run it
docker-compose exec rag-service python /app/test_toon.py
```

## Production Deployment

### Recommended Settings

```bash
# In .env file or docker-compose.yml
USE_LLM_TOKEN_FORMAT=hybrid  # Best balance
LLM_MAX_TOKENS=20000  # As you've already set
```

### Monitoring Commands

```bash
# Daily token usage report
docker-compose logs rag-service --since 24h | \
  grep "llm_context_formatted" | \
  jq -r '[.token_count] | add' | \
  awk '{sum+=$1} END {print "Total tokens:", sum}'

# Format usage breakdown
docker-compose logs rag-service --since 24h | \
  grep "llm_context_formatted" | \
  jq -r '.format' | \
  sort | uniq -c
```

## Example Workflow

### 1. Enable TOON Format
```bash
# Edit .env or docker-compose.yml
echo "USE_LLM_TOKEN_FORMAT=hybrid" >> .env
```

### 2. Restart Service
```bash
docker-compose restart rag-service
```

### 3. Verify
```bash
# Check logs
docker-compose logs -f rag-service | grep "llm_context_formatted"
```

### 4. Test
```bash
# Make a query
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

### 5. Monitor
```bash
# Watch token counts
docker-compose logs -f rag-service | grep "token_count"
```

## Next Steps

1. ✅ **Verify format is working**: Check logs for `llm_context_formatted` events
2. ✅ **Measure token savings**: Compare token counts before/after
3. ✅ **Monitor quality**: Ensure LLM responses are still good
4. ✅ **Optimize**: Adjust format based on results

The TOON format is ready to use in your Docker environment!


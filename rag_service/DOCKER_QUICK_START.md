# Docker Quick Start - TOON Format Testing

## Current Status

✅ **TOON format is already configured** in `docker-compose.yml` (line 77)
- Default format: `hybrid` (recommended)
- Already set: `USE_LLM_TOKEN_FORMAT=${USE_LLM_TOKEN_FORMAT:-hybrid}`

## Quick Test (30 seconds)

### 1. Verify Configuration

```bash
# Check if format is set
docker-compose exec rag-service env | grep USE_LLM_TOKEN_FORMAT
# Should output: USE_LLM_TOKEN_FORMAT=hybrid
```

### 2. Make a Test Query

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "How does authentication work?"}'
```

### 3. Check Logs for Token Count

```bash
# Watch for format usage
docker-compose logs rag-service | grep "llm_context_formatted" | tail -1

# Expected output:
# {"event": "llm_context_formatted", "format": "hybrid", "token_count": 320, ...}
```

## Change Format

### Option 1: Set in .env file

```bash
# Add to .env file
echo "USE_LLM_TOKEN_FORMAT=toon" >> .env

# Restart service
docker-compose restart rag-service
```

### Option 2: Override at runtime

```bash
# Test with different formats
USE_LLM_TOKEN_FORMAT=toon docker-compose up -d rag-service
USE_LLM_TOKEN_FORMAT=hybrid docker-compose up -d rag-service
USE_LLM_TOKEN_FORMAT=plain docker-compose up -d rag-service
```

## Monitor Token Usage

### Real-Time Monitoring

```bash
# Watch token counts live
docker-compose logs -f rag-service | grep --line-buffered "token_count"
```

### Daily Token Report

```bash
# Get total tokens used today
docker-compose logs rag-service --since 24h | \
  grep "llm_context_formatted" | \
  jq -r '.token_count' | \
  awk '{sum+=$1; count++} END {print "Total:", sum, "tokens, Average:", sum/count, "tokens/query"}'
```

## Run Test Script

```bash
# Quick test script
./test_toon_docker.sh

# Or manually
docker-compose exec rag-service python rag_service/test_toon_integration.py
```

## Verify It's Working

### Check 1: Format is being used

```bash
docker-compose logs rag-service | grep "llm_context_formatted" | tail -5
```

Look for:
- `"format": "hybrid"` (or your configured format)
- `"token_count": <number>`

### Check 2: Token savings

Compare token counts:
- Before TOON: ~500-600 tokens per query
- With Hybrid: ~350-420 tokens per query
- Savings: ~30%

### Check 3: Response quality

Make the same query multiple times and verify:
- Answers are complete
- No truncation
- Quality maintained

## Troubleshooting

### Format not being used?

```bash
# 1. Check environment variable
docker-compose exec rag-service env | grep USE_LLM_TOKEN_FORMAT

# 2. Restart service
docker-compose restart rag-service

# 3. Check logs for errors
docker-compose logs rag-service | grep -i "format\|error"
```

### No token count in logs?

```bash
# Make a query first
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Then check logs
docker-compose logs rag-service | grep "llm_context_formatted"
```

## Next Steps

1. ✅ **Verify**: Check logs to confirm format is being used
2. ✅ **Monitor**: Watch token counts over time
3. ✅ **Optimize**: Adjust format based on your needs
4. ✅ **Measure**: Track cost savings

**The TOON format is ready to use in your Docker environment!**


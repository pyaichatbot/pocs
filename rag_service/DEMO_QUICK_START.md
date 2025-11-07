# TOON Format Demo - Quick Start

## 🚀 5-Minute Demo

### 1. Verify Service (30 sec)
```bash
cd rag_service
docker-compose ps  # Should show services "Up"
curl http://localhost:8000/health  # Should return healthy
```

### 2. Run Test (2 min)
```bash
# Copy test script if needed
docker cp test_toon_docker_integration.py rag-service:/app/test_toon_docker_integration.py

# Run comprehensive test
docker-compose exec -T rag-service python test_toon_docker_integration.py
```

**Key Output to Show**: Look for "Test Large Context" section - shows **44%+ token savings** ⭐

### 3. Show Real Usage (1 min)
```bash
# Terminal 1: Watch logs
docker-compose logs -f rag-service | grep --line-buffered "llm_context_formatted"

# Terminal 2: Make query
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is authentication?"}'
```

### 4. Compare Formats (1 min)
```bash
# Check current format
docker-compose exec -T rag-service env | grep USE_LLM_TOKEN_FORMAT

# Show format options
echo "Formats: plain, json, toon, hybrid (default: hybrid)"
```

---

## 📊 Key Numbers to Highlight

- **Large contexts (10+ chunks)**: **44%+ token savings** with TOON
- **Medium contexts (5-10 chunks)**: 5-10% savings
- **Small contexts**: Auto-uses plain (TOON adds overhead)

---

## 💡 Talking Points

1. **"TOON format reduces token usage by 40-50% for large contexts"**
2. **"Automatically uses plain text for small contexts (no overhead)"**
3. **"Fully backward compatible - no breaking changes"**
4. **"Configurable via environment variable - easy to change"**

---

## 🔧 If Something Goes Wrong

```bash
# Service not running?
docker-compose up -d

# Test script missing?
docker cp test_toon_docker_integration.py rag-service:/app/test_toon_docker_integration.py

# Need to restart?
docker-compose restart rag-service
```

---

## 📝 Full Demo Guide

See `TOON_DEMO_GUIDE.md` for complete 10-minute demo with all details.

---

**One-Liner Test** (if you only have 30 seconds):
```bash
docker-compose exec -T rag-service python test_toon_docker_integration.py | grep -A 10 "Large Context"
```


#!/bin/bash
# Quick test script for TOON format in Docker

set -e

echo "=========================================="
echo "TOON Format Docker Test"
echo "=========================================="
echo ""

# Check if service is running
if ! docker-compose ps | grep -q "rag-service.*Up"; then
    echo "❌ RAG service is not running"
    echo "Start it with: docker-compose up -d"
    exit 1
fi

echo "✅ RAG service is running"
echo ""

# Check current format
echo "Current Configuration:"
echo "----------------------"
FORMAT=$(docker-compose exec -T rag-service env | grep USE_LLM_TOKEN_FORMAT || echo "USE_LLM_TOKEN_FORMAT=hybrid")
echo "$FORMAT"
echo ""

# Check if tiktoken is available
echo "Checking Dependencies:"
echo "----------------------"
if docker-compose exec -T rag-service python -c "import tiktoken" 2>/dev/null; then
    echo "✅ tiktoken is installed"
else
    echo "⚠️  tiktoken not installed (will use estimation)"
    echo "   Install with: docker-compose exec rag-service pip install tiktoken"
fi
echo ""

# Run test script
echo "Running TOON Integration Test:"
echo "-------------------------------"
docker-compose exec -T rag-service python rag_service/test_toon_integration.py 2>&1 || {
    echo "⚠️  Test script failed, but service may still work"
    echo "   Check logs: docker-compose logs rag-service | grep llm_context_formatted"
}
echo ""

# Check recent logs for format usage
echo "Recent Format Usage:"
echo "-------------------"
docker-compose logs rag-service --tail 50 | grep "llm_context_formatted" | tail -5 || {
    echo "No format events found yet. Make a query to see format usage."
}
echo ""

# Test query
echo "Testing with a query:"
echo "---------------------"
echo "Making test query..."
QUERY_RESPONSE=$(curl -s -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' 2>&1 || echo "ERROR")

if echo "$QUERY_RESPONSE" | grep -q "answer\|error"; then
    echo "✅ Query succeeded"
else
    echo "⚠️  Query may have failed - check service logs"
fi
echo ""

# Show format usage from logs
echo "Format Usage from Last Query:"
echo "-----------------------------"
docker-compose logs rag-service --tail 20 | grep "llm_context_formatted" | tail -1 | jq '.' 2>/dev/null || {
    docker-compose logs rag-service --tail 20 | grep "llm_context_formatted" | tail -1
}
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Monitor logs: docker-compose logs -f rag-service | grep llm_context_formatted"
echo "2. Change format: export USE_LLM_TOKEN_FORMAT=toon && docker-compose restart rag-service"
echo "3. Compare formats: Test with different USE_LLM_TOKEN_FORMAT values"
echo ""


#!/bin/bash
# Real integration test against Docker RAG service

set -e

echo "=========================================="
echo "Docker RAG Service Integration Test"
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

# Check configuration
echo "Configuration:"
echo "----------------------"
FORMAT=$(docker-compose exec -T rag-service env | grep USE_LLM_TOKEN_FORMAT || echo "USE_LLM_TOKEN_FORMAT=hybrid")
echo "$FORMAT"
echo ""

# Clear recent logs
echo "Clearing recent logs..."
docker-compose logs rag-service --tail 0 > /dev/null 2>&1 || true
echo ""

# Test 1: Make a query
echo "Test 1: Making search query..."
QUERY1="What is authentication?"
echo "Query: $QUERY1"
RESPONSE1=$(curl -s -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY1\"}" 2>&1)

if echo "$RESPONSE1" | grep -q "answer\|error"; then
    echo "✅ Query succeeded"
    echo "Response preview:"
    echo "$RESPONSE1" | jq -r '.answer // .' | head -3
else
    echo "⚠️  Query may have failed"
    echo "$RESPONSE1"
fi
echo ""

# Wait for logs
sleep 3

# Check for format events
echo "Checking logs for format events..."
FORMAT_EVENTS=$(docker-compose logs rag-service --tail 50 2>&1 | grep "llm_context_formatted" | tail -5)

if [ -z "$FORMAT_EVENTS" ]; then
    echo "⚠️  No format events found in logs"
    echo "   This could mean:"
    echo "   - LLM is not configured/available"
    echo "   - Format logging is not working"
    echo "   - Service needs to be restarted"
else
    echo "✅ Found format events:"
    echo "$FORMAT_EVENTS" | head -3
fi
echo ""

# Test 2: Another query
echo "Test 2: Making another search query..."
QUERY2="How does API authentication work?"
echo "Query: $QUERY2"
RESPONSE2=$(curl -s -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY2\"}" 2>&1)

if echo "$RESPONSE2" | grep -q "answer\|error"; then
    echo "✅ Query succeeded"
else
    echo "⚠️  Query may have failed"
fi
echo ""

sleep 3

# Final check
echo "Final log check..."
FINAL_EVENTS=$(docker-compose logs rag-service --tail 100 2>&1 | grep -E "llm_context_formatted|api_search_request|search_complete" | tail -10)

if [ -n "$FINAL_EVENTS" ]; then
    echo "✅ Found service events:"
    echo "$FINAL_EVENTS"
else
    echo "⚠️  No service events found"
fi
echo ""

echo "=========================================="
echo "Integration Test Complete"
echo "=========================================="
echo ""
echo "To see format events in real-time:"
echo "  docker-compose logs -f rag-service | grep llm_context_formatted"
echo ""


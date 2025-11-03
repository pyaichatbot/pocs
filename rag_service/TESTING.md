# Testing Guide

This guide explains how to test the RAG service with local markdown files.

## Test Data

Test markdown files are located in `test_data/docs/`. The folder contains:
- **14 markdown files** across multiple subdirectories
- Files with ~100 lines of content each
- Topics include: Machine Learning, Web Development, Cloud Computing, Databases, Testing, APIs, Git, and Containers

## Running the Service

### Start the FastAPI Server

```bash
# Using main.py entry point
uvicorn rag_service.main:app --reload --host 0.0.0.0 --port 8000

# Or directly
python -m rag_service.main
```

The service will be available at:
- API: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## Testing Local Folder Indexing

### 1. Index Local Folder

**Endpoint:** `POST /index-local`

**Request:**
```bash
curl -X POST "http://localhost:8000/index-local" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_path": "/path/to/rag_service/test_data/docs"
  }'
```

**Or using Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/index-local",
    json={"folder_path": "test_data/docs"}  # Relative path works too
)
print(response.json())
```

**Response:**
```json
{
  "files_indexed": 14,
  "chunks_indexed": 42
}
```

### 2. Test Search Without LLM

**Endpoint:** `POST /search`

**Request:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?"
  }'
```

**Response (without LLM):**
```json
{
  "contexts": [
    "Machine learning is a subset of artificial intelligence...",
    "There are three main types of machine learning...",
    ...
  ]
}
```

### 3. Test Search With LLM

**Setup:**
Set the `ANTHROPIC_API_KEY` environment variable (or use Azure OpenAI):

```bash
export ANTHROPIC_API_KEY=your-api-key
# Restart the service
```

**Request:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the different types of machine learning"
  }'
```

**Response (with LLM):**
```json
{
  "answer": "There are three main types of machine learning:\n\n1. Supervised Learning...\n2. Unsupervised Learning...\n3. Reinforcement Learning..."
}
```

## Testing Parallel Processing

### Monitor Parallel Processing

Check logs for parallel processing indicators:
- `"parallel": true` in ingestion logs
- Progress events every 10 files: `"ingestion_progress"`
- Batch upsert events: `"ingestion_batch_upserted"`

### Adjust Parallel Settings

```bash
# Set number of workers
export MAX_WORKERS=8

# Set batch size
export BATCH_SIZE=200

# Restart service
```

### Disable Parallel Processing

```bash
export MAX_WORKERS=1
```

## Complete Test Workflow

1. **Start the service:**
   ```bash
   uvicorn rag_service.main:app --reload
   ```

2. **Index test folder:**
   ```bash
   curl -X POST "http://localhost:8000/index-local" \
     -H "Content-Type: application/json" \
     -d '{"folder_path": "test_data/docs"}'
   ```

3. **Test search without LLM:**
   ```bash
   curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the types of machine learning?"}'
   ```

4. **Test search with LLM (if API key set):**
   ```bash
   curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "Explain cloud computing service models"}'
   ```

## Expected Behavior

### Indexing
- Should process all 14 files in parallel (if MAX_WORKERS > 1)
- Should create chunks from each file
- Should upsert documents in batches
- Should log progress events

### Search (Without LLM)
- Returns raw context chunks matching the query
- Uses hybrid search (semantic + keyword)
- May use reranking if enabled

### Search (With LLM)
- Returns generated answers based on retrieved contexts
- Uses Anthropic Claude by default (if API key set)
- Can be configured to use Azure OpenAI

## Troubleshooting

### No files found
- Check folder path is correct (use absolute path if relative doesn't work)
- Verify files have `.md` or `.markdown` extension
- Check folder permissions

### Search returns empty results
- Ensure indexing completed successfully
- Check if vector database is properly initialized
- Verify embedding model is loaded

### LLM not working
- Check API key is set correctly
- Verify provider is set: `LLM_PROVIDER=anthropic` or `azure`
- Check API credentials and endpoints


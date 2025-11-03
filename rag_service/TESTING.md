# Testing Guide

This guide explains how to test the RAG service with local markdown and PDF files.

## Test Data

Test files are located in `test_data/docs/`. The folder contains:
- **14 markdown files** (.md, .markdown) across multiple subdirectories
- **4 PDF files** (.pdf) with meaningful technical content
- Files with ~100 lines of content each
- Topics include: Machine Learning, Web Development, Cloud Computing, Databases, Testing, APIs, Git, Containers, Python Programming, Docker, and Microservices

### Creating Test PDFs

To generate test PDF files, run:
```bash
cd rag_service
python test_data/create_test_pdfs.py
```

This will create PDF files in `test_data/docs/` with content about:
- Python Programming
- Docker Containerization
- Microservices Architecture
- API Design Best Practices

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
- Chatbot Interface: `http://localhost:8000/` or `http://localhost:8000/chatbot`
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
  "files_indexed": 18,
  "chunks_indexed": 18
}
```

**Note:** The response includes both markdown (14 files) and PDF (4 files) documents. PDF files are parsed using pdfplumber to extract text content.

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

### 4. Test PDF Content Search

**Test queries that should find PDF content:**
```bash
# Search for Python programming content (from PDF)
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python programming language"}'

# Search for Docker content (from PDF)
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Docker containerization benefits"}'
```

**Expected:** These queries should return content extracted from the PDF files.

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
- Should process all 18 files (14 markdown + 4 PDFs) in parallel (if MAX_WORKERS > 1)
- Should extract text from PDF files using pdfplumber
- Should create chunks from each file (markdown and PDF)
- Should upsert documents in batches
- Should log progress events
- Should handle PDF parsing errors gracefully (logs warnings but continues)

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
- Verify files have `.md`, `.markdown`, or `.pdf` extension
- Check folder permissions
- For PDFs: Ensure pdfplumber is installed (`pip install pdfplumber`)

### Search returns empty results
- Ensure indexing completed successfully
- Check if vector database is properly initialized
- Verify embedding model is loaded

### LLM not working
- Check API key is set correctly
- Verify provider is set: `LLM_PROVIDER=anthropic` or `azure`
- Check API credentials and endpoints

### PDF processing issues
- Ensure pdfplumber is installed: `pip install pdfplumber`
- Check logs for PDF parsing errors
- Some PDFs with images or scanned content may not extract text properly
- Verify PDF files are not corrupted


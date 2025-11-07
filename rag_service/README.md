# RAG Service

A production-ready Retrieval-Augmented Generation (RAG) service for indexing GitLab repositories and local folders, enabling conversational search over markdown, PDF, and Word documentation.

## Features

- **Multi-Format Support**: Index markdown (.md, .markdown), PDF (.pdf), and Word (.docx) files
- **GitLab Integration**: Index documents from GitLab repositories
- **Local Folder Indexing**: Index documents from local directories
- **Delta Indexing**: Incremental updates for efficient indexing
- **Vector Search**: Semantic similarity search using embeddings
- **Hybrid Search**: Combines semantic and keyword search for better results
- **LLM Integration**: Supports Azure OpenAI and Anthropic for generating answers
- **Multiple Vector DB Support**: ChromaDB (default), pgvector, and Cosmos DB
- **Web Search**: Automatically searches the web when knowledge base results are insufficient (DuckDuckGo, Tavily, SerpAPI)
- **Web Crawler**: Extracts and crawls URLs from queries (with domain allowlist)
- **REST API**: FastAPI-based API with OpenAPI documentation
- **Chatbot Interface**: Interactive HTML chatbot for querying the knowledge base

## Architecture

The service follows a clean architecture pattern:

```
rag_service/
├── api.py              # FastAPI application and endpoints
├── config.py           # Configuration management
├── llm_client.py       # LLM provider abstractions
├── repositories/       # Vector database implementations
│   ├── base_kb_repo.py        # Abstract repository interface
│   ├── chromadb_kb_repo.py    # ChromaDB implementation
│   ├── pgvector_kb_repo.py     # pgvector implementation
│   ├── cosmosdb_kb_repo.py    # Cosmos DB implementation
│   └── factory.py             # Repository factory
├── services/           # Business logic
│   ├── ingestion_service.py   # Document indexing (GitLab & local)
│   └── search_service.py      # Query processing
├── static/             # Static files
│   └── chatbot.html    # Interactive chatbot interface
└── utils/              # Utilities
    ├── gitlab_loader.py       # GitLab integration
    ├── document_loader.py    # Multi-format document loading
    ├── md_parser.py          # Markdown parsing
    ├── pdf_parser.py         # PDF parsing (using pdfplumber)
    ├── word_parser.py        # Word document parsing (using python-docx)
    └── logging.py            # Structured logging
```

## Installation

### Prerequisites

- Python 3.10+
- Git (for cloning GitLab repositories)

### Setup

1. **Clone the repository** (if applicable) or navigate to the service directory

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   This installs all required dependencies including:
   - FastAPI and web server components
   - pdfplumber for PDF text extraction (license-safe alternative to pymupdf)
   - python-docx for Word document (.docx) text extraction
   - sentence-transformers for embeddings
   - ChromaDB, pgvector, or Cosmos DB drivers (depending on your choice)

## Configuration

Configuration is managed via environment variables:

### Required Settings

None - the service works out of the box with ChromaDB defaults.

### Optional Settings

#### Vector Database
- `REPOSITORY_TYPE`: Repository type (`chromadb`, `pgvector`, `cosmosdb`)
  - Default: `chromadb`
- `EMBEDDING_MODEL_ID`: Embedding model identifier
  - Default: `intfloat/e5-small-v2`
  - Options: `all-MiniLM-L6-v2`, `intfloat/e5-large-v2`, etc.

#### Search Configuration
- `MAX_CHUNKS`: Maximum chunks to return per query (default: `5`)
- `CHUNK_MAX_WORDS`: Maximum words per chunk (default: `300`)
- `CHUNK_OVERLAP_WORDS`: Overlap words between chunks (default: `50`)

#### LLM Providers

**Anthropic** (Default if API key is set):
- `ANTHROPIC_API_KEY`: API key (required)
- `ANTHROPIC_MODEL`: Model name (default: `claude-3-5-sonnet-20241022`)
- `LLM_PROVIDER=anthropic`: Explicitly set (optional, auto-detected if key is set)

**Azure OpenAI**:
- `LLM_PROVIDER=azure`: Must be explicitly set
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_KEY`: API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Deployment name

**LLM Token Format** (Token Optimization):
- `USE_LLM_TOKEN_FORMAT`: Token format for LLM context (default: `hybrid`)
  - `plain`: Plain text concatenation (no optimization, backward compatible)
  - `toon`: Fully flattened TOON format (maximum token savings, ~40%)
  - `hybrid`: TOON for content + JSON for metadata (recommended, ~30% savings)
  - `json`: JSON format (structured but verbose, for debugging)
  
  The `hybrid` format uses TOON for uniform content (efficient) and JSON for complex metadata (preserves structure), providing the best balance of token savings and information preservation.

### Example Environment File

Create a `.env` file:

```bash
# Vector Database (ChromaDB is default, no config needed)
REPOSITORY_TYPE=chromadb
EMBEDDING_MODEL_ID=intfloat/e5-small-v2

# Search
MAX_CHUNKS=5
CHUNK_MAX_WORDS=300
CHUNK_OVERLAP_WORDS=50

# LLM - Anthropic (Default, auto-detected if key is set)
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Or use Azure OpenAI (must explicitly set LLM_PROVIDER=azure)
# LLM_PROVIDER=azure
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_KEY=your-api-key
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# LLM Token Format (optional - for token optimization)
USE_LLM_TOKEN_FORMAT=hybrid  # Options: plain, toon, hybrid, json

# Web Search (optional - enable when KB results are insufficient)
# WEB_SEARCH_ENABLED=true
# WEB_SEARCH_PROVIDER=duckduckgo  # duckduckgo (free), tavily, or serpapi
# WEB_SEARCH_MAX_RESULTS=5  # Max search results to return
# WEB_SEARCH_MAX_CRAWL_URLS=3  # Max URLs to crawl (remaining use snippets)
# WEB_SEARCH_MAX_CONTENT_LENGTH=50000  # Total max chars across all URLs (~12-15k tokens)
# WEB_SEARCH_MAX_CONTENT_PER_URL=10000  # Max chars per URL (~2.5-3k tokens)
# WEB_SEARCH_MIN_SCORE_THRESHOLD=0.5  # KB score threshold to trigger web search
```

## Running the Service

### Development

Using `main.py` entry point:
```bash
uvicorn rag_service.main:app --reload --host 0.0.0.0 --port 8000
```

Or directly:
```bash
python -m rag_service.main
```

### Parallel Processing

The service uses parallel processing to improve indexing performance:

- **File Processing**: Multiple files (markdown and PDF) are processed simultaneously
  using `ThreadPoolExecutor` (configurable via `MAX_WORKERS`, default: 4)
- **Batch Upserts**: Documents are upserted in batches to avoid overwhelming
  the database (configurable via `BATCH_SIZE`, default: 100)
- **Automatic Optimization**: Small file sets (≤10 files) are processed
  sequentially to avoid overhead

**Configuration**:
```bash
MAX_WORKERS=4    # Number of parallel workers (set to 1 to disable)
BATCH_SIZE=100   # Batch size for document upserts
```

### Production

```bash
uvicorn rag_service.api:app --host 0.0.0.0 --port 8000 --workers 4
```

The service will be available at:
- API: `http://localhost:8000`
- Chatbot Interface: `http://localhost:8000/` or `http://localhost:8000/chatbot`
- Interactive Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## API Endpoints

### `POST /index`

Perform a full index of a GitLab repository.

**Request Body**:
```json
{
  "repo_url": "https://gitlab.com/namespace/project.git",
  "token": "your-gitlab-token",
  "branch": "main"
}
```

**Response**:
```json
{
  "files_indexed": 42,
  "chunks_indexed": 156
}
```

### `POST /delta-index`

Perform an incremental index, updating only modified files.

**Request Body**: Same as `/index`

**Response**:
```json
{
  "new_files": 3,
  "modified_files": 5,
  "deleted_files": 1,
  "chunks_indexed": 24
}
```

### `POST /index-local`

Index markdown, PDF, and Word files from a local folder path.

**Request Body**:
```json
{
  "folder_path": "/path/to/documents/folder"
}
```

**Response**:
```json
{
  "files_indexed": 14,
  "chunks_indexed": 42
}
```

**Note**: The endpoint recursively scans for `.md`, `.markdown`, `.pdf`, and `.docx` files. PDF files are parsed using pdfplumber, Word files using python-docx to extract text content.

### `POST /search`

Query the knowledge base and get an answer.

**Request Body**:
```json
{
  "query": "What is the authentication flow?"
}
```

**Response** (with LLM):
```json
{
  "answer": "The authentication flow consists of..."
}
```

**Response** (without LLM):
```json
{
  "contexts": [
    "Context chunk 1...",
    "Context chunk 2..."
  ]
}
```

### `GET /` or `GET /chatbot`

Serve the interactive chatbot HTML interface for querying the knowledge base.

**Response**: HTML page with chatbot interface

### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "rag-service",
  "repository_type": "chromadb"
}
```

## Usage Examples

### Index a GitLab Repository

```bash
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://gitlab.com/your-org/docs.git",
    "token": "your-token",
    "branch": "main"
  }'
```

### Search the Knowledge Base

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I configure authentication?"
  }'
```

## Local Testing

### Test Local Folder Indexing

Index markdown and PDF files from the local test data folder:

```bash
curl -X POST "http://localhost:8000/index-local" \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/app/test_data/docs"}' | python3 -m json.tool
```

**Expected Response**:
```json
{
    "files_indexed": 18,
    "chunks_indexed": 18
}
```

**Note:** This includes both markdown files (14) and PDF files (4) from the test data directory.

### Test Search Query

Query the indexed knowledge base:

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}' | python3 -m json.tool | head -30
```

**Expected Response** (without LLM):
```json
{
    "contexts": [
        "Machine learning is a subset of artificial intelligence...",
        "There are three main types of machine learning...",
        ...
    ]
}
```

**Expected Response** (with LLM configured):
```json
{
    "answer": "Machine learning is a subset of artificial intelligence that focuses on teaching computers to learn from data..."
}
```

### Test GitLab Repository Indexing

Perform a full index of a GitLab repository:

```bash
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://gitlab.com/your-org/your-project.git",
    "token": "your-gitlab-token",
    "branch": "main"
  }' | python3 -m json.tool
```

**Expected Response**:
```json
{
    "files_indexed": 42,
    "chunks_indexed": 156
}
```

**Note**: Replace `your-gitlab-token` with a valid GitLab personal access token with `read_repository` scope. The `branch` parameter is optional and defaults to the repository's default branch.

### Test GitLab Delta Indexing

Perform an incremental index, updating only modified files:

```bash
curl -X POST "http://localhost:8000/delta-index" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://gitlab.com/your-org/your-project.git",
    "token": "your-gitlab-token",
    "branch": "main"
  }' | python3 -m json.tool
```

**Expected Response**:
```json
{
    "new_files": 3,
    "modified_files": 5,
    "deleted_files": 1,
    "chunks_indexed": 24
}
```

**Delta Indexing Benefits**:
- Only processes new or modified files (detected via file hash comparison)
- Removes documents for files deleted from the repository
- Significantly faster than full indexing for large repositories with few changes
- Ideal for scheduled updates or CI/CD integration

## Architecture: Vector DB and LLM Provider Agnostic

The service uses abstraction patterns, making it easy to swap both vector databases and LLM providers.

### Vector Database Abstraction

The repository factory (`repositories/factory.py`) supports multiple vector databases:

**Supported Implementations**:
- **ChromaDB** (default): `REPOSITORY_TYPE=chromadb`
- **pgvector**: `REPOSITORY_TYPE=pgvector`
- **Cosmos DB**: `REPOSITORY_TYPE=cosmosdb`

No code changes needed - just set `REPOSITORY_TYPE` environment variable.

#### ChromaDB Configuration
```bash
REPOSITORY_TYPE=chromadb
CHROMADB_PATH=./chroma_db  # Local storage path
# Or use remote ChromaDB server:
# CHROMADB_HOST=localhost
# CHROMADB_PORT=8000
```

#### pgvector Configuration
```bash
REPOSITORY_TYPE=pgvector
POSTGRES_CONNECTION_STRING=postgresql://user:password@host:port/dbname
```

**PostgreSQL Setup**:
```sql
CREATE EXTENSION vector;
```

#### Cosmos DB Configuration
```bash
REPOSITORY_TYPE=cosmosdb
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key
```

### LLM Provider Abstraction

The LLM client (`llm_client.py`) abstracts LLM providers:

**Current**: Anthropic (default if API key is set)

**Switch to Azure OpenAI**:
1. Set `LLM_PROVIDER=azure`
2. Configure Azure OpenAI settings
3. No code changes needed

Both vector DB and LLM provider are completely agnostic - swap via configuration only.

### Advanced Features

#### Reranking
Improve search relevance with cross-encoder reranking:
```bash
RERANKER_ENABLED=true
RERANKER_MODEL_ID=cross-encoder/ms-marco-MiniLM-L-6-v2
```

#### Quantization
Enable binary quantization for reduced storage (when supported):
```bash
QUANTIZATION_ENABLED=true
```

#### Web Search
Enable web search when knowledge base results are insufficient. This allows the system to answer questions about topics not in the indexed knowledge base, similar to ChatGPT or Cursor.

**DuckDuckGo (Free, No API Key Required)**:
```bash
WEB_SEARCH_ENABLED=true
WEB_SEARCH_PROVIDER=duckduckgo
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_MAX_CRAWL_URLS=3
WEB_SEARCH_MAX_CONTENT_LENGTH=50000
WEB_SEARCH_MAX_CONTENT_PER_URL=10000
WEB_SEARCH_MIN_SCORE_THRESHOLD=0.5
```

**Tavily (Requires API Key)**:
```bash
WEB_SEARCH_ENABLED=true
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your-tavily-api-key
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_MAX_CRAWL_URLS=3
WEB_SEARCH_MAX_CONTENT_LENGTH=50000
WEB_SEARCH_MAX_CONTENT_PER_URL=10000
WEB_SEARCH_MIN_SCORE_THRESHOLD=0.5
```

**SerpAPI (Requires API Key)**:
```bash
WEB_SEARCH_ENABLED=true
WEB_SEARCH_PROVIDER=serpapi
SERPAPI_API_KEY=your-serpapi-key
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_MAX_CRAWL_URLS=3
WEB_SEARCH_MAX_CONTENT_LENGTH=50000
WEB_SEARCH_MAX_CONTENT_PER_URL=10000
WEB_SEARCH_MIN_SCORE_THRESHOLD=0.5
```

**How It Works**:
1. When a user queries the knowledge base, the system first searches the indexed documents
2. If the KB results have low relevance scores (below `WEB_SEARCH_MIN_SCORE_THRESHOLD`) or no results are found, web search is automatically triggered
3. Web search finds relevant URLs, then **automatically crawls those URLs** to extract full page content (not just snippets)
4. Full page content from web search is combined with KB results and sent to the LLM for answer generation
5. The system prioritizes KB results but supplements with web search when needed
6. If URL crawling fails, the system falls back to using search snippets

**Configuration Options**:
- `WEB_SEARCH_ENABLED`: Enable/disable web search (default: `false`)
- `WEB_SEARCH_PROVIDER`: Search provider - `duckduckgo`, `tavily`, or `serpapi` (default: `duckduckgo`)
- `WEB_SEARCH_MAX_RESULTS`: Maximum number of web search results to return (default: `5`)
- `WEB_SEARCH_MAX_CRAWL_URLS`: Maximum number of URLs to crawl for full content (default: `3`)
  - Limits crawling to manage context length and performance
  - Remaining results use snippets only
- `WEB_SEARCH_MAX_CONTENT_LENGTH`: Total maximum content length across all crawled URLs in characters (default: `50000`, ~12-15k tokens)
  - Content is truncated if this limit is exceeded
- `WEB_SEARCH_MAX_CONTENT_PER_URL`: Maximum content length per crawled URL in characters (default: `10000`, ~2.5-3k tokens)
  - Each URL's content is truncated if exceeded
- `WEB_SEARCH_MIN_SCORE_THRESHOLD`: Minimum average KB score to trigger web search (0.0-1.0, default: `0.5`)

**Example**: If a user asks "explain google adk agent creation" and your knowledge base has no information about it, the system will automatically search the web and provide an answer based on web search results.

## Docker Setup

### Quick Start

1. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services:**

   **Option A: ChromaDB (default, no additional services):**
   ```bash
   docker-compose up -d
   ```

   **Option B: ChromaDB (with ChromaDB server):**
   ```bash
   docker-compose --profile chromadb up -d
   # Or use override:
   docker-compose -f docker-compose.yml -f docker-compose.chromadb.yml up -d
   ```

   **Option C: PostgreSQL with pgvector:**
   ```bash
   docker-compose --profile pgvector up -d
   # Or use override:
   docker-compose -f docker-compose.yml -f docker-compose.pgvector.yml up -d
   ```

3. **Check logs:**
   ```bash
   docker-compose logs -f rag-service
   # For ChromaDB:
   docker-compose logs -f chromadb
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

### Using Docker Directly

1. **Build the image:**
   ```bash
   docker build -t rag-service:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name rag-service \
     -p 8000:8000 \
     -e REPOSITORY_TYPE=chromadb \
     -e ANTHROPIC_API_KEY=your-key \
     -v rag-data:/app/data \
     rag-service:latest
   ```

### Dockerfile Architecture

The Dockerfile uses a **multi-stage build** for optimal image size and security:

- **Builder stage**: Installs build dependencies and Python packages
- **Runtime stage**: Minimal production image with only runtime dependencies
- **Security**: Runs as non-root user (`raguser`)
- **Health check**: Monitors `/health` endpoint

### Docker Compose Services

#### rag-service
Main RAG service application.

- **Ports**: `8000` (FastAPI application)
- **Health Check**: Checks `/health` endpoint every 30 seconds

#### chromadb (ChromaDB Server)
Vector database service for ChromaDB.

- **Ports**: `8001:8000` (external:8001, internal:8000)
- **Profile**: `chromadb` (start with `--profile chromadb`)
- **Usage**: `docker-compose --profile chromadb up -d`

#### postgres (PostgreSQL with pgvector)
Vector database service for pgvector.

- **Ports**: `5432` (PostgreSQL database)
- **Profile**: `pgvector` (start with `--profile pgvector`)
- **Usage**: `docker-compose --profile pgvector up -d`

### Volumes

- `rag-data`: Persistent storage for vector database data
- `chromadb-data`: Persistent storage for ChromaDB
- `postgres-data`: Persistent storage for PostgreSQL
- `test_data`: Mounted test data folder (read-only)

### Production Deployment

**Security Best Practices:**
- Non-root user: Container runs as `raguser` (UID 1000)
- Read-only mounts: Test data mounted read-only
- Health checks: Automated health monitoring
- Network isolation: Services on isolated network

**Resource Limits** (add to `docker-compose.yml`):
```yaml
services:
  rag-service:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Development with Docker

**Hot Reload:**

Create a `docker-compose.override.yml` file:
```yaml
services:
  rag-service:
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
```

Then run:
```bash
docker-compose up
```

This mounts source code and enables hot-reload.

**Debugging:**
```bash
# View logs
docker-compose logs -f rag-service

# Execute commands in container
docker-compose exec rag-service bash

# Inspect container
docker inspect rag-service
```

### Troubleshooting

**Container won't start:**
```bash
docker-compose logs rag-service
docker-compose config  # Verify environment variables
lsof -i :8000  # Check port availability
```

**Health check failing:**
```bash
docker-compose exec rag-service python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"
```

**Out of memory:**
- Reduce `MAX_WORKERS` in environment
- Reduce `BATCH_SIZE`
- Increase container memory limits

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# With coverage
pytest --cov=rag_service tests/
```

### Code Quality

```bash
# Format code
black rag_service/

# Lint code
ruff rag_service/

# Type checking
mypy rag_service/
```

## Troubleshooting

### PDF Processing Issues

- Ensure pdfplumber is installed: `pip install pdfplumber`
- For complex PDFs, some text extraction may fail - check logs for details
- PDFs with images or scanned content may require OCR (not currently supported)
- **For scanned PDFs with tables/images**: See [OCR_IMPLEMENTATION_GUIDE.md](OCR_IMPLEMENTATION_GUIDE.md) for adding OCR support using open-source solutions like PaddleOCR, Tesseract, or OCRmyPDF

### Vector Database Connection Issues

- **ChromaDB**: Ensure the storage path is writable
- **pgvector**: Ensure PostgreSQL has the vector extension installed and connection string is correct
- **Cosmos DB**: Verify endpoint URL and access key

### GitLab Clone Failures

- Verify the token has `read_repository` scope
- Check network connectivity to GitLab
- Ensure the repository URL is correct

### LLM Errors

- Verify API keys are set correctly
- Check endpoint URLs (for Azure)
- Ensure deployment names match (for Azure)

## Security Considerations

- **Token Security**: Never commit GitLab tokens or API keys
- **Input Validation**: Validate repository URLs and queries
- **Rate Limiting**: Implement rate limiting in production
- **Authentication**: Add API key authentication for production use

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]


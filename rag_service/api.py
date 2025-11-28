"""
FastAPI application exposing the RAG service endpoints.

The API provides several endpoints:

* ``GET /`` or ``GET /chatbot`` – serve the chatbot HTML interface.
* ``POST /index`` – perform a full index of a GitLab repository.  Body
  must include ``repo_url`` and ``token``, with an optional ``branch``.
  Supports markdown (.md, .markdown), PDF (.pdf), and Word (.docx) files.
* ``POST /delta-index`` – perform a delta index, updating only
  modified files.  Same payload as ``/index``.
* ``POST /index-local`` – index markdown, PDF, and Word files from a local folder path.
  Body must include ``folder_path``.  Recursively scans for ``.md``,
  ``.markdown``, ``.pdf``, and ``.docx`` files in subdirectories.
* ``POST /search`` – answer a natural language query using the
  knowledge base and, if configured, an LLM.  Body must include
  ``query``.

The application initialises the repository and services on import
using configuration from environment variables.  Supported vector
databases include ChromaDB (default), pgvector, and Cosmos DB.
If required LLM libraries are missing, errors will be raised at start time.
"""

from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from .config import get_settings
from .repositories.factory import RepositoryFactory
from .services.ingestion_service import IngestionService
from .services.search_service import SearchService
from .llm_client import LLMClient
from .utils.logging import get_logger, log_event


settings = get_settings()

# Function to create repository based on RAG_MODE
def create_repository(rag_mode: str | None = None) -> tuple:
    """Create repository and services based on RAG_MODE.
    
    Args:
        rag_mode: Optional RAG mode override ("traditional" or "leann").
                  If None, uses settings.rag_mode.
    
    Returns:
        Tuple of (kb_repo, ingestion_service, search_service)
    """
    # Create a temporary settings object with overridden RAG_MODE if provided
    if rag_mode:
        import copy
        temp_settings = copy.deepcopy(settings)
        temp_settings.rag_mode = rag_mode.lower()
        repo_settings = temp_settings
    else:
        repo_settings = settings
    
    try:
        kb_repo = RepositoryFactory.create(repo_settings)
    except Exception as exc:
        raise
    
    # Initialize LLM client (defaults to Anthropic if API key is set)
    llm_client = LLMClient(settings) if settings.llm_provider else None
    ingestion_service = IngestionService(kb_repo, settings=repo_settings)
    search_service = SearchService(
        kb_repo, llm_client=llm_client, max_chunks=settings.max_chunks, settings=settings
    )
    
    return kb_repo, ingestion_service, search_service

# Initialise repository and services with default RAG_MODE
kb_repo, ingestion_service, search_service = create_repository()


app = FastAPI(
    title="RAG Service",
    description="RAG service for indexing GitLab repositories and local folders (markdown and PDF) and enabling conversational search",
    version="2.0.0",
)
logger = get_logger("api")

# Serve static files (chatbot HTML)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    """Redirect root to chatbot interface."""
    chatbot_path = os.path.join(static_dir, "chatbot.html")
    if os.path.exists(chatbot_path):
        return FileResponse(chatbot_path)
    return {"message": "RAG Service API", "docs": "/docs", "chatbot": "/static/chatbot.html"}


@app.get("/chatbot")
def chatbot():
    """Serve the chatbot HTML interface."""
    chatbot_path = os.path.join(static_dir, "chatbot.html")
    if os.path.exists(chatbot_path):
        return FileResponse(chatbot_path)
    raise HTTPException(status_code=404, detail="Chatbot interface not found")


class IndexRequest(BaseModel):
    repo_url: str
    token: str
    branch: str | None = None
    rag_mode: str | None = None  # Optional RAG mode override

    model_config = {
        "json_schema_extra": {
            "example": {
                "repo_url": "https://gitlab.com/namespace/project.git",
                "token": "your-gitlab-token",
                "branch": "main",
                "rag_mode": "leann"
            }
        }
    }


class SearchRequest(BaseModel):
    query: str
    rag_mode: str | None = None  # Optional RAG mode override

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "What is the authentication flow?",
                "rag_mode": "leann"
            }
        }
    }


class LocalIndexRequest(BaseModel):
    folder_path: str
    rag_mode: str | None = None  # Optional RAG mode override

    model_config = {
        "json_schema_extra": {
            "example": {
                "folder_path": "/path/to/markdown/folder",
                "rag_mode": "leann"
            }
        }
    }


@app.post("/index")
def index_repo(req: IndexRequest):
    """Full index of a GitLab repository.
    
    Indexes markdown (.md, .markdown), PDF (.pdf), and Word (.docx) files from the repository.
    
    Supports RAG_MODE parameter to switch between traditional and LEANN indexing.
    """
    log_event(logger, "api_index_request", repo=req.repo_url, branch=req.branch, rag_mode=req.rag_mode)
    try:
        # Use RAG_MODE from request or default from settings
        rag_mode = req.rag_mode or settings.rag_mode
        kb_repo, ingestion_svc, _ = create_repository(rag_mode)
        
        summary = ingestion_svc.index_repository(
            req.repo_url, req.token, branch=req.branch
        )
        
        # Auto-build LEANN index if using LEANN mode
        if rag_mode == "leann" and hasattr(kb_repo, "build_index"):
            try:
                kb_repo.build_index()
                summary["index_built"] = True
                log_event(logger, "api_leann_index_built", repo=req.repo_url)
            except Exception as build_exc:
                log_event(logger, "api_leann_index_build_error", error=str(build_exc))
                summary["index_build_warning"] = str(build_exc)
        
        return summary
    except Exception as exc:
        log_event(logger, "api_index_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/delta-index")
def delta_index_repo(req: IndexRequest):
    """Delta index of a GitLab repository.
    
    Note: LEANN mode requires full rebuild for delta indexing.
    """
    log_event(logger, "api_delta_index_request", repo=req.repo_url, branch=req.branch, rag_mode=req.rag_mode)
    try:
        rag_mode = req.rag_mode or settings.rag_mode
        kb_repo, ingestion_svc, _ = create_repository(rag_mode)
        
        summary = ingestion_svc.delta_index_repository(
            req.repo_url, req.token, branch=req.branch
        )
        
        # Auto-build LEANN index if using LEANN mode (delta requires rebuild)
        if rag_mode == "leann" and hasattr(kb_repo, "build_index"):
            try:
                kb_repo.build_index()
                summary["index_rebuilt"] = True
                log_event(logger, "api_leann_index_rebuilt", repo=req.repo_url)
            except Exception as build_exc:
                log_event(logger, "api_leann_index_build_error", error=str(build_exc))
                summary["index_build_warning"] = str(build_exc)
        
        return summary
    except Exception as exc:
        log_event(logger, "api_delta_index_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    try:
        # Check if repository is accessible
        # This is a lightweight check - doesn't query data
        return {
            "status": "healthy",
            "service": "markdown-rag",
            "rag_mode": settings.rag_mode,
            "repository_type": settings.repository_type,
        }
    except Exception as exc:
        log_event(logger, "health_check_error", error=str(exc))
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/index-local")
def index_local_folder(req: LocalIndexRequest):
    """Index markdown, PDF, and Word files from a local folder path.

    Recursively scans the specified folder for markdown files (`.md` or
    `.markdown`), PDF files (`.pdf`), and Word documents (`.docx`) and indexes
    them into the knowledge base. Useful for testing or indexing local documentation
    without requiring a GitLab repository.

    The folder path can be absolute or relative to the current working directory.
    PDF files are parsed using pdfplumber, Word files using python-docx to extract text content.
    
    Supports RAG_MODE parameter to switch between traditional and LEANN indexing.
    """
    log_event(logger, "api_local_index_request", folder=req.folder_path, rag_mode=req.rag_mode)
    try:
        rag_mode = req.rag_mode or settings.rag_mode
        kb_repo, ingestion_svc, _ = create_repository(rag_mode)
        
        summary = ingestion_svc.index_local_folder(req.folder_path)
        
        # Auto-build LEANN index if using LEANN mode
        if rag_mode == "leann" and hasattr(kb_repo, "build_index"):
            try:
                kb_repo.build_index()
                summary["index_built"] = True
                log_event(logger, "api_leann_index_built", folder=req.folder_path)
            except Exception as build_exc:
                log_event(logger, "api_leann_index_build_error", error=str(build_exc))
                summary["index_build_warning"] = str(build_exc)
        
        return summary
    except ValueError as exc:
        log_event(logger, "api_local_index_error", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        log_event(logger, "api_local_index_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/search")
def search(req: SearchRequest):
    """Answer a query using the indexed knowledge base and an LLM.
    
    This endpoint searches all indexed content (local folders and repositories).
    For repository-specific search with access control, use /search-repo instead.
    
    Supports RAG_MODE parameter to switch between traditional and LEANN search.
    """
    log_event(logger, "api_search_request", query=req.query, rag_mode=req.rag_mode)
    try:
        rag_mode = req.rag_mode or settings.rag_mode
        _, _, search_svc = create_repository(rag_mode)
        
        result = search_svc.answer(req.query)
        return result
    except Exception as exc:
        log_event(logger, "api_search_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/search-repo")
def search_repo(
    req: SearchRequest,
    x_gitlab_token: Optional[str] = Header(None, alias="X-GitLab-Token"),
    x_github_token: Optional[str] = Header(None, alias="X-GitHub-Token"),
):
    """Answer a query using indexed GitLab/GitHub repositories with access control.
    
    This endpoint:
    1. Gets all distinct repository URLs from the indexed data
    2. Validates which repositories the provided token can access
    3. Filters search results to only accessible repositories
    
    Headers:
    - X-GitLab-Token: GitLab personal access token (for GitLab repos)
    - X-GitHub-Token: GitHub personal access token (for GitHub repos)
    
    At least one token must be provided. The system will use the appropriate
    token based on the repository provider.
    
    Returns search results only from repositories the token has access to.
    """
    log_event(logger, "api_search_repo_request", query=req.query)
    
    # Get token from headers (prefer GitLab, fallback to GitHub)
    token = x_gitlab_token or x_github_token
    
    if not token:
        log_event(
            logger,
            "api_search_repo_no_token",
            query=req.query,
            message="No GitLab or GitHub token provided in headers",
        )
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide either X-GitLab-Token or X-GitHub-Token header.",
        )
    
    try:
        # Use RAG_MODE from request or default from settings
        rag_mode = req.rag_mode or settings.rag_mode
        _, _, search_svc = create_repository(rag_mode)
        
        result = search_svc.answer_with_token_validation(query=req.query, token=token)
        return result
    except Exception as exc:
        log_event(logger, "api_search_repo_error", query=req.query, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/build-leann-index")
def build_leann_index():
    """Explicitly build the LEANN index from buffered documents.
    
    This endpoint allows manual control over LEANN index building.
    Useful when you want to add documents incrementally and build the index later.
    
    Returns:
        Dictionary with build status and index information.
    """
    log_event(logger, "api_build_leann_index_request")
    try:
        # Check if current repository is LEANN
        if not hasattr(kb_repo, "build_index"):
            raise HTTPException(
                status_code=400,
                detail="Current RAG_MODE is not 'leann'. Set RAG_MODE=leann to use LEANN indexing."
            )
        
        # Build the index
        kb_repo.build_index()
        
        # Get index information
        index_path = getattr(kb_repo, "index_path", "unknown")
        index_size = 0
        if os.path.exists(index_path):
            index_size = os.path.getsize(index_path)
        
        result = {
            "status": "success",
            "index_path": index_path,
            "index_size_mb": round(index_size / (1024 * 1024), 2),
            "documents_count": len(kb_repo._pending_chunks) if hasattr(kb_repo, "_pending_chunks") else 0,
        }
        
        log_event(logger, "api_build_leann_index_success", **result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        log_event(logger, "api_build_leann_index_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
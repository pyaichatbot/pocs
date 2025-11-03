"""
FastAPI application exposing the RAG service endpoints.

The API provides four endpoints:

* ``POST /index`` – perform a full index of a GitLab repository.  Body
  must include ``repo_url`` and ``token``, with an optional ``branch``.
* ``POST /delta-index`` – perform a delta index, updating only
  modified files.  Same payload as ``/index``.
* ``POST /index-local`` – index markdown files from a local folder path.
  Body must include ``folder_path``.  Recursively scans for ``.md`` and
  ``.markdown`` files in subdirectories.
* ``POST /search`` – answer a natural language query using the
  knowledge base and, if configured, an LLM.  Body must include
  ``query``.

The application initialises the repository and services on import
using configuration from environment variables.  If Pixeltable or
required LLM libraries are missing, errors will be raised at start
time.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import get_settings
from .repositories.factory import RepositoryFactory
from .services.ingestion_service import IngestionService
from .services.search_service import SearchService
from .llm_client import LLMClient
from .utils.logging import get_logger, log_event


settings = get_settings()

# Initialise repository and services
try:
    kb_repo = RepositoryFactory.create(settings)
except Exception as exc:
    raise
# Initialize LLM client (defaults to Anthropic if API key is set)
llm_client = LLMClient(settings) if settings.llm_provider else None
ingestion_service = IngestionService(kb_repo, settings=settings)
search_service = SearchService(
    kb_repo, llm_client=llm_client, max_chunks=settings.max_chunks, settings=settings
)


app = FastAPI(
    title="Markdown RAG Service",
    description="RAG service for indexing GitLab repositories and enabling conversational search",
    version="1.0.0",
)
logger = get_logger("api")


class IndexRequest(BaseModel):
    repo_url: str
    token: str
    branch: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "repo_url": "https://gitlab.com/namespace/project.git",
                "token": "your-gitlab-token",
                "branch": "main"
            }
        }


class SearchRequest(BaseModel):
    query: str

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the authentication flow?"
            }
        }


class LocalIndexRequest(BaseModel):
    folder_path: str

    class Config:
        json_schema_extra = {
            "example": {
                "folder_path": "/path/to/markdown/folder"
            }
        }


@app.post("/index")
def index_repo(req: IndexRequest):
    """Full index of a GitLab repository."""
    log_event(logger, "api_index_request", repo=req.repo_url, branch=req.branch)
    try:
        summary = ingestion_service.index_repository(
            req.repo_url, req.token, branch=req.branch
        )
        return summary
    except Exception as exc:
        log_event(logger, "api_index_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/delta-index")
def delta_index_repo(req: IndexRequest):
    """Delta index of a GitLab repository."""
    log_event(logger, "api_delta_index_request", repo=req.repo_url, branch=req.branch)
    try:
        summary = ingestion_service.delta_index_repository(
            req.repo_url, req.token, branch=req.branch
        )
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
            "repository_type": settings.repository_type,
        }
    except Exception as exc:
        log_event(logger, "health_check_error", error=str(exc))
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/index-local")
def index_local_folder(req: LocalIndexRequest):
    """Index markdown files from a local folder path.

    Recursively scans the specified folder for markdown files (`.md` or
    `.markdown`) and indexes them into the knowledge base. Useful for testing
    or indexing local documentation without requiring a GitLab repository.

    The folder path can be absolute or relative to the current working directory.
    """
    log_event(logger, "api_local_index_request", folder=req.folder_path)
    try:
        summary = ingestion_service.index_local_folder(req.folder_path)
        return summary
    except ValueError as exc:
        log_event(logger, "api_local_index_error", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        log_event(logger, "api_local_index_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/search")
def search(req: SearchRequest):
    """Answer a query using the indexed knowledge base and an LLM."""
    log_event(logger, "api_search_request", query=req.query)
    try:
        result = search_service.answer(req.query)
        return result
    except Exception as exc:
        log_event(logger, "api_search_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
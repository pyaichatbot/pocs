"""
Configuration settings for the RAG service.

Configurations are loaded from environment variables with sensible
defaults.  This module centralises all configuration to avoid
scattering environment lookups throughout the codebase.  If you need
to add a new configuration option, add it here and document its
purpose.

Key settings include:

**Vector Database**:
* ``REPOSITORY_TYPE`` – vector database type ("chromadb", "pgvector",
  "cosmosdb").  Defaults to "chromadb".
* ``EMBEDDING_MODEL_ID`` – embedding model identifier.  Defaults to
  "intfloat/e5-small-v2".  Options: "all-MiniLM-L6-v2", "intfloat/e5-large-v2", etc.

**ChromaDB** (when REPOSITORY_TYPE=chromadb):
* ``CHROMADB_PATH`` – local storage path.  Defaults to "./chroma_db".
* ``CHROMADB_HOST`` – remote server host (optional).
* ``CHROMADB_PORT`` – remote server port (optional).

**pgvector** (when REPOSITORY_TYPE=pgvector):
* ``POSTGRES_CONNECTION_STRING`` – PostgreSQL connection string (required).

**Cosmos DB** (when REPOSITORY_TYPE=cosmosdb):
* ``COSMOS_ENDPOINT`` – Cosmos DB endpoint URL (required).
* ``COSMOS_KEY`` – Cosmos DB access key (required).

**Search Configuration**:
* ``MAX_CHUNKS`` – maximum chunks per query.  Defaults to 5.
* ``CHUNK_MAX_WORDS`` – maximum words per chunk.  Defaults to 300.
* ``CHUNK_OVERLAP_WORDS`` – overlap words between chunks.  Defaults to 50.
* ``RERANKER_ENABLED`` – enable cross-encoder reranking.  Defaults to false.
* ``RERANKER_MODEL_ID`` – reranker model.  Defaults to "cross-encoder/ms-marco-MiniLM-L-6-v2".
* ``QUANTIZATION_ENABLED`` – enable binary quantization.  Defaults to false.

**Parallel Processing**:
* ``MAX_WORKERS`` – number of parallel workers for file processing.  Defaults to 4.
  Set to 1 to disable parallel processing.
* ``BATCH_SIZE`` – batch size for document upserts.  Defaults to 100.
  Larger batches improve throughput but use more memory.

**LLM Provider**:
* ``LLM_PROVIDER`` – provider ("azure" or "anthropic").  Defaults to "anthropic"
  if ANTHROPIC_API_KEY is set.
* ``ANTHROPIC_API_KEY`` – Anthropic API key.
* ``ANTHROPIC_MODEL`` – Anthropic model.  Defaults to "claude-3-5-sonnet-20241022".
* ``AZURE_OPENAI_ENDPOINT`` – Azure OpenAI endpoint URL.
* ``AZURE_OPENAI_API_KEY`` – Azure OpenAI API key.
* ``AZURE_OPENAI_DEPLOYMENT_NAME`` – Azure OpenAI deployment name.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Configuration loaded from environment variables."""


    # Large language model provider: "azure" or "anthropic".  
    # Defaults to "anthropic" if ANTHROPIC_API_KEY is set, otherwise None.
    llm_provider: str | None = os.environ.get(
        "LLM_PROVIDER",
        "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else None,
    )

    # Azure OpenAI settings
    azure_endpoint: str | None = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_api_key: str | None = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_deployment_name: str | None = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")

    # Anthropic settings
    anthropic_api_key: str | None = os.environ.get("ANTHROPIC_API_KEY")
    anthropic_model: str = os.environ.get(
        "ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"
    )

    # Embedding model configuration
    embedding_model_id: str = os.environ.get(
        "EMBEDDING_MODEL_ID",
        "intfloat/e5-small-v2",
    )

    # Search configuration
    max_chunks: int = int(os.environ.get("MAX_CHUNKS", "5"))
    chunk_max_words: int = int(os.environ.get("CHUNK_MAX_WORDS", "300"))
    chunk_overlap_words: int = int(os.environ.get("CHUNK_OVERLAP_WORDS", "50"))

    # Repository type (chromadb, pgvector, cosmosdb)
    repository_type: str = os.environ.get("REPOSITORY_TYPE", "chromadb")

    # ChromaDB settings
    chromadb_path: str = os.environ.get("CHROMADB_PATH", "./chroma_db")
    chromadb_host: str | None = os.environ.get("CHROMADB_HOST")
    chromadb_port: int | None = (
        int(os.environ.get("CHROMADB_PORT")) if os.environ.get("CHROMADB_PORT") else None
    )

    # PostgreSQL/pgvector settings
    postgres_connection_string: str | None = os.environ.get("POSTGRES_CONNECTION_STRING")

    # Cosmos DB settings
    cosmos_endpoint: str | None = os.environ.get("COSMOS_ENDPOINT")
    cosmos_key: str | None = os.environ.get("COSMOS_KEY")

    # Reranking configuration
    reranker_enabled: bool = os.environ.get("RERANKER_ENABLED", "false").lower() == "true"
    reranker_model_id: str = os.environ.get(
        "RERANKER_MODEL_ID", "cross-encoder/ms-marco-MiniLM-L-6-v2"
    )

    # Quantization configuration
    quantization_enabled: bool = os.environ.get("QUANTIZATION_ENABLED", "false").lower() == "true"

    # Parallel processing configuration
    max_workers: int = int(os.environ.get("MAX_WORKERS", "4"))  # Number of parallel workers for file processing
    batch_size: int = int(os.environ.get("BATCH_SIZE", "100"))  # Batch size for document upserts


def get_settings() -> Settings:
    """Return a new Settings instance loaded from the environment."""
    return Settings()

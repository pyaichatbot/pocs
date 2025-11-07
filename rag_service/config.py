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

**Web Crawler**:
* ``WEB_CRAWLER_ENABLED`` – enable web crawler for URL extraction from queries.  Defaults to false.
* ``ALLOWED_WEB_DOMAINS`` – comma-separated list of allowed domains (e.g., "docs.anthropic.com,cloud.google.com").
  If not set or empty, all domains are blocked (whitelist-only mode). If set, only listed domains are allowed.
* ``WEB_CRAWLER_TIMEOUT`` – request timeout in seconds.  Defaults to 10.
* ``WEB_CRAWLER_MAX_SIZE`` – maximum content size to download in bytes.  Defaults to 1000000 (1MB).

**Web Search**:
* ``WEB_SEARCH_ENABLED`` – enable web search when knowledge base results are insufficient.  Defaults to false.
* ``WEB_SEARCH_PROVIDER`` – search provider ("duckduckgo", "tavily", "serpapi").  Defaults to "duckduckgo".
  DuckDuckGo is free and requires no API key. Tavily and SerpAPI require API keys.
* ``WEB_SEARCH_MAX_RESULTS`` – maximum number of web search results to return.  Defaults to 5.
* ``WEB_SEARCH_MAX_CRAWL_URLS`` – maximum number of URLs to crawl for full content.  Defaults to 3.
  This limits how many URLs are crawled to manage context length and crawling time.
* ``WEB_SEARCH_MAX_CONTENT_LENGTH`` – total maximum content length (characters) across all crawled URLs.
  Defaults to 50000 (50k chars, ~12-15k tokens). Content is truncated if exceeded.
* ``WEB_SEARCH_MAX_CONTENT_PER_URL`` – maximum content length (characters) per crawled URL.
  Defaults to 10000 (10k chars, ~2.5-3k tokens). Each URL's content is truncated if exceeded.
* ``WEB_SEARCH_MIN_SCORE_THRESHOLD`` – minimum average KB score threshold to trigger web search.
  If KB results average score is below this (0.0-1.0), web search is triggered.  Defaults to 0.5.
* ``TAVILY_API_KEY`` – Tavily API key (required if WEB_SEARCH_PROVIDER=tavily).
* ``SERPAPI_API_KEY`` – SerpAPI key (required if WEB_SEARCH_PROVIDER=serpapi).

**LLM Provider**:
* ``LLM_PROVIDER`` – provider ("azure" or "anthropic").  Defaults to "anthropic"
  if ANTHROPIC_API_KEY is set.
* ``ANTHROPIC_API_KEY`` – Anthropic API key.
* ``ANTHROPIC_MODEL`` – Anthropic model.  Defaults to "claude-3-5-sonnet-20241022".
* ``AZURE_OPENAI_ENDPOINT`` – Azure OpenAI endpoint URL.
* ``AZURE_OPENAI_API_KEY`` – Azure OpenAI API key.
* ``AZURE_OPENAI_DEPLOYMENT_NAME`` – Azure OpenAI deployment name.
* ``LLM_MAX_TOKENS`` – Maximum tokens for LLM response.  Defaults to 4096.
  Increase for longer responses, decrease to save costs.
* ``USE_LLM_TOKEN_FORMAT`` – Token format for LLM context ("plain", "toon", "hybrid", "json").
  Defaults to "hybrid". Options:
  - "plain": Plain text concatenation (no optimization, backward compatible)
  - "toon": Fully flattened TOON format (maximum token savings, ~40%)
  - "hybrid": TOON for content + JSON for metadata (recommended, ~30% savings)
  - "json": JSON format (structured but verbose, for debugging)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


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

    # LLM response configuration
    llm_max_tokens: int = int(os.environ.get("LLM_MAX_TOKENS", "20000"))
    
    # LLM token format configuration
    # Options: "plain" (default), "toon", "hybrid", "json"
    # - "plain": Plain text concatenation (no optimization)
    # - "toon": Fully flattened TOON format (maximum token savings)
    # - "hybrid": TOON for content + JSON for metadata (recommended)
    # - "json": JSON format (structured, but more tokens)
    use_llm_token_format: str = os.environ.get("USE_LLM_TOKEN_FORMAT", "hybrid").lower()

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

    # Web crawler configuration
    web_crawler_enabled: bool = os.environ.get("WEB_CRAWLER_ENABLED", "false").lower() == "true"
    allowed_web_domains: list[str] = field(
        default_factory=lambda: [
            d.strip()
            for d in os.environ.get("ALLOWED_WEB_DOMAINS", "").split(",")
            if d.strip()
        ]
    )
    web_crawler_timeout: int = int(os.environ.get("WEB_CRAWLER_TIMEOUT", "10"))
    web_crawler_max_size: int = int(os.environ.get("WEB_CRAWLER_MAX_SIZE", "1000000"))

    # Web search configuration
    web_search_enabled: bool = os.environ.get("WEB_SEARCH_ENABLED", "false").lower() == "true"
    web_search_provider: str = os.environ.get("WEB_SEARCH_PROVIDER", "duckduckgo").lower()
    web_search_max_results: int = int(os.environ.get("WEB_SEARCH_MAX_RESULTS", "5"))
    web_search_max_crawl_urls: int = int(os.environ.get("WEB_SEARCH_MAX_CRAWL_URLS", "3"))
    web_search_max_content_length: int = int(os.environ.get("WEB_SEARCH_MAX_CONTENT_LENGTH", "50000"))  # Total chars across all URLs
    web_search_max_content_per_url: int = int(os.environ.get("WEB_SEARCH_MAX_CONTENT_PER_URL", "10000"))  # Max chars per URL
    web_search_min_score_threshold: float = float(
        os.environ.get("WEB_SEARCH_MIN_SCORE_THRESHOLD", "0.5")
    )
    tavily_api_key: str | None = os.environ.get("TAVILY_API_KEY")
    serpapi_api_key: str | None = os.environ.get("SERPAPI_API_KEY")


def get_settings() -> Settings:
    """Return a new Settings instance loaded from the environment."""
    return Settings()

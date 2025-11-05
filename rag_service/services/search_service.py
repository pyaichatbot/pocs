"""
Search and answer service for the RAG system.

This service encapsulates the logic for retrieving relevant
information from the knowledge base and, optionally, generating a
conversational answer via a large language model.  It delegates
database operations to a ``BaseKnowledgeBaseRepository`` and LLM
interaction to an ``LLMClient``.

The primary method ``answer`` accepts a natural language query and
returns either a generated answer or, if no LLM provider is
available, the top documents as context.  Keyword and similarity
search results are combined using the hybrid search method defined on
the repository.  The number of context chunks can be tuned via
``max_chunks``.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..repositories.base_kb_repo import BaseKnowledgeBaseRepository
from ..llm_client import DocumentChunk, LLMClient
from ..utils.logging import get_logger, log_event
from ..utils.reranker import Reranker
from ..utils.web_crawler import WebCrawler
from ..config import Settings


class SearchService:
    """Service for searching and answering queries using the KB and an LLM."""

    def __init__(
        self,
        kb_repo: BaseKnowledgeBaseRepository,
        llm_client: LLMClient | None = None,
        max_chunks: int = 5,
        settings: Settings | None = None,
    ) -> None:
        self.kb_repo = kb_repo
        self.llm_client = llm_client
        self.max_chunks = max_chunks
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize reranker if enabled
        if settings:
            self.reranker = Reranker(settings) if getattr(settings, "reranker_enabled", False) else None
        else:
            self.reranker = None

        # Initialize web crawler if enabled
        self.web_crawler: Optional[WebCrawler] = None
        if settings:
            web_crawler_enabled = getattr(settings, "web_crawler_enabled", False)
            log_event(
                self.logger,
                "web_crawler_config_check",
                enabled=web_crawler_enabled,
                settings_present=settings is not None,
            )
            if web_crawler_enabled:
                allowed_domains = getattr(settings, "allowed_web_domains", None)
                self.web_crawler = WebCrawler(
                    allowed_domains=allowed_domains,
                    timeout=getattr(settings, "web_crawler_timeout", 10),
                    max_content_length=getattr(settings, "web_crawler_max_size", 1000000),
                    llm_client=llm_client,  # Pass LLM client for relevance checking
                )
                log_event(
                    self.logger,
                    "web_crawler_initialized",
                    enabled=True,
                    allowed_domains=allowed_domains,
                )
            else:
                log_event(self.logger, "web_crawler_disabled", reason="not_enabled_in_config")
        else:
            log_event(self.logger, "web_crawler_disabled", reason="no_settings_provided")

    def answer(self, query: str) -> Dict[str, object]:
        """Retrieve relevant contexts and optionally generate an answer.

        Args:
            query: The user's natural language question.
        Returns:
            A dictionary containing either an ``answer`` field with the
            generated response or a ``contexts`` field with the raw
            document chunks.
        """
        log_event(self.logger, "search_start", query=query)
        try:
            # Perform hybrid search
            results = self.kb_repo.hybrid_search(query, k=self.max_chunks * 2)
            
            # Apply reranking if enabled
            if self.reranker and self.reranker.enabled:
                results = self.reranker.rerank(query, results, top_k=self.max_chunks)
            else:
                # Limit to max_chunks if no reranking
                results = results[:self.max_chunks]
        except Exception as exc:
            log_event(self.logger, "search_error", error=str(exc))
            raise
        # Convert results to DocumentChunk objects for LLM
        contexts: List[DocumentChunk] = []
        for r in results:
            contexts.append(
                DocumentChunk(
                    doc_id=r["doc_id"],
                    chunk_id=r["chunk_id"],
                    path=r.get("path", ""),
                    content=r["content"],
                    metadata=r.get("metadata", {}),
                )
            )

        # Extract and crawl URLs from query if web crawler is enabled
        web_crawled_contexts: List[DocumentChunk] = []
        if self.web_crawler:
            try:
                log_event(self.logger, "web_crawl_attempt", query=query)
                crawled_results = self.web_crawler.extract_and_crawl(query)
                log_event(
                    self.logger,
                    "web_crawl_extraction_complete",
                    urls_found=len(crawled_results),
                    results_count=len(crawled_results),
                )
                for idx, crawled in enumerate(crawled_results):
                    # Add crawled content as additional context
                    web_crawled_contexts.append(
                        DocumentChunk(
                            doc_id=f"web_crawl_{idx}",
                            chunk_id=f"web_crawl_{idx}_chunk",
                            path=crawled["url"],
                            content=crawled["content"],
                            metadata={
                                "source": "web_crawl",
                                "url": crawled["url"],
                            },
                        )
                    )
                if web_crawled_contexts:
                    log_event(
                        self.logger,
                        "web_crawl_success",
                        urls_found=len(crawled_results),
                        contexts_added=len(web_crawled_contexts),
                    )
                    # Combine vector DB contexts with web crawled contexts
                    # Prioritize vector DB results, but include web crawled content
                    contexts = contexts + web_crawled_contexts
                else:
                    log_event(
                        self.logger,
                        "web_crawl_no_results",
                        message="No URLs were crawled successfully - check domain allowlist and logs",
                    )
            except Exception as exc:
                log_event(self.logger, "web_crawl_error", error=str(exc), exc_info=True)
                # Continue with vector DB results only if web crawl fails
        else:
            log_event(
                self.logger,
                "web_crawler_not_available",
                message="Web crawler is None - check initialization logs at startup",
            )

        if self.llm_client and self.llm_client.is_available():
            answer = self.llm_client.generate_answer(query, contexts)
            log_event(self.logger, "search_complete", query=query, answer=answer)
            return {"answer": answer}
        else:
            # No LLM available; return contexts for caller to process
            log_event(self.logger, "search_complete", query=query, answer="none")
            return {"contexts": [c.content for c in contexts]}
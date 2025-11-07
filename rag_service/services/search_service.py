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
from ..utils.web_search import WebSearch, WebSearchError
from ..utils.repo_validator import RepoAccessValidator
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

        # Initialize web search if enabled
        self.web_search: Optional[WebSearch] = None
        if settings:
            web_search_enabled = getattr(settings, "web_search_enabled", False)
            log_event(
                self.logger,
                "web_search_config_check",
                enabled=web_search_enabled,
                settings_present=settings is not None,
            )
            if web_search_enabled:
                try:
                    # Pass web crawler to web search so it can crawl URLs for full content
                    # If web crawler is not enabled, web search will create a basic one
                    self.web_search = WebSearch(
                        provider=getattr(settings, "web_search_provider", "duckduckgo"),
                        max_results=getattr(settings, "web_search_max_results", 5),
                        max_crawl_urls=getattr(settings, "web_search_max_crawl_urls", 3),
                        max_content_length=getattr(settings, "web_search_max_content_length", 50000),
                        max_content_per_url=getattr(settings, "web_search_max_content_per_url", 10000),
                        timeout=getattr(settings, "web_crawler_timeout", 10),  # Reuse crawler timeout
                        llm_client=llm_client,  # Pass LLM client for relevance checking
                        web_crawler=self.web_crawler,  # Reuse web crawler if available
                        crawl_urls=True,  # Always crawl URLs to get full content
                    )
                    log_event(
                        self.logger,
                        "web_search_initialized",
                        enabled=True,
                        provider=getattr(settings, "web_search_provider", "duckduckgo"),
                    )
                except WebSearchError as exc:
                    log_event(
                        self.logger,
                        "web_search_initialization_failed",
                        error=str(exc),
                        reason="configuration_error",
                    )
                    self.web_search = None
            else:
                log_event(self.logger, "web_search_disabled", reason="not_enabled_in_config")
        else:
            log_event(self.logger, "web_search_disabled", reason="no_settings_provided")

        # Initialize repo validator for access control
        self.repo_validator = RepoAccessValidator()

    def answer(self, query: str, filter_repo_urls: List[str] | None = None) -> Dict[str, object]:
        """Retrieve relevant contexts and optionally generate an answer.

        Args:
            query: The user's natural language question.
            filter_repo_urls: Optional list of repository URLs to filter results by.
                           If provided, only return results from these repositories.
        Returns:
            A dictionary containing either an ``answer`` field with the
            generated response or a ``contexts`` field with the raw
            document chunks.
        """
        log_event(
            self.logger,
            "search_start",
            query=query,
            filter_repos=filter_repo_urls is not None,
            repo_count=len(filter_repo_urls) if filter_repo_urls else 0,
        )
        try:
            # Perform similarity search with optional repository filtering
            # Use similarity_search directly since hybrid_search doesn't support filtering yet
            if filter_repo_urls:
                # If filtering is requested, use similarity search with filter
                sim_results = self.kb_repo.similarity_search(
                    query, k=self.max_chunks * 2, filter_repo_urls=filter_repo_urls
                )
                # For hybrid search with filtering, we'd need to also filter keyword search
                # For now, use similarity results only when filtering
                results = sim_results
            else:
                # No filtering - use hybrid search as before
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

        # Check if web search should be triggered (before processing KB results)
        web_search_contexts: List[DocumentChunk] = []
        if self.web_search:
            try:
                min_score_threshold = getattr(
                    self.settings, "web_search_min_score_threshold", 0.5
                ) if self.settings else 0.5

                should_trigger = self.web_search.should_trigger_web_search(
                    kb_results=results,
                    query=query,
                    min_score_threshold=min_score_threshold,
                )

                if should_trigger:
                    log_event(self.logger, "web_search_triggering", query=query)
                    search_results = self.web_search.search(query)

                    for idx, search_result in enumerate(search_results):
                        # Use full content if available, otherwise fall back to snippet
                        content = search_result.get("content", "")
                        snippet = search_result.get("snippet", "")
                        
                        # If content is just the snippet (short), try to get more context
                        if content and len(content) > 200:
                            # Full content was crawled
                            full_content = f"Title: {search_result.get('title', '')}\n\n{content}"
                        elif snippet:
                            # Use snippet if full content not available
                            full_content = f"Title: {search_result.get('title', '')}\n\nSnippet: {snippet}\n\nURL: {search_result.get('url', '')}"
                        else:
                            # Fallback
                            full_content = f"Title: {search_result.get('title', '')}\n\nURL: {search_result.get('url', '')}"

                        web_search_contexts.append(
                            DocumentChunk(
                                doc_id=f"web_search_{idx}",
                                chunk_id=f"web_search_{idx}_chunk",
                                path=search_result.get("url", ""),
                                content=full_content,
                                metadata={
                                    "source": "web_search",
                                    "url": search_result.get("url", ""),
                                    "title": search_result.get("title", ""),
                                    "provider": self.web_search.provider,
                                    "crawled": len(content) > len(snippet) if content and snippet else bool(content),
                                },
                            )
                        )

                    if web_search_contexts:
                        log_event(
                            self.logger,
                            "web_search_success",
                            query=query,
                            results_count=len(web_search_contexts),
                        )
                    else:
                        log_event(
                            self.logger,
                            "web_search_no_results",
                            query=query,
                        )
                else:
                    log_event(
                        self.logger,
                        "web_search_not_triggered",
                        query=query,
                        reason="sufficient_kb_results",
                    )
            except WebSearchError as exc:
                log_event(
                    self.logger,
                    "web_search_error",
                    query=query,
                    error=str(exc),
                    exc_info=True,
                )
                # Continue with KB results only if web search fails
            except Exception as exc:
                log_event(
                    self.logger,
                    "web_search_unexpected_error",
                    query=query,
                    error=str(exc),
                    exc_info=True,
                )
                # Continue with KB results only if web search fails

        # Convert KB results to DocumentChunk objects for LLM
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

        # Combine all contexts: KB results first, then web search results, then web crawled results
        # Prioritize KB results, but supplement with web search when KB is insufficient
        all_contexts = contexts + web_search_contexts

        if self.llm_client and self.llm_client.is_available():
            answer = self.llm_client.generate_answer(query, all_contexts)
            log_event(self.logger, "search_complete", query=query, answer=answer)
            return {"answer": answer}
        else:
            # No LLM available; return contexts for caller to process
            log_event(self.logger, "search_complete", query=query, answer="none")
            return {"contexts": [c.content for c in all_contexts]}

    def answer_with_token_validation(self, query: str, token: str) -> Dict[str, object]:
        """Answer query with repository access control based on user token.

        This method:
        1. Gets all distinct repository URLs from the database
        2. Validates which repos the token can access
        3. Filters search results to only accessible repositories

        Args:
            query: The user's natural language question.
            token: GitLab or GitHub personal access token (from request headers).

        Returns:
            A dictionary containing either an ``answer`` field with the
            generated response or a ``contexts`` field with the raw
            document chunks.
        """
        log_event(self.logger, "search_repo_start", query=query)
        
        try:
            # 1. Get all distinct repository URLs from database
            all_repo_urls = self.kb_repo.get_distinct_repo_urls()
            
            if not all_repo_urls:
                log_event(
                    self.logger,
                    "search_repo_no_repos",
                    query=query,
                    message="No repositories found in database",
                )
                # No repos indexed, return empty result
                if self.llm_client and self.llm_client.is_available():
                    return {
                        "answer": "No repositories are currently indexed in the knowledge base."
                    }
                return {"contexts": []}

            log_event(
                self.logger,
                "search_repo_repos_found",
                query=query,
                total_repos=len(all_repo_urls),
            )

            # 2. Validate token access to repositories
            accessible_repo_urls = self.repo_validator.get_accessible_repos(
                token=token,
                repo_urls=all_repo_urls,
            )

            if not accessible_repo_urls:
                log_event(
                    self.logger,
                    "search_repo_no_access",
                    query=query,
                    total_repos=len(all_repo_urls),
                    message="Token does not have access to any indexed repositories",
                )
                # No accessible repos
                if self.llm_client and self.llm_client.is_available():
                    return {
                        "answer": "You do not have access to any indexed repositories, or the provided token is invalid."
                    }
                return {"contexts": []}

            log_event(
                self.logger,
                "search_repo_access_validated",
                query=query,
                total_repos=len(all_repo_urls),
                accessible_repos=len(accessible_repo_urls),
            )

            # 3. Search with repository filter
            return self.answer(query=query, filter_repo_urls=list(accessible_repo_urls))

        except Exception as exc:
            log_event(
                self.logger,
                "search_repo_error",
                query=query,
                error=str(exc),
                exc_info=True,
            )
            raise
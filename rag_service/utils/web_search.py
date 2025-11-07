"""
Web search utility for performing web searches when knowledge base results are insufficient.

This module provides functionality to:
- Perform web searches using DuckDuckGo (free, no API key required)
- Extract and return search results as document chunks
- Support multiple search providers (DuckDuckGo, Tavily, SerpAPI)
- Filter and rank search results by relevance

The web search is triggered when the knowledge base search returns insufficient
or low-quality results, allowing the system to answer questions about topics
not in the indexed knowledge base.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any, TYPE_CHECKING

from .logging import get_logger, log_event

if TYPE_CHECKING:
    from ..llm_client import LLMClient
    from .web_crawler import WebCrawler

logger = get_logger(__name__)


class WebSearchError(Exception):
    """Raised when an error occurs during web search."""


class WebSearch:
    """Web search utility for finding information on the internet."""

    def __init__(
        self,
        provider: str = "duckduckgo",
        max_results: int = 5,
        max_crawl_urls: int = 3,
        max_content_length: int = 50000,
        max_content_per_url: int = 10000,
        timeout: int = 10,
        llm_client: Optional["LLMClient"] = None,
        web_crawler: Optional["WebCrawler"] = None,
        crawl_urls: bool = True,
    ) -> None:
        """Initialize the web search utility.

        Args:
            provider: Search provider ("duckduckgo", "tavily", "serpapi").
                     Defaults to "duckduckgo".
            max_results: Maximum number of search results to return. Defaults to 5.
            max_crawl_urls: Maximum number of URLs to crawl for full content. Defaults to 3.
                           Limits crawling to manage context length and performance.
            max_content_length: Total maximum content length (characters) across all crawled URLs.
                               Defaults to 50000 (50k chars, ~12-15k tokens).
            max_content_per_url: Maximum content length (characters) per crawled URL.
                                Defaults to 10000 (10k chars, ~2.5-3k tokens).
            timeout: Request timeout in seconds. Defaults to 10.
            llm_client: Optional LLM client for result relevance checking.
            web_crawler: Optional web crawler instance to fetch full content from URLs.
                        If None and crawl_urls=True, a basic crawler will be created.
            crawl_urls: Whether to crawl URLs from search results to get full content.
                       If True, URLs will be crawled to extract full page content instead of
                       just using snippets. Defaults to True.
        """
        self.provider = provider.lower()
        self.max_results = max_results
        self.max_crawl_urls = max_crawl_urls
        self.max_content_length = max_content_length
        self.max_content_per_url = max_content_per_url
        self.timeout = timeout
        self.llm_client = llm_client
        self.web_crawler = web_crawler
        self.crawl_urls = crawl_urls

        # Initialize provider-specific clients
        self._duckduckgo = None
        self._tavily_api_key = None
        self._serpapi_api_key = None

        if self.provider == "duckduckgo":
            try:
                # Try new package name first (ddgs)
                try:
                    from ddgs import DDGS
                    self._duckduckgo = DDGS()
                    log_event(logger, "web_search_initialized", provider="duckduckgo", package="ddgs")
                except ImportError:
                    # Fallback to old package name for backward compatibility
                    try:
                        from duckduckgo_search import DDGS
                        self._duckduckgo = DDGS()
                        log_event(logger, "web_search_initialized", provider="duckduckgo", package="duckduckgo_search")
                    except ImportError:
                        raise ImportError("Neither 'ddgs' nor 'duckduckgo-search' package found")
            except ImportError as exc:
                log_event(
                    logger,
                    "web_search_import_error",
                    provider="duckduckgo",
                    message="ddgs package not installed",
                    error=str(exc),
                )
                raise WebSearchError(
                    "DuckDuckGo search requires 'ddgs' package. "
                    "Install with: pip install ddgs"
                ) from exc
        elif self.provider == "tavily":
            import os
            self._tavily_api_key = os.environ.get("TAVILY_API_KEY")
            if not self._tavily_api_key:
                log_event(
                    logger,
                    "web_search_config_error",
                    provider="tavily",
                    message="TAVILY_API_KEY not set",
                )
                raise WebSearchError("Tavily search requires TAVILY_API_KEY environment variable")
            log_event(logger, "web_search_initialized", provider="tavily")
        elif self.provider == "serpapi":
            import os
            self._serpapi_api_key = os.environ.get("SERPAPI_API_KEY")
            if not self._serpapi_api_key:
                log_event(
                    logger,
                    "web_search_config_error",
                    provider="serpapi",
                    message="SERPAPI_API_KEY not set",
                )
                raise WebSearchError("SerpAPI search requires SERPAPI_API_KEY environment variable")
            log_event(logger, "web_search_initialized", provider="serpapi")
        else:
            raise WebSearchError(f"Unsupported search provider: {provider}")

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a web search and return results with full content.

        Args:
            query: Search query string.

        Returns:
            List of search result dictionaries with keys:
            - 'title': Result title
            - 'url': Result URL
            - 'content': Full page content (if crawl_urls=True) or snippet
            - 'snippet': Original snippet from search (if available)
            - 'score': Relevance score (if available)
        """
        log_event(logger, "web_search_start", query=query, provider=self.provider, crawl_urls=self.crawl_urls)

        try:
            # Get search results (URLs and snippets)
            if self.provider == "duckduckgo":
                results = self._search_duckduckgo(query)
            elif self.provider == "tavily":
                results = self._search_tavily(query)
            elif self.provider == "serpapi":
                results = self._search_serpapi(query)
            else:
                raise WebSearchError(f"Unsupported provider: {self.provider}")

            # Limit results before crawling (more efficient)
            results = results[:self.max_results]

            # If crawl_urls is enabled, fetch full content from URLs
            # Limit to max_crawl_urls to manage context length and performance
            if self.crawl_urls:
                results = self._crawl_search_results(results, query)

            log_event(
                logger,
                "web_search_complete",
                query=query,
                results_count=len(results),
                provider=self.provider,
                crawled=self.crawl_urls,
            )

            return results

        except Exception as exc:
            log_event(logger, "web_search_error", query=query, error=str(exc), exc_info=True)
            raise WebSearchError(f"Web search failed: {exc}") from exc

    def _crawl_search_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """Crawl URLs from search results to get full content.

        Args:
            results: List of search results with URLs and snippets.
            query: Original search query (for logging).

        Returns:
            List of results with full content crawled from URLs.
        """
        if not results:
            return results

        # For web search, ALWAYS create a new crawler without domain restrictions
        # The existing web_crawler (if any) has domain restrictions for user-provided URLs,
        # but web search results should be crawlable from any domain
        if self.crawl_urls:
            try:
                from .web_crawler import WebCrawler
                # Create a crawler specifically for web search with no domain restrictions
                # Pass None for allowed_domains, but we'll override is_domain_allowed to allow all
                crawler = WebCrawler(
                    allowed_domains=None,  # Will be overridden
                    timeout=self.timeout,
                    max_content_length=1000000,  # 1MB
                    llm_client=self.llm_client,
                )
                # Override domain check to allow all domains for web search
                def allow_all_domains(url: str) -> bool:
                    return True  # Allow all domains for web search
                crawler.is_domain_allowed = allow_all_domains
                log_event(
                    logger,
                    "web_search_crawler_created",
                    query=query,
                    allow_all=True,
                    message="Created crawler without domain restrictions for web search",
                )
            except Exception as exc:
                log_event(
                    logger,
                    "web_search_crawler_creation_failed",
                    query=query,
                    error=str(exc),
                    exc_info=True,
                )
                # Fall back to snippets if crawler creation fails
                return results
        else:
            # If crawling is disabled, return results as-is
            return results

        crawled_results = []
        total_content_length = 0
        urls_crawled = 0
        
        for result in results:
            url = result.get("url", "")
            snippet = result.get("content", "")  # Original snippet
            title = result.get("title", "")

            # Check if we've reached the limit for crawling URLs
            if urls_crawled >= self.max_crawl_urls:
                # Keep remaining results with snippets only
                log_event(
                    logger,
                    "web_search_crawl_limit_reached",
                    urls_crawled=urls_crawled,
                    max_crawl_urls=self.max_crawl_urls,
                    remaining_results=len(results) - len(crawled_results),
                )
                crawled_results.append(result)  # Keep with snippet
                continue

            # Check if we've reached total content length limit
            if total_content_length >= self.max_content_length:
                log_event(
                    logger,
                    "web_search_content_limit_reached",
                    total_length=total_content_length,
                    max_length=self.max_content_length,
                    remaining_results=len(results) - len(crawled_results),
                )
                crawled_results.append(result)  # Keep with snippet
                continue

            if not url:
                # Keep result with snippet if no URL
                crawled_results.append(result)
                continue

            try:
                log_event(logger, "web_search_crawling_url", url=url, query=query, urls_crawled=urls_crawled)
                full_content = crawler.crawl(url)

                if full_content:
                    urls_crawled += 1
                    original_length = len(full_content)
                    
                    # Truncate content per URL if needed
                    if original_length > self.max_content_per_url:
                        full_content = full_content[:self.max_content_per_url] + "\n\n[Content truncated due to length limit]"
                        log_event(
                            logger,
                            "web_search_content_truncated_per_url",
                            url=url,
                            original_length=original_length,
                            truncated_to=self.max_content_per_url,
                        )
                    
                    # Check if adding this content would exceed total limit
                    content_length = len(full_content)
                    if total_content_length + content_length > self.max_content_length:
                        # Truncate to fit within remaining limit
                        remaining_space = self.max_content_length - total_content_length
                        if remaining_space > 100:  # Only truncate if meaningful space remains
                            full_content = full_content[:remaining_space] + "\n\n[Content truncated due to total length limit]"
                            content_length = len(full_content)
                            log_event(
                                logger,
                                "web_search_content_truncated_total",
                                url=url,
                                total_length_before=total_content_length,
                                content_length=content_length,
                                max_length=self.max_content_length,
                            )
                        else:
                            # No space left, use snippet instead
                            log_event(
                                logger,
                                "web_search_content_limit_exceeded_using_snippet",
                                url=url,
                                total_length=total_content_length,
                                content_length=content_length,
                                max_length=self.max_content_length,
                            )
                            crawled_results.append(result)  # Keep with snippet
                            continue
                    
                    total_content_length += content_length
                    
                    # Use full content, but keep snippet in metadata
                    crawled_results.append({
                        "title": title,
                        "url": url,
                        "content": full_content,  # Full crawled content (possibly truncated)
                        "snippet": snippet,  # Original snippet preserved
                        "score": result.get("score", 1.0),
                    })
                    log_event(
                        logger,
                        "web_search_url_crawled",
                        url=url,
                        content_length=content_length,
                        total_length=total_content_length,
                        urls_crawled=urls_crawled,
                    )
                else:
                    # Crawling failed, use snippet as fallback
                    log_event(
                        logger,
                        "web_search_crawl_failed_using_snippet",
                        url=url,
                        reason="crawl_returned_none",
                    )
                    crawled_results.append(result)  # Keep original with snippet

            except Exception as exc:
                # Crawling failed, use snippet as fallback
                log_event(
                    logger,
                    "web_search_crawl_error_using_snippet",
                    url=url,
                    error=str(exc),
                )
                crawled_results.append(result)  # Keep original with snippet

        # Count successfully crawled results (those with full content longer than snippet)
        crawled_count = sum(
            1 for r in crawled_results
            if r.get("content") and r.get("snippet")
            and len(r.get("content", "")) > len(r.get("snippet", ""))
        )
        
        log_event(
            logger,
            "web_search_crawl_complete",
            query=query,
            total_results=len(results),
            crawled_successfully=crawled_count,
            urls_crawled=urls_crawled,
            total_content_length=total_content_length,
            max_content_length=self.max_content_length,
        )

        return crawled_results

    def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo."""
        try:
            results = []
            # Use text() method for general web search
            # Note: text() returns an iterator, so we need to iterate over it
            search_results = self._duckduckgo.text(
                query,
                max_results=self.max_results,
                region="wt-wt",  # Worldwide
                safesearch="moderate",
            )

            # Convert iterator to list and process results
            result_count = 0
            for result in search_results:
                result_count += 1
                # Handle both old and new API formats
                title = result.get("title", "")
                url = result.get("href") or result.get("url") or result.get("link", "")
                content = result.get("body") or result.get("snippet") or result.get("description", "")
                
                if url:  # Only add results with valid URLs
                    results.append({
                        "title": title,
                        "url": url,
                        "content": content,
                        "score": 1.0,  # DuckDuckGo doesn't provide scores
                    })

            if result_count == 0:
                log_event(
                    logger,
                    "duckduckgo_search_no_results",
                    query=query,
                    message="DuckDuckGo search returned no results - this may be due to rate limiting or API changes",
                )
            elif len(results) == 0:
                log_event(
                    logger,
                    "duckduckgo_search_no_valid_urls",
                    query=query,
                    result_count=result_count,
                    message="DuckDuckGo search returned results but none had valid URLs",
                )

            log_event(
                logger,
                "duckduckgo_search_results",
                query=query,
                total_results=result_count,
                valid_results=len(results),
            )

            return results

        except Exception as exc:
            log_event(
                logger,
                "duckduckgo_search_error",
                query=query,
                error=str(exc),
                error_type=type(exc).__name__,
                exc_info=True,
            )
            # Return empty list instead of raising to allow graceful degradation
            return []

    def _search_tavily(self, query: str) -> List[Dict[str, Any]]:
        """Search using Tavily API."""
        try:
            import requests

            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self._tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": self.max_results,
            }

            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            results = []

            for result in data.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 1.0),
                })

            return results

        except Exception as exc:
            log_event(logger, "tavily_search_error", query=query, error=str(exc))
            raise

    def _search_serpapi(self, query: str) -> List[Dict[str, Any]]:
        """Search using SerpAPI."""
        try:
            from serpapi import GoogleSearch

            params = {
                "q": query,
                "api_key": self._serpapi_api_key,
                "num": self.max_results,
            }

            search = GoogleSearch(params)
            results_data = search.get_dict()

            results = []
            organic_results = results_data.get("organic_results", [])

            for result in organic_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "content": result.get("snippet", ""),
                    "score": 1.0,  # SerpAPI doesn't provide relevance scores
                })

            return results

        except ImportError:
            raise WebSearchError(
                "SerpAPI search requires 'google-search-results' package. "
                "Install with: pip install google-search-results"
            )
        except Exception as exc:
            log_event(logger, "serpapi_search_error", query=query, error=str(exc))
            raise

    def should_trigger_web_search(
        self,
        kb_results: List[Dict[str, Any]],
        query: str,
        min_score_threshold: float = 0.5,
    ) -> bool:
        """Determine if web search should be triggered based on KB results quality.

        Args:
            kb_results: Knowledge base search results.
            query: Original user query.
            min_score_threshold: Minimum average score threshold for KB results.
                                If average score is below this, trigger web search.
                                Defaults to 0.5.

        Returns:
            True if web search should be triggered, False otherwise.
        """
        # If no KB results, trigger web search
        if not kb_results:
            log_event(
                logger,
                "web_search_triggered",
                reason="no_kb_results",
                query=query,
            )
            return True

        # Calculate average score from KB results
        scores = []
        for result in kb_results:
            score = result.get("score", 0.0)
            if score is not None:
                scores.append(float(score))

        if not scores:
            # No scores available, check if results are meaningful
            # If results exist but have no scores, assume they might be relevant
            # Only trigger web search if we have very few results
            if len(kb_results) < 2:
                log_event(
                    logger,
                    "web_search_triggered",
                    reason="few_kb_results_no_scores",
                    query=query,
                    result_count=len(kb_results),
                )
                return True
            return False

        avg_score = sum(scores) / len(scores) if scores else 0.0

        # If average score is below threshold, trigger web search
        if avg_score < min_score_threshold:
            log_event(
                logger,
                "web_search_triggered",
                reason="low_kb_scores",
                query=query,
                avg_score=avg_score,
                threshold=min_score_threshold,
            )
            return True

        # Use LLM to assess if KB results are sufficient (optional)
        if self.llm_client and self.llm_client.is_available():
            try:
                # Create a summary of KB results
                kb_summary = "\n".join([
                    f"- {r.get('content', '')[:200]}..." 
                    for r in kb_results[:3]
                ])

                prompt = (
                    f"User query: '{query}'\n\n"
                    f"Knowledge base search results summary:\n{kb_summary}\n\n"
                    f"Based on the knowledge base results above, can the query be adequately answered? "
                    f"Respond with only 'yes' or 'no'."
                )

                if self.llm_client.provider == "anthropic":
                    try:
                        message = self.llm_client.anthropic.messages.create(
                            model=self.llm_client.settings.anthropic_model,
                            max_tokens=10,
                            temperature=0.0,
                            messages=[{"role": "user", "content": prompt}],
                        )
                        response = message.content[0].text.strip().lower()
                        sufficient = "yes" in response

                        if not sufficient:
                            log_event(
                                logger,
                                "web_search_triggered",
                                reason="llm_insufficient_kb",
                                query=query,
                            )
                        return not sufficient

                    except Exception as exc:
                        log_event(logger, "llm_sufficiency_check_error", error=str(exc))
                        # Fallback to score-based decision
                        pass

                elif self.llm_client.provider == "azure":
                    try:
                        messages = [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": prompt},
                        ]
                        response = self.llm_client.openai.ChatCompletion.create(
                            engine=self.llm_client.settings.azure_deployment_name,
                            messages=messages,
                            temperature=0.0,
                            max_tokens=10,
                        )
                        result = response["choices"][0]["message"]["content"].strip().lower()
                        sufficient = "yes" in result

                        if not sufficient:
                            log_event(
                                logger,
                                "web_search_triggered",
                                reason="llm_insufficient_kb",
                                query=query,
                            )
                        return not sufficient

                    except Exception as exc:
                        log_event(logger, "llm_sufficiency_check_error", error=str(exc))
                        # Fallback to score-based decision
                        pass

            except Exception as exc:
                log_event(logger, "llm_sufficiency_check_error", error=str(exc))
                # Fallback to score-based decision
                pass

        # Results are sufficient
        log_event(
            logger,
            "web_search_not_triggered",
            reason="sufficient_kb_results",
            query=query,
            avg_score=avg_score,
        )
        return False


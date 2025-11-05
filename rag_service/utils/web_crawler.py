"""
Web crawler utility for extracting content from URLs provided in queries.

This module provides functionality to:
- Extract URLs from user queries
- Validate URLs
- Whitelist-only domain filtering (only allowed domains are permitted)
- Crawl URLs and extract text content
- Respect robots.txt and rate limits

The crawler uses a strict whitelist approach: if ALLOWED_WEB_DOMAINS is not set
or empty, all domains are blocked. If set, only listed domains are allowed.
"""

from __future__ import annotations

import re
import time
from typing import List, Optional, TYPE_CHECKING
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logging import get_logger, log_event

if TYPE_CHECKING:
    from ..llm_client import LLMClient

logger = get_logger(__name__)



class WebCrawlerError(Exception):
    """Raised when an error occurs while crawling a URL."""


class WebCrawler:
    """Web crawler for extracting content from URLs."""

    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        timeout: int = 10,
        max_content_length: int = 1000000,  # 1MB
        user_agent: str = "RAG-Service-Bot/1.0 (+https://github.com/yourorg/rag-service)",
        llm_client: Optional["LLMClient"] = None,
    ) -> None:
        """Initialize the web crawler.

        Args:
            allowed_domains: List of allowed domains (e.g., ["docs.anthropic.com", "cloud.google.com"]).
                            If None or empty, all domains are blocked (whitelist-only mode).
                            If set, only listed domains are allowed.
            timeout: Request timeout in seconds. Defaults to 10.
            max_content_length: Maximum content length to download in bytes. Defaults to 1MB.
            user_agent: User agent string for requests. Defaults to a bot user agent.
            llm_client: Optional LLM client for relevance checking. If provided, will be used to
                       determine if URLs are relevant to the query before crawling.
        """
        self.allowed_domains = [d.lower().strip() for d in (allowed_domains or [])]
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.user_agent = user_agent
        self.llm_client = llm_client

        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({"User-Agent": self.user_agent})

        # Cache for robots.txt parsers
        self._robots_cache: dict[str, tuple[RobotFileParser, float]] = {}
        self._robots_cache_ttl = 3600  # 1 hour

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text.

        Args:
            text: Input text that may contain URLs.

        Returns:
            List of extracted URLs.
        """
        # Pattern to match URLs
        url_pattern = r"https?://[^\s<>\"{}|\\^`\[\]]+"
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        # Clean URLs (remove trailing punctuation)
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation that might not be part of URL
            url = url.rstrip(".,;:!?)")
            cleaned_urls.append(url)
        return cleaned_urls

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and parseable.

        Args:
            url: URL to validate.

        Returns:
            True if URL is valid, False otherwise.
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ["http", "https"], result.netloc])
        except Exception:
            return False

    def is_domain_allowed(self, url: str) -> bool:
        """Check if URL's domain is allowed (whitelist-only mode).

        Args:
            url: URL to check.

        Returns:
            True if domain is in allowed list, False otherwise.
            If allowed_domains is empty, returns False (all domains blocked).
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]

            # Remove www. prefix for comparison
            if domain.startswith("www."):
                domain = domain[4:]

            # If allowed_domains is empty, block everything (whitelist-only mode)
            if not self.allowed_domains:
                log_event(logger, "domain_blocked_no_whitelist", domain=domain, url=url)
                return False

            # Check if domain is in allowed list
            for allowed in self.allowed_domains:
                allowed_clean = allowed.lower().strip()
                if allowed_clean.startswith("www."):
                    allowed_clean = allowed_clean[4:]
                # Exact match
                if domain == allowed_clean:
                    return True
                # Subdomain match: google.github.io matches github.io (if github.io is in allowed list)
                if domain.endswith(f".{allowed_clean}"):
                    return True

            # Domain not in allowed list
            log_event(
                logger,
                "domain_not_allowed",
                domain=domain,
                url=url,
                allowed_domains=self.allowed_domains,
            )
            return False

        except Exception as exc:
            log_event(logger, "domain_check_error", url=url, error=str(exc))
            return False

    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check.

        Returns:
            True if URL can be fetched, False otherwise.
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            robots_url = urljoin(base_url, "/robots.txt")

            # Check cache
            current_time = time.time()
            if robots_url in self._robots_cache:
                rp, cache_time = self._robots_cache[robots_url]
                if current_time - cache_time < self._robots_cache_ttl:
                    return rp.can_fetch(self.user_agent, url)

            # Fetch robots.txt
            try:
                response = self.session.get(robots_url, timeout=self.timeout)
                if response.status_code == 200:
                    rp = RobotFileParser()
                    rp.set_url(robots_url)
                    rp.read()
                    self._robots_cache[robots_url] = (rp, current_time)
                    return rp.can_fetch(self.user_agent, url)
                else:
                    # If robots.txt doesn't exist, assume allowed
                    return True
            except Exception:
                # If we can't fetch robots.txt, assume allowed (fail open)
                return True

        except Exception as exc:
            log_event(logger, "robots_check_error", url=url, error=str(exc))
            # Fail open - assume allowed if we can't check
            return True

    def crawl(self, url: str) -> Optional[str]:
        """Crawl a URL and extract text content.

        Args:
            url: URL to crawl.

        Returns:
            Extracted text content, or None if crawling failed.
        """
        if not self.is_valid_url(url):
            log_event(logger, "crawl_invalid_url", url=url)
            return None

        if not self.is_domain_allowed(url):
            log_event(logger, "crawl_domain_blocked", url=url)
            return None

        if not self.can_fetch(url):
            log_event(logger, "crawl_robots_disallowed", url=url)
            return None

        try:
            log_event(logger, "crawl_start", url=url)
            response = self.session.get(url, timeout=self.timeout, stream=True)

            # Check content length
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > self.max_content_length:
                log_event(
                    logger,
                    "crawl_too_large",
                    url=url,
                    size=content_length,
                    max=self.max_content_length,
                )
                return None

            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "text/plain" not in content_type:
                log_event(logger, "crawl_unsupported_type", url=url, type=content_type)
                return None

            # Read content (with size limit)
            content = ""
            total_size = 0
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                total_size += len(chunk.encode("utf-8"))
                if total_size > self.max_content_length:
                    log_event(
                        logger,
                        "crawl_content_too_large",
                        url=url,
                        size=total_size,
                        max=self.max_content_length,
                    )
                    break
                content += chunk

            # Parse HTML
            if "text/html" in content_type:
                soup = BeautifulSoup(content, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Extract text
                text = soup.get_text(separator="\n", strip=True)

                # Clean up whitespace
                lines = [line.strip() for line in text.splitlines()]
                lines = [line for line in lines if line]
                text = "\n".join(lines)

                log_event(logger, "crawl_success", url=url, length=len(text))
                return text
            else:
                # Plain text
                log_event(logger, "crawl_success", url=url, length=len(content))
                return content

        except requests.exceptions.Timeout:
            log_event(logger, "crawl_timeout", url=url)
            return None
        except requests.exceptions.RequestException as exc:
            log_event(logger, "crawl_error", url=url, error=str(exc))
            return None
        except Exception as exc:
            log_event(logger, "crawl_unexpected_error", url=url, error=str(exc))
            return None

    def _is_query_only_urls(self, query: str, urls: List[str]) -> bool:
        """Check if query is mostly just URLs with minimal text.

        Args:
            query: User query text.
            urls: List of URLs found in the query.

        Returns:
            True if query is mostly URLs, False otherwise.
        """
        # Remove URLs from query to check remaining text
        query_without_urls = query
        for url in urls:
            query_without_urls = query_without_urls.replace(url, "")

        # Remove whitespace and common URL-related words
        query_without_urls = query_without_urls.strip()
        # Remove common URL-related phrases
        url_phrases = ["please", "can you", "summarize", "explain", "what is", "tell me about"]
        for phrase in url_phrases:
            query_without_urls = query_without_urls.replace(phrase, "")
        query_without_urls = query_without_urls.strip()

        # If remaining text is very short (less than 20 chars), consider it URL-only
        return len(query_without_urls) < 20

    def _is_url_relevant_to_query(self, url: str, query: str, all_urls: List[str]) -> bool:
        """Check if URL is relevant to the query using LLM or heuristics.

        Args:
            url: URL to check.
            query: User query text.
            all_urls: All URLs found in the query (for proper text extraction).

        Returns:
            True if URL is relevant, False otherwise.
        """
        # Remove all URLs from query to get the actual question/text
        query_text = query
        for q_url in all_urls:
            query_text = query_text.replace(q_url, "")

        # Use LLM for relevance checking if available
        if self.llm_client and self.llm_client.is_available():
            try:
                prompt = (
                    f"Given the user query: '{query_text.strip()}'\n\n"
                    f"And this URL: '{url}'\n\n"
                    f"Determine if the URL is likely to be relevant to answering the query. "
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
                        return "yes" in response
                    except Exception as exc:
                        log_event(logger, "llm_relevance_check_error", error=str(exc))
                        # Fallback to heuristic
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
                        return "yes" in result
                    except Exception as exc:
                        log_event(logger, "llm_relevance_check_error", error=str(exc))
                        # Fallback to heuristic
                        pass
            except Exception as exc:
                log_event(logger, "llm_relevance_check_error", error=str(exc))
                # Fallback to heuristic
                pass

        # Fallback: Simple heuristic-based relevance check
        # Extract domain and keywords from URL
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            url_keywords = set((domain + " " + path).split())
            # Remove common words
            url_keywords = {kw for kw in url_keywords if len(kw) > 3 and kw not in ["http", "https", "www", "com", "org"]}

            # Extract keywords from query text (with all URLs removed)
            query_words = set(re.findall(r"\b\w{4,}\b", query_text.lower()))

            # Check if there's any overlap or if query is very short (likely asking about URL)
            if len(query_words) == 0 or len(query_text.strip()) < 10:
                return True  # Likely asking about the URL itself

            # Check for keyword overlap
            overlap = url_keywords.intersection(query_words)
            if overlap:
                return True

            # Check if query contains words that suggest the URL is relevant
            relevance_indicators = ["this", "that", "here", "link", "page", "document", "site", "website"]
            if any(indicator in query_text.lower() for indicator in relevance_indicators):
                return True

            return False
        except Exception as exc:
            log_event(logger, "heuristic_relevance_check_error", error=str(exc))
            # If we can't determine, assume relevant (fail open)
            return True

    def extract_and_crawl(self, query: str) -> List[dict[str, str]]:
        """Extract URLs from query and crawl them if relevant.

        Args:
            query: User query that may contain URLs.

        Returns:
            List of dictionaries with 'url' and 'content' keys.
        """
        urls = self.extract_urls(query)
        log_event(logger, "urls_extracted", urls=urls, count=len(urls))
        if not urls:
            log_event(logger, "no_urls_found", query=query)
            return []

        # Check if query is mostly just URLs
        is_only_urls = self._is_query_only_urls(query, urls)

        results = []
        blocked_urls = []
        for url in urls:
            # Check domain before attempting crawl
            if not self.is_domain_allowed(url):
                blocked_urls.append(url)
                log_event(
                    logger,
                    "url_blocked_domain_not_allowed",
                    url=url,
                    is_only_urls=is_only_urls,
                )
                continue

            # Always crawl if query is only URLs (user wants summary/explanation)
            if is_only_urls:
                log_event(logger, "url_crawl_only_urls_mode", url=url)
                content = self.crawl(url)
                if content:
                    results.append({"url": url, "content": content})
                else:
                    log_event(logger, "url_crawl_failed", url=url, reason="crawl_returned_none")
            else:
                # Check relevance before crawling
                if self._is_url_relevant_to_query(url, query, urls):
                    log_event(logger, "url_crawl_relevant", url=url)
                    content = self.crawl(url)
                    if content:
                        results.append({"url": url, "content": content})
                    else:
                        log_event(logger, "url_crawl_failed", url=url, reason="crawl_returned_none")
                else:
                    log_event(logger, "url_crawl_not_relevant", url=url)

        if blocked_urls and is_only_urls:
            # Log warning when user provides only URLs but they're blocked
            log_event(
                logger,
                "urls_blocked_url_only_query",
                urls=blocked_urls,
                allowed_domains=self.allowed_domains,
                message="URLs blocked because domains not in ALLOWED_WEB_DOMAINS",
            )

        return results


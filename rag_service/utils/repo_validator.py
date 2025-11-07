"""
Repository access validator for GitLab and GitHub tokens.

This module validates user tokens against repositories to determine
which repositories a user can access. Used for filtering search results
to only show data from repositories the user has access to.
"""

from __future__ import annotations

import hashlib
import time
from typing import List, Set, Optional
from urllib.parse import urlparse

import requests
from .logging import get_logger, log_event

logger = get_logger(__name__)


class RepoValidationError(Exception):
    """Raised when repository validation fails."""


class RepoAccessValidator:
    """Validates GitLab/GitHub token access to repositories."""

    def __init__(self, cache_ttl: int = 300):
        """Initialize the validator.

        Args:
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes).
        """
        self.cache_ttl = cache_ttl
        # Cache: (token_hash, repo_url) -> (has_access, timestamp)
        self._cache: dict[tuple[str, str], tuple[bool, float]] = {}

    def _hash_token(self, token: str) -> str:
        """Hash token for cache key (never store tokens)."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _normalize_repo_url(self, repo_url: str) -> str:
        """Normalize repository URL to consistent format.

        Args:
            repo_url: Repository URL (various formats).

        Returns:
            Normalized URL (https://gitlab.com/group/project or https://github.com/owner/repo).
        """
        # Remove .git suffix
        url = repo_url.rstrip(".git")
        
        # Handle git@ format: git@gitlab.com:group/project.git -> https://gitlab.com/group/project
        if url.startswith("git@"):
            url = url.replace("git@", "https://").replace(":", "/", 1)
        
        # Ensure https://
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        
        return url

    def _detect_provider(self, repo_url: str) -> str:
        """Detect repository provider (gitlab or github).

        Args:
            repo_url: Repository URL.

        Returns:
            'gitlab' or 'github'.
        """
        url = self._normalize_repo_url(repo_url)
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        
        if "gitlab" in hostname:
            return "gitlab"
        elif "github" in hostname:
            return "github"
        else:
            # Default to gitlab for unknown hosts
            log_event(
                logger,
                "unknown_repo_provider",
                url=repo_url,
                hostname=hostname,
                default="gitlab",
            )
            return "gitlab"

    def _validate_gitlab_access(self, token: str, repo_url: str) -> bool:
        """Validate GitLab token access to repository.

        Args:
            token: GitLab personal access token.
            repo_url: Repository URL.

        Returns:
            True if token has access, False otherwise.
        """
        try:
            # Normalize URL and extract project path
            normalized_url = self._normalize_repo_url(repo_url)
            parsed = urlparse(normalized_url)
            
            # Extract project path (e.g., "group/project" from "https://gitlab.com/group/project")
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) < 2:
                log_event(
                    logger,
                    "gitlab_invalid_path",
                    url=repo_url,
                    path=parsed.path,
                )
                return False
            
            # Get GitLab instance (gitlab.com or self-hosted)
            gitlab_host = parsed.netloc
            project_path = "/".join(path_parts)
            
            # Use GitLab API to check access
            # GET /projects/:id or /projects/:path
            api_url = f"https://{gitlab_host}/api/v4/projects/{project_path.replace('/', '%2F')}"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                log_event(
                    logger,
                    "gitlab_access_validated",
                    url=repo_url,
                    project_path=project_path,
                    access=True,
                )
                return True
            elif response.status_code == 404:
                log_event(
                    logger,
                    "gitlab_access_denied",
                    url=repo_url,
                    project_path=project_path,
                    reason="not_found_or_no_access",
                )
                return False
            else:
                log_event(
                    logger,
                    "gitlab_access_error",
                    url=repo_url,
                    status_code=response.status_code,
                    error=response.text[:200],
                )
                return False

        except requests.exceptions.RequestException as exc:
            log_event(
                logger,
                "gitlab_validation_error",
                url=repo_url,
                error=str(exc),
                exc_info=True,
            )
            return False
        except Exception as exc:
            log_event(
                logger,
                "gitlab_validation_unexpected_error",
                url=repo_url,
                error=str(exc),
                exc_info=True,
            )
            return False

    def _validate_github_access(self, token: str, repo_url: str) -> bool:
        """Validate GitHub token access to repository.

        Args:
            token: GitHub personal access token.
            repo_url: Repository URL.

        Returns:
            True if token has access, False otherwise.
        """
        try:
            # Normalize URL and extract owner/repo
            normalized_url = self._normalize_repo_url(repo_url)
            parsed = urlparse(normalized_url)
            
            # Extract owner/repo (e.g., "owner/repo" from "https://github.com/owner/repo")
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) < 2:
                log_event(
                    logger,
                    "github_invalid_path",
                    url=repo_url,
                    path=parsed.path,
                )
                return False
            
            owner, repo = path_parts[0], path_parts[1]
            
            # Use GitHub API to check access
            # GET /repos/:owner/:repo
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
            }
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                log_event(
                    logger,
                    "github_access_validated",
                    url=repo_url,
                    owner=owner,
                    repo=repo,
                    access=True,
                )
                return True
            elif response.status_code == 404:
                log_event(
                    logger,
                    "github_access_denied",
                    url=repo_url,
                    owner=owner,
                    repo=repo,
                    reason="not_found_or_no_access",
                )
                return False
            else:
                log_event(
                    logger,
                    "github_access_error",
                    url=repo_url,
                    status_code=response.status_code,
                    error=response.text[:200],
                )
                return False

        except requests.exceptions.RequestException as exc:
            log_event(
                logger,
                "github_validation_error",
                url=repo_url,
                error=str(exc),
                exc_info=True,
            )
            return False
        except Exception as exc:
            log_event(
                logger,
                "github_validation_unexpected_error",
                url=repo_url,
                error=str(exc),
                exc_info=True,
            )
            return False

    def validate_repo_access(self, token: str, repo_url: str) -> bool:
        """Validate token access to a repository (with caching).

        Args:
            token: GitLab or GitHub personal access token.
            repo_url: Repository URL.

        Returns:
            True if token has access, False otherwise.
        """
        if not token or not repo_url:
            return False

        token_hash = self._hash_token(token)
        normalized_url = self._normalize_repo_url(repo_url)
        cache_key = (token_hash, normalized_url)

        # Check cache
        if cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                log_event(
                    logger,
                    "repo_access_cache_hit",
                    url=normalized_url,
                    cached_result=cached_result,
                )
                return cached_result

        # Validate access
        provider = self._detect_provider(normalized_url)
        
        if provider == "gitlab":
            has_access = self._validate_gitlab_access(token, normalized_url)
        elif provider == "github":
            has_access = self._validate_github_access(token, normalized_url)
        else:
            log_event(
                logger,
                "unknown_provider",
                url=normalized_url,
                provider=provider,
            )
            has_access = False

        # Cache result
        self._cache[cache_key] = (has_access, time.time())
        
        log_event(
            logger,
            "repo_access_validated",
            url=normalized_url,
            provider=provider,
            has_access=has_access,
            cached=False,
        )

        return has_access

    def get_accessible_repos(
        self, token: str, repo_urls: List[str]
    ) -> Set[str]:
        """Get set of accessible repository URLs for a token.

        Args:
            token: GitLab or GitHub personal access token.
            repo_urls: List of repository URLs to check.

        Returns:
            Set of repository URLs the token can access.
        """
        if not token or not repo_urls:
            return set()

        accessible: Set[str] = set()
        
        log_event(
            logger,
            "repo_access_validation_start",
            token_hash=self._hash_token(token),
            total_repos=len(repo_urls),
        )

        for repo_url in repo_urls:
            try:
                if self.validate_repo_access(token, repo_url):
                    accessible.add(self._normalize_repo_url(repo_url))
            except Exception as exc:
                log_event(
                    logger,
                    "repo_access_validation_error",
                    url=repo_url,
                    error=str(exc),
                )
                # Continue with other repos even if one fails
                continue

        log_event(
            logger,
            "repo_access_validation_complete",
            token_hash=self._hash_token(token),
            total_repos=len(repo_urls),
            accessible_repos=len(accessible),
        )

        return accessible

    def get_repo_info(self, token: str, repo_url: str) -> Optional[dict]:
        """Get repository information (ID, path, etc.) using token.

        Args:
            token: GitLab or GitHub personal access token.
            repo_url: Repository URL.

        Returns:
            Dictionary with repo_id, repo_url, repo_full_path, or None if access denied.
        """
        provider = self._detect_provider(repo_url)
        normalized_url = self._normalize_repo_url(repo_url)
        
        try:
            if provider == "gitlab":
                return self._get_gitlab_repo_info(token, normalized_url)
            elif provider == "github":
                return self._get_github_repo_info(token, normalized_url)
        except Exception as exc:
            log_event(
                logger,
                "repo_info_error",
                url=normalized_url,
                provider=provider,
                error=str(exc),
            )
            return None

    def _get_gitlab_repo_info(self, token: str, repo_url: str) -> Optional[dict]:
        """Get GitLab repository information."""
        try:
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) < 2:
                return None
            
            project_path = "/".join(path_parts)
            gitlab_host = parsed.netloc
            api_url = f"https://{gitlab_host}/api/v4/projects/{project_path.replace('/', '%2F')}"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "repo_id": str(data.get("id", "")),
                    "repo_url": repo_url,
                    "repo_full_path": data.get("path_with_namespace", project_path),
                    "provider": "gitlab",
                }
            return None
        except Exception as exc:
            log_event(
                logger,
                "gitlab_repo_info_error",
                url=repo_url,
                error=str(exc),
            )
            return None

    def _get_github_repo_info(self, token: str, repo_url: str) -> Optional[dict]:
        """Get GitHub repository information."""
        try:
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) < 2:
                return None
            
            owner, repo = path_parts[0], path_parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
            }
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "repo_id": str(data.get("id", "")),
                    "repo_url": repo_url,
                    "repo_full_path": f"{owner}/{repo}",
                    "provider": "github",
                }
            return None
        except Exception as exc:
            log_event(
                logger,
                "github_repo_info_error",
                url=repo_url,
                error=str(exc),
            )
            return None


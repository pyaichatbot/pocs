"""
Utilities for fetching files from a GitLab repository.

To support indexing of a GitLab project the service needs to clone the
repository using an access token and extract markdown files.  This
module encapsulates that logic.  In the future it could be extended
to use the GitLab REST API instead of cloning, or to handle other
document formats.

Note: network access is required for cloning.  In restricted
environments you may need to provide the repository in another way.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Tuple

from .md_parser import load_markdown_recursive, read_file


class GitLabError(Exception):
    """Raised when an error occurs while interacting with GitLab."""


def clone_repo(
    repo_url: str,
    token: str,
    branch: str | None = None,
    dest_dir: str | None = None,
) -> str:
    """Clone a GitLab repository using a personal access token.

    The repository URL should be the HTTPS URL to the GitLab project
    (e.g. ``https://gitlab.com/namespace/project.git``).  The token
    must have at least ``read_repository`` scope.  The repository is
    cloned into a temporary directory unless ``dest_dir`` is provided.

    Args:
        repo_url: GitLab repository URL ending with ``.git``.
        token: Personal access token with appropriate permissions.
        branch: Optional branch name to checkout.  If omitted the
            default branch is used.
        dest_dir: Optional directory into which to clone the repo.
    Returns:
        The path of the cloned repository on disk.
    Raises:
        GitLabError: If the clone fails.
    """
    target_dir = dest_dir or tempfile.mkdtemp(prefix="gitlab_repo_")
    # build clone URL with token
    # Git uses the token as username with OAuth2: https://oauth2:<token>@gitlab.com/...git
    if repo_url.startswith("https://"):
        url_with_token = repo_url.replace(
            "https://",
            f"https://oauth2:{token}@",
            1,
        )
    else:
        # unknown protocol
        raise GitLabError("Repository URL must start with https://")

    clone_args = ["git", "clone", url_with_token, target_dir]
    if branch:
        clone_args.extend(["--branch", branch])
    try:
        subprocess.run(
            clone_args,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        # Clean up on failure
        if dest_dir is None:
            shutil.rmtree(target_dir, ignore_errors=True)
        raise GitLabError(
            f"Failed to clone repository: {exc.stderr.strip() or exc.stdout.strip()}"
        )
    return target_dir


def extract_markdown_files(repo_path: str) -> List[Tuple[str, str]]:
    """Return a list of (relative_path, content) for markdown files in a repo.

    Args:
        repo_path: Local path to the cloned repository.
    Returns:
        A list of tuples where the first element is the relative path to
        the markdown file within the repository and the second element
        is its text content.
    """
    md_paths = load_markdown_recursive(repo_path)
    results: List[Tuple[str, str]] = []
    for path in md_paths:
        # Determine relative path within repository
        rel = os.path.relpath(path, repo_path)
        text = read_file(path)
        results.append((rel, text))
    return results
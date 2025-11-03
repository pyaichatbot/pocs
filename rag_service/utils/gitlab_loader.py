"""
Utilities for fetching files from a GitLab repository.

To support indexing of a GitLab project the service needs to clone the
repository using an access token and extract markdown and PDF files.  This
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

from .document_loader import load_documents_recursive


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
    """Return a list of (relative_path, content) for markdown and PDF files in a repo.

    Extracts both markdown (.md, .markdown) and PDF (.pdf) files from the
    repository. PDF files are parsed using pdfplumber to extract text content.

    Args:
        repo_path: Local path to the cloned repository.
    Returns:
        A list of tuples where the first element is the relative path to
        the document file within the repository and the second element is
        its text content.
    """
    return load_documents_recursive(
        repo_path, include_markdown=True, include_pdf=True
    )
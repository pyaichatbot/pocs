"""
Helpers for loading and splitting markdown documents.

These functions provide simple ways to walk a directory tree to find
markdown files and split the contents of a markdown file into chunks
that are roughly equal in size.  Splitting is necessary because large
language models have context length limits; providing the entire
document as context would be inefficient.

The splitter implemented here is intentionally simple: it groups
paragraphs into chunks until a maximum number of words is reached.
This can be improved later using a dedicated tokenizer if needed.
"""

from __future__ import annotations

import os
from typing import List


def load_markdown_recursive(root: str) -> List[str]:
    """Return a list of markdown file paths under the given root.

    The function descends into all subdirectories and collects files
    ending with ``.md`` or ``.markdown``.  Non‑ASCII filenames are
    supported.

    Args:
        root: Base directory to search.
    Returns:
        A list of absolute file paths.
    """
    md_files: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.lower().endswith((".md", ".markdown")):
                md_files.append(os.path.join(dirpath, fname))
    return md_files


def read_file(path: str) -> str:
    """Return the contents of a text file decoded as UTF‑8.

    Files are read with errors ignored to avoid exceptions on
    unexpected encoding issues.
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def split_markdown(text: str, max_words: int = 300, overlap: int = 50) -> List[str]:
    """Split markdown text into chunks of roughly ``max_words`` words.

    The algorithm splits the text into paragraphs on blank lines and
    accumulates paragraphs until the running total exceeds ``max_words``.
    When a chunk is emitted the last ``overlap`` words of the previous
    chunk are prepended to the next chunk to provide some context
    overlap.  This helps reduce the likelihood of losing important
    information at boundaries.

    Args:
        text: Markdown document as a single string.
        max_words: Target number of words per chunk.
        overlap: Number of words to repeat between consecutive chunks.
    Returns:
        A list of text chunks.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current_words: List[str] = []
    for para in paragraphs:
        words = para.split()
        if not words:
            continue
        # If adding this paragraph would exceed the maximum, emit a chunk
        if len(current_words) + len(words) > max_words:
            if current_words:
                chunks.append(" ".join(current_words))
                # prepare overlap for next chunk
                current_words = current_words[-overlap:] + words
            else:
                # single paragraph longer than max_words
                chunks.append(" ".join(words))
                current_words = []
        else:
            current_words.extend(words)
    if current_words:
        chunks.append(" ".join(current_words))
    return chunks
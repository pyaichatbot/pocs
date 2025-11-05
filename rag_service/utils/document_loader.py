"""
Generic document loader for supporting multiple file types.

This module provides a unified interface for loading and processing
different document types (markdown, PDF, etc.) following the same
standards and chunking strategies.
"""

from __future__ import annotations

import os
from typing import List, Tuple

from .md_parser import (
    load_markdown_recursive,
    read_file as read_markdown_file,
    split_markdown,
)
from .pdf_parser import (
    PDFParseError,
    extract_text_from_pdf,
    load_pdf_recursive,
    split_pdf_text,
)
from .word_parser import (
    WordParseError,
    extract_text_from_word,
    load_word_recursive,
    split_word_text,
)
from .logging import get_logger, log_event

logger = get_logger(__name__)


class DocumentLoaderError(Exception):
    """Raised when an error occurs while loading documents."""


def load_documents_recursive(
    root: str,
    include_markdown: bool = True,
    include_pdf: bool = True,
    include_word: bool = True,
) -> List[Tuple[str, str]]:
    """Return a list of (relative_path, content) tuples for supported documents.

    Recursively scans the directory for markdown, PDF, and Word files, extracts
    their content, and returns them with their relative paths. This function
    handles multiple file types using the same interface.

    Args:
        root: Base directory to search.
        include_markdown: Whether to include markdown files (default: True).
        include_pdf: Whether to include PDF files (default: True).
        include_word: Whether to include Word documents (default: True).
    Returns:
        A list of tuples where the first element is the relative path to
        the file within the root directory and the second element is its
        text content.
    Raises:
        ValueError: If the root directory doesn't exist or is not a directory.
        DocumentLoaderError: If there are critical errors during loading.
    """
    if not os.path.exists(root):
        raise ValueError(f"Directory does not exist: {root}")
    if not os.path.isdir(root):
        raise ValueError(f"Path is not a directory: {root}")

    abs_root = os.path.abspath(root)
    documents: List[Tuple[str, str]] = []
    errors: List[str] = []

    # Load markdown files
    if include_markdown:
        try:
            md_paths = load_markdown_recursive(abs_root)
            for md_path in md_paths:
                try:
                    rel_path = os.path.relpath(md_path, abs_root)
                    content = read_markdown_file(md_path)
                    documents.append((rel_path, content))
                except Exception as exc:
                    error_msg = f"Failed to load markdown {md_path}: {exc}"
                    errors.append(error_msg)
                    log_event(logger, "document_load_error", file=md_path, error=str(exc))
        except Exception as exc:
            log_event(
                logger,
                "document_load_error",
                file_type="markdown",
                error=str(exc),
            )
            errors.append(f"Failed to load markdown files: {exc}")

    # Load PDF files
    if include_pdf:
        try:
            pdf_paths = load_pdf_recursive(abs_root)
            for pdf_path in pdf_paths:
                try:
                    rel_path = os.path.relpath(pdf_path, abs_root)
                    content = extract_text_from_pdf(pdf_path)
                    if content:  # Only add if content was extracted
                        documents.append((rel_path, content))
                except PDFParseError as exc:
                    error_msg = f"Failed to parse PDF {pdf_path}: {exc}"
                    errors.append(error_msg)
                    log_event(logger, "document_load_error", file=pdf_path, error=str(exc))
                except Exception as exc:
                    error_msg = f"Unexpected error loading PDF {pdf_path}: {exc}"
                    errors.append(error_msg)
                    log_event(logger, "document_load_error", file=pdf_path, error=str(exc))
        except Exception as exc:
            log_event(
                logger,
                "document_load_error",
                file_type="pdf",
                error=str(exc),
            )
            errors.append(f"Failed to load PDF files: {exc}")

    # Load Word documents
    if include_word:
        try:
            word_paths = load_word_recursive(abs_root)
            for word_path in word_paths:
                try:
                    rel_path = os.path.relpath(word_path, abs_root)
                    content = extract_text_from_word(word_path)
                    if content:  # Only add if content was extracted
                        documents.append((rel_path, content))
                except WordParseError as exc:
                    error_msg = f"Failed to parse Word document {word_path}: {exc}"
                    errors.append(error_msg)
                    log_event(logger, "document_load_error", file=word_path, error=str(exc))
                except Exception as exc:
                    error_msg = f"Unexpected error loading Word document {word_path}: {exc}"
                    errors.append(error_msg)
                    log_event(logger, "document_load_error", file=word_path, error=str(exc))
        except Exception as exc:
            log_event(
                logger,
                "document_load_error",
                file_type="word",
                error=str(exc),
            )
            errors.append(f"Failed to load Word documents: {exc}")

    # Log summary
    log_event(
        logger,
        "document_load_complete",
        total=len(documents),
        markdown_included=include_markdown,
        pdf_included=include_pdf,
        word_included=include_word,
        errors=len(errors),
    )

    # If we have critical errors (no documents loaded at all) and errors exist, raise
    if not documents and errors:
        raise DocumentLoaderError(
            f"Failed to load any documents. Errors: {'; '.join(errors[:5])}"
        )

    return documents


def split_document_text(
    content: str, file_path: str, max_words: int = 300, overlap: int = 50
) -> List[str]:
    """Split document text into chunks based on file type.

    Automatically determines the chunking strategy based on file extension.
    For PDF files, uses PDF-specific chunking. For Word documents, uses Word-specific
    chunking. For markdown and other text files, uses markdown chunking.

    Args:
        content: Document text content.
        file_path: Path to the document (used to determine file type).
        max_words: Target number of words per chunk.
        overlap: Number of words to repeat between consecutive chunks.
    Returns:
        A list of text chunks.
    """
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == ".pdf":
        return split_pdf_text(content, max_words=max_words, overlap=overlap)
    elif file_ext == ".docx":
        return split_word_text(content, max_words=max_words, overlap=overlap)
    else:
        # Default to markdown-style chunking for markdown and other text files
        return split_markdown(content, max_words=max_words, overlap=overlap)


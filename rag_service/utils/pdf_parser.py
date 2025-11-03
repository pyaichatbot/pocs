"""
Helpers for loading and parsing PDF documents.

This module provides utilities for extracting text from PDF files and
splitting them into chunks. PDF processing uses pdfplumber which is
license-safe and production-ready.

The splitter follows the same approach as markdown: it groups text into
chunks until a maximum number of words is reached, with overlap between
chunks to maintain context.
"""

from __future__ import annotations

import os
from typing import List

from ..utils.logging import get_logger

logger = get_logger(__name__)

try:
    import pdfplumber
    _pdfplumber_available = True
except ImportError:
    pdfplumber = None  # type: ignore
    _pdfplumber_available = False
    _import_error = ImportError(
        "pdfplumber is not installed. Install it with: pip install pdfplumber"
    )


class PDFParseError(Exception):
    """Raised when an error occurs while parsing a PDF file."""


def load_pdf_recursive(root: str) -> List[str]:
    """Return a list of PDF file paths under the given root.

    The function descends into all subdirectories and collects files
    ending with ``.pdf``. Non-ASCII filenames are supported.

    Args:
        root: Base directory to search.
    Returns:
        A list of absolute file paths.
    Raises:
        ValueError: If the root directory doesn't exist.
    """
    if not os.path.exists(root):
        raise ValueError(f"Directory does not exist: {root}")
    if not os.path.isdir(root):
        raise ValueError(f"Path is not a directory: {root}")

    pdf_files: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(dirpath, fname))
    return pdf_files


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file.

    Uses pdfplumber to extract text from all pages of the PDF.
    Handles errors gracefully and logs issues for troubleshooting.

    Args:
        pdf_path: Path to the PDF file.
    Returns:
        Extracted text content as a single string.
    Raises:
        PDFParseError: If the PDF cannot be read or parsed.
        ImportError: If pdfplumber is not installed.
    """
    if not _pdfplumber_available or pdfplumber is None:
        raise ImportError(
            "pdfplumber is not installed. Install it with: pip install pdfplumber"
        )

    if not os.path.exists(pdf_path):
        raise PDFParseError(f"PDF file does not exist: {pdf_path}")

    try:
        text_parts: List[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        # Clean up extracted text
                        cleaned_text = page_text.strip()
                        text_parts.append(cleaned_text)
                except Exception as page_exc:
                    logger.warning(
                        f"Failed to extract text from page {page_num} of {pdf_path}: {page_exc}"
                    )
                    # Continue processing other pages even if one fails

        if not text_parts:
            logger.warning(f"No text extracted from PDF: {pdf_path}")
            return ""

        # Join pages with double newline (similar to markdown paragraph separation)
        full_text = "\n\n".join(text_parts)
        return full_text

    except Exception as exc:
        logger.error(f"Failed to parse PDF {pdf_path}: {exc}")
        raise PDFParseError(f"Failed to parse PDF {pdf_path}: {exc}") from exc


def split_pdf_text(text: str, max_words: int = 300, overlap: int = 50) -> List[str]:
    """Split PDF-extracted text into chunks of roughly ``max_words`` words.

    The algorithm splits the text into paragraphs on blank lines and
    accumulates paragraphs until the running total exceeds ``max_words``.
    When a chunk is emitted, the last ``overlap`` words of the previous
    chunk are prepended to the next chunk to provide context overlap.

    Args:
        text: PDF-extracted text as a single string.
        max_words: Target number of words per chunk.
        overlap: Number of words to repeat between consecutive chunks.
    Returns:
        A list of text chunks.
    """
    if not text.strip():
        return []

    # Split into paragraphs (similar to markdown processing)
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
                # Prepare overlap for next chunk
                current_words = current_words[-overlap:] + words
            else:
                # Single paragraph longer than max_words - split it
                chunks.append(" ".join(words))
                current_words = []
        else:
            current_words.extend(words)

    # Emit remaining words
    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


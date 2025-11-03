"""
RAG Service package initialization.

This package provides a simple retrieval‑augmented generation (RAG) API
built around Pixeltable.  The service is designed to be document type
agnostic and supports indexing of GitLab repositories containing
markdown files.  Additional document types can be added later
without modifying the API surface by extending the ingestion logic.

The implementation follows SOLID principles by separating concerns
into independent layers:

* ``repositories`` contain database abstractions.  They hide the
  details of how and where documents are stored and how similarity
  search is performed.
* ``services`` implement business logic such as ingesting a GitLab
  project or performing a retrieval and generation task.
* ``utils`` provide helper functions for interacting with external
  systems (GitLab, markdown parsing) and logging.
* ``api`` exposes a FastAPI application with the HTTP endpoints
  ``/index``, ``/delta-index`` and ``/search``.

The goal of this design is to make it easy to swap out the underlying
storage (e.g. move from Pixeltable to pgvector or another vector
database) and to extend the ingestion pipeline to new document
formats.
"""

# Expose the FastAPI application at the package level
from .api import app  # noqa: F401
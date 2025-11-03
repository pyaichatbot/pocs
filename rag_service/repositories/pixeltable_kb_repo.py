"""
Pixeltable implementation of the knowledge base repository.

This module provides a concrete implementation of ``BaseKnowledgeBaseRepository``
using Pixeltable for storage and semantic search.  The table schema is
defined on initialisation if it does not already exist.  An embedding
index is added on the ``content`` column to enable similarity search.

If Pixeltable is not installed, initialising this repository will
raise an ImportError.  Ensure you have installed Pixeltable and its
dependencies (e.g. ``pip install pixeltable sentence-transformers``)
before using this class.

Note: Keyword search processes documents in-memory for lexical scoring.
For very large datasets (>100K documents), consider implementing
indexed full-text search or using Pixeltable's full-text search features.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .base_kb_repo import BaseKnowledgeBaseRepository
from ..config import Settings
from ..utils.logging import get_logger

try:
    import pixeltable as pxt  # type: ignore
    from pixeltable.functions.huggingface import sentence_transformer  # type: ignore
except ImportError as exc:
    pxt = None  # type: ignore
    sentence_transformer = None  # type: ignore
    _import_error = exc


class PixeltableKnowledgeBaseRepository(BaseKnowledgeBaseRepository):
    """Knowledge base repository backed by Pixeltable."""

    def __init__(self, settings: Settings, table_name: str = "kb.documents"):
        if pxt is None:
            raise ImportError(
                "Pixeltable is not installed. Please install pixeltable and its"
                " dependencies (e.g. pip install pixeltable sentence-transformers)"
            ) from _import_error
        self.logger = get_logger(__name__)
        self.settings = settings
        self.table_name = table_name
        # Connect to Pixeltable and create media directory if required
        # The connection string defines where metadata is stored
        try:
            self.conn = pxt.connect(settings.pixeltable_connection)
        except Exception as exc:
            self.logger.error(
                "Failed to connect to Pixeltable at %s: %s",
                settings.pixeltable_connection,
                exc,
            )
            raise ConnectionError(
                f"Failed to connect to Pixeltable: {exc}"
            ) from exc
        # Ensure the namespace (directory) exists
        namespace = table_name.split(".")[0]
        # create_dir will be a no‑op if the directory already exists
        pxt.create_dir(namespace)
        # Obtain or create the table
        try:
            self.table = pxt.get_table(table_name)
            self.logger.info("Connected to existing Pixeltable table %s", table_name)
        except (AttributeError, KeyError, ValueError):
            # Table doesn't exist, create it
            # Define schema: doc_id+chunk_id uniquely identify a chunk; path is
            # the original file path; content holds the text; metadata holds
            # arbitrary JSON such as file hash or last modified timestamp.
            schema = {
                "doc_id": pxt.String,
                "chunk_id": pxt.String,
                "path": pxt.String,
                "content": pxt.String,
                "metadata": pxt.Json,
            }
            self.table = pxt.create_table(table_name, schema)
            # Add embedding index on content column if not present.
            # Embedding model is configurable via settings.
            if sentence_transformer is None:
                raise ImportError(
                    "sentence-transformers integration not available."
                    " Install sentence-transformers to create embedding indexes."
                )
            embed_model = sentence_transformer.using(model_id=settings.embedding_model_id)
            self.table.add_embedding_index(column="content", string_embed=embed_model)
            self.logger.info(
                "Created Pixeltable table %s with embedding index using model %s",
                table_name,
                settings.embedding_model_id,
            )
        else:
            # Table exists - check if embedding index exists
            # If not, add it (for tables created before index support)
            try:
                # Try to use similarity to check if index exists
                # This will raise an error if index doesn't exist
                _ = self.table.content.similarity("test")
            except (AttributeError, TypeError, Exception):
                # Index doesn't exist, add it
                self.logger.info(
                    "Adding embedding index to existing table %s", table_name
                )
                if sentence_transformer is None:
                    raise ImportError(
                        "sentence-transformers integration not available."
                        " Install sentence-transformers to create embedding indexes."
                    )
                embed_model = sentence_transformer.using(model_id=settings.embedding_model_id)
                self.table.add_embedding_index(column="content", string_embed=embed_model)
                self.logger.info(
                    "Added embedding index to table %s using model %s",
                    table_name,
                    settings.embedding_model_id,
                )

    def _row_exists(self, doc_id: str, chunk_id: str) -> bool:
        """Return True if a row with the given composite key exists."""
        try:
            result = (
                self.table.where(
                    (self.table.doc_id == doc_id) & (self.table.chunk_id == chunk_id)
                ).limit(1).collect()
            )
            return len(result) > 0
        except (AttributeError, KeyError, ValueError) as exc:
            # Table or column doesn't exist
            self.logger.debug("Row existence check failed (expected for new tables): %s", exc)
            return False
        except Exception as exc:
            self.logger.error("Failed to check row existence: %s", exc)
            raise

    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Insert or update documents in the Pixeltable.

        Args:
            documents: List of dicts with keys: doc_id, chunk_id, path,
                content, metadata.
        """
        # Use batch insertion and conditional updates
        inserts: List[Dict[str, Any]] = []
        updates: List[Dict[str, Any]] = []
        for doc in documents:
            doc_id = doc["doc_id"]
            chunk_id = doc["chunk_id"]
            if self._row_exists(doc_id, chunk_id):
                updates.append(doc)
            else:
                inserts.append(doc)
        # Perform inserts
        if inserts:
            try:
                self.table.insert(inserts)
            except Exception as exc:
                self.logger.error(f"Failed to insert documents: {exc}")
                raise
        # Perform updates one by one using conditional where clause
        for doc in updates:
            try:
                cond = (self.table.doc_id == doc["doc_id"]) & (self.table.chunk_id == doc["chunk_id"])
                self.table.where(cond).update({
                    "path": doc["path"],
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                })
            except Exception as exc:
                self.logger.error(f"Failed to update document {doc['doc_id']}:{doc['chunk_id']}: {exc}")
                raise

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Return the top k documents most similar to the query using embeddings."""
        try:
            sim = self.table.content.similarity(query)
            results = (
                self.table.order_by(sim, asc=False)
                .select(
                    self.table.doc_id,
                    self.table.chunk_id,
                    self.table.path,
                    self.table.content,
                    self.table.metadata,
                    score=sim,
                )
                .limit(k)
                .collect()
            )
            return [dict(row) for row in results]
        except Exception as exc:
            self.logger.error(f"Similarity search failed: {exc}")
            return []

    def keyword_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform a naive keyword search on the content field."""
        # Fetch up to 1000 rows; for small corpora this will capture all
        try:
            all_rows = (
                self.table.select(
                    self.table.doc_id,
                    self.table.chunk_id,
                    self.table.path,
                    self.table.content,
                    self.table.metadata,
                ).limit(1000).collect()
            )
        except Exception as exc:
            self.logger.error(f"Keyword search failed to fetch rows: {exc}")
            return []
        # Compute a simple score: count of query words in the content
        tokens = [w.lower() for w in query.split() if w.strip()]
        scored: List[Dict[str, Any]] = []
        for row in all_rows:
            text = (row["content"] or "").lower()
            score = sum(text.count(tok) for tok in tokens)
            if score > 0:
                record = dict(row)
                record["kw_score"] = score
                scored.append(record)
        # Sort by descending score and return top k
        scored.sort(key=lambda x: x["kw_score"], reverse=True)
        return scored[:k]

    # Additional helper not part of the base interface
    def list_all_documents(self) -> List[Dict[str, Any]]:
        """Return all documents in the table.

        This is used by the ingestion service to determine which
        documents have already been indexed and to support delta
        indexing.  Returns dictionaries with keys ``doc_id``,
        ``chunk_id``, ``path``, ``content`` and ``metadata``.
        """
        try:
            rows = (
                self.table.select(
                    self.table.doc_id,
                    self.table.chunk_id,
                    self.table.path,
                    self.table.content,
                    self.table.metadata,
                ).collect()
            )
            return [dict(r) for r in rows]
        except Exception as exc:
            self.logger.error(f"Failed to list documents: {exc}")
            return []

    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete all chunks belonging to the specified document IDs."""
        if not doc_ids:
            return
        try:
            # Build condition: doc_id is in list
            cond = self.table.doc_id.isin(doc_ids)
            self.table.where(cond).delete()
        except Exception as exc:
            self.logger.error(f"Failed to delete documents {doc_ids}: {exc}")
            raise
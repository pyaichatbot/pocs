"""
ChromaDB implementation of the knowledge base repository.

This module provides a production-ready implementation using ChromaDB for
storage and semantic search. ChromaDB is an open-source vector database
designed for AI applications with built-in support for embeddings.

Features:
- Semantic similarity search
- Keyword search with metadata filtering
- Automatic embedding generation
- Persistence support
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base_kb_repo import BaseKnowledgeBaseRepository
from ..config import Settings
from ..utils.logging import get_logger

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings as ChromaSettings  # type: ignore
    from chromadb.utils import embedding_functions  # type: ignore
except ImportError as exc:
    chromadb = None  # type: ignore
    ChromaSettings = None  # type: ignore
    embedding_functions = None  # type: ignore
    _import_error = exc


class ChromaDBKnowledgeBaseRepository(BaseKnowledgeBaseRepository):
    """Knowledge base repository backed by ChromaDB."""

    def __init__(self, settings: Settings, collection_name: str = "kb_documents"):
        if chromadb is None or embedding_functions is None:
            raise ImportError(
                "ChromaDB is not installed. Please install chromadb: pip install chromadb"
            ) from _import_error

        self.logger = get_logger(__name__)
        self.settings = settings
        self.collection_name = collection_name

        # Get ChromaDB configuration from settings or use defaults
        chroma_path = getattr(settings, "chromadb_path", "./chroma_db")
        chroma_host = getattr(settings, "chromadb_host", None)
        chroma_port = getattr(settings, "chromadb_port", None)

        # Initialize ChromaDB client
        try:
            if chroma_host and chroma_port:
                # Connect to remote ChromaDB server
                self.client = chromadb.HttpClient(
                    host=chroma_host,
                    port=chroma_port,
                )
            else:
                # Use local persistent client
                self.client = chromadb.PersistentClient(
                    path=chroma_path,
                )
        except Exception as exc:
            self.logger.error("Failed to connect to ChromaDB: %s", exc)
            raise ConnectionError(f"Failed to connect to ChromaDB: {exc}") from exc

        # Create or get collection with embedding function
        try:
            # Use sentence transformers for embeddings (matches Pixeltable default)
            embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=settings.embedding_model_id
            )

            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_fn,
                metadata={"description": "Knowledge base documents"},
            )
            self.logger.info(
                "Connected to ChromaDB collection %s with embedding model %s",
                collection_name,
                settings.embedding_model_id,
            )
        except Exception as exc:
            self.logger.error("Failed to create/get ChromaDB collection: %s", exc)
            raise

    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Insert or update documents in ChromaDB.

        Args:
            documents: List of dicts with keys: doc_id, chunk_id, path,
                content, metadata.
        """
        try:
            # Prepare data for ChromaDB
            ids: List[str] = []
            contents: List[str] = []
            metadatas: List[Dict[str, Any]] = []

            for doc in documents:
                # Create unique ID from doc_id and chunk_id
                unique_id = f"{doc['doc_id']}::{doc['chunk_id']}"
                ids.append(unique_id)
                contents.append(str(doc["content"]))
                # ChromaDB metadata must be flat, string-compatible
                metadata = {
                    "doc_id": str(doc["doc_id"]),
                    "chunk_id": str(doc["chunk_id"]),
                    "path": str(doc.get("path", "")),
                    **(doc.get("metadata", {}) or {}),
                }
                # Convert all values to strings (ChromaDB requirement)
                metadatas.append(
                    {k: str(v) for k, v in metadata.items() if v is not None}
                )

            # ChromaDB handles upserts automatically (if ID exists, it updates)
            self.collection.upsert(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
            )
            self.logger.info("Upserted %d documents to ChromaDB", len(documents))
        except Exception as exc:
            self.logger.error("Failed to upsert documents: %s", exc)
            raise

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Return the top k documents most similar to the query using embeddings.

        Args:
            query: Natural language query string.
            k: Number of results to return.

        Returns:
            List of result dictionaries with doc_id, chunk_id, content, metadata, score.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                include=["documents", "metadatas", "distances"],
            )

            # Convert ChromaDB results to standard format
            output: List[Dict[str, Any]] = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    # Extract doc_id and chunk_id from unique_id
                    parts = doc_id.split("::")
                    doc_id_part = parts[0] if len(parts) > 0 else doc_id
                    chunk_id_part = parts[1] if len(parts) > 1 else doc_id

                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    content = results["documents"][0][i] if results["documents"] else ""
                    distance = results["distances"][0][i] if results["distances"] else 1.0

                    # Convert distance to similarity score (1 - normalized distance)
                    score = max(0.0, 1.0 - float(distance))

                    output.append(
                        {
                            "doc_id": metadata.get("doc_id", doc_id_part),
                            "chunk_id": metadata.get("chunk_id", chunk_id_part),
                            "path": metadata.get("path", ""),
                            "content": content,
                            "metadata": metadata,
                            "score": score,
                        }
                    )

            return output
        except Exception as exc:
            self.logger.error("Similarity search failed: %s", exc)
            return []

    def keyword_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform keyword search on document contents.

        Args:
            query: Query string with keywords.
            k: Number of results to return.

        Returns:
            List of result dictionaries with keyword relevance scores.
        """
        try:
            # Fetch documents for keyword scoring
            # For large datasets (>10K documents), consider using ChromaDB's
            # where filters or implementing full-text search indexing
            all_results = self.collection.get(
                include=["documents", "metadatas"],
                limit=1000,  # Limit for performance with large datasets
            )

            # Tokenize query (normalize and filter)
            query_tokens = [
                t.lower().strip()
                for t in query.split()
                if t.strip() and len(t.strip()) > 1
            ]

            if not query_tokens:
                return []

            scored_results: List[Dict[str, Any]] = []
            if all_results["ids"]:
                for i, doc_id in enumerate(all_results["ids"]):
                    content = (
                        all_results["documents"][i]
                        if all_results["documents"] and i < len(all_results["documents"])
                        else ""
                    )
                    metadata = (
                        all_results["metadatas"][i]
                        if all_results["metadatas"] and i < len(all_results["metadatas"])
                        else {}
                    )

                    if not content:
                        continue

                    # Calculate keyword score (TF-based with word boundaries)
                    content_lower = content.lower()
                    # Count occurrences with word boundaries for better matching
                    score = sum(
                        content_lower.count(f" {token} ") + content_lower.count(f"{token} ")
                        + content_lower.count(f" {token}")
                        for token in query_tokens
                    )

                    if score > 0:
                        parts = doc_id.split("::")
                        doc_id_part = parts[0] if len(parts) > 0 else doc_id
                        chunk_id_part = parts[1] if len(parts) > 1 else doc_id

                        scored_results.append(
                            {
                                "doc_id": metadata.get("doc_id", doc_id_part),
                                "chunk_id": metadata.get("chunk_id", chunk_id_part),
                                "path": metadata.get("path", ""),
                                "content": content,
                                "metadata": metadata,
                                "kw_score": float(score),
                            }
                        )

            # Sort by score descending and return top k
            scored_results.sort(key=lambda x: x["kw_score"], reverse=True)
            return scored_results[:k]
        except Exception as exc:
            self.logger.error("Keyword search failed: %s", exc)
            return []

    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete all chunks belonging to the specified document IDs.

        Args:
            doc_ids: List of document IDs to delete.
        """
        if not doc_ids:
            return

        try:
            # ChromaDB uses unique IDs, so we need to find all chunks for each doc_id
            all_results = self.collection.get(
                include=["metadatas"],
            )

            ids_to_delete: List[str] = []
            if all_results["ids"]:
                for i, unique_id in enumerate(all_results["ids"]):
                    metadata = (
                        all_results["metadatas"][i] if all_results["metadatas"] else {}
                    )
                    doc_id = metadata.get("doc_id", unique_id.split("::")[0])
                    if doc_id in doc_ids:
                        ids_to_delete.append(unique_id)

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                self.logger.info(
                    "Deleted %d chunks from ChromaDB for %d document IDs",
                    len(ids_to_delete),
                    len(doc_ids),
                )
        except Exception as exc:
            self.logger.error("Failed to delete documents: %s", exc)
            raise

    def list_all_documents(self) -> List[Dict[str, Any]]:
        """Return all documents in the collection.

        Returns:
            List of dictionaries with doc_id, chunk_id, path, content, metadata.
        """
        try:
            results = self.collection.get(include=["documents", "metadatas"])
            output: List[Dict[str, Any]] = []

            if results["ids"]:
                for i, doc_id in enumerate(results["ids"]):
                    parts = doc_id.split("::")
                    doc_id_part = parts[0] if len(parts) > 0 else doc_id
                    chunk_id_part = parts[1] if len(parts) > 1 else doc_id

                    metadata = results["metadatas"][i] if results["metadatas"] else {}
                    content = results["documents"][i] if results["documents"] else ""

                    output.append(
                        {
                            "doc_id": metadata.get("doc_id", doc_id_part),
                            "chunk_id": metadata.get("chunk_id", chunk_id_part),
                            "path": metadata.get("path", ""),
                            "content": content,
                            "metadata": metadata,
                        }
                    )

            return output
        except Exception as exc:
            self.logger.error("Failed to list documents: %s", exc)
            return []


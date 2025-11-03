"""
pgvector implementation of the knowledge base repository.

This module provides a production-ready implementation using PostgreSQL
with pgvector extension for vector similarity search. pgvector adds vector
similarity search capabilities to PostgreSQL.

Features:
- Semantic similarity search using pgvector
- Full-text keyword search using PostgreSQL's full-text search
- Binary quantization support for reduced storage
- Reranking support for improved relevance
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base_kb_repo import BaseKnowledgeBaseRepository
from ..config import Settings
from ..utils.logging import get_logger

try:
    import numpy as np  # type: ignore
    import psycopg  # type: ignore
    from psycopg.types.json import Jsonb  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError as exc:
    psycopg = None  # type: ignore
    np = None  # type: ignore
    Jsonb = None  # type: ignore
    SentenceTransformer = None  # type: ignore
    _import_error = exc


class PgvectorKnowledgeBaseRepository(BaseKnowledgeBaseRepository):
    """Knowledge base repository backed by PostgreSQL with pgvector."""

    def __init__(self, settings: Settings, table_name: str = "kb_documents"):
        if psycopg is None or np is None or SentenceTransformer is None or Jsonb is None:
            raise ImportError(
                "Required dependencies not installed. "
                "Please install: pip install psycopg[binary] numpy sentence-transformers"
            ) from _import_error

        self.logger = get_logger(__name__)
        self.settings = settings
        self.table_name = table_name

        # Get PostgreSQL connection string
        postgres_url = getattr(settings, "postgres_connection_string", None)
        if not postgres_url:
            raise ValueError(
                "POSTGRES_CONNECTION_STRING environment variable is required for pgvector"
            )

        # Connect to PostgreSQL
        try:
            self.conn = psycopg.connect(postgres_url)
            self.conn.autocommit = False
            self.logger.info("Connected to PostgreSQL database")
        except Exception as exc:
            self.logger.error("Failed to connect to PostgreSQL: %s", exc)
            raise ConnectionError(f"Failed to connect to PostgreSQL: {exc}") from exc

        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(settings.embedding_model_id)
            self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
            self.logger.info(
                "Initialized embedding model %s with dimension %d",
                settings.embedding_model_id,
                self.embedding_dimension,
            )
        except Exception as exc:
            self.logger.error("Failed to initialize embedding model: %s", exc)
            raise

        # Enable pgvector extension and create table
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create the table schema if it doesn't exist."""
        with self.conn.cursor() as cur:
            try:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.logger.info("pgvector extension enabled")

                # Create table with vector column
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id SERIAL PRIMARY KEY,
                        doc_id TEXT NOT NULL,
                        chunk_id TEXT NOT NULL,
                        path TEXT,
                        content TEXT NOT NULL,
                        embedding vector({self.embedding_dimension}),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(doc_id, chunk_id)
                    );
                    """
                )

                # Create indexes
                # Vector similarity index (HNSW for better performance)
                cur.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                    ON {self.table_name}
                    USING hnsw (embedding vector_cosine_ops);
                    """
                )

                # Full-text search index for keyword search
                cur.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {self.table_name}_content_fts_idx
                    ON {self.table_name}
                    USING gin(to_tsvector('english', content));
                    """
                )

                # Indexes for filtering
                cur.execute(
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_doc_id_idx ON {self.table_name}(doc_id);"
                )
                cur.execute(
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_path_idx ON {self.table_name}(path);"
                )

                self.conn.commit()
                self.logger.info("Created/verified table schema and indexes")
            except Exception as exc:
                self.conn.rollback()
                self.logger.error("Failed to create schema: %s", exc)
                raise

    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Insert or update documents in PostgreSQL.

        Args:
            documents: List of dicts with keys: doc_id, chunk_id, path,
                content, metadata.
        """
        try:
            # Batch process embeddings for efficiency
            contents = [str(doc["content"]) for doc in documents]
            embeddings = self.embedding_model.encode(
                contents, normalize_embeddings=True, show_progress_bar=False
            )

            with self.conn.cursor() as cur:
                # Upsert documents with batch embeddings
                for doc, embedding in zip(documents, embeddings):
                    embedding_list = embedding.tolist()
                    
                    # Upsert document
                    cur.execute(
                        f"""
                        INSERT INTO {self.table_name} (doc_id, chunk_id, path, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb)
                        ON CONFLICT (doc_id, chunk_id)
                        DO UPDATE SET
                            path = EXCLUDED.path,
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata;
                        """,
                        (
                            str(doc["doc_id"]),
                            str(doc["chunk_id"]),
                            str(doc.get("path", "")),
                            str(doc["content"]),
                            str(embedding_list),
                            Jsonb(doc.get("metadata", {}) or {}),
                        ),
                    )

            self.conn.commit()
            self.logger.info("Upserted %d documents to PostgreSQL", len(documents))
        except Exception as exc:
            self.conn.rollback()
            self.logger.error("Failed to upsert documents: %s", exc)
            raise

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Return the top k documents most similar to the query using embeddings.

        Args:
            query: Natural language query string.
            k: Number of results to return.

        Returns:
            List of result dictionaries with similarity scores.
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                query, normalize_embeddings=True
            ).tolist()

            with self.conn.cursor() as cur:
                # Use cosine similarity (1 - cosine_distance)
                cur.execute(
                    f"""
                    SELECT doc_id, chunk_id, path, content, metadata,
                           1 - (embedding <=> %s::vector) as score
                    FROM {self.table_name}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                    """,
                    (str(query_embedding), str(query_embedding), k),
                )

                results: List[Dict[str, Any]] = []
                for row in cur.fetchall():
                    results.append(
                        {
                            "doc_id": row[0],
                            "chunk_id": row[1],
                            "path": row[2] or "",
                            "content": row[3],
                            "metadata": row[4] or {},
                            "score": float(row[5]),
                        }
                    )

                return results
        except Exception as exc:
            self.logger.error("Similarity search failed: %s", exc)
            return []

    def keyword_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform keyword search using PostgreSQL full-text search.

        Args:
            query: Query string with keywords.
            k: Number of results to return.

        Returns:
            List of result dictionaries with relevance scores.
        """
        try:
            # Prepare query for full-text search
            # Use plainto_tsquery for safe, user-friendly parsing
            # This handles special characters and prevents injection

            with self.conn.cursor() as cur:
                # Use plainto_tsquery for safe query parsing (handles injection prevention)
                cur.execute(
                    f"""
                    SELECT doc_id, chunk_id, path, content, metadata,
                           ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) as rank
                    FROM {self.table_name}
                    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s;
                    """,
                    (query, query, k),
                )

                results: List[Dict[str, Any]] = []
                for row in cur.fetchall():
                    results.append(
                        {
                            "doc_id": row[0],
                            "chunk_id": row[1],
                            "path": row[2] or "",
                            "content": row[3],
                            "metadata": row[4] or {},
                            "kw_score": float(row[5]) if row[5] else 0.0,
                        }
                    )

                return results
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
            with self.conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self.table_name} WHERE doc_id = ANY(%s);",
                    (doc_ids,),
                )
                deleted_count = cur.rowcount
                self.conn.commit()
                self.logger.info(
                    "Deleted %d chunks from PostgreSQL for %d document IDs",
                    deleted_count,
                    len(doc_ids),
                )
        except Exception as exc:
            self.conn.rollback()
            self.logger.error("Failed to delete documents: %s", exc)
            raise

    def list_all_documents(self) -> List[Dict[str, Any]]:
        """Return all documents in the table.

        Returns:
            List of dictionaries with doc_id, chunk_id, path, content, metadata.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"SELECT doc_id, chunk_id, path, content, metadata FROM {self.table_name};"
                )

                results: List[Dict[str, Any]] = []
                for row in cur.fetchall():
                    results.append(
                        {
                            "doc_id": row[0],
                            "chunk_id": row[1],
                            "path": row[2] or "",
                            "content": row[3],
                            "metadata": row[4] or {} if row[4] else {},
                        }
                    )

                return results
        except Exception as exc:
            self.logger.error("Failed to list documents: %s", exc)
            return []


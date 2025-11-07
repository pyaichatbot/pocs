"""
Abstract knowledge base repository.

This module defines an abstract interface for storing and retrieving
documents.  Implementations of this interface hide the details of
vector indexing and database persistence so that the rest of the code
remains agnostic of the underlying technology.

All methods that can raise exceptions should raise implementation
specific subclasses of ``Exception`` so that callers can catch and
handle them appropriately.
"""

from __future__ import annotations

import abc
from typing import Any, Dict, List


class BaseKnowledgeBaseRepository(abc.ABC):
    """Abstract base class for knowledge base repositories."""

    @abc.abstractmethod
    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Insert or update a list of documents.

        Each document must have at least the keys ``doc_id``, ``chunk_id``,
        ``content`` and ``metadata``.  The repository implementation is
        responsible for computing any embeddings and updating or
        inserting rows accordingly.  If a document with the same
        ``doc_id`` and ``chunk_id`` already exists its content
        should be updated.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def similarity_search(
        self, query: str, k: int = 5, filter_repo_urls: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        """Return the top ``k`` documents most similar to the query.

        Results should be ordered by descending similarity.  Each result
        is a dictionary containing at least the keys ``doc_id``,
        ``chunk_id``, ``content`` and ``metadata``.  Additional keys
        (e.g. similarity score) may be included.

        Args:
            query: Natural language query string.
            k: Number of results to return.
            filter_repo_urls: Optional list of repository URLs to filter by.
                            If provided, only return results from these repositories.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def keyword_search(
        self, query: str, k: int = 5
    ) -> List[Dict[str, Any]]:
        """Return the top ``k`` documents matching the query terms.

        A simple lexical search implementation can count occurrences
        of query words.  Implementations are free to choose an
        appropriate algorithm as long as results are ordered by
        decreasing relevance.
        """
        raise NotImplementedError

    def hybrid_search(
        self, query: str, k: int = 5, weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Combine similarity and keyword search to produce results.

        The default implementation performs a weighted merge of the
        similarity and keyword scores.  Subclasses may override this
        method for better performance.

        Args:
            query: Natural language query string.
            k: Number of results to return.
            weight: Weight assigned to similarity score vs. keyword score.
        Returns:
            A list of result dictionaries.
        """
        # Get similarity and keyword results
        sim_results = self.similarity_search(query, k * 2)
        kw_results = self.keyword_search(query, k * 2)
        
        # Normalize scores to [0, 1] range for fair combination
        sim_scores = {}
        kw_scores = {}
        
        # Extract similarity scores (already normalized to [0, 1])
        for r in sim_results:
            key = (r["doc_id"], r["chunk_id"])
            sim_scores[key] = float(r.get("score", 0.0))
        
        # Extract keyword scores and normalize
        kw_max_score = max([r.get("kw_score", 0.0) for r in kw_results], default=1.0)
        for r in kw_results:
            key = (r["doc_id"], r["chunk_id"])
            kw_score = float(r.get("kw_score", 0.0))
            # Normalize to [0, 1]
            kw_scores[key] = kw_score / kw_max_score if kw_max_score > 0 else 0.0
        
        # Combine scores using weighted average
        all_keys = set(sim_scores.keys()) | set(kw_scores.keys())
        combined: List[tuple[tuple, float, Dict[str, Any]]] = []
        
        for key in all_keys:
            sim_score = sim_scores.get(key, 0.0)
            kw_score = kw_scores.get(key, 0.0)
            # Weighted combination: weight for semantic, (1-weight) for keyword
            combined_score = weight * sim_score + (1 - weight) * kw_score
            
            # Get the full record (prefer similarity result)
            record = next(
                (r for r in sim_results if (r["doc_id"], r["chunk_id"]) == key),
                next(
                    (r for r in kw_results if (r["doc_id"], r["chunk_id"]) == key),
                    None,
                ),
            )
            
            if record:
                combined.append((key, combined_score, record))
        
        # Sort by combined score descending and return top k
        combined.sort(key=lambda x: x[1], reverse=True)
        results = [record for _, _, record in combined[:k]]
        
        return results

    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete all chunks for the given document IDs.

        Default implementation raises ``NotImplementedError``.  Repositories
        may override this method if they support deletions.  Deleting
        documents is useful when re‑indexing updated files in a delta
        index operation.
        """
        raise NotImplementedError

    def get_distinct_repo_urls(self) -> List[str]:
        """Get distinct repository URLs from all indexed documents.

        Returns:
            List of unique repository URLs (normalized).
        """
        # Default implementation uses list_all_documents
        # Subclasses should override for better performance
        try:
            all_docs = self.list_all_documents()
            repo_urls = set()
            for doc in all_docs:
                metadata = doc.get("metadata") or {}
                repo_url = metadata.get("repo_url")
                if repo_url:
                    # Normalize URL
                    repo_url = repo_url.rstrip(".git")
                    if not repo_url.startswith("http"):
                        repo_url = f"https://{repo_url}"
                    repo_urls.add(repo_url)
            return sorted(list(repo_urls))
        except Exception:
            # If list_all_documents not available, return empty
            return []
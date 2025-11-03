"""
Reranking utilities for improving search result relevance.

Reranking uses cross-encoder models to re-score retrieved documents
based on their relevance to the query, providing more accurate results.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import Settings
from ..utils.logging import get_logger

try:
    from sentence_transformers import CrossEncoder  # type: ignore
except ImportError:
    CrossEncoder = None  # type: ignore


class Reranker:
    """Reranker for improving search result relevance using cross-encoder models."""

    def __init__(self, settings: Settings, enabled: bool = True):
        """Initialize reranker.

        Args:
            settings: Configuration settings.
            enabled: Whether reranking is enabled. Defaults to True.
        """
        self.logger = get_logger(__name__)
        self.settings = settings
        self.enabled = enabled and self._is_available()

        if self.enabled and CrossEncoder is None:
            self.logger.warning(
                "CrossEncoder not available. Install sentence-transformers for reranking."
            )
            self.enabled = False

        self.model: Optional[CrossEncoder] = None
        if self.enabled:
            try:
                # Default cross-encoder model for reranking
                model_name = getattr(
                    settings, "reranker_model_id", "cross-encoder/ms-marco-MiniLM-L-6-v2"
                )
                self.model = CrossEncoder(model_name)
                self.logger.info("Reranker initialized with model %s", model_name)
            except Exception as exc:
                self.logger.error("Failed to initialize reranker: %s", exc)
                self.enabled = False

    def _is_available(self) -> bool:
        """Check if reranking is available."""
        return CrossEncoder is not None

    def rerank(
        self, query: str, results: List[Dict[str, Any]], top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Rerank search results based on query relevance.

        Args:
            query: The search query.
            results: List of search result dictionaries.
            top_k: Number of top results to return. If None, returns all reranked.

        Returns:
            Reranked list of results with updated scores.
        """
        if not self.enabled or not self.model or not results:
            return results

        try:
            # Prepare pairs for cross-encoder
            pairs = [[query, result.get("content", "")] for result in results]

            # Get rerank scores
            rerank_scores = self.model.predict(pairs)

            # Update results with rerank scores
            for i, result in enumerate(results):
                # Combine original score with rerank score (weighted)
                original_score = result.get("score", result.get("kw_score", 0.0))
                rerank_score = float(rerank_scores[i])

                # Weighted combination: 70% rerank, 30% original
                combined_score = 0.7 * rerank_score + 0.3 * original_score
                result["rerank_score"] = rerank_score
                result["score"] = combined_score

            # Sort by combined score descending
            results.sort(key=lambda x: x.get("score", 0.0), reverse=True)

            # Return top_k if specified
            if top_k is not None:
                return results[:top_k]

            return results
        except Exception as exc:
            self.logger.error("Reranking failed: %s", exc)
            # Return original results on failure
            return results


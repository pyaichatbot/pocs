"""
Search and answer service for the RAG system.

This service encapsulates the logic for retrieving relevant
information from the knowledge base and, optionally, generating a
conversational answer via a large language model.  It delegates
database operations to a ``BaseKnowledgeBaseRepository`` and LLM
interaction to an ``LLMClient``.

The primary method ``answer`` accepts a natural language query and
returns either a generated answer or, if no LLM provider is
available, the top documents as context.  Keyword and similarity
search results are combined using the hybrid search method defined on
the repository.  The number of context chunks can be tuned via
``max_chunks``.
"""

from __future__ import annotations

from typing import Dict, List

from ..repositories.base_kb_repo import BaseKnowledgeBaseRepository
from ..llm_client import DocumentChunk, LLMClient
from ..utils.logging import get_logger, log_event
from ..utils.reranker import Reranker
from ..config import Settings


class SearchService:
    """Service for searching and answering queries using the KB and an LLM."""

    def __init__(
        self,
        kb_repo: BaseKnowledgeBaseRepository,
        llm_client: LLMClient | None = None,
        max_chunks: int = 5,
        settings: Settings | None = None,
    ) -> None:
        self.kb_repo = kb_repo
        self.llm_client = llm_client
        self.max_chunks = max_chunks
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize reranker if enabled
        if settings:
            self.reranker = Reranker(settings) if getattr(settings, "reranker_enabled", False) else None
        else:
            self.reranker = None

    def answer(self, query: str) -> Dict[str, object]:
        """Retrieve relevant contexts and optionally generate an answer.

        Args:
            query: The user's natural language question.
        Returns:
            A dictionary containing either an ``answer`` field with the
            generated response or a ``contexts`` field with the raw
            document chunks.
        """
        log_event(self.logger, "search_start", query=query)
        try:
            # Perform hybrid search
            results = self.kb_repo.hybrid_search(query, k=self.max_chunks * 2)
            
            # Apply reranking if enabled
            if self.reranker and self.reranker.enabled:
                results = self.reranker.rerank(query, results, top_k=self.max_chunks)
            else:
                # Limit to max_chunks if no reranking
                results = results[:self.max_chunks]
        except Exception as exc:
            log_event(self.logger, "search_error", error=str(exc))
            raise
        # Convert results to DocumentChunk objects for LLM
        contexts: List[DocumentChunk] = []
        for r in results:
            contexts.append(
                DocumentChunk(
                    doc_id=r["doc_id"],
                    chunk_id=r["chunk_id"],
                    path=r.get("path", ""),
                    content=r["content"],
                    metadata=r.get("metadata", {}),
                )
            )
        if self.llm_client and self.llm_client.is_available():
            answer = self.llm_client.generate_answer(query, contexts)
            log_event(self.logger, "search_complete", query=query, answer="generated")
            return {"answer": answer}
        else:
            # No LLM available; return contexts for caller to process
            log_event(self.logger, "search_complete", query=query, answer="none")
            return {"contexts": [c.content for c in contexts]}
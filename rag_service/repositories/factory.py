"""
Repository factory for creating knowledge base repository instances.

This factory allows easy swapping of vector database implementations
(ChromaDB, pgvector, Cosmos DB) via configuration without changing
the rest of the codebase.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..config import Settings
from .base_kb_repo import BaseKnowledgeBaseRepository

if TYPE_CHECKING:
    pass


class RepositoryFactory:
    """Factory for creating knowledge base repository instances."""

    @staticmethod
    def create(settings: Settings) -> BaseKnowledgeBaseRepository:
        """Create a knowledge base repository based on configuration.

        Args:
            settings: Configuration settings containing repository type and
                connection details.

        Returns:
            A concrete implementation of BaseKnowledgeBaseRepository.

        Raises:
            ValueError: If the configured repository type is not supported.
            ImportError: If required dependencies are not installed.
        """
        # Check RAG_MODE first - if leann, use LEANN repository
        rag_mode = getattr(settings, "rag_mode", "traditional").lower()
        
        if rag_mode == "leann":
            from .leann_kb_repo import LeannKnowledgeBaseRepository
            return LeannKnowledgeBaseRepository(settings)

        # Otherwise, use traditional vector database based on REPOSITORY_TYPE
        repo_type = getattr(settings, "repository_type", None) or "chromadb"

        if repo_type.lower() == "chromadb":
            from .chromadb_kb_repo import ChromaDBKnowledgeBaseRepository
            return ChromaDBKnowledgeBaseRepository(settings)

        elif repo_type.lower() == "pgvector":
            from .pgvector_kb_repo import PgvectorKnowledgeBaseRepository
            return PgvectorKnowledgeBaseRepository(settings)

        elif repo_type.lower() == "cosmosdb":
            from .cosmosdb_kb_repo import CosmosDBKnowledgeBaseRepository
            return CosmosDBKnowledgeBaseRepository(settings)

        else:
            raise ValueError(
                f"Unsupported repository type: {repo_type}. "
                "Supported types: chromadb, pgvector, cosmosdb, leann (via RAG_MODE=leann)"
            )


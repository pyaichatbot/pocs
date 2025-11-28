"""
LEANN implementation of the knowledge base repository.

This module provides an implementation using LEANN (Low-Storage Vector Index)
for storage and semantic search. LEANN uses graph-based selective recomputation
to achieve 95-97% storage savings compared to traditional vector databases.

Features:
- On-demand embedding computation (only for nodes in search path)
- Pruned graph structure storage
- Semantic similarity search
- Metadata support for filtering
"""

from __future__ import annotations

import os
from typing import Any, Dict, List
from pathlib import Path

from .base_kb_repo import BaseKnowledgeBaseRepository
from ..config import Settings
from ..utils.logging import get_logger

try:
    from leann import LeannBuilder, LeannSearcher
except ImportError as exc:
    LeannBuilder = None  # type: ignore
    LeannSearcher = None  # type: ignore
    _import_error = exc


class LeannKnowledgeBaseRepository(BaseKnowledgeBaseRepository):
    """Knowledge base repository backed by LEANN."""

    def __init__(self, settings: Settings, index_path: str | None = None):
        if LeannBuilder is None or LeannSearcher is None:
            raise ImportError(
                "LEANN is not installed. Please install leann: pip install leann"
            ) from _import_error

        self.logger = get_logger(__name__)
        self.settings = settings
        self.index_path = index_path or settings.leann_index_path
        
        # Ensure index directory exists
        # Handle permission issues gracefully (e.g., when volume is mounted)
        index_dir = os.path.dirname(self.index_path)
        if index_dir:
            try:
                os.makedirs(index_dir, exist_ok=True)
            except PermissionError:
                # If we can't create the directory, try to use a path we can write to
                # Fallback to a writable location in /tmp or current directory
                self.logger.warning(
                    "Cannot create index directory %s due to permissions. "
                    "Using fallback location.",
                    index_dir
                )
                # Use /tmp as fallback (always writable)
                fallback_dir = "/tmp/leann_indexes"
                os.makedirs(fallback_dir, exist_ok=True)
                filename = os.path.basename(self.index_path)
                self.index_path = os.path.join(fallback_dir, filename)
                self.logger.info("Using fallback index path: %s", self.index_path)

        # Initialize builder for indexing
        self.builder: LeannBuilder | None = None
        self._pending_chunks: List[Dict[str, Any]] = []
        self._index_built = False

        # Initialize searcher (will be loaded when index is built)
        self.searcher: LeannSearcher | None = None

        # Try to load existing index if it exists
        # LEANN creates metadata file as {index_path}.meta.json based on the path passed to build_index()
        # The backend may create the index file with a different extension, but the metadata file
        # is always named after the index_path parameter
        meta_path = f"{self.index_path}.meta.json"
        
        if os.path.exists(meta_path):
            try:
                meta_size = os.path.getsize(meta_path)
                self.logger.info(
                    "Attempting to load LEANN index from %s (metadata: %d bytes)",
                    self.index_path,
                    meta_size
                )
                # Use the original index_path - LeannSearcher will look for {index_path}.meta.json
                self.searcher = LeannSearcher(self.index_path)
                self._index_built = True
                self.logger.info(
                    "Loaded existing LEANN index from %s", self.index_path
                )
            except Exception as exc:
                self.logger.warning(
                    "Failed to load LEANN index from %s: %s", self.index_path, exc
                )
                self.searcher = None
                self._index_built = False
        else:
            self.logger.debug(
                "No existing LEANN index found at %s (metadata file %s not found). "
                "Index will be built on first document addition.",
                self.index_path,
                meta_path
            )
            self.searcher = None
            self._index_built = False

    def _initialize_builder(self) -> None:
        """Initialize LEANN builder if not already initialized."""
        if self.builder is None:
            # LEANN builder signature: backend_name, embedding_model, dimensions, embedding_mode, embedding_options, **backend_kwargs
            # graph_degree is a backend-specific kwarg for HNSW
            # Note: complexity is a search parameter, not a build parameter
            backend_kwargs = {
                "graph_degree": self.settings.leann_graph_degree,
            }
            self.builder = LeannBuilder(
                backend_name=self.settings.leann_backend,
                embedding_model=self.settings.leann_embedding_model,
                **backend_kwargs,
            )
            self.logger.info(
                "Initialized LEANN builder with backend=%s, model=%s, graph_degree=%d",
                self.settings.leann_backend,
                self.settings.leann_embedding_model,
                self.settings.leann_graph_degree,
            )

    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Insert or update documents in LEANN index.

        Note: LEANN requires building the index after all documents are added.
        Documents are buffered until build_index() is called.

        Args:
            documents: List of dicts with keys: doc_id, chunk_id, path,
                content, metadata.
        """
        try:
            self._initialize_builder()
            
            # Buffer documents for batch building
            for doc in documents:
                content = str(doc["content"])
                metadata = doc.get("metadata", {})
                
                # Store document info for later retrieval
                chunk_info = {
                    "doc_id": doc["doc_id"],
                    "chunk_id": doc["chunk_id"],
                    "path": doc.get("path", ""),
                    "content": content,
                    "metadata": metadata,
                }
                self._pending_chunks.append(chunk_info)
                
                # Add text to builder (LEANN will handle embeddings on-demand)
                # LEANN's add_text accepts metadata as dict[str, Any]
                # Ensure metadata includes 'id' field for proper passage retrieval
                metadata_with_id = {**metadata, "id": doc.get("chunk_id", doc.get("doc_id", str(len(self._pending_chunks))))}
                self.builder.add_text(content, metadata=metadata_with_id)
            
            self.logger.info(
                "Buffered %d documents for LEANN index (total pending: %d)",
                len(documents),
                len(self._pending_chunks),
            )
        except Exception as exc:
            self.logger.error("Failed to upsert documents: %s", exc)
            raise

    def build_index(self) -> None:
        """Build the LEANN index from buffered documents.
        
        This must be called after all documents have been added via upsert_documents().
        """
        if self.builder is None:
            if not self._pending_chunks:
                self.logger.warning("No documents to build index from")
                return
            self._initialize_builder()
            # Re-add all pending chunks
            for chunk_info in self._pending_chunks:
                metadata = chunk_info["metadata"]
                # Ensure metadata includes 'id' field
                metadata_with_id = {**metadata, "id": chunk_info.get("chunk_id", chunk_info.get("doc_id", ""))}
                self.builder.add_text(chunk_info["content"], metadata=metadata_with_id)

        try:
            self.logger.info(
                "Building LEANN index with %d documents to %s",
                len(self._pending_chunks),
                self.index_path,
            )
            
            # LEANN build_index takes just the path
            # The metadata file is created based on the index_path parameter, not the actual backend index file
            # So we must use the original index_path when loading the searcher
            self.builder.build_index(self.index_path)
            
            # Verify metadata file exists (required by LEANN)
            # LEANN creates metadata file as: {index_path}.meta.json
            # This is based on the path we passed to build_index(), not the backend index file
            meta_file = f"{self.index_path}.meta.json"
            if not os.path.exists(meta_file):
                raise RuntimeError(
                    f"LEANN build_index completed but metadata file not found at {meta_file}. "
                    f"This indicates the build did not complete successfully."
                )
            
            self.logger.debug(
                "LEANN metadata file found at %s", meta_file
            )
            
            # Verify backend index file was created (may have different extension)
            index_base = os.path.splitext(self.index_path)[0]
            possible_index_files = [
                self.index_path,
                f"{index_base}.index",
                f"{index_base}.leann",
            ]
            
            actual_index_file = None
            for index_file in possible_index_files:
                if os.path.exists(index_file):
                    actual_index_file = index_file
                    break
            
            if not actual_index_file:
                self.logger.warning(
                    "LEANN metadata file exists but no backend index file found at any of: %s. "
                    "This may be normal if the backend uses a different naming convention.",
                    possible_index_files
                )
            
            # Load searcher using the ORIGINAL index_path (not the backend file)
            # LeannSearcher expects the path that was used in build_index() because
            # it looks for {index_path}.meta.json based on the path parameter
            try:
                self.searcher = LeannSearcher(self.index_path)
                self._index_built = True
                self.logger.info(
                    "Successfully loaded LEANN searcher with index_path=%s", self.index_path
                )
            except Exception as load_exc:
                # If loading fails, provide helpful error
                raise RuntimeError(
                    f"LEANN index built but cannot load searcher: {load_exc}. "
                    f"Index path: {self.index_path}, Metadata file: {meta_file} (exists: {os.path.exists(meta_file)}). "
                    f"Backend index file: {actual_index_file} (exists: {os.path.exists(actual_index_file) if actual_index_file else False})."
                ) from load_exc
            
            # Get index size for logging - check multiple possible file locations
            # Note: The metadata file is always named {index_path}.meta.json
            # The backend may create the index file with a different extension (.index, .leann, etc.)
            index_base = os.path.splitext(self.index_path)[0]
            index_dir = os.path.dirname(self.index_path)
            index_size = 0
            meta_size = os.path.getsize(meta_file) if os.path.exists(meta_file) else 0
            backend_index_file = None
            
            # Check for backend index files that LEANN might have created
            # Backend typically creates {index_base}.index file
            possible_files = [
                f"{index_base}.index",  # Most common - backend creates this
                self.index_path,        # Original path
                f"{index_base}.leann",  # Alternative
            ]
            
            for file_path in possible_files:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    if file_size > index_size:  # Use the largest file found
                        index_size = file_size
                        backend_index_file = file_path
            
            # Also list all files in the index directory for debugging
            if index_dir and os.path.exists(index_dir):
                index_files = [f for f in os.listdir(index_dir) if 'kb_index' in f or 'index' in f.lower()]
                if index_files:
                    self.logger.debug(
                        "Index directory contains: %s", ", ".join(index_files)
                    )
            
            self.logger.info(
                "LEANN index built successfully. Index: %.2f MB, Metadata: %.2f KB, Documents: %d, Index path: %s",
                index_size / (1024 * 1024) if index_size > 0 else 0.0,
                meta_size / 1024 if meta_size > 0 else 0.0,
                len(self._pending_chunks),
                self.index_path
            )
            
            if backend_index_file and backend_index_file != self.index_path:
                self.logger.debug(
                    "Backend created index file at %s (metadata file is at %s)",
                    backend_index_file,
                    meta_file
                )
        except Exception as exc:
            self.logger.error("Failed to build LEANN index: %s", exc)
            raise

    def similarity_search(
        self, query: str, k: int = 5, filter_repo_urls: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        """Return the top k documents most similar to the query.

        Args:
            query: Natural language query string.
            k: Number of results to return.
            filter_repo_urls: Optional list of repository URLs to filter by.
                            Note: LEANN metadata filtering may be limited.

        Returns:
            List of result dictionaries with doc_id, chunk_id, content, metadata, score.
        """
        if not self._index_built or self.searcher is None:
            # Try to reload index if it exists but wasn't loaded in __init__
            # This handles the case where index was built in a different instance
            index_base = os.path.splitext(self.index_path)[0]
            alternative_paths = [
                self.index_path,
                f"{index_base}.index",
                f"{index_base}.leann",
            ]
            
            for alt_path in alternative_paths:
                # Check if index file exists
                if not os.path.exists(alt_path):
                    continue
                
                # Check if metadata file exists (required by LEANN)
                meta_path = self._find_metadata_file(alt_path)
                if not meta_path:
                    self.logger.warning(
                        "Index file found at %s but metadata file (.meta.json) is missing. "
                        "This may indicate an incomplete build. The index cannot be loaded without the metadata file.",
                        alt_path
                    )
                    continue
                
                try:
                    self.logger.info(
                        "Attempting to reload LEANN index from %s for search",
                        alt_path
                    )
                    self.searcher = LeannSearcher(alt_path)
                    self._index_built = True
                    self.index_path = alt_path
                    self.logger.info(
                        "Successfully reloaded LEANN index from %s", alt_path
                    )
                    break
                except Exception as exc:
                    self.logger.warning(
                        "Failed to reload LEANN index from %s: %s", alt_path, exc
                    )
                    continue
            
            # If still not loaded, try to build from pending chunks
            if not self._index_built or self.searcher is None:
                if self._pending_chunks:
                    self.logger.info(
                        "Building LEANN index from %d pending chunks", len(self._pending_chunks)
                    )
                    self.build_index()
                else:
                    self.logger.warning(
                        "LEANN index not built and no documents available. "
                        "Index path checked: %s. File exists: %s",
                        self.index_path,
                        os.path.exists(self.index_path)
                    )
                    return []

        try:
            # Perform search with LEANN
            # Official SDK returns list[SearchResult] with .id, .score, .text, .metadata attributes
            results = self.searcher.search(
                query,
                top_k=k,
                complexity=self.settings.leann_complexity,
                recompute_embeddings=self.settings.leann_recompute,  # Correct parameter name
            )

            # Convert LEANN SearchResult objects to standard format
            output: List[Dict[str, Any]] = []
            
            # Official SDK returns SearchResult objects with attributes:
            # - result.id (str)
            # - result.score (float)
            # - result.text (str)
            # - result.metadata (dict)
            for result in results:
                # Access SearchResult attributes
                text = result.text
                score = result.score
                result_id = result.id
                metadata_dict = result.metadata or {}

                # Try to find matching chunk by ID first, then by content
                chunk_info = None
                if result_id:
                    # Try to find by chunk_id or doc_id matching result_id
                    for chunk in self._pending_chunks:
                        if chunk.get("chunk_id") == result_id or chunk.get("doc_id") == result_id:
                            chunk_info = chunk
                            break
                
                # Fallback to content matching if ID match failed
                if not chunk_info:
                    chunk_info = self._find_chunk_by_content(text)
                
                if chunk_info:
                    # Apply repository filtering if requested
                    if filter_repo_urls:
                        repo_url = chunk_info["metadata"].get("repo_url", "")
                        if repo_url:
                            normalized = repo_url.rstrip(".git")
                            if not normalized.startswith("http"):
                                normalized = f"https://{normalized}"
                            if normalized not in filter_repo_urls:
                                continue

                    output.append({
                        "doc_id": chunk_info["doc_id"],
                        "chunk_id": chunk_info["chunk_id"],
                        "path": chunk_info["path"],
                        "content": chunk_info["content"],
                        "metadata": chunk_info["metadata"],
                        "score": float(score),
                    })
                else:
                    # Fallback: create result from LEANN SearchResult data
                    # Use metadata from SearchResult, which may contain our original metadata
                    output.append({
                        "doc_id": metadata_dict.get("doc_id", result_id or ""),
                        "chunk_id": metadata_dict.get("chunk_id", result_id or ""),
                        "path": metadata_dict.get("path", ""),
                        "content": text,
                        "metadata": metadata_dict,
                        "score": float(score),
                    })

            return output[:k]
        except Exception as exc:
            self.logger.error("Similarity search failed: %s", exc)
            return []

    def keyword_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform keyword search using semantic search with keyword scoring.

        Note: LEANN's grep search has a bug where it looks for hardcoded file names.
        We use semantic search instead and calculate keyword relevance scores.

        Args:
            query: Query string with keywords.
            k: Number of results to return.

        Returns:
            List of result dictionaries with keyword relevance scores.
        """
        if not self._index_built or self.searcher is None:
            if self._pending_chunks:
                self.build_index()
            else:
                return []

        try:
            # Use semantic search instead of grep (more reliable)
            # LEANN's grep search has a bug in _find_jsonl_file() that looks for
            # hardcoded "documents.leann.passages.jsonl" instead of the actual file name
            results = self.searcher.search(
                query,
                top_k=k * 2,  # Get more results to filter by keyword relevance
                recompute_embeddings=self.settings.leann_recompute,
            )

            # Convert SearchResult objects to standard format
            output: List[Dict[str, Any]] = []
            for result in results:
                # Access SearchResult attributes
                text = result.text
                result_id = result.id
                metadata_dict = result.metadata or {}

                # Try to find chunk by ID first, then by content
                chunk_info = None
                if result_id:
                    for chunk in self._pending_chunks:
                        if chunk.get("chunk_id") == result_id or chunk.get("doc_id") == result_id:
                            chunk_info = chunk
                            break
                
                if not chunk_info:
                    chunk_info = self._find_chunk_by_content(text)
                
                if chunk_info:
                    # Calculate keyword score (simple word count)
                    query_words = query.lower().split()
                    content_lower = chunk_info["content"].lower()
                    kw_score = sum(1 for word in query_words if word in content_lower)
                    
                    output.append({
                        "doc_id": chunk_info["doc_id"],
                        "chunk_id": chunk_info["chunk_id"],
                        "path": chunk_info["path"],
                        "content": chunk_info["content"],
                        "metadata": chunk_info["metadata"],
                        "kw_score": float(kw_score),
                    })
                else:
                    # Fallback: use SearchResult data
                    query_words = query.lower().split()
                    content_lower = text.lower()
                    kw_score = sum(1 for word in query_words if word in content_lower)
                    
                    output.append({
                        "doc_id": metadata_dict.get("doc_id", result_id or ""),
                        "chunk_id": metadata_dict.get("chunk_id", result_id or ""),
                        "path": metadata_dict.get("path", ""),
                        "content": text,
                        "metadata": metadata_dict,
                        "kw_score": float(kw_score),
                    })

            return output[:k]
        except Exception as exc:
            self.logger.error("Keyword search failed: %s", exc)
            return []

    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete all chunks for the given document IDs.

        Note: LEANN doesn't support efficient deletions. This requires
        rebuilding the index without the deleted documents.

        Args:
            doc_ids: List of document IDs to delete.
        """
        if not doc_ids:
            return

        try:
            # Remove chunks from pending list
            self._pending_chunks = [
                chunk for chunk in self._pending_chunks
                if chunk["doc_id"] not in doc_ids
            ]

            # If index is built, we need to rebuild it
            if self._index_built:
                self.logger.warning(
                    "LEANN index will be rebuilt after deletion of %d documents",
                    len(doc_ids),
                )
                # Rebuild index with remaining chunks
                if self._pending_chunks:
                    self.builder = None  # Reset builder
                    self._index_built = False
                    self.searcher = None
                    # Rebuild will happen on next search or explicit build call
                else:
                    # No chunks left, delete index file
                    if os.path.exists(self.index_path):
                        os.remove(self.index_path)
                        self.logger.info("Deleted LEANN index file (no documents remaining)")

            self.logger.info(
                "Marked %d documents for deletion from LEANN index",
                len(doc_ids),
            )
        except Exception as exc:
            self.logger.error("Failed to delete documents: %s", exc)
            raise

    def list_all_documents(self) -> List[Dict[str, Any]]:
        """Return all documents in the index.

        Returns:
            List of dictionaries with doc_id, chunk_id, path, content, metadata.
        """
        return self._pending_chunks.copy()

    def get_distinct_repo_urls(self) -> List[str]:
        """Get distinct repository URLs from all indexed documents.

        Returns:
            List of unique repository URLs (normalized).
        """
        repo_urls = set()
        for chunk in self._pending_chunks:
            metadata = chunk.get("metadata", {})
            repo_url = metadata.get("repo_url")
            if repo_url:
                normalized = repo_url.rstrip(".git")
                if not normalized.startswith("http"):
                    normalized = f"https://{normalized}"
                repo_urls.add(normalized)
        return sorted(list(repo_urls))

    def _serialize_metadata(self, metadata: Dict[str, Any]) -> str:
        """Serialize metadata dict to string for LEANN storage."""
        import json
        return json.dumps(metadata) if metadata else ""

    def _deserialize_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """Deserialize metadata string from LEANN to dict."""
        import json
        try:
            return json.loads(metadata_str) if metadata_str else {}
        except Exception:
            return {}

    def _find_chunk_by_content(self, content: str) -> Dict[str, Any] | None:
        """Find chunk info by matching content (fuzzy match)."""
        content_lower = content.lower().strip()
        for chunk in self._pending_chunks:
            chunk_content = chunk["content"].lower().strip()
            # Exact match or substring match
            if chunk_content == content_lower or content_lower in chunk_content or chunk_content in content_lower:
                return chunk
        return None
    
    def _find_metadata_file(self, index_path: str) -> str | None:
        """Find the metadata file for a given index path.
        
        LEANN requires a .meta.json file alongside the index file.
        This method checks for the metadata file in the expected location.
        
        Args:
            index_path: Path to the index file
            
        Returns:
            Path to metadata file if found, None otherwise
        """
        meta_path = f"{os.path.splitext(index_path)[0]}.meta.json"
        if os.path.exists(meta_path):
            return meta_path
        
        # Check alternative locations
        index_dir = os.path.dirname(index_path)
        index_base = os.path.basename(os.path.splitext(index_path)[0])
        
        # Check for metadata files in the same directory
        if index_dir and os.path.exists(index_dir):
            for filename in os.listdir(index_dir):
                if filename.startswith(index_base) and filename.endswith('.meta.json'):
                    return os.path.join(index_dir, filename)
        
        return None


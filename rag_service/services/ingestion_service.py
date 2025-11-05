"""
Document ingestion service for the RAG system.

This service is responsible for pulling content from external sources
and storing it in the knowledge base repository.  Currently it
supports cloning a GitLab repository, extracting markdown files, and
splitting them into manageable chunks.  New document types can be
added later by extending this service.

Two indexing modes are supported:

* Full index: clone the repository and index all markdown files,
  overwriting any existing entries.
* Delta index: clone the repository and compare file hashes with
  previously indexed files.  Only new or modified files are reindexed,
  and any removed files are deleted from the knowledge base.

Observability is handled via structured logging.  Each step
emits events that can be ingested by a logging system.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

from ..repositories.base_kb_repo import BaseKnowledgeBaseRepository
from ..utils.gitlab_loader import GitLabError, clone_repo, extract_markdown_files
from ..utils.document_loader import (
    load_documents_recursive,
    split_document_text,
)
from ..utils.logging import get_logger, log_event
from ..config import Settings


class IngestionService:
    """Service for indexing documents from a GitLab repository."""

    def __init__(self, kb_repo: BaseKnowledgeBaseRepository, settings: Settings | None = None) -> None:
        self.kb_repo = kb_repo
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)
        # Get chunking parameters from settings
        if settings:
            self.chunk_max_words = settings.chunk_max_words
            self.chunk_overlap_words = settings.chunk_overlap_words
            self.max_workers = getattr(settings, "max_workers", 4)
            self.batch_size = getattr(settings, "batch_size", 100)
        else:
            self.chunk_max_words = 300
            self.chunk_overlap_words = 50
            self.max_workers = 4
            self.batch_size = 100

    def _hash_text(self, text: str) -> str:
        """Return a SHA256 hash of the given text."""
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

    def _process_single_file(
        self, rel_path: str, content: str
    ) -> List[Dict[str, Any]]:
        """Process a single document file (markdown or PDF) into chunks.

        Automatically determines the chunking strategy based on file extension.
        Supports both markdown and PDF files.

        Args:
            rel_path: Relative path of the file.
            content: File content.
        Returns:
            List of document dictionaries for this file.
        """
        doc_id = rel_path
        file_hash = self._hash_text(content)
        chunks = split_document_text(
            content,
            file_path=rel_path,
            max_words=self.chunk_max_words,
            overlap=self.chunk_overlap_words,
        )
        documents = []
        for idx, chunk in enumerate(chunks):
            documents.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}:{idx}",
                    "path": rel_path,
                    "content": chunk,
                    "metadata": {"file_hash": file_hash},
                }
            )
        return documents

    def _prepare_documents(
        self, files: List[Tuple[str, str]], parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """Split markdown files into chunks and attach metadata.

        Uses parallel processing for large file sets to improve performance.
        Processing is done in parallel using ThreadPoolExecutor for I/O-bound
        chunking operations.

        Args:
            files: A list of tuples (relative_path, file_content).
            parallel: Whether to process files in parallel. Defaults to True.
        Returns:
            A list of document dictionaries ready for insertion into the
            knowledge base.
        """
        if not files:
            return []

        # For small file sets, process sequentially
        if len(files) <= 10 or not parallel:
            documents: List[Dict[str, Any]] = []
            for rel_path, content in files:
                documents.extend(self._process_single_file(rel_path, content))
            return documents

        # Parallel processing for larger file sets
        documents: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file processing tasks
            future_to_file = {
                executor.submit(self._process_single_file, rel_path, content): rel_path
                for rel_path, content in files
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_file):
                rel_path = future_to_file[future]
                try:
                    file_documents = future.result()
                    documents.extend(file_documents)
                    completed += 1
                    if completed % 10 == 0:
                        log_event(
                            self.logger,
                            "ingestion_progress",
                            processed=completed,
                            total=len(files),
                        )
                except Exception as exc:
                    log_event(
                        self.logger,
                        "ingestion_file_error",
                        file=rel_path,
                        error=str(exc),
                    )
                    # Continue processing other files even if one fails

        return documents

    def _batch_upsert(
        self, documents: List[Dict[str, Any]]
    ) -> None:
        """Upsert documents in batches to avoid overwhelming the database.

        Args:
            documents: List of document dictionaries to upsert.
        """
        if not documents:
            return

        # Process in batches
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i : i + self.batch_size]
            try:
                self.kb_repo.upsert_documents(batch)
                log_event(
                    self.logger,
                    "ingestion_batch_upserted",
                    batch_start=i,
                    batch_size=len(batch),
                    total=len(documents),
                )
            except Exception as exc:
                log_event(
                    self.logger,
                    "ingestion_batch_error",
                    batch_start=i,
                    batch_size=len(batch),
                    error=str(exc),
                )
                raise

    def index_repository(
        self, repo_url: str, token: str, branch: str | None = None
    ) -> Dict[str, int]:
        """Perform a full index of the given GitLab repository.

        All markdown files in the repository will be processed and
        stored in the knowledge base.  Existing entries for the same
        document IDs will be replaced.

        Returns:
            A summary dictionary with counts of indexed documents and chunks.
        """
        log_event(self.logger, "index_start", repo=repo_url, branch=branch)
        try:
            repo_dir = clone_repo(repo_url, token, branch)
        except GitLabError as exc:
            log_event(self.logger, "index_clone_error", error=str(exc))
            raise
        try:
            files = extract_markdown_files(repo_dir)
            log_event(
                self.logger,
                "ingestion_files_extracted",
                count=len(files),
                parallel=self.max_workers > 1,
            )
            documents = self._prepare_documents(files, parallel=True)
            # Replace any existing documents for these doc_ids
            doc_ids = list({doc["doc_id"] for doc in documents})
            try:
                self.kb_repo.delete_documents(doc_ids)
            except Exception:
                # deletion might not be supported; ignore
                pass
            # Upsert all chunks in batches
            self._batch_upsert(documents)
            log_event(
                self.logger,
                "index_complete",
                repo=repo_url,
                branch=branch,
                files=len(files),
                chunks=len(documents),
            )
            return {"files_indexed": len(files), "chunks_indexed": len(documents)}
        finally:
            # Clean up the cloned repo
            shutil.rmtree(repo_dir, ignore_errors=True)

    def delta_index_repository(
        self, repo_url: str, token: str, branch: str | None = None
    ) -> Dict[str, int]:
        """Perform a delta index of the repository.

        Only new or modified markdown files are reindexed.  Files that
        have been deleted from the repository are removed from the
        knowledge base.

        Returns:
            Summary dictionary with counts of processed files and chunks.
        """
        log_event(self.logger, "delta_index_start", repo=repo_url, branch=branch)
        try:
            repo_dir = clone_repo(repo_url, token, branch)
        except GitLabError as exc:
            log_event(self.logger, "delta_index_clone_error", error=str(exc))
            raise
        try:
            files = extract_markdown_files(repo_dir)
            log_event(
                self.logger,
                "delta_ingestion_files_extracted",
                count=len(files),
                parallel=self.max_workers > 1,
            )
            
            # Build a map of current file hashes using parallel processing
            def process_file_for_hash(rel_path: str, content: str) -> Tuple[str, Tuple[str, List[str]]]:
                """Process a single file to compute hash and chunks."""
                return (
                    rel_path,
                    (
                        self._hash_text(content),
                        split_document_text(
                            content,
                            file_path=rel_path,
                            max_words=self.chunk_max_words,
                            overlap=self.chunk_overlap_words,
                        ),
                    ),
                )
            
            incoming: Dict[str, Tuple[str, List[str]]] = {}
            if len(files) > 10 and self.max_workers > 1:
                # Parallel processing for larger file sets
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_file = {
                        executor.submit(process_file_for_hash, rel_path, content): rel_path
                        for rel_path, content in files
                    }
                    for future in as_completed(future_to_file):
                        rel_path = future_to_file[future]
                        try:
                            rel_path_result, (file_hash, chunks) = future.result()
                            incoming[rel_path_result] = (file_hash, chunks)
                        except Exception as exc:
                            log_event(
                                self.logger,
                                "delta_ingestion_file_error",
                                file=rel_path,
                                error=str(exc),
                            )
            else:
                # Sequential processing for small file sets
                for rel_path, content in files:
                    incoming[rel_path] = (
                        self._hash_text(content),
                        split_document_text(
                            content,
                            file_path=rel_path,
                            max_words=self.chunk_max_words,
                            overlap=self.chunk_overlap_words,
                        ),
                    )
            # Build a map of existing documents by path
            existing_rows = []
            try:
                if hasattr(self.kb_repo, "list_all_documents"):
                    existing_rows = self.kb_repo.list_all_documents()
            except Exception:
                # Listing might not be supported; treat as empty
                existing_rows = []
            existing_hash: Dict[str, str] = {}
            for row in existing_rows:
                # metadata may be None if older rows do not have file_hash
                meta = row.get("metadata") or {}
                file_hash = meta.get("file_hash")
                if file_hash:
                    existing_hash[row["path"]] = file_hash
            # Determine which files are new or changed
            # Process in parallel for large file sets
            new_docs: List[Dict[str, Any]] = []
            modified_doc_ids: List[str] = []
            
            def process_file_for_delta(
                rel_path: str, file_hash: str, chunks: List[str]
            ) -> Tuple[List[Dict[str, Any]], bool]:
                """Process a single file and return documents and whether it was modified."""
                docs = []
                is_modified = False
                if rel_path not in existing_hash:
                    # New file
                    doc_id = rel_path
                    for idx, chunk in enumerate(chunks):
                        docs.append(
                            {
                                "doc_id": doc_id,
                                "chunk_id": f"{doc_id}:{idx}",
                                "path": rel_path,
                                "content": chunk,
                                "metadata": {"file_hash": file_hash},
                            }
                        )
                elif existing_hash[rel_path] != file_hash:
                    # Modified file
                    is_modified = True
                    doc_id = rel_path
                    for idx, chunk in enumerate(chunks):
                        docs.append(
                            {
                                "doc_id": doc_id,
                                "chunk_id": f"{doc_id}:{idx}",
                                "path": rel_path,
                                "content": chunk,
                                "metadata": {"file_hash": file_hash},
                            }
                        )
                return docs, is_modified
            
            # Use parallel processing for large file sets
            if len(incoming) > 10 and self.max_workers > 1:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_file = {
                        executor.submit(
                            process_file_for_delta, rel_path, file_hash, chunks
                        ): rel_path
                        for rel_path, (file_hash, chunks) in incoming.items()
                    }
                    for future in as_completed(future_to_file):
                        rel_path = future_to_file[future]
                        try:
                            docs, is_modified = future.result()
                            new_docs.extend(docs)
                            if is_modified:
                                modified_doc_ids.append(rel_path)
                        except Exception as exc:
                            log_event(
                                self.logger,
                                "delta_ingestion_process_error",
                                file=rel_path,
                                error=str(exc),
                            )
            else:
                # Sequential processing for small file sets
                for rel_path, (file_hash, chunks) in incoming.items():
                    docs, is_modified = process_file_for_delta(
                        rel_path, file_hash, chunks
                    )
                    new_docs.extend(docs)
                    if is_modified:
                        modified_doc_ids.append(rel_path)
            # Determine which documents were deleted
            deleted_doc_ids: List[str] = []
            for path in existing_hash.keys():
                if path not in incoming:
                    deleted_doc_ids.append(path)
            # Apply deletions first
            if deleted_doc_ids:
                try:
                    self.kb_repo.delete_documents(deleted_doc_ids)
                except Exception:
                    # Deletion might not be supported; log and continue
                    log_event(self.logger, "delta_index_delete_failed", docs=deleted_doc_ids)
            # Delete modified docs before reindexing them
            if modified_doc_ids:
                try:
                    self.kb_repo.delete_documents(modified_doc_ids)
                except Exception:
                    log_event(self.logger, "delta_index_delete_failed", docs=modified_doc_ids)
            # Insert new/modified docs in batches
            if new_docs:
                self._batch_upsert(new_docs)
            log_event(
                self.logger,
                "delta_index_complete",
                repo=repo_url,
                branch=branch,
                new_files=len([p for p in incoming.keys() if p not in existing_hash]),
                modified_files=len(modified_doc_ids),
                deleted_files=len(deleted_doc_ids),
                chunks=len(new_docs),
            )
            return {
                "new_files": len([p for p in incoming.keys() if p not in existing_hash]),
                "modified_files": len(modified_doc_ids),
                "deleted_files": len(deleted_doc_ids),
                "chunks_indexed": len(new_docs),
            }
        finally:
            shutil.rmtree(repo_dir, ignore_errors=True)

    def index_local_folder(self, folder_path: str) -> Dict[str, int]:
        """Perform a full index of markdown files from a local folder.

        Recursively scans the folder for markdown files (`.md` or `.markdown`)
        and indexes them into the knowledge base. This is useful for testing
        or indexing local documentation without requiring a GitLab repository.

        Args:
            folder_path: Absolute or relative path to the folder containing
                markdown files. The function will recursively search subdirectories.

        Returns:
            A summary dictionary with counts of indexed documents and chunks.

        Raises:
            ValueError: If the folder path doesn't exist or is not a directory.
            IOError: If there are issues reading files from the folder.
        """
        log_event(self.logger, "local_index_start", folder=folder_path)

        # Validate folder path
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder path does not exist: {folder_path}")
        if not os.path.isdir(folder_path):
            raise ValueError(f"Path is not a directory: {folder_path}")

        # Get absolute path for consistent relative paths
        abs_folder_path = os.path.abspath(folder_path)

        # Extract markdown, PDF, and Word files recursively
        files = load_documents_recursive(
            abs_folder_path, include_markdown=True, include_pdf=True, include_word=True
        )
        if not files:
            log_event(self.logger, "local_index_no_files", folder=folder_path)
            return {"files_indexed": 0, "chunks_indexed": 0}

        log_event(
            self.logger,
            "local_index_files_extracted",
            count=len(files),
            parallel=self.max_workers > 1,
        )

        # Process files in parallel
        documents = self._prepare_documents(files, parallel=True)

        # Replace any existing documents for these doc_ids
        doc_ids = list({doc["doc_id"] for doc in documents})
        try:
            self.kb_repo.delete_documents(doc_ids)
        except Exception:
            # deletion might not be supported; ignore
            pass

        # Upsert all chunks in batches
        self._batch_upsert(documents)

        log_event(
            self.logger,
            "local_index_complete",
            folder=folder_path,
            files=len(files),
            chunks=len(documents),
        )

        return {"files_indexed": len(files), "chunks_indexed": len(documents)}
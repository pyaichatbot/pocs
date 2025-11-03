"""
FastAPI application entry point for the RAG service.

This module serves as the main entry point for running the FastAPI
application. It imports the app from the api module and can be run
directly using uvicorn or via the command line.

Usage:
    uvicorn rag_service.main:app --reload
    # or
    python -m rag_service.main
"""

from rag_service.api import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


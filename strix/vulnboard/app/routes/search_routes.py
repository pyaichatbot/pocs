"""Search routes - SQL injection and XSS vulnerabilities."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from app.core.db import Database
from app.services.search_service import SearchService
from app.routes.auth_routes import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
db = Database()
search_service = SearchService(db)


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = Query("")):
    """
    Search page with SQL injection and XSS vulnerabilities.
    VULNERABILITY: SQL Injection - uses unsafe_query method
    VULNERABILITY: Reflected XSS - search query reflected without sanitization
    """
    current_user = get_current_user(request)
    
    results = []
    sql_error = None
    if q:
        try:
            # VULNERABILITY: SQL Injection
            # Uses unsafe search method that concatenates user input directly into SQL
            # Attack example: q = "'; DROP TABLE posts; --"
            results = search_service.search_posts_unsafe(q)
        except ValueError as e:
            # Catch SQL injection errors and display them for demo purposes
            sql_error = str(e)
            results = []
    
    # VULNERABILITY: Reflected XSS
    # Search query 'q' is reflected in template without sanitization
    # Attack example: q = "<script>alert('XSS')</script>"
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "query": q,  # VULNERABILITY: Unescaped user input
            "results": results,
            "sql_error": sql_error,  # Show SQL injection error for demo
            "current_user": current_user
        }
    )


@router.get("/posts", response_class=HTMLResponse)
async def posts_page(request: Request):
    """List all posts."""
    current_user = get_current_user(request)
    
    # Safe query using parameterized queries
    all_posts = search_service.get_posts_by_user(0)  # Get all posts (user_id 0 doesn't exist, so returns empty)
    # Actually get all posts
    query = "SELECT * FROM posts ORDER BY created_at DESC"
    results = db.execute_query(query)
    
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "query": "",
            "results": results,
            "current_user": current_user
        }
    )


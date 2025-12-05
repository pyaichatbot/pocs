"""Authentication routes - login/logout."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.templating import Jinja2Templates
from app.core.db import Database
from app.services.auth_service import AuthService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
db = Database()
auth_service = AuthService(db)


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Anonymous landing page."""
    return templates.TemplateResponse("landing.html", {"request": request, "current_user": None})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Login endpoint.
    Uses parameterized queries correctly (no SQL injection here).
    """
    user = auth_service.authenticate(username, password)
    
    if user:
        # In a real app, would set secure session cookie
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie(key="user_id", value=str(user.id))
        response.set_cookie(key="username", value=user.username)
        response.set_cookie(key="role", value=user.role)
        return response
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )


@router.get("/logout")
async def logout():
    """Logout endpoint."""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user_id")
    response.delete_cookie(key="username")
    response.delete_cookie(key="role")
    return response


def get_current_user(request: Request):
    """Helper to get current user from cookies."""
    user_id = request.cookies.get("user_id")
    username = request.cookies.get("username")
    role = request.cookies.get("role")
    
    if user_id:
        return {"id": int(user_id), "username": username, "role": role}
    return None


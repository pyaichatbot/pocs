"""User routes - IDOR vulnerability."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from app.core.db import Database
from app.services.user_service import UserService
from app.routes.auth_routes import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
db = Database()
user_service = UserService(db)


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user_id: int = None):
    """
    User profile page.
    VULNERABILITY: IDOR (Insecure Direct Object Reference)
    - Allows any user to view any profile by changing the user_id parameter
    - No authorization check - missing call to check_authorization()
    """
    current_user = get_current_user(request)
    
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    # VULNERABILITY: Uses user_id from query parameter without authorization check
    # Should verify: current_user["id"] == user_id or current_user["role"] == "admin"
    # But intentionally bypassed to demonstrate IDOR
    profile_user_id = user_id if user_id else current_user["id"]
    
    user = user_service.get_user_profile(
        profile_user_id,
        requesting_user_id=current_user["id"],
        requesting_user_role=current_user["role"]
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # VULNERABILITY: XSS - user data reflected without sanitization in template
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "current_user": current_user,
            "is_own_profile": current_user["id"] == user.id
        }
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def get_user(request: Request, user_id: int):
    """
    Get user by ID endpoint.
    VULNERABILITY: IDOR - no authorization check.
    """
    current_user = get_current_user(request)
    
    # VULNERABILITY: No authorization check - any logged-in user can access any profile
    user = user_service.get_user_profile(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "current_user": current_user or {},
            "is_own_profile": False
        }
    )


"""Main FastAPI application setup and route wiring."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from app.routes import auth_routes, user_routes, search_routes, ai_routes
from app.config import DEBUG, HOST, PORT

app = FastAPI(
    title="VulnBoard",
    description="Intentionally Vulnerable AI Application for Security Training",
    version="1.0.0",
    debug=DEBUG
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(search_routes.router)
app.include_router(ai_routes.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "VulnBoard is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)


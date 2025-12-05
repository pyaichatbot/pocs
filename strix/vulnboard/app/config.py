"""Configuration settings for VulnBoard application."""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Database
DATABASE_PATH = BASE_DIR / "vulnboard.db"

# Security (intentionally weak for demo)
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-secret-key-for-demo-only")
SESSION_COOKIE_NAME = "vulnboard_session"

# AI Configuration (intentionally insecure - hardcoded keys, no validation)
# VULNERABILITY: Insecure AI Model Usage - API keys should not be hardcoded
AI_API_KEY = os.getenv("AI_API_KEY", "sk-hardcoded-key-for-demo-only")
AI_MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
# VULNERABILITY: No rate limiting configured
AI_RATE_LIMIT = None

# Application
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


"""Configuration module for DeepTeam Demo Suite."""

from .settings import Settings, get_settings
from .logging_config import setup_logging

__all__ = ["Settings", "get_settings", "setup_logging"]


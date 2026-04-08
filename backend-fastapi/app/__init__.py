"""Document Intelligence Platform - Backend Services"""

__version__ = "1.0.0"
__author__ = "AI Engineering Team"

from app.config import settings
from app.core.logger import setup_logging

# Setup logging on import
setup_logging()

__all__ = ["settings"]
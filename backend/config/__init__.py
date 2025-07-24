"""
Configuration package for iloveresume backend
"""

from .settings import *
from .cors import get_cors_config

__all__ = ['get_cors_config', 'DATABASE_URL', 'PROJECT_ID', 'LOCATION', 'CORS_ORIGINS'] 
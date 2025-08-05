"""
CORS 설정 관리
"""

from .settings import CORS_ORIGINS

def get_cors_config():
    """CORS 설정 반환"""
    return {
        r"/api/*": {
            "origins": CORS_ORIGINS,
            "methods": ["GET", "POST", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    } 
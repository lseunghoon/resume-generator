"""
환경 설정 및 애플리케이션 설정 통합 관리
"""

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 설정
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///resume_ai.db')

# Vertex AI 설정
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")

# 환경 변수 검증
if not PROJECT_ID or not LOCATION:
    raise ValueError("환경 변수 파일(.env)에 PROJECT_ID와 LOCATION을 반드시 설정해야 합니다.")

# CORS 설정
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# 로깅 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_MAX_BYTES = int(os.getenv("LOG_FILE_MAX_BYTES", "1048576"))  # 1MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "10"))

# 파일 업로드 설정
ALLOWED_EXTENSIONS = {'.pdf', '.docx'}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB

# AI 모델 설정
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-001")

# 크롤링 설정
CRAWLING_TIMEOUT = int(os.getenv("CRAWLING_TIMEOUT", "10"))
OCR_TEXT_MIN_LENGTH = int(os.getenv("OCR_TEXT_MIN_LENGTH", "200"))
MIN_REQUIRED_KEYWORDS = int(os.getenv("MIN_REQUIRED_KEYWORDS", "2"))

# ChromeDriver 설정
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")  # 수동 경로 지정 옵션
USE_CHROME_HEADLESS = os.getenv("USE_CHROME_HEADLESS", "true").lower() == "true"
CHROME_FALLBACK_MODE = os.getenv("CHROME_FALLBACK_MODE", "true").lower() == "true"

# 디렉토리 설정
LOGS_DIR = "logs"
UPLOADS_DIR = "uploads"

def validate_settings():
    """설정값 유효성 검증"""
    required_env_vars = ["PROJECT_ID", "LOCATION"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
    
    return True

def get_database_config():
    """데이터베이스 설정 반환"""
    return {
        'url': DATABASE_URL,
        'echo': LOG_LEVEL.upper() == 'DEBUG'
    }

def get_vertex_ai_config():
    """Vertex AI 설정 반환"""
    return {
        'project_id': PROJECT_ID,
        'location': LOCATION,
        'model_name': GEMINI_MODEL_NAME
    }

def get_file_config():
    """파일 처리 설정 반환"""
    return {
        'allowed_extensions': ALLOWED_EXTENSIONS,
        'max_file_size': MAX_FILE_SIZE,
        'uploads_dir': UPLOADS_DIR
    }

def get_crawling_config():
    """크롤링 설정 반환"""
    return {
        'timeout': CRAWLING_TIMEOUT,
        'ocr_text_min_length': OCR_TEXT_MIN_LENGTH,
        'min_required_keywords': MIN_REQUIRED_KEYWORDS,
        'chrome_driver_path': CHROME_DRIVER_PATH,
        'use_chrome_headless': USE_CHROME_HEADLESS,
        'chrome_fallback_mode': CHROME_FALLBACK_MODE
    } 
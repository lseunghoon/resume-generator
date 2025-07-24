"""
로깅 설정 통합 관리
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from config.settings import LOG_LEVEL, LOG_FILE_MAX_BYTES, LOG_BACKUP_COUNT, LOGS_DIR


def setup_logger(name=None, log_file='app.log'):
    """
    로거 설정 및 반환
    
    Args:
        name (str): 로거 이름 (None이면 root logger)
        log_file (str): 로그 파일명
        
    Returns:
        logging.Logger: 설정된 로거 객체
    """
    # 로그 디렉토리 생성
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # 이미 핸들러가 있으면 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    # 파일 핸들러 설정
    log_path = os.path.join(LOGS_DIR, log_file)
    file_handler = RotatingFileHandler(
        log_path, 
        maxBytes=LOG_FILE_MAX_BYTES, 
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    
    # 포매터 설정
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # 콘솔 핸들러 설정 (개발 환경용)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 상위 로거로의 전파 방지 (중복 로깅 방지)
    logger.propagate = False
    
    return logger


def get_logger(name=None):
    """
    기존 로거 반환 또는 새로 생성
    
    Args:
        name (str): 로거 이름
        
    Returns:
        logging.Logger: 로거 객체
    """
    logger = logging.getLogger(name)
    
    # 핸들러가 없으면 새로 설정
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


def setup_flask_logger(app):
    """
    Flask 애플리케이션 로거 설정
    
    Args:
        app: Flask 앱 인스턴스
    """
    # Flask 기본 로거 설정
    app.logger = setup_logger('flask_app', 'flask.log')
    
    # Werkzeug 로거 설정 (요청 로깅)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)  # 요청 로그 최소화
    
    return app.logger


class LoggerMixin:
    """
    클래스에 로거 기능을 추가하는 믹스인
    """
    
    @property
    def logger(self):
        """클래스별 로거 반환"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_function_call(func):
    """
    함수 호출을 로깅하는 데코레이터
    
    Usage:
        @log_function_call
        def my_function():
            pass
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"함수 호출: {func.__name__}({args}, {kwargs})")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"함수 완료: {func.__name__} -> {type(result)}")
            return result
        except Exception as e:
            logger.error(f"함수 오류: {func.__name__} -> {str(e)}")
            raise
    
    return wrapper


def log_api_request(func):
    """
    API 요청을 로깅하는 데코레이터
    
    Usage:
        @app.route('/api/test')
        @log_api_request
        def test_api():
            pass
    """
    def wrapper(*args, **kwargs):
        from flask import request
        
        logger = get_logger('api')
        logger.info(f"API 요청: {request.method} {request.path}")
        logger.debug(f"요청 데이터: {request.get_json() if request.is_json else 'Non-JSON'}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"API 성공: {request.method} {request.path}")
            return result
        except Exception as e:
            logger.error(f"API 오류: {request.method} {request.path} -> {str(e)}")
            raise
    
    return wrapper 
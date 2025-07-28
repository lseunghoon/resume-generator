"""
Utility functions package for iloveresume backend
"""

from .file_processor import parse_pdf, parse_docx, validate_file_type, extract_text_from_file, get_file_info, FileProcessingError
from .logger import setup_logger, get_logger, setup_flask_logger
from .validators import (
    validate_session_data, validate_question_data, validate_revision_request,
    validate_session_id, validate_question_index, ValidationError
)


__all__ = [
    'parse_pdf', 'parse_docx', 'validate_file_type', 'extract_text_from_file', 'get_file_info', 'FileProcessingError',
    'setup_logger', 'get_logger', 'setup_flask_logger',
    'validate_session_data', 'validate_question_data', 'validate_revision_request',
    'validate_session_id', 'validate_question_index', 'ValidationError'
] 
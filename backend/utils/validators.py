"""
데이터 검증 유틸리티 함수들
"""

import re
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """데이터 검증 관련 예외"""
    pass


def validate_session_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    세션 데이터 검증
    
    Args:
        data (Dict[str, Any]): 검증할 세션 데이터
        
    Returns:
        Dict[str, Any]: 검증된 세션 데이터
        
    Raises:
        ValidationError: 데이터가 유효하지 않은 경우
    """
    if not data or not isinstance(data, dict):
        raise ValidationError("세션 데이터가 필요합니다.")
    
    # 필수 필드 검증
    required_fields = ['resumeText', 'jobDescription']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"필수 필드가 누락되었습니다: {field}")
        
        if not data[field] or not isinstance(data[field], str):
            raise ValidationError(f"필드 {field}는 비어있지 않은 문자열이어야 합니다.")
    
    # 텍스트 길이 검증
    if len(data['resumeText'].strip()) < 50:
        raise ValidationError("이력서 텍스트는 최소 50자 이상이어야 합니다.")
    
    if len(data['jobDescription'].strip()) < 50:
        raise ValidationError("채용공고 텍스트는 최소 50자 이상이어야 합니다.")
    
    # 질문 필드 검증 (선택사항)
    questions = data.get('questions', [])
    if not isinstance(questions, list):
        questions = []
    
    # 텍스트 정제
    validated_data = {
        'resumeText': sanitize_text(data['resumeText']),
        'jobDescription': sanitize_text(data['jobDescription']),
        'questions': questions,
        # 사용자가 입력한 개별 필드들 추가
        'companyName': data.get('companyName', ''),
        'jobTitle': data.get('jobTitle', ''),
        'mainResponsibilities': data.get('mainResponsibilities', ''),
        'requirements': data.get('requirements', ''),
        'preferredQualifications': data.get('preferredQualifications', '')
    }
    
    return validated_data


def validate_question_data(question: str) -> Dict[str, Any]:
    """
    질문 데이터 검증
    
    Args:
        question (str): 검증할 질문 텍스트
    
    Returns:
        Dict[str, Any]: 검증된 질문 데이터
        
    Raises:
        ValidationError: 검증 실패 시
    """
    if not question or not question.strip():
        raise ValidationError("질문을 입력해주세요.")
    
    validated_question = question.strip()
    
    if len(validated_question) > 2000:
        raise ValidationError("질문은 최대 2000자까지 입력 가능합니다.")
    
    return {
        'question': validated_question,
        'length': len(validated_question)
    }


def validate_revision_request(revision_text: str) -> str:
    """
    수정 요청 텍스트 검증
    
    Args:
        revision_text (str): 검증할 수정 요청 텍스트
        
    Returns:
        str: 검증된 수정 요청 텍스트
        
    Raises:
        ValidationError: 수정 요청이 유효하지 않은 경우
    """
    if not revision_text or not isinstance(revision_text, str):
        raise ValidationError("수정 요청 텍스트가 필요합니다.")
    
    revision_text = revision_text.strip()
    
    if len(revision_text) < 5:
        raise ValidationError("수정 요청은 최소 5자 이상이어야 합니다.")
    
    if len(revision_text) > 1000:
        raise ValidationError("수정 요청은 최대 1000자까지 입력 가능합니다.")
    
    return sanitize_text(revision_text)


def validate_json_data(json_string: str) -> Dict[str, Any]:
    """
    JSON 문자열 검증 및 파싱
    
    Args:
        json_string (str): 검증할 JSON 문자열
        
    Returns:
        Dict[str, Any]: 파싱된 JSON 데이터
        
    Raises:
        ValidationError: JSON이 유효하지 않은 경우
    """
    if not json_string or not isinstance(json_string, str):
        raise ValidationError("JSON 문자열이 필요합니다.")
    
    try:
        data = json.loads(json_string)
        if not isinstance(data, dict):
            raise ValidationError("JSON은 객체 형태여야 합니다.")
        return data
    except json.JSONDecodeError as e:
        raise ValidationError(f"유효하지 않은 JSON 형식입니다: {str(e)}")


def validate_session_id(session_id: str) -> str:
    """
    세션 ID 검증
    
    Args:
        session_id (str): 검증할 세션 ID
        
    Returns:
        str: 검증된 세션 ID
        
    Raises:
        ValidationError: 세션 ID가 유효하지 않은 경우
    """
    if not session_id or not isinstance(session_id, str):
        raise ValidationError("세션 ID가 필요합니다.")
    
    session_id = session_id.strip()
    
    # 길이 검증 (UUID는 36자)
    if len(session_id) != 36:
        raise ValidationError("세션 ID 길이가 올바르지 않습니다.")
    
    # UUID 형식 검증 (정확한 패턴)
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, session_id, re.IGNORECASE):
        raise ValidationError("유효하지 않은 세션 ID 형식입니다.")
    
    # 특수 문자나 위험한 패턴 검증
    dangerous_patterns = [
        r'\.\.',  # 경로 순회 공격 방지
        r'[<>"\']',  # XSS 방지
        r'javascript:',  # JavaScript 인젝션 방지
        r'data:',  # Data URL 방지
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, session_id, re.IGNORECASE):
            raise ValidationError("세션 ID에 허용되지 않는 문자가 포함되어 있습니다.")
    
    return session_id


def validate_question_index(index: Any, max_questions: int = 3) -> int:
    """
    질문 인덱스 검증
    
    Args:
        index (Any): 검증할 인덱스
        max_questions (int): 최대 질문 수
        
    Returns:
        int: 검증된 인덱스
        
    Raises:
        ValidationError: 인덱스가 유효하지 않은 경우
    """
    try:
        question_index = int(index)
    except (ValueError, TypeError):
        raise ValidationError("질문 인덱스는 정수여야 합니다.")
    
    if question_index < 1 or question_index > max_questions:
        raise ValidationError(f"질문 인덱스는 1부터 {max_questions}까지의 값이어야 합니다.")
    
    return question_index


def sanitize_text(text: str) -> str:
    """
    텍스트 정제 (XSS 방지, 불필요한 공백 제거)
    
    Args:
        text (str): 정제할 텍스트
        
    Returns:
        str: 정제된 텍스트
    """
    if not text:
        return ""
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # 특수 문자 이스케이프 (XSS 방지)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    
    # 연속된 공백을 하나로 치환
    text = re.sub(r'\s+', ' ', text)
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    return text 
"""
Supabase 기반 모델 정의
기존 SQLAlchemy 모델을 Supabase로 대체
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase_client import SupabaseService

def _parse_answer_history(history_str: str) -> list:
    """
    answer_history 문자열을 파싱합니다.
    """
    if not history_str:
        return []
    try:
        return json.loads(history_str)
    except json.JSONDecodeError as e:
        if 'Invalid control character' in str(e):
            # 줄바꿈 문자를 이스케이프하여 수정 시도
            fixed_str = history_str.replace('\n', '\\n').replace('\r', '')
            try:
                return json.loads(fixed_str)
            except json.JSONDecodeError:
                pass
        return []

class SupabaseSession:
    """Supabase 기반 세션 모델"""
    
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
    
    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 세션 생성"""
        return self.supabase.create_session(user_id, session_data)
    
    def get_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """세션 조회"""
        return self.supabase.get_session(session_id, user_id)
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 모든 세션 조회"""
        return self.supabase.get_user_sessions(user_id)
    
    def update_session(self, session_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """세션 업데이트"""
        return self.supabase.update_session(session_id, user_id, update_data)
    
    def delete_session(self, session_id: str, user_id: str) -> bool:
        """세션 삭제"""
        return self.supabase.delete_session(session_id, user_id)
    
    def to_dict(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """세션 데이터를 딕셔너리로 변환"""
        return {
            'id': session_data.get('id'),
            'created_at': session_data.get('created_at'),
            'company_name': session_data.get('company_name'),
            'job_title': session_data.get('job_title'),
            'main_responsibilities': session_data.get('main_responsibilities'),
            'requirements': session_data.get('requirements'),
            'preferred_qualifications': session_data.get('preferred_qualifications'),
            'jd_text': session_data.get('jd_text'),
            'resume_text': session_data.get('resume_text'),
            'company_info': session_data.get('company_info')
        }

class SupabaseQuestion:
    """Supabase 기반 질문 모델"""
    
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
    
    def create_question(self, session_id: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """질문 생성"""
        return self.supabase.create_question(session_id, question_data)
    
    def get_session_questions(self, session_id: str) -> List[Dict[str, Any]]:
        """세션의 모든 질문 조회"""
        return self.supabase.get_session_questions(session_id)
    
    def update_question(self, question_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """질문 업데이트"""
        return self.supabase.update_question(question_id, update_data)
    
    def delete_question(self, question_id: int) -> bool:
        """질문 삭제"""
        return self.supabase.delete_question(question_id)
    
    def to_dict(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """질문 데이터를 딕셔너리로 변환"""
        answerHistory = _parse_answer_history(question_data.get('answer_history', ''))
        current_answer = answerHistory[question_data.get('current_version_index', 0)] if answerHistory and 0 <= question_data.get('current_version_index', 0) < len(answerHistory) else None
        
        return {
            'id': question_data.get('id'),
            'question_number': question_data.get('question_number'),
            'question': question_data.get('question'),
            'answer': current_answer,
            'answer_history': answerHistory,
            'current_version_index': question_data.get('current_version_index', 0),
            'length': len(current_answer) if current_answer else 0,
            'has_undo': (question_data.get('current_version_index', 0) > 0),
            'has_redo': len(answerHistory) > (question_data.get('current_version_index', 0) + 1)
        }

class SupabaseUser:
    """Supabase 기반 사용자 모델"""
    
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 조회"""
        return self.supabase.get_user_by_email(email)
    
    def create_user(self, email: str, password: str) -> Dict[str, Any]:
        """새 사용자 생성"""
        return self.supabase.create_user(email, password)

# 전역 Supabase 서비스 인스턴스
_supabase_service = None
_session_model = None
_question_model = None
_user_model = None

def init_supabase_models():
    """Supabase 모델 초기화"""
    global _supabase_service, _session_model, _question_model, _user_model
    
    from supabase_client import SupabaseService
    _supabase_service = SupabaseService()
    _session_model = SupabaseSession(_supabase_service)
    _question_model = SupabaseQuestion(_supabase_service)
    _user_model = SupabaseUser(_supabase_service)

def get_session_model() -> SupabaseSession:
    """세션 모델 반환"""
    global _session_model
    if _session_model is None:
        init_supabase_models()
    return _session_model

def get_question_model() -> SupabaseQuestion:
    """질문 모델 반환"""
    global _question_model
    if _question_model is None:
        init_supabase_models()
    return _question_model

def get_user_model() -> SupabaseUser:
    """사용자 모델 반환"""
    global _user_model
    if _user_model is None:
        init_supabase_models()
    return _user_model

def get_supabase_service() -> SupabaseService:
    """Supabase 서비스 반환"""
    global _supabase_service
    if _supabase_service is None:
        init_supabase_models()
    return _supabase_service 
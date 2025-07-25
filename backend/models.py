"""
SQLAlchemy 모델 정의 (리팩토링 버전)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

from config.settings import get_database_config

Base = declarative_base()

def _parse_answer_history(history_str: str) -> list:
    """
    answer_history 문자열을 파싱합니다.
    이전 마이그레이션 스크립트 오류로 인해 이스케이프되지 않은
    제어 문자가 포함된 경우를 대비한 폴백 로직을 포함합니다.
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
                pass  # 수정 실패 시 아래의 빈 리스트 반환으로 넘어감
        # 그 외 JSON 오류거나 수정 실패 시
        return []

class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    jd_url = Column(Text)
    jd_text = Column(Text)
    resume_text = Column(Text)
    
    # 관계 설정
    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'jd_url': self.jd_url,
            'jd_text': self.jd_text,
            'resume_text': self.resume_text,
            'questions': [q.to_dict() for q in self.questions]
        }

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    length = Column(Integer, nullable=False)
    
    # 세션 내 질문 번호 (1, 2, 3...)
    question_number = Column(Integer, nullable=False)
    
    # 버전 히스토리 시스템
    answer_history = Column(Text, nullable=True)  # JSON 형태의 문자열로 답변 리스트 저장
    current_version_index = Column(Integer, default=0, nullable=False)

    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False)
    
    # 관계 설정
    session = relationship("Session", back_populates="questions")
    
    def to_dict(self):
        history = _parse_answer_history(self.answer_history)
        current_answer = history[self.current_version_index] if history and 0 <= self.current_version_index < len(history) else None
        
        return {
            'question_number': self.question_number,  # 전역 ID 대신 세션 내 번호 사용
            'question': self.question,
            'length': self.length,
            'answer': current_answer,
            'has_undo': self.current_version_index > 0,
            'has_redo': self.current_version_index < len(history) - 1
        }

# 데이터베이스 설정 가져오기
db_config = get_database_config()

# 엔진 생성
engine = create_engine(db_config['url'], echo=db_config['echo'])

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 초기화
def init_db():
    Base.metadata.create_all(bind=engine)

# 데이터베이스 세션 제너레이터
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
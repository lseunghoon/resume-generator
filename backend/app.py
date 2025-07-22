from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import io
import json
import uuid
from datetime import datetime
import google.generativeai as genai
from bs4 import BeautifulSoup
import requests
from PyPDF2 import PdfReader
from docx import Document
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from models import Session, Question, get_db, init_db, _parse_answer_history
from sqlalchemy.orm import Session as DBSession
from werkzeug.utils import secure_filename
from job_crawler import crawl_job_description
from cover_letter_generator import generate_cover_letter, revise_cover_letter

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 로그 파일 핸들러 설정
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=1024*1024, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
logger.addHandler(file_handler)

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# CORS 설정
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
        "methods": ["GET", "POST", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

# 데이터베이스 초기화
init_db()

class APIError(Exception):
    """API 에러를 위한 커스텀 예외 클래스"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(APIError)
def handle_api_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/')
def index():
    """API 서버 상태 확인을 위한 루트 경로 핸들러"""
    return jsonify({
        'status': 'ok',
        'message': 'Resume AI API Server is running',
        'version': '1.0.0'
    })

@app.route('/api/v1/health')
def health_check():
    """API 서버 상태 확인을 위한 헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'ok',
        'message': 'API server is healthy'
    })

def validate_file_type(filename):
    """파일 타입 검증"""
    allowed_extensions = {'.pdf', '.docx'}
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        raise APIError(f"지원하지 않는 파일 형식입니다: {ext}. 지원되는 형식: {', '.join(allowed_extensions)}")

def parse_pdf(file_stream):
    """PDF 파일을 파싱하여 텍스트 추출"""
    stream = io.BytesIO(file_stream.read())
    reader = PdfReader(stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def parse_docx(file_stream):
    """DOCX 파일을 파싱하여 텍스트 추출"""
    stream = io.BytesIO(file_stream.read())
    doc = Document(stream)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

@app.route('/api/v1/upload', methods=['POST'])
def upload():
    """파일 업로드 및 세션 생성 (SQLAlchemy 사용)"""
    app.logger.info("===== /upload 요청 시작 =====")
    db = next(get_db()) # get_db() 제너레이터로부터 세션 객체를 가져옵니다.
    try:
        app.logger.info(f"Content-Type: {request.content_type}")
        app.logger.info(f"전체 Form 데이터: {request.form.to_dict()}")
        app.logger.info(f"파일 키: {list(request.files.keys())}")
        
        files = request.files.getlist('files')
        data_str = request.form.get('data')
        
        if not files or not any(f.filename for f in files):
            raise APIError("파일이 없습니다.", status_code=400)
        if not data_str:
            raise APIError("'data' 필드가 없습니다.", status_code=400)
            
        data = json.loads(data_str)
        job_description_url = data.get('jobDescriptionUrl')
        questions_data = data.get('questions', [])
        lengths_data = data.get('lengths', [])
        job_description = data.get('jobDescription')  # 추가: 미리 크롤링된 데이터 받기

        if not job_description_url or not questions_data:
            raise APIError("URL 또는 질문 데이터가 부족합니다.", status_code=400)
        
        # 직무 정보가 이미 제공된 경우 크롤링 건너뛰기 (최적화)
        if not job_description:
            app.logger.info("직무 정보가 없어 크롤링 시작")
            job_description = crawl_job_description(job_description_url)
            if not job_description:
                raise APIError("채용공고 크롤링에 실패했습니다.", status_code=400)
            app.logger.info("채용공고 크롤링 성공")
        else:
            app.logger.info("미리 크롤링된 직무 정보 사용 (크롤링 건너뛰기)")

        # 파일 텍스트 추출 (첫 번째 파일만 사용)
        resume_text = ""
        first_file = files[0]
        if first_file.filename.endswith('.pdf'):
            resume_text = parse_pdf(first_file.stream)
        elif first_file.filename.endswith('.docx'):
            resume_text = parse_docx(first_file.stream)

        # SQLAlchemy 세션을 사용하여 데이터베이스 작업 수행
        new_session = Session(
            id=str(uuid.uuid4()),
            jd_url=job_description_url,
            jd_text=job_description,
            resume_text=resume_text
        )

        for i, q_text in enumerate(questions_data):
            # lengths_data가 questions_data보다 짧을 수 있으므로, 인덱스 존재 여부 확인
            q_length_str = lengths_data[i] if i < len(lengths_data) else "1000" # 기본값 1000으로 설정
            try:
                # q_length_str이 비어있거나 None일 경우를 대비하여 기본값 설정
                q_length = int(q_length_str) if q_length_str else 1000
            except (ValueError, TypeError):
                q_length = 1000 # 숫자로 변환 실패 시 기본값

            new_question = Question(
                question=q_text,
                length=q_length
            )
            new_session.questions.append(new_question)

        db.add(new_session)
        db.commit()
        db.refresh(new_session) # 커밋된 객체 정보를 다시 로드합니다.
        
        app.logger.info(f"세션 생성 성공: {new_session.id}")
        return jsonify({
            'sessionId': new_session.id,
            'message': 'Files uploaded and session created successfully'
        }), 201

    except Exception as e:
        db.rollback() # 오류 발생 시 롤백
        app.logger.error(f"업로드 처리 중 오류 발생: {str(e)}")
        # 스택 트레이스를 로깅하여 디버깅 정보 확보
        import traceback
        app.logger.error(traceback.format_exc())
        raise APIError(f"세션 생성에 실패했습니다: {str(e)}", status_code=500)
    finally:
        db.close() # 세션 종료

@app.route('/api/v1/generate', methods=['POST'])
def generate():
    """세션 ID를 받아 자기소개서 생성 (배치 처리로 최적화)"""
    db = next(get_db())
    try:
        app.logger.info("자기소개서 생성 요청 시작 (배치 처리)")
        data = request.get_json()
        session_id = data.get('sessionId')

        if not session_id:
            raise APIError("세션 ID가 없습니다.", status_code=400)

        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise APIError("세션을 찾을 수 없습니다.", status_code=404)

        # 배치 처리를 위한 데이터 준비
        questions = [q.question for q in session.questions]
        lengths = [q.length for q in session.questions]
        
        app.logger.info(f"배치 처리 시작: {len(questions)}개 질문, 한 번의 모델 호출")
        
        # 한 번의 모델 호출로 모든 답변 생성
        from cover_letter_generator import generate_cover_letters_batch
        answers = generate_cover_letters_batch(questions, session.jd_text, session.resume_text, lengths)
        
        # 생성된 답변들을 각 질문에 저장
        for i, (question, answer) in enumerate(zip(session.questions, answers)):
            # 버전 히스토리 초기화
            question.answer_history = json.dumps([answer])
            question.current_version_index = 0
            app.logger.info(f"질문 ID {question.id}에 대한 답변 저장 완료")
        
        db.commit()
        app.logger.info(f"배치 처리 완료: {len(questions)}개 질문에 대한 답변 생성 성공")

        # 프론트엔드에 전달할 데이터 직렬화
        questions_with_answers = [q.to_dict() for q in session.questions]
        
        return jsonify({
            'questions': questions_with_answers,
            'message': f'자기소개서가 성공적으로 생성되었습니다. (배치 처리: {len(questions)}개 문항)'
        }), 200

    except Exception as e:
        db.rollback()
        app.logger.error(f"자기소개서 생성 중 오류: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        raise APIError(f"자기소개서 생성에 실패했습니다: {str(e)}", status_code=500)
    finally:
        db.close()

@app.route('/api/v1/revise', methods=['POST'])
def revise():
    """자기소개서 수정, undo, redo 처리"""
    db = next(get_db())
    try:
        app.logger.info("자기소개서 수정/버전 관리 요청 시작")
        data = request.get_json()
        session_id = data.get('sessionId')
        question_index = data.get('questionIndex')  # 새로운 파라미터명
        action = data.get('action', 'revise')  # 기본 액션은 'revise'
        revision_request = data.get('revisionRequest')  # 새로운 파라미터명

        if not all([session_id]) or question_index is None:
            raise APIError("세션 ID 또는 질문 인덱스가 없습니다.", status_code=400)
        
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session or question_index >= len(session.questions):
            raise APIError("세션 또는 질문을 찾을 수 없습니다.", status_code=404)

        question = session.questions[question_index]
        history = _parse_answer_history(question.answer_history)
        
        if action == 'undo':
            if question.current_version_index > 0:
                question.current_version_index -= 1
        
        elif action == 'redo':
            if question.current_version_index < len(history) - 1:
                question.current_version_index += 1
        
        elif action == 'revise':
            if not revision_request:
                raise APIError("수정 프롬프트가 없습니다.", status_code=400)
            
            # 현재 버전 이후의 히스토리 삭제
            history = history[:question.current_version_index + 1]
            
            revised_text = revise_cover_letter(
                question=question.question,
                jd_text=session.jd_text,
                resume_text=session.resume_text,
                original_answer=history[question.current_version_index],
                user_edit_prompt=revision_request
            )
            history.append(revised_text)
            question.answer_history = json.dumps(history)
            question.current_version_index = len(history) - 1

        else:
            raise APIError(f"알 수 없는 액션입니다: {action}", status_code=400)

        db.commit()
        db.refresh(question)
        return jsonify({'revised_answer': question.to_dict()['answer']}), 200

    except Exception as e:
        db.rollback()
        app.logger.error(f"자기소개서 수정 중 오류: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        raise APIError(f"자기소개서 수정에 실패했습니다: {str(e)}", status_code=500)
    finally:
        db.close()

@app.route('/api/v1/session/<string:id>', methods=['DELETE'])
def delete_session(id):
    try:
        app.logger.info(f"세션 삭제 요청: {id}")
        db = get_db()
        session = db.query(Session).filter_by(id=id).first()
        
        if not session:
            app.logger.error(f"삭제할 세션을 찾을 수 없음: {id}")
            raise APIError("Session not found", status_code=404)

        try:
            db.delete(session)
            db.commit()
            app.logger.info(f"세션 삭제 성공: {id}")
            return jsonify({'message': 'Session deleted successfully'}), 200

        except Exception as e:
            db.rollback()
            app.logger.error(f"세션 삭제 중 오류: {str(e)}")
            raise APIError(f"Failed to delete session: {str(e)}", status_code=500)

    except Exception as e:
        app.logger.error(f"세션 삭제 요청 처리 중 오류: {str(e)}")
        raise APIError(f"Deletion failed: {str(e)}", status_code=500)

@app.route('/api/v1/session/<string:id>', methods=['GET'])
def get_session(id):
    """세션 ID로 자기소개서 생성 결과 조회"""
    db = next(get_db())
    try:
        session = db.query(Session).filter(Session.id == id).first()
        if not session:
            raise APIError("세션을 찾을 수 없습니다.", status_code=404)

        questions_with_answers = [q.to_dict() for q in session.questions]

        return jsonify({
            'questions': questions_with_answers,
            'message': '자기소개서 조회에 성공했습니다.'
        }), 200

    except Exception as e:
        app.logger.error(f"세션 조회 중 오류: {str(e)}")
        raise APIError(f"세션 조회에 실패했습니다: {str(e)}", status_code=500)
    finally:
        db.close()

@app.route('/api/v1/extract-job', methods=['POST'])
def extract_job():
    """채용공고 URL에서 직무 정보만 추출하는 엔드포인트"""
    try:
        app.logger.info("직무 정보 추출 요청 시작")
        data = request.get_json()
        job_posting_url = data.get('jobPostingUrl')
        
        if not job_posting_url:
            raise APIError("채용공고 URL이 없습니다.", status_code=400)
        
        # 채용공고에서 직무 정보 추출
        job_description = crawl_job_description(job_posting_url)
        if not job_description:
            raise APIError("채용공고 정보를 추출할 수 없습니다.", status_code=400)
        
        app.logger.info("직무 정보 추출 성공")
        
        # 간단한 키워드 분석으로 직무 추출 (실제로는 더 정교한 분석 필요)
        extracted_jobs = extract_job_positions(job_description)
        
        return jsonify({
            'jobDescription': job_description,
            'extractedJobs': extracted_jobs,
            'message': '직무 정보 추출이 완료되었습니다.'
        }), 200
        
    except Exception as e:
        app.logger.error(f"직무 정보 추출 중 오류: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        raise APIError(f"직무 정보 추출에 실패했습니다: {str(e)}", status_code=500)

def extract_job_positions(job_description):
    """채용공고 텍스트에서 직무 정보를 정교한 규칙 기반으로 추출 (모델 호출 없음)"""
    try:
        # 1단계: 직무명이 명시적으로 언급된 경우 우선 추출
        explicit_positions = _extract_explicit_positions(job_description)
        if explicit_positions:
            return explicit_positions[:3]
        
        # 2단계: 직무명이 없으면 키워드 분석으로 추출
        keyword_positions = _extract_by_keywords(job_description)
        if keyword_positions:
            return keyword_positions[:3]
        
        # 3단계: 기본값 반환
        return ['기타']
        
    except Exception as e:
        app.logger.error(f"직무 추출 실패: {e}")
        return ['기타']

def _extract_explicit_positions(job_description):
    """채용공고에서 명시적으로 언급된 직무명 추출"""
    # 직무명 패턴들 (우선순위 순)
    position_patterns = [
        # 구체적인 직무명 패턴
        r'([가-힣a-zA-Z\s]+(?:개발자|엔지니어|매니저|디자이너|분석가|기획자|운영자|관리자|인턴|신입|경력))',
        r'(?:모집|채용|구인|인재|인력)\s*:\s*([가-힣a-zA-Z\s]+)',
        r'(?:포지션|직무|담당)\s*:\s*([가-힣a-zA-Z\s]+)',
        r'(?:담당업무|주요업무|업무내용)\s*[:\-]\s*([가-힣a-zA-Z\s]+)',
        # 제목에서 직무 추출
        r'^([가-힣a-zA-Z\s]+(?:개발자|엔지니어|매니저|디자이너|분석가|기획자|운영자|관리자|인턴|신입|경력))',
    ]
    
    import re
    extracted = []
    
    for pattern in position_patterns:
        matches = re.findall(pattern, job_description, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            position = match.strip()
            if position and len(position) > 2:
                # 불필요한 단어 제거
                position = re.sub(r'(모집|채용|구인|인재|인력|포지션|직무|담당|업무|내용|주요|담당업무|주요업무|업무내용)', '', position).strip()
                if position and position not in extracted:
                    extracted.append(position)
    
    return extracted

def _extract_by_keywords(job_description):
    """키워드 분석으로 직무 분야 추출"""
    # 직무별 키워드 가중치 시스템
    position_keywords = {
        '광고/마케팅': {
            'keywords': ['광고', '마케팅', 'Advertising', 'Marketing', '퍼포먼스', '디지털 마케팅', '브랜드', '홍보', '프로모션'],
            'weight': 0
        },
        '개발/엔지니어': {
            'keywords': ['개발', '엔지니어', 'Developer', 'Engineer', '프로그래머', '코딩', '프로그래밍', '소프트웨어', '앱', '웹'],
            'weight': 0
        },
        '데이터/분석': {
            'keywords': ['데이터', '분석', 'Data', 'Analytics', '통계', '인사이트', '리포팅', '대시보드'],
            'weight': 0
        },
        '디자인': {
            'keywords': ['디자인', 'Design', 'UI', 'UX', '그래픽', '시각', '레이아웃', '인터페이스'],
            'weight': 0
        },
        '기획/전략': {
            'keywords': ['기획', '전략', '기획자', '전략가', 'Planning', '전략기획', '사업기획', '제품기획'],
            'weight': 0
        },
        '영업/고객': {
            'keywords': ['영업', '세일즈', 'Sales', '고객', 'Customer', '파트너', '계약', '매출'],
            'weight': 0
        },
        '운영/관리': {
            'keywords': ['운영', '관리', 'Operation', 'Management', '서비스', '고객지원', 'CS'],
            'weight': 0
        },
        '인사/채용': {
            'keywords': ['인사', '채용', 'HR', 'Human Resource', '인재', '조직', '문화'],
            'weight': 0
        },
        '재무/회계': {
            'keywords': ['재무', '회계', 'Finance', 'Accounting', '예산', '투자', '재정'],
            'weight': 0
        },
        '법무/규정': {
            'keywords': ['법무', '법률', 'Legal', 'Compliance', '규정', '정책'],
            'weight': 0
        }
    }
    
    text_lower = job_description.lower()
    
    # 각 직무별 키워드 매칭 및 가중치 계산
    for position, config in position_keywords.items():
        for keyword in config['keywords']:
            if keyword.lower() in text_lower:
                config['weight'] += 1
                # 연속된 키워드 발견 시 추가 가중치
                if f"{keyword.lower()} " in text_lower or f" {keyword.lower()}" in text_lower:
                    config['weight'] += 0.5
    
    # 가중치가 높은 순으로 정렬
    sorted_positions = sorted(position_keywords.items(), key=lambda x: x[1]['weight'], reverse=True)
    
    # 가중치가 0보다 큰 직무들만 반환
    extracted = [position for position, config in sorted_positions if config['weight'] > 0]
    
    return extracted

def _fallback_job_extraction(job_description):
    """AI 추출 실패 시 사용하는 기본 키워드 매칭"""
    # 더 정교한 키워드 매칭
    position_keywords = {
        '광고/마케팅': ['광고', '마케팅', 'Advertising', 'Marketing', '퍼포먼스', '디지털 마케팅'],
        '개발/엔지니어': ['개발', '엔지니어', 'Developer', 'Engineer', '프로그래머', '코딩'],
        '데이터/분석': ['데이터', '분석', 'Data', 'Analytics', '통계'],
        '디자인': ['디자인', 'Design', 'UI', 'UX', '그래픽'],
        '기획/전략': ['기획', '전략', '기획자', '전략가', 'Planning'],
        '영업/고객': ['영업', '세일즈', 'Sales', '고객', 'Customer'],
        '운영/관리': ['운영', '관리', 'Operation', 'Management'],
        '인사/채용': ['인사', '채용', 'HR', 'Human Resource'],
        '재무/회계': ['재무', '회계', 'Finance', 'Accounting'],
        '법무/규정': ['법무', '법률', 'Legal', 'Compliance']
    }
    
    extracted = []
    text_lower = job_description.lower()
    
    for position, keywords in position_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                if position not in extracted:
                    extracted.append(position)
                break
    
    # 기본값 제공
    if not extracted:
        extracted = ['기타']
    
    return extracted[:3]

if __name__ == '__main__':
    app.run(debug=True)

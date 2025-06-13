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

        if not job_description_url or not questions_data:
            raise APIError("URL 또는 질문 데이터가 부족합니다.", status_code=400)
        
        job_description = crawl_job_description(job_description_url)
        if not job_description:
            raise APIError("채용공고 크롤링에 실패했습니다.", status_code=400)
        
        app.logger.info("채용공고 크롤링 성공")

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
    """세션 ID를 받아 자기소개서 생성 (SQLAlchemy 사용)"""
    db = next(get_db())
    try:
        app.logger.info("자기소개서 생성 요청 시작")
        data = request.get_json()
        session_id = data.get('sessionId')

        if not session_id:
            raise APIError("세션 ID가 없습니다.", status_code=400)

        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise APIError("세션을 찾을 수 없습니다.", status_code=404)

        # 질문별로 답변 생성 및 저장
        for question in session.questions:
            answer_text = generate_cover_letter(
                question.question, session.jd_text, session.resume_text, question.length
            )
            # 버전 히스토리 초기화
            question.answer_history = json.dumps([answer_text])
            question.current_version_index = 0
            app.logger.info(f"질문 ID {question.id}에 대한 답변 생성 성공")
        
        db.commit()

        # 프론트엔드에 전달할 데이터 직렬화
        questions_with_answers = [q.to_dict() for q in session.questions]
        
        return jsonify({
            'questions': questions_with_answers,
            'message': '자기소개서가 성공적으로 생성되었습니다.'
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
        q_idx = data.get('q_idx')
        action = data.get('action', 'revise')  # 기본 액션은 'revise'
        prompt = data.get('prompt')

        if not all([session_id]) or q_idx is None:
            raise APIError("세션 ID 또는 질문 인덱스가 없습니다.", status_code=400)
        
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session or q_idx >= len(session.questions):
            raise APIError("세션 또는 질문을 찾을 수 없습니다.", status_code=404)

        question = session.questions[q_idx]
        history = _parse_answer_history(question.answer_history)
        
        if action == 'undo':
            if question.current_version_index > 0:
                question.current_version_index -= 1
        
        elif action == 'redo':
            if question.current_version_index < len(history) - 1:
                question.current_version_index += 1
        
        elif action == 'revise':
            if not prompt:
                raise APIError("수정 프롬프트가 없습니다.", status_code=400)
            
            # 현재 버전 이후의 히스토리 삭제
            history = history[:question.current_version_index + 1]
            
            revised_text = revise_cover_letter(
                question=question.question,
                jd_text=session.jd_text,
                resume_text=session.resume_text,
                original_answer=history[question.current_version_index],
                prompt=prompt
            )
            history.append(revised_text)
            question.answer_history = json.dumps(history)
            question.current_version_index = len(history) - 1

        else:
            raise APIError(f"알 수 없는 액션입니다: {action}", status_code=400)

        db.commit()
        db.refresh(question)
        return jsonify({'updatedQuestion': question.to_dict()}), 200

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

if __name__ == '__main__':
    app.run(debug=True)

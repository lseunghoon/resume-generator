from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import io
import json
import uuid
import traceback
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
from job_crawler import crawl_job_description, _crawl_text_content, _crawl_image_content, _combine_content
from cover_letter_generator import generate_cover_letter, revise_cover_letter
from job_posting_filter import JobPostingFilter
from ocr_processor import OCRProcessor

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
    db = next(get_db())
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
        job_description = data.get('jobDescription')

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
            q_length_str = lengths_data[i] if i < len(lengths_data) else "1000"
            try:
                q_length = int(q_length_str) if q_length_str else 1000
            except (ValueError, TypeError):
                q_length = 1000

            new_question = Question(
                question=q_text,
                length=q_length
            )
            new_session.questions.append(new_question)

        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        app.logger.info(f"세션 생성 성공: {new_session.id}")
        return jsonify({
            'sessionId': new_session.id,
            'message': 'Files uploaded and session created successfully'
        }), 201

    except Exception as e:
        db.rollback()
        app.logger.error(f"업로드 처리 중 오류 발생: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        raise APIError(f"세션 생성에 실패했습니다: {str(e)}", status_code=500)
    finally:
        db.close()

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
        question_index = data.get('questionIndex')
        action = data.get('action', 'revise')
        revision_request = data.get('revisionRequest')

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
        
        # job 정보 추출
        job_description_url = session.jd_url or ''
        selected_job = ''
        
        # jd_text에서 직무 정보 추출 시도
        if session.jd_text:
            try:
                extracted_jobs = _extract_job_positions_from_structured_data(session.jd_text)
                if extracted_jobs:
                    selected_job = extracted_jobs[0]
            except Exception as e:
                app.logger.warning(f"직무 정보 추출 실패: {e}")
                selected_job = '직무 정보 없음'

        return jsonify({
            'questions': questions_with_answers,
            'jobDescriptionUrl': job_description_url,
            'selectedJob': selected_job,
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
        
        # 요청 데이터 파싱
        data = request.get_json()
        job_posting_url = data.get('jobPostingUrl')
        
        # URL 검증
        if not job_posting_url:
            raise APIError("채용공고 URL이 제공되지 않았습니다.", status_code=400)
        
        app.logger.info(f"채용공고 URL: {job_posting_url}")
        
        # 채용공고에서 직무 정보 추출
        job_description = crawl_job_description(job_posting_url)
        if not job_description:
            raise APIError("채용공고 정보를 추출할 수 없습니다.", status_code=400)
        
        app.logger.info("직무 정보 추출 성공")
        
        # 구조화된 데이터에서 직무 정보 추출
        positions = _extract_job_positions_from_structured_data(job_description)
        
        return jsonify({
            'positions': positions,
            'jobDescription': job_description,
            'message': '직무 정보 추출이 완료되었습니다.'
        }), 200
        
    except APIError:
        raise
    except Exception as e:
        app.logger.error(f"직무 정보 추출 중 오류: {str(e)}")
        app.logger.error(traceback.format_exc())
        raise APIError(f"직무 정보 추출에 실패했습니다: {str(e)}", status_code=500)

@app.route('/api/v1/add-question', methods=['POST'])
def add_question():
    """기존 세션에 새로운 질문 추가 및 답변 생성"""
    db = next(get_db())
    try:
        app.logger.info("새 질문 추가 요청 시작")
        
        # 요청 데이터 파싱
        data = request.get_json()
        session_id = data.get('sessionId')
        new_question = data.get('question')
        
        if not session_id or not new_question:
            raise APIError("세션 ID와 질문은 필수입니다.", status_code=400)
        
        # 세션 조회
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise APIError("세션을 찾을 수 없습니다.", status_code=404)
        
        # 최대 질문 수 제한 (3개)
        if len(session.questions) >= 3:
            raise APIError("최대 3개의 질문까지만 추가할 수 있습니다.", status_code=400)
        
        app.logger.info(f"세션 {session_id}에 새 질문 추가: {new_question}")
        
        # 자기소개서 생성을 위한 데이터 준비
        resume_text = session.resume_text or ""
        job_description = session.jd_text or ""
        
        if not resume_text or not job_description:
            raise APIError("이력서나 채용공고 정보가 없어 답변을 생성할 수 없습니다.", status_code=400)
        
        # AI를 사용하여 새로운 질문에 대한 답변 생성
        app.logger.info("AI 답변 생성 시작")
        
        try:
            generated_answer = generate_cover_letter(
                question=new_question,
                jd_text=job_description,
                resume_text=resume_text,
                length="500"
            )
            
            if not generated_answer:
                raise APIError("답변 생성에 실패했습니다.", status_code=500)
                
        except Exception as e:
            app.logger.error(f"AI 답변 생성 실패: {str(e)}")
            raise APIError(f"답변 생성 중 오류가 발생했습니다: {str(e)}", status_code=500)
        
        # 새로운 Question 객체 생성 및 저장
        new_question_obj = Question(
            question=new_question,
            length=len(generated_answer),
            answer_history=json.dumps([generated_answer]),
            current_version_index=0,
            session_id=session_id
        )
        
        db.add(new_question_obj)
        db.commit()
        db.refresh(new_question_obj)
        
        app.logger.info(f"새 질문 저장 완료 - ID: {new_question_obj.id}")
        
        return jsonify({
            'questionId': new_question_obj.id,
            'question': new_question,
            'answer': generated_answer,
            'length': len(generated_answer),
            'message': '새로운 질문과 답변이 생성되었습니다.'
        }), 200
        
    except APIError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        app.logger.error(f"새 질문 추가 중 오류: {str(e)}")
        app.logger.error(traceback.format_exc())
        raise APIError(f"새 질문 추가에 실패했습니다: {str(e)}", status_code=500)
    finally:
        db.close()

def _extract_job_positions_from_structured_data(structured_content):
    """구조화된 데이터에서 직무 정보 추출"""
    try:
        app.logger.info("구조화된 데이터에서 직무 정보 추출 시작")
        
        # 구조화된 데이터에서 직무 키워드 추출
        job_keywords = []
        
        # 섹션별로 직무 관련 키워드 추출
        sections_to_check = ['주요업무', '담당업무', '업무내용']
        
        for section in sections_to_check:
            if f"=== {section} ===" in structured_content:
                # 해당 섹션 내용 추출
                section_start = structured_content.find(f"=== {section} ===")
                section_end = structured_content.find("===", section_start + 10)
                if section_end == -1:
                    section_content = structured_content[section_start:]
                else:
                    section_content = structured_content[section_start:section_end]
                
                # 직무 관련 키워드 패턴
                job_patterns = [
                    r'([가-힣]+)\s*(?:담당|업무|개발|기획|분석|설계)',
                    r'(?:담당|업무):\s*([가-힣\s]+)',
                    r'([A-Za-z\s]+)\s*(?:development|analysis|design|management)',
                ]
                
                import re
                for pattern in job_patterns:
                    matches = re.findall(pattern, section_content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]
                        clean_match = match.strip()
                        if len(clean_match) > 2 and clean_match not in job_keywords:
                            job_keywords.append(clean_match)
        
        # 키워드가 없으면 기본 추론
        if not job_keywords:
            # 전체 텍스트에서 일반적인 직무 키워드 찾기
            common_jobs = [
                'Research Assistant', 'RA', '리서치 어시스턴트', '연구 보조',
                '인턴', '인턴십', 'Intern', 'Internship',
                '개발자', 'Developer', '기획자', 'Planner',
                '분석가', 'Analyst', '매니저', 'Manager'
            ]
            
            content_lower = structured_content.lower()
            for job in common_jobs:
                if job.lower() in content_lower:
                    job_keywords.append(job)
                    break
        
        # 결과 정리
        if job_keywords:
            app.logger.info(f"구조화된 데이터에서 직무 키워드 추출 성공: {job_keywords}")
            return job_keywords[:3]
        else:
            app.logger.info("구조화된 데이터에서 직무 키워드 미발견 - 기본값 반환")
            return ['인턴']
        
    except Exception as e:
        app.logger.error(f"구조화된 데이터 직무 추출 실패: {e}")
        return ['인턴']

if __name__ == '__main__':
    app.run(debug=True) 
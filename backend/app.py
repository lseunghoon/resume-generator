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
        
        # job 정보 추출
        job_description_url = session.jd_url or ''
        selected_job = ''
        
        # jd_text에서 직무 정보 추출 시도
        if session.jd_text:
            try:
                extracted_jobs = extract_job_positions(session.jd_text)
                if extracted_jobs:
                    selected_job = extracted_jobs[0]  # 첫 번째 직무 사용
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
        
        # 채용공고에서 직무 정보 추출
        job_description = crawl_job_description(job_posting_url)
        if not job_description:
            raise APIError("채용공고 정보를 추출할 수 없습니다.", status_code=400)
        
        app.logger.info("직무 정보 추출 성공")
        
        # 간단한 키워드 분석으로 직무 추출 (실제로는 더 정교한 분석 필요)
        positions = extract_job_positions(job_description)
        
        return jsonify({
            'positions': positions,
            'jobDescription': job_description,  # 크롤링된 전체 텍스트 추가
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
                length="500"  # 기본 길이 설정
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

@app.route('/api/v1/debug-crawling', methods=['POST'])
def debug_crawling():
    """크롤링 프로세스 단계별 분석 및 디버깅 엔드포인트"""
    try:
        app.logger.info("크롤링 디버깅 분석 시작")
        data = request.get_json()
        job_posting_url = data.get('jobPostingUrl')
        
        if not job_posting_url:
            raise APIError("채용공고 URL이 없습니다.", status_code=400)
        
        debug_results = {
            'url': job_posting_url,
            'steps': {},
            'summary': {},
            'recommendations': []
        }
        
        # 1단계: 텍스트 크롤링
        app.logger.info("1단계: 텍스트 크롤링 분석")
        text_content = _crawl_text_content(job_posting_url)
        debug_results['steps']['text_crawling'] = {
            'success': text_content is not None,
            'content_length': len(text_content) if text_content else 0,
            'content_preview': text_content[:500] + '...' if text_content and len(text_content) > 500 else text_content,
            'content_full': text_content
        }
        
        # 2단계: 이미지 OCR 처리
        app.logger.info("2단계: 이미지 OCR 분석")
        try:
            ocr_processor = OCRProcessor()
            is_ocr_ready, ocr_status = ocr_processor.test_ocr_setup()
            
            if is_ocr_ready:
                ocr_content = _crawl_image_content(job_posting_url)
                debug_results['steps']['ocr_processing'] = {
                    'ocr_setup': 'OK',
                    'success': ocr_content is not None,
                    'content_length': len(ocr_content) if ocr_content else 0,
                    'content_preview': ocr_content[:500] + '...' if ocr_content and len(ocr_content) > 500 else ocr_content,
                    'content_full': ocr_content
                }
            else:
                debug_results['steps']['ocr_processing'] = {
                    'ocr_setup': 'FAIL',
                    'error': ocr_status,
                    'success': False
                }
                ocr_content = None
        except Exception as e:
            debug_results['steps']['ocr_processing'] = {
                'ocr_setup': 'ERROR',
                'error': str(e),
                'success': False
            }
            ocr_content = None
        
        # 3단계: 콘텐츠 통합
        app.logger.info("3단계: 콘텐츠 통합 분석")
        combined_content = _combine_content(text_content, ocr_content)
        debug_results['steps']['content_combination'] = {
            'success': combined_content is not None,
            'has_text': text_content is not None,
            'has_ocr': ocr_content is not None,
            'combined_length': len(combined_content) if combined_content else 0,
            'content_preview': combined_content[:500] + '...' if combined_content and len(combined_content) > 500 else combined_content
        }
        
        # 4단계: 키워드 기반 사전 분석
        app.logger.info("4단계: 키워드 분석")
        if combined_content:
            keyword_score = JobPostingFilter._calculate_keyword_score(combined_content)
            debug_results['steps']['keyword_analysis'] = {
                'score': keyword_score,
                'threshold_pass': keyword_score >= 0.3,
                'details': _analyze_keywords_detail(combined_content)
            }
        else:
            debug_results['steps']['keyword_analysis'] = {
                'score': 0.0,
                'threshold_pass': False,
                'error': '분석할 콘텐츠가 없습니다'
            }
        
        # 5단계: AI 필터링
        app.logger.info("5단계: AI 필터링 분석")
        if combined_content:
            filtered_content = JobPostingFilter.filter_job_posting_content(combined_content)
            debug_results['steps']['ai_filtering'] = {
                'success': filtered_content is not None,
                'original_length': len(combined_content),
                'filtered_length': len(filtered_content) if filtered_content else 0,
                'reduction_ratio': 1 - (len(filtered_content) / len(combined_content)) if filtered_content and combined_content else 0,
                'content_preview': filtered_content[:500] + '...' if filtered_content and len(filtered_content) > 500 else filtered_content
            }
        else:
            debug_results['steps']['ai_filtering'] = {
                'success': False,
                'error': '필터링할 콘텐츠가 없습니다'
            }
            filtered_content = None
        
        # 6단계: 최종 검증
        app.logger.info("6단계: 최종 검증")
        if filtered_content:
            is_valid, validation_score, validation_status = JobPostingFilter.validate_job_posting(filtered_content)
            debug_results['steps']['final_validation'] = {
                'is_valid': is_valid,
                'score': validation_score,
                'status': validation_status,
                'threshold': 0.1 if "이미지에서 추출된 콘텐츠" in filtered_content else 0.15  # OCR 텍스트는 더 완화된 기준
            }
        else:
            debug_results['steps']['final_validation'] = {
                'is_valid': False,
                'score': 0.0,
                'status': '검증할 콘텐츠가 없습니다'
            }
        
        # 종합 분석 및 권장사항
        debug_results['summary'] = _generate_crawling_summary(debug_results)
        debug_results['recommendations'] = _generate_recommendations(debug_results)
        
        app.logger.info("크롤링 디버깅 분석 완료")
        
        return jsonify({
            'debug_results': debug_results,
            'message': '크롤링 프로세스 분석이 완료되었습니다.'
        }), 200
        
    except Exception as e:
        app.logger.error(f"크롤링 디버깅 중 오류: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        raise APIError(f"크롤링 디버깅에 실패했습니다: {str(e)}", status_code=500)

def _analyze_keywords_detail(text):
    """키워드 분석 세부 결과"""
    text_lower = text.lower()
    
    required_found = [kw for kw in JobPostingFilter.JOB_POSTING_KEYWORDS['required'] if kw in text_lower]
    company_found = [kw for kw in JobPostingFilter.JOB_POSTING_KEYWORDS['company_info'] if kw in text_lower]
    application_found = [kw for kw in JobPostingFilter.JOB_POSTING_KEYWORDS['application'] if kw in text_lower]
    
    return {
        'required_keywords': {
            'found': required_found,
            'count': len(required_found),
            'total': len(JobPostingFilter.JOB_POSTING_KEYWORDS['required'])
        },
        'company_keywords': {
            'found': company_found,
            'count': len(company_found),
            'total': len(JobPostingFilter.JOB_POSTING_KEYWORDS['company_info'])
        },
        'application_keywords': {
            'found': application_found,
            'count': len(application_found),
            'total': len(JobPostingFilter.JOB_POSTING_KEYWORDS['application'])
        }
    }

def _generate_crawling_summary(debug_results):
    """크롤링 결과 종합 요약"""
    steps = debug_results['steps']
    
    total_steps = 6
    successful_steps = sum(1 for step in steps.values() if step.get('success', False))
    
    return {
        'overall_success_rate': successful_steps / total_steps,
        'text_crawling_success': steps.get('text_crawling', {}).get('success', False),
        'ocr_available': steps.get('ocr_processing', {}).get('success', False),
        'filtering_success': steps.get('ai_filtering', {}).get('success', False),
        'validation_pass': steps.get('final_validation', {}).get('is_valid', False),
        'total_content_length': steps.get('content_combination', {}).get('combined_length', 0),
        'keyword_score': steps.get('keyword_analysis', {}).get('score', 0.0)
    }

def _generate_recommendations(debug_results):
    """개선 권장사항 생성"""
    recommendations = []
    steps = debug_results['steps']
    
    # 텍스트 크롤링 관련
    if not steps.get('text_crawling', {}).get('success', False):
        recommendations.append({
            'type': 'critical',
            'area': 'text_crawling',
            'message': '텍스트 크롤링이 실패했습니다. 웹사이트 구조나 접근 권한을 확인하세요.'
        })
    
    # OCR 관련
    ocr_step = steps.get('ocr_processing', {})
    if ocr_step.get('ocr_setup') == 'FAIL':
        recommendations.append({
            'type': 'warning',
            'area': 'ocr_setup',
            'message': 'OCR 설정에 문제가 있습니다. Tesseract 설치를 확인하세요.',
            'details': ocr_step.get('error', '')
        })
    
    # 키워드 분석 관련
    keyword_score = steps.get('keyword_analysis', {}).get('score', 0.0)
    if keyword_score < 0.3:
        recommendations.append({
            'type': 'warning',
            'area': 'keyword_analysis',
            'message': f'키워드 점수가 낮습니다 ({keyword_score:.2f}). 채용공고가 아닐 가능성이 있습니다.'
        })
    
    # AI 필터링 관련
    if not steps.get('ai_filtering', {}).get('success', False):
        recommendations.append({
            'type': 'critical',
            'area': 'ai_filtering',
            'message': 'AI 필터링이 실패했습니다. 콘텐츠가 너무 적거나 AI 모델에 문제가 있을 수 있습니다.'
        })
    
    # 검증 관련
    if not steps.get('final_validation', {}).get('is_valid', False):
        validation_score = steps.get('final_validation', {}).get('score', 0.0)
        recommendations.append({
            'type': 'warning',
            'area': 'validation',
            'message': f'최종 검증에 실패했습니다 (점수: {validation_score:.2f}/0.4). 채용공고 품질이 기준에 미달합니다.'
        })
    
    # 성공적인 경우
    if not recommendations:
        recommendations.append({
            'type': 'success',
            'area': 'overall',
            'message': '모든 크롤링 단계가 성공적으로 완료되었습니다.'
        })
    
    return recommendations

def extract_job_positions(job_description):
    """채용공고 텍스트에서 실제 사용된 직무명을 그대로 추출"""
    try:
        app.logger.info("직무 추출 시작 - 실제 공고의 직무명 그대로 추출")
        
        # 텍스트에서 제목 분리
        title = ""
        content = job_description
        
        if "=== 제목 ===" in job_description:
            parts = job_description.split("=== 내용 ===", 1)
            if len(parts) == 2:
                title_part = parts[0].replace("=== 제목 ===", "").strip()
                content = parts[1].strip()
                title = title_part
                app.logger.info(f"제목 추출: {title[:100]}...")
        
        # 1단계: 제목에서 실제 직무명 추출
        if title:
            title_positions = _extract_actual_positions_from_title(title)
            if title_positions:
                app.logger.info(f"제목에서 실제 직무명 추출 성공: {title_positions}")
                return title_positions[:3]
        
        # 2단계: 본문에서 실제 직무명 추출
        content_positions = _extract_actual_positions_from_content(content)
        if content_positions:
            app.logger.info(f"본문에서 실제 직무명 추출 성공: {content_positions}")
            return content_positions[:3]
        
        # 3단계: 패턴 매칭으로 실제 직무명 찾기
        pattern_positions = _extract_positions_by_patterns(job_description)
        if pattern_positions:
            app.logger.info(f"패턴 매칭으로 실제 직무명 추출 성공: {pattern_positions}")
            return pattern_positions[:3]
        
        # 4단계: 기본값 반환
        app.logger.warning("실제 직무명 추출 실패 - 기본값 반환")
        return ['인턴']  # 링커리어의 경우 대부분 인턴
        
    except Exception as e:
        app.logger.error(f"직무 추출 실패: {e}")
        return ['인턴']

def extract_company_name(job_description):
    """채용공고 텍스트에서 회사명 추출"""
    import re
    
    try:
        app.logger.info("회사명 추출 시작")
        
        # 텍스트에서 제목 분리
        title = ""
        if "=== 제목 ===" in job_description:
            parts = job_description.split("=== 내용 ===", 1)
            if len(parts) == 2:
                title_part = parts[0].replace("=== 제목 ===", "").strip()
                title = title_part
        
        # 1순위: 제목에서 회사명 추출
        if title:
            company_name = _extract_company_from_title(title)
            if company_name:
                app.logger.info(f"제목에서 회사명 추출 성공: {company_name}")
                return company_name
        
        # 2순위: 본문에서 회사명 추출
        company_name = _extract_company_from_content(job_description)
        if company_name:
            app.logger.info(f"본문에서 회사명 추출 성공: {company_name}")
            return company_name
        
        app.logger.warning("회사명 추출 실패")
        return "채용 기업"
        
    except Exception as e:
        app.logger.error(f"회사명 추출 실패: {e}")
        return "채용 기업"

def _extract_company_from_title(title):
    """제목에서 회사명 추출"""
    import re
    
    app.logger.info(f"제목에서 회사명 추출 시작: '{title}'")
    
    # 링커리어 제목 정제: | 이후 부분 제거
    clean_title = title
    if '|' in title:
        clean_title = title.split('|')[0].strip()
        app.logger.info(f"제목 정제 (| 이후 제거): '{clean_title}'")
    
    # 링커리어 특화: [전환형/체험형 인턴] 회사명 직무명
    linkareer_pattern = r'\[.*?\]\s*(.+)'
    match = re.search(linkareer_pattern, clean_title)
    if match:
        main_title = match.group(1).strip()
        app.logger.info(f"링커리어 패턴에서 추출된 메인 제목: '{main_title}'")
        
        # 단순하고 정확한 회사명-직무명 분리 패턴들
        company_job_patterns = [
            # 1. "회사명 Business Development" 패턴 (링글 Business Development)
            r'^([가-힣A-Za-z0-9\s]{2,15})\s+(Business\s+Development)$',
            
            # 2. "회사명 Product Manager" 패턴  
            r'^([가-힣A-Za-z0-9\s]{2,15})\s+(Product\s+Manager)$',
            
            # 3. "회사명 Software Engineer" 패턴
            r'^([가-힣A-Za-z0-9\s]{2,15})\s+(Software\s+Engineer)$',
            
            # 4. "회사명 Data Analyst" 패턴
            r'^([가-힣A-Za-z0-9\s]{2,15})\s+(Data\s+(?:Analyst|Scientist|Engineer))$',
            
            # 5. "회사명 [영문직무]" 일반 패턴
            r'^([가-힣A-Za-z0-9\s]{2,15})\s+([A-Z][a-zA-Z\s]{3,}(?:Manager|Director|Lead|Engineer|Developer|Designer|Analyst|Specialist|Coordinator|Associate|Assistant))$',
            
            # 6. "회사명 [한글직무]" 일반 패턴  
            r'^([가-힣A-Za-z0-9\s]{2,15})\s+([가-힣\s]{2,}(?:매니저|관리자|담당자|기획자|개발자|엔지니어|디자이너|분석가|운영자|상담원|컨설턴트|인턴))$',
            
            # 7. "회사명 Senior/Junior [직무]" 패턴
            r'^([가-힣A-Za-z0-9\s]{2,15})\s+(?:Senior|Junior|Lead|Principal)\s+([A-Z][a-zA-Z\s]{3,}(?:Engineer|Developer|Designer|Manager|Analyst))$'
        ]
        
        for i, pattern in enumerate(company_job_patterns):
            pattern_match = re.search(pattern, main_title, re.IGNORECASE)
            if pattern_match:
                company_name = pattern_match.group(1).strip()
                job_title = pattern_match.group(2).strip()
                
                app.logger.info(f"패턴 {i+1} 매치 성공 - 회사명: '{company_name}', 직무명: '{job_title}'")
                
                # 회사명 검증 - 더 엄격한 기준
                if _is_valid_company_name(company_name):
                    # 직무명과 중복되지 않는지 확인
                    if company_name.lower() != job_title.lower():
                        app.logger.info(f"회사명 추출 최종 성공: '{company_name}'")
                        return company_name
                    else:
                        app.logger.warning(f"회사명과 직무명이 동일하여 스킵: '{company_name}'")
                else:
                    app.logger.warning(f"유효하지 않은 회사명: '{company_name}'")
        
        # 패턴 매칭 실패 시 간단한 첫 단어 추출 시도
        words = main_title.split()
        if len(words) >= 2:
            first_word = words[0].strip()
            if _is_valid_company_name(first_word):
                app.logger.info(f"첫 단어에서 회사명 추출: '{first_word}'")
                return first_word
    
    # 링커리어 패턴이 아닌 경우의 회사명 패턴 (더 엄격한 검증)
    general_patterns = [
        # 명시적인 회사명 패턴만
        r'([가-힣]{2,10}(?:주식회사|㈜|회사|기업|그룹|코퍼레이션))',
        r'([A-Z][a-zA-Z]{2,15}(?:\s+(?:Corp|Inc|Ltd|LLC|Company|Co\.))+)',
    ]
    
    for i, pattern in enumerate(general_patterns):
        matches = re.findall(pattern, clean_title)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            
            if _is_valid_company_name(match):
                app.logger.info(f"일반 패턴 {i+1}에서 회사명 추출: '{match}'")
                return match
    
    app.logger.warning("제목에서 회사명 추출 실패")
    return None

def _is_valid_company_name(company_name):
    """회사명이 유효한지 검증 (더 엄격한 기준)"""
    if not company_name or len(company_name.strip()) < 2:
        return False
    
    company_clean = company_name.strip()
    
    # 길이 검증
    if len(company_clean) > 20:
        return False
    
    # 금지 단어들 (더 포괄적)
    forbidden_words = [
        # 일반적인 노이즈 단어
        '채용', '모집', '구인', '공고', '인재', '신입', '경력', '지원', '안내',
        # 직무 관련 단어들
        '개발', '기획', '디자인', '마케팅', '영업', '관리', '운영', '서비스',
        '매니저', '엔지니어', '디자이너', '분석가', '컨설턴트',
        'manager', 'engineer', 'developer', 'designer', 'analyst',
        # 일반적인 대명사/형용사
        '우리', '저희', '당사', '해당', '이번', '금번', '신규', '최신',
        '전체', '모든', '각종', '다양한', '여러', '기타', '등등', '기타',
        # 업무 관련 단어
        '업무', '담당', '책임', '역할', '포지션', '직무', '분야', '파트',
        '팀', '그룹', '부서', '센터', '본부', '사업부'
    ]
    
    # 금지 단어 확인
    company_lower = company_clean.lower()
    for forbidden in forbidden_words:
        if forbidden in company_lower:
            return False
    
    # 숫자만으로 구성된 경우 제외
    if company_clean.isdigit():
        return False
    
    # 특수문자만 있는 경우 제외
    if not re.search(r'[가-힣a-zA-Z]', company_clean):
        return False
    
    # 알려진 회사명이거나 적절한 길이의 단어인 경우 유효
    known_companies = [
        '링글', 'Ringle', '네이버', 'Naver', '카카오', 'Kakao', '라인', 'Line', 
        '쿠팡', 'Coupang', '토스', 'Toss', '삼성', 'Samsung', 'LG', 'SK', 
        '현대', 'Hyundai', '배달의민족', '우아한형제들', '넥슨', 'Nexon', 
        '넷마블', 'Netmarble', '롯데', 'Lotte', 'KT', 'NHN', 'NCsoft'
    ]
    
    # 알려진 회사명이면 바로 유효
    if any(known in company_clean for known in known_companies):
        return True
    
    # 적절한 길이와 구성인지 확인
    if 2 <= len(company_clean) <= 10:
        # 한글 또는 영문으로만 구성된 경우
        if re.match(r'^[가-힣]+$', company_clean) or re.match(r'^[A-Za-z]+$', company_clean):
            return True
        # 한글+영문 조합
        if re.match(r'^[가-힣A-Za-z\s]+$', company_clean):
            return True
    
    return False

def _extract_company_from_content(content):
    """본문에서 회사명 추출"""
    import re
    
    app.logger.info("본문에서 회사명 추출 시작")
    
    # 우선순위가 높은 패턴들만 사용 (더 엄격한 기준)
    high_priority_patterns = [
        # 1. 명시적인 라벨이 있는 경우 (가장 신뢰할 수 있음)
        r'회사명\s*[:\-]\s*([^\n\r,()]+?)(?:\s*[,()|\n\r]|$)',
        r'기업명\s*[:\-]\s*([^\n\r,()]+?)(?:\s*[,()|\n\r]|$)',
        r'회사\s*[:\-]\s*([^\n\r,()]+?)(?:\s*[,()|\n\r]|$)',
        
        # 2. 기업 형태가 명시된 경우
        r'([가-힣]{2,10})(?:\s*주식회사|\s*㈜|\s*회사|\s*기업|\s*그룹)',
        r'([A-Z][a-zA-Z]{2,15})(?:\s*Corporation|\s*Corp\.?|\s*Inc\.?|\s*Ltd\.?|\s*Company)',
        
        # 3. "~에서 함께할" 패턴 (높은 신뢰도)
        r'([가-힣]{2,10})에서\s*(?:함께|근무|일|채용)',
        r'([A-Z][a-zA-Z]{2,15})에서\s*(?:함께|근무|일|채용)',
    ]
    
    # 높은 우선순위 패턴 먼저 시도
    for i, pattern in enumerate(high_priority_patterns):
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        
        app.logger.info(f"우선순위 패턴 {i+1} 시도: '{pattern[:30]}...' - {len(matches)}개 매치")
        
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            
            company_name = match.strip()
            
            # 엄격한 검증
            if _is_valid_company_name(company_name):
                app.logger.info(f"본문에서 회사명 추출 성공 (우선순위 패턴 {i+1}): '{company_name}'")
                return company_name
            else:
                app.logger.debug(f"검증 실패: '{company_name}'")
    
    # 우선순위 패턴에서 찾지 못한 경우, 더 보수적인 패턴 시도
    conservative_patterns = [
        # 알려진 회사명만 매칭 (가장 안전)
        r'\b(링글|Ringle|네이버|Naver|카카오|Kakao|라인|Line|쿠팡|Coupang|토스|Toss|삼성|Samsung|LG|SK|현대|Hyundai|배달의민족|우아한형제들|넥슨|Nexon|넷마블|Netmarble|롯데|Lotte|KT|NHN|NCsoft)\b',
    ]
    
    for i, pattern in enumerate(conservative_patterns):
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        app.logger.info(f"보수적 패턴 {i+1} 시도: {len(matches)}개 매치")
        
        for match in matches:
            company_name = match.strip()
            
            # 알려진 회사명이므로 추가 검증 없이 반환
            if company_name:
                app.logger.info(f"본문에서 알려진 회사명 발견: '{company_name}'")
                return company_name
    
    app.logger.warning("본문에서 회사명 추출 실패 - 신뢰할 수 있는 패턴이 없음")
    return None

def _extract_actual_positions_from_title(title):
    """제목에서 실제 직무명 그대로 추출"""
    import re
    
    app.logger.info(f"제목에서 실제 직무명 추출 시작: {title}")
    
    # 링커리어 제목 정제: | 이후 부분 제거
    clean_title = title
    if '|' in title:
        clean_title = title.split('|')[0].strip()
        app.logger.info(f"제목 정제 (| 이후 제거): {clean_title}")
    
    # 링커리어 특화: [전환형/체험형 인턴] 회사명 직무명
    linkareer_pattern = r'\[.*?\]\s*(.+)'
    match = re.search(linkareer_pattern, clean_title)
    if match:
        main_title = match.group(1).strip()
        app.logger.info(f"링커리어 패턴에서 추출: {main_title}")
        
        # 회사명과 직무명 분리 (회사명 추출과 동일한 패턴 사용)
        company_job_patterns = [
            # 1. 명확한 영문 직무명이 있는 경우
            r'^(.+?)\s+((?:Business|Product|Software|Digital|Data|Marketing|Sales|Customer|Technical|Content|Growth|Operations|Analytics)\s+(?:Development|Manager|Engineer|Designer|Analyst|Specialist|Strategy|Operations|Director|Lead))$',
            
            # 2. 영문 직무 키워드가 포함된 경우
            r'^(.+?)\s+(?:Senior|Junior|Lead|Principal)?\s*((?:Software|Frontend|Backend|Full-?Stack|Data|DevOps|AI|ML|QA|Security|Cloud|Mobile|Web|iOS|Android|React|Vue|Angular|Python|Java|JavaScript|TypeScript)\s*(?:Engineer|Developer|Architect|Specialist))$',
            
            # 3. 일반적인 영문 직무명
            r'^(.+?)\s+((?:Product|Project|Program|Marketing|Sales|Business|Content|Community|Brand|UX|UI|Graphic|Motion|Service|Quality|Test|Security|Legal|Finance|HR|People|Talent|Operations|Strategy|Analytics|Intelligence)\s*(?:Manager|Director|Lead|Designer|Analyst|Engineer|Specialist|Coordinator|Associate|Assistant|Representative|Consultant|Planner))$',
            
            # 4. 한글 직무명이 있는 경우
            r'^(.+?)\s+([가-힣\s]{2,}(?:매니저|관리자|담당자|기획자|개발자|엔지니어|디자이너|분석가|운영자|상담원|컨설턴트|기획|개발|디자인|마케팅|영업|인사|재무|법무|전략|운영|서비스|품질|보안|데이터|AI|ML|프로덕트|프로젝트|콘텐츠|커뮤니티|브랜드)(?:\s*(?:팀|파트|그룹|실|부|센터|TF))?\s*(?:인턴|신입|주니어|시니어|리드|매니저|디렉터|VP|C레벨)?)',
            
            # 5. 단순한 영문 두 단어 조합 (Business Development 같은)
            r'^(.+?)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)$',
            
            # 6. 마지막 단어가 명확한 직무 키워드인 경우
            r'^(.+?)\s+(.*(?:Manager|Director|Lead|Engineer|Developer|Designer|Analyst|Specialist|Coordinator|Associate|Assistant|Representative|Consultant|Planner|Architect|인턴))$'
        ]
        
        for i, pattern in enumerate(company_job_patterns):
            pattern_match = re.search(pattern, main_title, re.IGNORECASE)
            if pattern_match:
                company_name = pattern_match.group(1).strip()
                job_title = pattern_match.group(2).strip() if len(pattern_match.groups()) > 1 else ""
                
                app.logger.info(f"패턴 {i+1} 매치: 회사명='{company_name}', 직무명='{job_title}'")
                
                # 직무명 검증
                if job_title and len(job_title) >= 3:
                    # 의미있는 직무명인지 확인
                    if _is_valid_job_title(job_title):
                        # 회사명과 중복되지 않는지 확인
                        if company_name.lower() != job_title.lower():
                            app.logger.info(f"제목에서 직무명 추출 성공: '{job_title}'")
                            return [job_title]
                        else:
                            app.logger.warning(f"회사명과 직무명이 동일하여 스킵: '{job_title}'")
                    else:
                        app.logger.warning(f"유효하지 않은 직무명: '{job_title}'")
                
                app.logger.debug(f"직무명 검증 실패: '{job_title}' (길이: {len(job_title) if job_title else 0})")
        
        # 패턴 매칭이 실패한 경우 전체 제목에서 직무 키워드 찾기
        if main_title:
            job_keywords = _extract_job_keywords_from_text(main_title)
            if job_keywords:
                app.logger.info(f"제목 전체에서 직무 키워드 추출: {job_keywords}")
                return job_keywords[:1]  # 첫 번째만 반환
    
    # 일반적인 제목에서 직무 추출
    else:
        job_patterns = [
            r'([A-Z][a-zA-Z\s&\/\-]+(?:Manager|Director|Lead|Engineer|Developer|Designer|Analyst|Specialist|Coordinator|Associate|Assistant|Intern))',
            r'([가-힣\s]+(?:매니저|관리자|담당자|기획자|개발자|엔지니어|디자이너|분석가|운영자|상담원|컨설턴트|인턴))',
            r'((?:Business|Product|Software|Digital|Data|Marketing|Sales)\s+(?:Development|Manager|Engineer|Designer|Analyst))'
        ]
        
        for pattern in job_patterns:
            matches = re.findall(pattern, clean_title, re.IGNORECASE)
            if matches:
                valid_jobs = []
                for match in matches:
                    job_title = match.strip()
                    if len(job_title) >= 3 and _is_valid_job_title(job_title):
                        valid_jobs.append(job_title)
                
                if valid_jobs:
                    app.logger.info(f"일반 제목에서 직무명 추출: {valid_jobs}")
                    return valid_jobs[:3]
    
    app.logger.warning("제목에서 직무명 추출 실패")
    return []

def _is_valid_job_title(job_title):
    """직무명이 유효한지 검증"""
    if not job_title or len(job_title) < 3:
        return False
    
    # 직무 관련 키워드가 포함되어 있는지 확인
    job_keywords = [
        # 영문 직무 키워드
        'manager', 'director', 'lead', 'engineer', 'developer', 'designer', 'analyst', 
        'specialist', 'coordinator', 'associate', 'assistant', 'representative', 
        'consultant', 'planner', 'architect', 'intern', 'marketing', 'sales', 
        'business', 'product', 'project', 'program', 'data', 'software', 'frontend', 
        'backend', 'fullstack', 'devops', 'security', 'qa', 'testing', 'operations',
        'strategy', 'analytics', 'intelligence', 'development', 'growth', 'content',
        
        # 한글 직무 키워드
        '매니저', '관리자', '담당자', '기획자', '개발자', '엔지니어', '디자이너', '분석가',
        '운영자', '상담원', '컨설턴트', '인턴', '마케팅', '영업', '기획', '개발', '디자인',
        '데이터', '프로덕트', '프로젝트', '전략', '운영', '서비스', '품질', '보안',
        '백엔드', '프론트엔드', '풀스택', '데브옵스', 'AI', 'ML', '머신러닝', '인공지능'
    ]
    
    job_title_lower = job_title.lower()
    has_job_keyword = any(keyword.lower() in job_title_lower for keyword in job_keywords)
    
    # 노이즈 키워드 체크
    noise_keywords = [
        '채용', '모집', '구인', '공고', '지원', '신청', '안내', '모집요강',
        '전환형', '체험형', '프로그램', '과정', '교육', '훈련'
    ]
    
    has_noise = any(noise in job_title_lower for noise in noise_keywords)
    
    return has_job_keyword and not has_noise

def _extract_job_keywords_from_text(text):
    """텍스트에서 직무 키워드 추출"""
    import re
    
    # 직무 키워드 패턴들
    job_patterns = [
        r'\b(Business\s+Development)\b',
        r'\b(Product\s+Manager)\b',
        r'\b(Data\s+(?:Analyst|Scientist|Engineer))\b',
        r'\b(Software\s+(?:Engineer|Developer))\b',
        r'\b(Frontend\s+(?:Engineer|Developer))\b',
        r'\b(Backend\s+(?:Engineer|Developer))\b',
        r'\b(Full[-\s]?Stack\s+(?:Engineer|Developer))\b',
        r'\b(DevOps\s+Engineer)\b',
        r'\b(UX\s+Designer)\b',
        r'\b(UI\s+Designer)\b',
        r'\b(Marketing\s+Manager)\b',
        r'\b(Sales\s+Manager)\b',
        r'\b([가-힣]*\s*(?:개발자|엔지니어|기획자|디자이너|매니저|분석가))\b',
    ]
    
    extracted = []
    for pattern in job_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if match and len(match.strip()) >= 3:
                extracted.append(match.strip())
    
    # 중복 제거
    return list(set(extracted))

def _extract_actual_positions_from_content(content):
    """본문에서 실제 직무명 그대로 추출 (더 엄격한 기준)"""
    import re
    
    app.logger.info("본문에서 실제 직무명 추출 시작")
    
    # 더 정확한 직무명 추출 패턴들 (우선순위별로 정렬)
    job_extraction_patterns = [
        # 1. 명시적 직무 표기 (콜론 뒤의 내용)
        r'직무\s*[:\-]\s*([^\n\r,()]+?)(?:\s*[,()|\n\r]|$)',
        r'포지션\s*[:\-]\s*([^\n\r,()]+?)(?:\s*[,()|\n\r]|$)', 
        r'채용\s*직무\s*[:\-]\s*([^\n\r,()]+?)(?:\s*[,()|\n\r]|$)',
        r'모집\s*분야\s*[:\-]\s*([^\n\r,()]+?)(?:\s*[,()|\n\r]|$)',
        r'담당\s*업무\s*[:\-]\s*([^\n\r,()]+?)(?:\s*[,()|\n\r]|$)',
        
        # 2. "~을 담당할" "~를 맡을" 패턴
        r'([가-힣a-zA-Z\s&\/\-]{5,}(?:개발|기획|디자인|분석|마케팅|영업|관리|운영))\s*을?\s*담당할',
        r'([가-힣a-zA-Z\s&\/\-]{5,}(?:Manager|Engineer|Developer|Designer|Analyst))\s*를?\s*맡을',
        
        # 3. "~업무를 수행" 패턴
        r'([가-힣a-zA-Z\s&\/\-]{5,}(?:개발|기획|디자인|분석|마케팅|영업|관리|운영))\s*업무를?\s*수행',
        
        # 4. 채용 공고 패턴 (전체 직무명만, 회사명 제외)
        r'(?!.*(?:링글|네이버|카카오|라인|쿠팡|삼성|LG|SK|현대|토스|배달|우아한|넥슨|넷마블))([가-힣a-zA-Z\s&\/\-]{5,}(?:매니저|관리자|담당자|기획자|개발자|엔지니어|디자이너|분석가|운영자|상담원|컨설턴트|인턴))\s*모집',
        r'(?!.*(?:링글|네이버|카카오|라인|쿠팡|삼성|LG|SK|현대|토스|배달|우아한|넥슨|넷마블))([가-힣a-zA-Z\s&\/\-]{5,}(?:Manager|Director|Lead|Engineer|Developer|Designer|Analyst|Specialist|Coordinator|Associate|Assistant|Intern))\s*모집',
        
        # 5. 영문 직무명 (전체 직무명만, 약어 및 회사명 제외)
        r'\b((?:Senior|Junior|Lead|Principal)?\s*(?:Business|Product|Marketing|Sales|Customer|Technical|Content|Growth|Operations|Analytics)\s+(?:Development|Manager|Engineer|Designer|Analyst|Specialist|Strategy|Operations|Director|Lead))\b',
        r'\b((?:Senior|Junior|Lead|Principal)?\s*(?:Software|Frontend|Backend|Full-?Stack|Data|DevOps|AI|ML|QA|Security|Cloud|Mobile|Web)\s*(?:Engineer|Developer|Architect|Specialist))\b',
        
        # 6. 한글 직무명 (회사명이 아닌 것)
        r'\b([가-힣\s]{3,}(?:매니저|관리자|담당자|기획자|개발자|엔지니어|디자이너|분석가|운영자|상담원|컨설턴트)(?:\s*(?:팀|파트|그룹|실|부|센터))?)\b',
        
        # 7. 특정 복합 직무명
        r'\b(Business\s+Development(?:\s+Manager)?)\b',
        r'\b(Product\s+Manager)\b',
        r'\b(Data\s+(?:Analyst|Scientist|Engineer))\b',
        r'\b(Software\s+(?:Engineer|Developer))\b',
        r'\b(UX\/UI\s*Designer)\b',
    ]
    
    extracted_jobs = []
    
    for i, pattern in enumerate(job_extraction_patterns):
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        
        app.logger.info(f"패턴 {i+1} 시도: '{pattern[:50]}...' - {len(matches)}개 매치")
        
        for match in matches:
            if isinstance(match, tuple):
                match = match[0] if match[0] else match[1]
            
            job_title = match.strip()
            
            # 길이 및 품질 검증
            if 5 <= len(job_title) <= 50:  # 적절한 길이
                cleaned_job = _clean_extracted_job_title(job_title)
                if cleaned_job and _is_valid_job_title(cleaned_job):
                    # 약어가 아닌지 확인
                    if not _is_abbreviation(cleaned_job):
                        # 회사명이 아닌지 확인
                        if not _is_company_name(cleaned_job):
                            # 중복 확인
                            if cleaned_job not in extracted_jobs:
                                app.logger.info(f"본문에서 직무명 추출 (패턴 {i+1}): '{cleaned_job}'")
                                extracted_jobs.append(cleaned_job)
                        else:
                            app.logger.debug(f"회사명으로 판단되어 스킵: '{cleaned_job}'")
                    else:
                        app.logger.debug(f"약어로 판단되어 스킵: '{cleaned_job}'")
                else:
                    app.logger.debug(f"유효하지 않은 직무명: '{job_title}'")
    
    return extracted_jobs[:3]

def _is_abbreviation(text):
    """텍스트가 약어인지 판단"""
    import re
    
    # 약어 패턴들
    abbreviation_patterns = [
        r'^[A-Z]{1,4}$',  # BD, PM, QA, CEO 등 2-4글자 대문자
        r'^[a-z]{1,4}$',  # pm, bd 등 2-4글자 소문자
        r'^[A-Z]{1,2}/[A-Z]{1,2}$',  # UI/UX 같은 패턴
    ]
    
    for pattern in abbreviation_patterns:
        if re.match(pattern, text.strip()):
            return True
    
    return False

def _extract_positions_by_patterns(full_text):
    """전체 텍스트에서 패턴 매칭으로 실제 직무명 찾기 (약어 제외)"""
    import re
    
    app.logger.info("패턴 매칭으로 직무명 추출 시작")
    
    # 텍스트를 줄 단위로 분석
    lines = full_text.split('\n')
    job_candidates = []
    
    for line in lines:
        line = line.strip()
        if len(line) < 10 or len(line) > 100:  # 너무 짧거나 긴 줄 제외
            continue
            
        # 직무명이 포함될 가능성이 높은 줄 패턴 (더 엄격)
        job_line_patterns = [
            r'.*(?:직무|포지션|담당|업무|채용|모집).*(?:Manager|Engineer|Developer|Designer|Analyst|Development).*',
            r'.*(?:Manager|Engineer|Developer|Designer|Analyst|Development).*(?:직무|포지션|담당|업무|채용|모집).*',
            r'.*(?:매니저|개발자|기획자|디자이너|분석가|인턴).*'
        ]
        
        for pattern in job_line_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                extracted = _extract_job_from_line(line)
                if extracted:
                    # 약어가 아닌 것만 추가
                    non_abbrev = [job for job in extracted if not _is_abbreviation(job) and len(job) >= 5]
                    if non_abbrev:
                        app.logger.info(f"줄에서 직무명 추출: {non_abbrev}")
                        job_candidates.extend(non_abbrev)
                break
    
    # 중복 제거 및 정제
    unique_jobs = []
    for job in job_candidates:
        cleaned = _clean_extracted_job_title(job)
        if cleaned and cleaned not in unique_jobs and len(cleaned) >= 5:
            unique_jobs.append(cleaned)
    
    return unique_jobs[:3]

def _extract_job_from_line(line):
    """한 줄에서 직무명 추출 (약어 제외)"""
    import re
    
    # 줄에서 전체 직무명 추출 패턴 (약어 제외)
    patterns = [
        r'([A-Z][a-zA-Z\s&\/\-]{4,}(?:Manager|Director|Lead|Engineer|Developer|Designer|Analyst|Specialist|Coordinator|Associate|Assistant|Intern))',
        r'([가-힣\s]{3,}(?:매니저|관리자|담당자|기획자|개발자|엔지니어|디자이너|분석가|운영자|상담원|컨설턴트|인턴))',
        r'((?:Business|Product|Software|Digital|Data|Marketing|Sales)\s+(?:Development|Manager|Engineer|Designer|Analyst))'
    ]
    
    extracted = []
    for pattern in patterns:
        matches = re.findall(pattern, line, re.IGNORECASE)
        for match in matches:
            if len(match.strip()) >= 5:  # 최소 5글자 이상
                extracted.append(match.strip())
    
    return extracted

def _clean_title_for_job_extraction(title):
    """제목에서 직무 추출을 위한 정제"""
    import re
    
    # 제거할 패턴들 (직무명이 아닌 것들)
    noise_patterns = [
        r'D-\d+',  # D-8
        r'\d+명',  # 5명  
        r'모집|채용|구인|지원|신청',
        r'전환형|체험형|인턴십|프로그램',
        r'공고|공지|안내',
        r'서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주',
        r'급여|연봉|시급|월급|\d+만원',
        r'마감|지원|접수'
    ]
    
    cleaned = title
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    
    # 연속 공백 제거
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def _clean_extracted_job_title(job_title):
    """추출된 직무명 정제"""
    import re
    
    if not job_title:
        return ""
    
    # 기본 정제
    cleaned = job_title.strip()
    
    # 불필요한 단어 제거
    noise_words = ['모집', '채용', '담당', '업무', '내용', '주요', '관련', '분야', '부문']
    for word in noise_words:
        cleaned = re.sub(rf'\b{word}\b', '', cleaned, flags=re.IGNORECASE)
    
    # 연속 공백 제거
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # 길이 체크
    if len(cleaned) < 2 or len(cleaned) > 30:
        return ""
    
    # 의미있는 키워드가 있는지 확인
    meaningful_keywords = [
        'manager', 'engineer', 'developer', 'designer', 'analyst', 'specialist', 'coordinator',
        'associate', 'assistant', 'intern', 'director', 'lead', 'chief',
        '매니저', '개발자', '기획자', '디자이너', '분석가', '운영자', '상담원', '컨설턴트', '인턴',
        '관리자', '담당자', 'bd', 'pm', 'po', 'qa', 'ui/ux', 'devops', 'mlops', 'sre'
    ]
    
    if any(keyword.lower() in cleaned.lower() for keyword in meaningful_keywords):
        return cleaned
    
    return ""

def _is_company_name(text):
    """텍스트가 회사명인지 판단"""
    # 알려진 회사명 리스트
    known_companies = [
        '링글', 'Ringle', '네이버', 'Naver', '카카오', 'Kakao', '라인', 'Line', '쿠팡', 'Coupang',
        '배달의민족', '우아한형제들', '토스', 'Toss', '삼성', 'Samsung', 'LG', 'SK', '현대', 'Hyundai',
        '롯데', 'Lotte', 'KT', 'KTB', 'NHN', 'NCsoft', '넥슨', 'Nexon', '넷마블', 'Netmarble',
        '한화', 'Hanwha', 'GS', 'LS', '포스코', 'POSCO', '신한', '하나', '국민', 'KB', 'IBK'
    ]
    
    # 회사명 지시어
    company_indicators = [
        '주식회사', '㈜', '회사', '기업', '그룹', '코퍼레이션',
        'Corporation', 'Corp', 'Inc', 'Ltd', 'LLC', 'Company', 'Co.'
    ]
    
    text_clean = text.strip()
    
    # 알려진 회사명 포함 확인
    if any(company in text_clean for company in known_companies):
        return True
    
    # 회사 지시어 포함 확인
    if any(indicator in text_clean for indicator in company_indicators):
        return True
    
    # 직무 키워드가 없으면서 짧은 텍스트는 회사명일 가능성 높음
    if len(text_clean) <= 8:
        job_indicators = [
            'manager', 'engineer', 'developer', 'designer', 'analyst', 'specialist',
            '매니저', '개발자', '기획자', '디자이너', '분석가', '엔지니어'
        ]
        has_job_indicator = any(indicator.lower() in text_clean.lower() for indicator in job_indicators)
        if not has_job_indicator:
            return True
    
    return False

if __name__ == '__main__':
    app.run(debug=True)

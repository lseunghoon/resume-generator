"""
sseojum(써줌) 백엔드 메인 애플리케이션 (리팩토링 버전)
분리된 모듈들을 사용하여 깔끔하게 정리된 Flask 애플리케이션
"""
import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# .env 파일 로드를 가장 먼저 실행합니다.
load_dotenv()

# --- 1. Flask 앱 인스턴스를 먼저 생성합니다. ---
app = Flask(__name__)

# --- 2. 로깅 설정 함수를 import 하고, 생성된 app 인스턴스를 전달하여 즉시 실행합니다. ---
# 이 시점에서 애플리케이션의 전역 로깅 규칙이 설정됩니다.
from utils import setup_flask_logger
setup_flask_logger(app)

# --- 3. 이제 로깅이 완벽히 설정되었으니, 나머지 모든 모듈을 import 합니다. ---
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import traceback
import json
import werkzeug
import uuid
import threading
import time

# 설정 및 유틸리티 모듈
from config import get_cors_config, validate_settings
from config.settings import get_database_config, get_vertex_ai_config
from utils import (
    get_logger,
    validate_session_data, validate_question_data, validate_revision_request,
    validate_session_id, validate_question_index, ValidationError,
    FileProcessingError
)

# 새로운 서비스 모듈들
# 이 서비스 모듈들은 import 되는 시점에 내부적으로 로거를 생성하며,
# 이미 설정된 전역 로깅 규칙을 상속받게 됩니다.
from services import AIService, OCRService, FileService
from services.auth_service import AuthService
from services.mail_service import MailService
from supabase_models import get_session_model, get_question_model, get_user_model, get_feedback_model


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


def create_app():
    """Flask 애플리케이션 팩토리"""
    # 설정 검증
    validate_settings()
    
    # Flask 앱 생성
    app = Flask(__name__)
    
    # === 보안: 파일 업로드 크기 제한을 50MB로 설정 ===
    # 이력서/포트폴리오는 보통 수십 MB를 넘지 않음
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    
    # 추가 설정
    app.config['MAX_CONTENT_PATH'] = None
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Werkzeug 설정도 동일하게 설정
    import werkzeug
    werkzeug.formparser.MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    
    # 로거 설정
    setup_flask_logger(app)
    
    # CORS 설정
    CORS(app, resources=get_cors_config())
    
    # Rate Limiting 설정
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    
    # 서비스 초기화 (Lazy Loading 방식)
    def get_ai_service():
        if not hasattr(app, '_ai_service'):
            app._ai_service = AIService()
        return app._ai_service
    

    
    def get_ocr_service():
        if not hasattr(app, '_ocr_service'):
            app._ocr_service = OCRService()
        return app._ocr_service
    
    def get_file_service():
        if not hasattr(app, '_file_service'):
            app._file_service = FileService()
        return app._file_service
    
    def get_auth_service():
        if not hasattr(app, '_auth_service'):
            app._auth_service = AuthService()
        return app._auth_service
    
    def get_mail_service():
        if not hasattr(app, '_mail_service'):
            app._mail_service = MailService(app)
        return app._mail_service
    
    # Rate Limiter 접근자
    def get_limiter():
        return limiter
    
    # 서비스 접근자 등록
    app.get_ai_service = get_ai_service
    app.get_ocr_service = get_ocr_service
    app.get_file_service = get_file_service
    app.get_auth_service = get_auth_service
    app.get_mail_service = get_mail_service
    app.get_limiter = get_limiter
    
    # API 라우트 등록
    register_routes(app)
    
    # 에러 핸들러 등록
    register_error_handlers(app)

    # --- AI 서비스 사전 예열 (비동기, 환경변수로 제어) ---
    def _prewarm_ai_service():
        try:
            start_ms = int(time.time() * 1000)
            app.logger.info("AI 서비스 예열 시작...")
            # 첫 접근 시 내부에서 AIService 인스턴스화 및 모델 로드 수행
            _ = app.get_ai_service()
            elapsed_ms = int(time.time() * 1000) - start_ms
            app.logger.info(f"AI 서비스 예열 완료 ({elapsed_ms}ms)")
        except Exception as e:
            app.logger.error(f"AI 서비스 예열 실패: {str(e)}")

    prewarm_env = os.getenv("PREWARM_AI", "true").strip().lower()
    if prewarm_env in ("1", "true", "yes", "on"): 
        threading.Thread(target=_prewarm_ai_service, name="ai-prewarm", daemon=True).start()
    else:
        app.logger.info("환경변수 PREWARM_AI=false 감지: AI 서비스 예열을 비활성화합니다.")
    # -----------------------------------
    
    return app


def register_error_handlers(app):
    """에러 핸들러 등록"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        response = jsonify({'message': str(error)})
        response.status_code = 400
        return response
    
    # FileProcessingError는 이제 서비스 레벨에서 처리됨
    
    @app.errorhandler(413)
    def handle_request_entity_too_large(error):
        app.logger.error(f"파일 크기 초과: {str(error)}")
        response = jsonify({'message': '첨부파일의 용량이 50mb를 초과했습니다.'})
        response.status_code = 413
        return response
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        app.logger.error(f"내부 서버 오류: {str(error)}")
        response = jsonify({'message': '서버 내부 오류가 발생했습니다.'})
        response.status_code = 500
        return response
    
    @app.errorhandler(429)  # Too Many Requests
    def handle_rate_limit_error(error):
        """Rate Limiting 에러 핸들러"""
        app.logger.warning(f"Rate Limiting 에러: {request.remote_addr}")
        response = jsonify({
            'success': False,
            'message': '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.',
            'status_code': 429,
            'retry_after': '1분 후'
        })
        response.status_code = 429
        return response


def register_routes(app):
    """라우트 등록"""
    
    @app.route('/')
    def index():
        """API 서버 상태 확인을 위한 루트 경로 핸들러"""
        return jsonify({
            'status': 'ok',
            'message': 'Resume AI API Server is running (Refactored)',
            'version': '2.0.0'
        })

    @app.route('/api/v1/health')
    def health_check():
        """API 서버 상태 확인을 위한 헬스 체크 엔드포인트"""
        return jsonify({
            'status': 'ok',
            'message': 'API server is healthy'
        })

    @app.route('/api/v1/upload', methods=['POST'])
    def upload():
        """파일 업로드 및 세션 생성"""
        app.logger.info("===== /upload 요청 시작 =====")
        
        # 인증 확인
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise APIError("인증 토큰이 필요합니다.", status_code=401)
        
        access_token = auth_header.split(' ')[1]
        auth_service = app.get_auth_service()
        user = auth_service.get_user(access_token)
        
        if not user:
            raise APIError("유효하지 않은 토큰입니다.", status_code=401)
        
        app.logger.info(f"인증된 사용자: {user['email']}")
        
        # Supabase 모델 가져오기
        session_model = get_session_model()
        question_model = get_question_model()
        
        try:
            # 413 오류를 가장 먼저 처리
            if request.content_length and request.content_length > 50 * 1024 * 1024:
                app.logger.error(f"요청 크기가 50MB를 초과합니다: {request.content_length / 1024 / 1024:.2f} MB")
                return jsonify({'message': '업로드된 파일의 크기가 너무 큽니다. (최대 50MB)'}), 413
            
            # 파일 검증 (파일이 없어도 허용)
            try:
                files = request.files.getlist('files')
                if not files or not any(f.filename for f in files):
                    app.logger.info("파일이 없습니다. 건너뛰기 모드로 진행합니다.")
                    files = []  # 빈 리스트로 설정
                
                # 디버깅: 파일 크기 로깅 (파일이 있을 때만)
                total_size = 0
                if files:
                    for file in files:
                        file.seek(0, 2)  # 파일 끝으로 이동
                        file_size = file.tell()  # 현재 위치 (파일 크기)
                        file.seek(0)  # 파일 시작으로 되돌리기
                        total_size += file_size
                        app.logger.info(f"파일: {file.filename}, 크기: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
                    
                    app.logger.info(f"총 파일 크기: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)")
                else:
                    app.logger.info("업로드된 파일이 없습니다.")
                
            except werkzeug.exceptions.RequestEntityTooLarge:
                app.logger.error("파일 크기가 너무 큽니다.")
                return jsonify({'message': '첨부파일의 용량이 50mb를 초과했습니다.'}), 413
            
            # 데이터 검증
            data_str = request.form.get('data')
            if not data_str:
                raise APIError("'data' 필드가 없습니다.", status_code=400)
            
            # 디버깅: FormData 크기 로깅
            data_size_mb = len(data_str) / 1024 / 1024
            app.logger.info(f"FormData 'data' 필드 크기: {data_size_mb:.2f} MB")
            if data_size_mb > 10:  # 10MB가 넘으면 경고
                app.logger.warning("경고: 'data' 필드에 포함된 콘텐츠(htmlContent/preloadedContent)가 너무 큽니다. 'contentId' 사용을 권장합니다.")
            
            # 전체 요청 크기 확인
            content_length = request.content_length
            if content_length:
                app.logger.info(f"전체 요청 크기: {content_length} bytes ({content_length / 1024 / 1024:.2f} MB)")
                if content_length > 50 * 1024 * 1024:  # 50MB 초과
                    app.logger.error(f"전체 요청이 50MB를 초과합니다: {content_length / 1024 / 1024:.2f} MB")
                    return jsonify({'message': '첨부파일의 용량이 50mb를 초과했습니다.'}), 413
            
            # FormData 개별 필드 크기 확인
            app.logger.info("=== FormData 필드별 크기 분석 ===")
            for field_name in request.form:
                field_data = request.form[field_name]
                if isinstance(field_data, str):
                    field_size = len(field_data.encode('utf-8'))
                    app.logger.info(f"필드 '{field_name}': {field_size} bytes ({field_size / 1024 / 1024:.2f} MB)")
                else:
                    app.logger.info(f"필드 '{field_name}': 파일 또는 바이너리 데이터")
            
            # 파일 크기 확인
            if 'files' in request.files:
                for i, file in enumerate(request.files.getlist('files')):
                    file.seek(0, 2)  # 파일 끝으로 이동
                    file_size = file.tell()
                    file.seek(0)  # 파일 시작으로 복원
                    app.logger.info(f"파일 {i+1} '{file.filename}': {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
            app.logger.info("==================================")
            
            # JSON 파싱 및 검증
            data = json.loads(data_str)
            validated_data = validate_session_data(data)
            
            # 사용자 직접 입력 채용정보 사용
            job_description = validated_data['jobDescription'].strip()
            resume_text = validated_data['resumeText'].strip()
            questions = validated_data.get('questions', [])
            
            app.logger.info(f"채용정보 텍스트: {len(job_description)}자")
            app.logger.info(f"이력서 텍스트: {len(resume_text)}자")
            app.logger.info(f"질문 개수: {len(questions)}개")


            # 파일 텍스트 추출 (파일이 있으면 파일에서 추출, 없으면 사용자 입력 사용)
            if files:
                file_result = app.get_file_service().process_uploaded_files(files)
                if not file_result['success']:
                    raise APIError(file_result['message'], status_code=400)
                
                file_resume_text = file_result['extracted_text']
                file_count = file_result.get('file_count', 1)
                total_text_length = file_result.get('text_length', len(file_resume_text))
                
                app.logger.info(f"파일 처리 완료: {file_count}개 파일에서 총 {total_text_length}자 추출")
                app.logger.info(f"파일에서 이력서 텍스트 추출 완료: {len(file_resume_text)}자")
                
                # 파일에서 추출한 텍스트와 사용자 입력 텍스트를 결합 (플레이스홀더 안전 처리)
                placeholder_indicators = [
                    "파일에서 추출된 이력서 내용이 있습니다",
                    "파일에서 추출된 이력서 내용입니다"
                ]

                # 프론트의 안내용 플레이스홀더 텍스트가 온 경우, 합치지 말고 파일 텍스트만 사용
                if resume_text and any(ind in resume_text for ind in placeholder_indicators):
                    resume_text = file_resume_text
                    app.logger.info("플레이스홀더 이력서 텍스트 감지: 파일 텍스트만 사용")
                elif resume_text and file_resume_text:
                    resume_text = f"{resume_text}\n\n=== 파일에서 추출한 내용 ===\n{file_resume_text}"
                    app.logger.info(f"사용자 입력과 파일 내용 결합: {len(resume_text)}자")
                elif file_resume_text:
                    resume_text = file_resume_text
                    app.logger.info("파일에서 추출한 텍스트만 사용")
            else:
                app.logger.info("파일이 없어서 사용자 입력 텍스트만 사용")

            # 세션 생성 (Supabase 사용)
            # 사용자가 직접 입력한 데이터를 그대로 사용
            app.logger.info("사용자가 직접 입력한 데이터를 DB에 저장합니다.")
            
            # 사용자가 입력한 개별 필드들을 직접 사용
            company_name = validated_data.get('companyName', '')
            job_title = validated_data.get('jobTitle', '')
            main_responsibilities = validated_data.get('mainResponsibilities', '')
            requirements = validated_data.get('requirements', '')
            preferred_qualifications = validated_data.get('preferredQualifications', '')
            
            app.logger.info(f"사용자 입력 데이터:")
            app.logger.info(f"  - 회사명: '{company_name}'")
            app.logger.info(f"  - 직무: '{job_title}'")
            app.logger.info(f"  - 주요업무: {len(main_responsibilities)}자")
            app.logger.info(f"  - 자격요건: {len(requirements)}자")
            app.logger.info(f"  - 우대사항: {len(preferred_qualifications)}자")
            
            # Supabase에 세션 생성
            session_data = {
                'company_name': company_name,
                'job_title': job_title,
                'main_responsibilities': main_responsibilities,
                'requirements': requirements,
                'preferred_qualifications': preferred_qualifications,
                'resume_text': resume_text
            }
            
            new_session = session_model.create_session(user['id'], session_data)
            
            app.logger.info(f"세션 생성 성공: {new_session['id']}")
            
            # 질문이 있으면 자기소개서 생성
            if questions:
                app.logger.info("자기소개서 생성 요청 시작")
                try:
                    # AI 서비스를 사용하여 자기소개서 생성
                    ai_service = app.get_ai_service()
                    
                    for i, question_text in enumerate(questions):
                        if question_text and question_text.strip():
                            app.logger.info(f"질문 {i+1} 처리 중: {question_text[:50]}...")
                            
                            # AI 서비스로 자기소개서 생성
                            result = ai_service.generate_cover_letter(
                                question=question_text,
                                jd_text=job_description,
                                resume_text=resume_text,
                                company_name=company_name,
                                job_title=job_title
                            )
                            
                            # 튜플에서 답변과 회사 정보 추출
                            answer, company_info = result
                            
                            # 질문과 답변을 Supabase에 저장
                            question_data = {
                                'question_number': i+1,  # 세션 내 질문 번호
                                'question': question_text.strip(),
                                'answer_history': [answer],
                                'current_version_index': 0
                            }
                            
                            question_model.create_question(new_session['id'], question_data)
                    
                    app.logger.info("질문 저장 완료")
                    app.logger.info("자기소개서 생성 완료")
                    
                    # DB 트랜잭션이 완전히 완료되도록 짧은 대기 시간 추가
                    import time
                    time.sleep(0.5)  # 0.5초 대기
                    
                except Exception as e:
                    app.logger.error(f"자기소개서 생성 중 오류: {str(e)}")
                    # 자기소개서 생성 실패해도 세션은 성공으로 처리
                    pass
            else:
                app.logger.info("질문이 없어서 자기소개서 생성 건너뜀")
            
            return jsonify({
                'sessionId': new_session['id'],
                'message': 'Files uploaded and session created successfully'
            }), 201

        except (APIError, ValidationError, FileProcessingError):
            raise
        except Exception as e:
            app.logger.error(f"업로드 처리 중 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"세션 생성에 실패했습니다: {str(e)}", status_code=500)

    @app.route('/api/v1/job-info', methods=['POST'])
    def job_info():
        """채용정보 직접 입력 API"""
        try:
            # 인증 확인
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.", status_code=401)
            
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            user = auth_service.get_user(access_token)
            
            if not user:
                raise APIError("유효하지 않은 토큰입니다.", status_code=401)
            
            app.logger.info("채용정보 입력 요청 시작")
            data = request.get_json()
            
            # 필수 필드 검증
            required_fields = ['companyName', 'jobTitle', 'mainResponsibilities', 'requirements', 'preferredQualifications']
            for field in required_fields:
                if not data.get(field):
                    raise APIError(f"필수 필드가 누락되었습니다: {field}", status_code=400)
            
            # 텍스트 길이 검증
            if len(data['companyName'].strip()) < 2:
                raise APIError("회사명은 최소 2자 이상이어야 합니다.", status_code=400)
            
            if len(data['jobTitle'].strip()) < 2:
                raise APIError("직무는 최소 2자 이상이어야 합니다.", status_code=400)
            
            if len(data['mainResponsibilities'].strip()) < 10:
                raise APIError("주요업무는 최소 10자 이상이어야 합니다.", status_code=400)
            
            if len(data['requirements'].strip()) < 10:
                raise APIError("자격요건은 최소 10자 이상이어야 합니다.", status_code=400)
            
            # 우대사항은 선택사항이므로 빈 문자열도 허용
            preferred_qualifications = data.get('preferredQualifications', '').strip()
            
            # 채용정보 텍스트 구성
            job_description = f"""
회사명: {data['companyName'].strip()}
직무: {data['jobTitle'].strip()}

주요업무:
{data['mainResponsibilities'].strip()}

자격요건:
{data['requirements'].strip()}
"""
            
            if preferred_qualifications:
                job_description += f"""
우대사항:
{preferred_qualifications}
"""
            
            app.logger.info(f"채용정보 구성 완료: {len(job_description)}자")
            
            # Supabase에 세션 생성
            session_model = get_session_model()
            session_data = {
                'company_name': data['companyName'].strip(),
                'job_title': data['jobTitle'].strip(),
                'main_responsibilities': data['mainResponsibilities'].strip(),
                'requirements': data['requirements'].strip(),
                'preferred_qualifications': preferred_qualifications,
                'resume_text': ""
            }
            
            session = session_model.create_session(user['id'], session_data)
            
            return jsonify({
                'success': True,
                'sessionId': session['id'],
                'jobDescription': job_description,
                'message': '채용정보가 성공적으로 저장되었습니다.'
            }), 200
            
        except APIError:
            raise
        except Exception as e:
            app.logger.error(f"채용정보 입력 처리 중 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"채용정보 입력에 실패했습니다: {str(e)}", status_code=500)

    @app.route('/api/v1/generate', methods=['POST'])
    def generate():
        """세션 ID를 받아 자기소개서 생성 (배치 처리) - 비활성화됨"""
        # 이 엔드포인트는 더 이상 사용되지 않습니다.
        # 자기소개서 생성은 /api/v1/upload에서 세션 생성과 함께 처리됩니다.
        return jsonify({
            'message': '이 엔드포인트는 더 이상 사용되지 않습니다. 자기소개서 생성은 세션 생성과 함께 처리됩니다.'
        }), 410  # Gone

    @app.route('/api/v1/revise', methods=['POST'])
    def revise():
        """자기소개서 수정, undo, redo 처리"""
        # Supabase 모델 가져오기
        session_model = get_session_model()
        question_model = get_question_model()
        
        try:
            app.logger.info("자기소개서 수정 요청 시작")
            
            # 인증 확인
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.", status_code=401)
            
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            user = auth_service.get_user(access_token)
            
            if not user:
                raise APIError("유효하지 않은 토큰입니다.", status_code=401)
            
            data = request.get_json()
            
            session_id = validate_session_id(data.get('sessionId'))
            question_index = validate_question_index(data.get('questionIndex'))
            action = data.get('action', 'revise')
            
            session = session_model.get_session(session_id, user['id'])
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)
            
            # 세션의 질문들 조회
            questions = question_model.get_session_questions(session_id)
            if not questions or question_index <= 0 or question_index > len(questions):
                raise APIError("질문을 찾을 수 없습니다.", status_code=404)

            # question_index는 1부터 시작하므로 0부터 시작하는 배열 인덱스로 변환
            question = questions[question_index - 1]
            history = question.get('answer_history', [])
            if not history:
                history = []
            
            
            if action == 'undo':
                current_version_index = question.get('current_version_index', 0)
                if current_version_index > 0:
                    question['current_version_index'] = current_version_index - 1
            
            elif action == 'redo':
                current_version_index = question.get('current_version_index', 0)
                if current_version_index < len(history) - 1:
                    question['current_version_index'] = current_version_index + 1
            
            elif action == 'revise':
                revision_request = validate_revision_request(data.get('revisionRequest'))
                
                # 현재 버전 이후의 히스토리 삭제
                current_version_index = question.get('current_version_index', 0)
                history = history[:current_version_index + 1]
                
                # 개별 필드들을 조합하여 JD 텍스트 생성
                jd_text = f"""
회사명: {session.get('company_name', '')}
직무: {session.get('job_title', '')}

주요업무:
{session.get('main_responsibilities', '')}

자격요건:
{session.get('requirements', '')}

우대사항:
{session.get('preferred_qualifications', '')}
                """.strip()
                
                revised_text = app.get_ai_service().revise_cover_letter(
                    question=question['question'],
                    jd_text=jd_text,
                    resume_text=session.get('resume_text', ''),
                    original_answer=history[current_version_index] if history and 0 <= current_version_index < len(history) else '',
                    user_edit_prompt=revision_request,
                    company_info="",  # 회사 정보 사용 비활성화
                    company_name=session.get('company_name', ''),
                    job_title=session.get('job_title', ''),
                    answer_history=history
                )
                
                # 수정 프롬프트를 revision_prompts 배열에 추가
                revision_prompts = question.get('revision_prompts', [])
                revision_prompts.append({
                    'prompt': revision_request,
                    'timestamp': int(time.time() * 1000),  # 밀리초 단위 타임스탬프
                    'version_index': len(history)  # 새로 생성될 버전의 인덱스
                })
                question['revision_prompts'] = revision_prompts
                
                history.append(revised_text)
                question['answer_history'] = history
                question['current_version_index'] = len(history) - 1
            
            else:
                raise APIError(f"알 수 없는 액션입니다: {action}", status_code=400)

            # 질문 업데이트
            question_model.update_question(question['id'], question)
            
            # 응답 반환
            return jsonify({
                'revisedAnswer': history[question['current_version_index']] if history and 0 <= question.get('current_version_index', 0) < len(history) else '',
                'message': '자기소개서가 성공적으로 수정되었습니다.'
            }), 200

        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"자기소개서 수정 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"자기소개서 수정에 실패했습니다: {str(e)}", status_code=500)

    @app.route('/api/v1/session/<string:id>', methods=['DELETE'])
    def delete_session(id):
        """세션 삭제 및 관련 데이터 정리"""
        try:
            session_id = validate_session_id(id)
            app.logger.info(f"세션 삭제 요청: {session_id}")
            
            # 인증 확인
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.", status_code=401)
            
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            user = auth_service.get_user(access_token)
            
            if not user:
                raise APIError("유효하지 않은 토큰입니다.", status_code=401)
            
            # Supabase에서 세션 삭제
            session_model = get_session_model()
            success = session_model.delete_session(session_id, user['id'])
            
            if not success:
                raise APIError("Session not found", status_code=404)

            # 파일 정리 (업로드된 파일이 있다면 정리)
            try:
                file_service = app.get_file_service()
                cleanup_result = file_service.cleanup_old_files(max_age_days=0)  # 즉시 정리
                app.logger.info(f"파일 정리 결과: {cleanup_result}")
            except Exception as file_error:
                app.logger.warning(f"파일 정리 중 오류 (무시됨): {file_error}")
            
            app.logger.info(f"세션 삭제 및 데이터 정리 완료: {session_id}")
            return jsonify({
                'success': True,
                'message': 'Session and related data deleted successfully'
            }), 200

        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"세션 삭제 오류: {str(e)}")
            raise APIError(f"Deletion failed: {str(e)}", status_code=500)

    @app.route('/api/v1/session/<string:id>', methods=['GET'])
    @app.get_limiter().limit("50 per minute, 200 per hour")  # 세션 조회용 제한
    def get_session(id):
        """세션 조회"""
        try:
            session_id = validate_session_id(id)
            
            # 인증 확인
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.", status_code=401)
            
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            user = auth_service.get_user(access_token)
            
            if not user:
                raise APIError("유효하지 않은 토큰입니다.", status_code=401)
            
            # Supabase에서 세션 조회
            session_model = get_session_model()
            session = session_model.get_session(session_id, user['id'])
            
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)
            
            # Supabase에서 질문 조회
            question_model = get_question_model()
            questions = question_model.get_session_questions(session_id)
            
            questions_with_answers = []
            for question in questions:
                answer_history = question.get('answer_history', [])
                if not answer_history:
                    answer_history = []
                current_answer = answer_history[question['current_version_index']] if answer_history and 0 <= question.get('current_version_index', 0) < len(answer_history) else ''
                questions_with_answers.append({
                    'id': question['id'],
                    'question': question['question'],
                    'answer': current_answer,
                    'answer_history': question['answer_history'],
                    'current_version_index': question['current_version_index'],
                    'revision_prompts': question.get('revision_prompts', []),
                    'length': len(current_answer),
                    'question_number': question['question_number']
                })

            # 개별 필드들을 조합하여 JD 텍스트 생성
            jd_text = f"""
회사명: {session.get('company_name', '')}
직무: {session.get('job_title', '')}

주요업무:
{session.get('main_responsibilities', '')}

자격요건:
{session.get('requirements', '')}

우대사항:
{session.get('preferred_qualifications', '')}
            """.strip()

            # 건너뛰기 여부 판단: 실제 의미있는 이력서 데이터가 있는지 확인
            resume_text_value = session.get('resume_text') or ''
            
            # 건너뛰기 케이스: 빈 문자열이거나 플레이스홀더만 있는 경우
            is_skip_case = (
                not resume_text_value.strip() or
                resume_text_value.strip() in [
                    "파일에서 추출된 이력서 내용이 있습니다. 업로드된 파일에서 텍스트가 추출됩니다.",
                    "파일에서 추출된 이력서 내용입니다."
                ]
            )
            
            generated_from_skip = is_skip_case

            return jsonify({
                'questions': questions_with_answers,
                'jobDescription': jd_text,
                'companyName': session['company_name'] or '',
                'jobTitle': session['job_title'] or '',
                'generatedFromSkip': generated_from_skip,
                'message': '자기소개서 조회에 성공했습니다.'
            }), 200

        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"세션 조회 오류: {str(e)}")
            raise APIError(f"세션 조회에 실패했습니다: {str(e)}", status_code=500)







    @app.route('/api/v1/add-question', methods=['POST'])
    def add_question():
        """기존 세션에 새로운 질문 추가"""
        try:
            app.logger.info("새 질문 추가 요청 시작")
            
            # 인증 확인
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.", status_code=401)
            
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            user = auth_service.get_user(access_token)
            
            if not user:
                raise APIError("유효하지 않은 토큰입니다.", status_code=401)
            
            data = request.get_json()
            session_id = validate_session_id(data.get('sessionId'))
            question_text = data.get('question')
            
            # 질문 검증
            validated_question = validate_question_data(question_text)
            
            # Supabase에서 세션 조회
            session_model = get_session_model()
            session = session_model.get_session(session_id, user['id'])
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)
            
            # Supabase에서 기존 질문 수 확인
            question_model = get_question_model()
            existing_questions = question_model.get_session_questions(session_id)
            
            # 최대 질문 수 제한
            if len(existing_questions) >= 3:
                raise APIError("최대 3개의 질문까지만 추가할 수 있습니다.", status_code=400)
            
            # 데이터 유효성 검증
            if not session['resume_text'] or not session['main_responsibilities']:
                raise APIError("이력서나 채용공고 정보가 없어 답변을 생성할 수 없습니다.", status_code=400)
            
            # 개별 필드들을 조합하여 JD 텍스트 생성
            jd_text = f"""
회사명: {session['company_name'] or ''}
직무: {session['job_title'] or ''}

주요업무:
{session['main_responsibilities'] or ''}

자격요건:
{session['requirements'] or ''}

우대사항:
{session['preferred_qualifications'] or ''}
            """.strip()
            
            # AI 답변 생성
            result = app.get_ai_service().generate_cover_letter(
                question=validated_question['question'],
                jd_text=jd_text,
                resume_text=session['resume_text'],
                company_name=session['company_name'] or "",
                job_title=session['job_title'] or ""
            )
            
            # 튜플에서 답변과 회사 정보 추출
            generated_answer, company_info = result
            
            if not generated_answer:
                raise APIError("답변 생성에 실패했습니다.", status_code=500)
            
            # 세션 내 질문 번호 계산
            question_number = len(existing_questions) + 1
            
            # Supabase에 새 질문 저장
            question_data = {
                'question_number': question_number,
                'question': validated_question['question'],
                'answer_history': [generated_answer],
                'current_version_index': 0
            }
            
            new_question = question_model.create_question(session_id, question_data)
            
            app.logger.info(f"새 질문 저장 완료 - 세션 내 번호: {question_number}")
            
            return jsonify({
                'questionId': new_question['id'],
                'question': validated_question['question'],
                'answer': generated_answer,
                'length': len(generated_answer),
                'message': '새로운 질문과 답변이 생성되었습니다.'
            }), 200
            
        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"새 질문 추가 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"새 질문 추가에 실패했습니다: {str(e)}", status_code=500)

    @app.route('/api/v1/sessions/<string:session_id>/questions', methods=['POST'])
    def add_question_to_session(session_id):
        """특정 세션에 새로운 질문 추가 (RESTful 엔드포인트)"""
        # Supabase 모델 가져오기
        session_model = get_session_model()
        question_model = get_question_model()
        
        try:
            app.logger.info(f"새 질문 추가 요청 시작 - 세션: {session_id}")
            
            # 인증 확인
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.", status_code=401)
            
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            user = auth_service.get_user(access_token)
            
            if not user:
                raise APIError("유효하지 않은 토큰입니다.", status_code=401)
            
            data = request.get_json()
            if not data or 'question' not in data:
                raise APIError("question이 필요합니다.", status_code=400)
            
            question_text = data.get('question')
            
            # 질문 검증
            validated_question = validate_question_data(question_text)
            
            # 세션 조회
            session = session_model.get_session(session_id, user['id'])
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)
            
            # 기존 질문 수 확인
            existing_questions = question_model.get_session_questions(session_id)
            
            # 최대 질문 수 제한
            if len(existing_questions) >= 3:
                raise APIError("최대 3개의 질문까지만 추가할 수 있습니다.", status_code=400)
            
            # [수정] "건너뛰기" 케이스를 허용하기 위해 이력서/JD 유무 검증 로직을 제거합니다.
            # 이 책임은 AIService로 넘어갑니다.
            
            # 개별 필드들을 조합하여 JD 텍스트 생성
            jd_text = f"""
회사명: {session.get('company_name', '')}
직무: {session.get('job_title', '')}

주요업무:
{session.get('main_responsibilities', '')}

자격요건:
{session.get('requirements', '')}

우대사항:
{session.get('preferred_qualifications', '')}
            """.strip()
            
            # AI 답변 생성
            generated_answer, company_info = app.get_ai_service().generate_cover_letter(
                question=validated_question['question'],
                jd_text=jd_text,
                resume_text=session.get('resume_text', ''), # 빈 문자열이 전달될 수 있음
                company_name=session.get('company_name') or "",
                job_title=session.get('job_title') or ""
            )
            
            if not generated_answer:
                raise APIError("답변 생성에 실패했습니다.", status_code=500)
            
            # 세션 내 질문 번호 계산
            question_number = len(existing_questions) + 1
            
            # 새 질문 저장
            new_question = question_model.create_question(session_id, {
                'question_number': question_number,
                'question': validated_question['question'],
                'answer_history': [generated_answer],
                'current_version_index': 0
            })
            
            app.logger.info(f"새 질문 저장 완료 - 세션 내 번호: {question_number}")
            
            return jsonify({
                'questionId': new_question['id'],
                'question': validated_question['question'],
                'answer': generated_answer,
                'length': len(generated_answer),
                'message': '새로운 질문과 답변이 생성되었습니다.'
            }), 200
            
        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"새 질문 추가 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"새 질문 추가에 실패했습니다: {str(e)}", status_code=500)

    # 인증 관련 API 엔드포인트
    @app.route('/api/v1/auth/google/url', methods=['GET'])
    def get_google_auth_url():
        """Google OAuth URL 생성"""
        try:
            print("Google OAuth URL 요청 받음")
            auth_service = app.get_auth_service()
            print(f"AuthService 객체 생성됨: {type(auth_service)}")
            print(f"AuthService 메서드들: {dir(auth_service)}")
            auth_url = auth_service.get_google_auth_url()
            print(f"생성된 auth_url: {auth_url}")
            return jsonify({"success": True, "auth_url": auth_url})
        except Exception as e:
            print(f"Google OAuth URL 생성 오류: {str(e)}")
            print(f"오류 타입: {type(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": f"Google OAuth URL 생성 오류: {str(e)}"}), 500

    @app.route('/api/v1/auth/google/callback', methods=['POST'])
    def handle_google_callback():
        """Google OAuth 콜백 처리"""
        try:
            data = request.get_json()
            code = data.get('code')
            
            if not code:
                raise APIError("인증 코드가 필요합니다.")
            
            auth_service = app.get_auth_service()
            result = auth_service.handle_google_callback(code)
            
            return jsonify(result)
            
        except APIError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"Google OAuth 콜백 오류: {str(e)}"}), 500

    @app.route('/api/v1/auth/signout', methods=['POST'])
    def signout():
        """로그아웃"""
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.")
            
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            result = auth_service.sign_out(access_token)
            
            return jsonify(result)
            
        except APIError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"로그아웃 오류: {str(e)}"}), 500

    @app.route('/api/v1/auth/user', methods=['GET'])
    @app.get_limiter().limit("200 per minute, 1000 per hour")  # 사용자 정보 조회용 관대한 제한
    def get_user():
        """현재 사용자 정보 조회"""
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.")
            
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            user = auth_service.get_user(access_token)
            
            if user:
                return jsonify({"success": True, "user": user})
            else:
                return jsonify({"success": False, "message": "사용자 정보를 찾을 수 없습니다."}), 404
                
        except APIError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"사용자 정보 조회 오류: {str(e)}"}), 500

    @app.route('/api/v1/user/sessions', methods=['GET'])
    @app.get_limiter().limit("100 per minute, 500 per hour")  # 세션 목록 조회용 관대한 제한
    def get_user_sessions():
        """사용자별 자기소개서 세션 목록 조회"""
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.")
            
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            user = auth_service.get_user(access_token)
            
            if not user:
                raise APIError("사용자 정보를 찾을 수 없습니다.")
            
            # 사용자의 세션 목록 조회
            session_model = get_session_model()
            sessions = session_model.get_user_sessions(user['id'])
            
            return jsonify({
                "success": True, 
                "sessions": sessions
            })
                
        except APIError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"세션 목록 조회 오류: {str(e)}"}), 500

    @app.route('/api/v1/auth/refresh', methods=['POST'])
    def refresh_token():
        """토큰 갱신"""
        try:
            data = request.get_json()
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                raise APIError("리프레시 토큰이 필요합니다.")
            
            auth_service = app.get_auth_service()
            result = auth_service.refresh_token(refresh_token)
            
            return jsonify(result)
            
        except APIError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"토큰 갱신 오류: {str(e)}"}), 500

    @app.route('/api/v1/auth/reset-password', methods=['POST'])
    def reset_password():
        """비밀번호 재설정"""
        try:
            data = request.get_json()
            email = data.get('email')
            
            if not email:
                raise APIError("이메일을 입력해 주세요")
            
            auth_service = app.get_auth_service()
            result = auth_service.reset_password(email)
            
            return jsonify(result)
            
        except APIError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"비밀번호 재설정 오류: {str(e)}"}), 500

    @app.route('/api/v1/sessions/<string:session_id>/questions/<int:question_index>/revise', methods=['POST'])
    def revise_answer(session_id, question_index):
        """특정 질문의 답변 수정 (세션 내 인덱스 기반)"""
        # Supabase 모델 가져오기
        session_model = get_session_model()
        question_model = get_question_model()
        
        try:
            app.logger.info(f"답변 수정 요청 시작 - 세션: {session_id}, 질문 인덱스: {question_index}")
            # 인증 확인
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise APIError("인증 토큰이 필요합니다.", status_code=401)
            access_token = auth_header.split(' ')[1]
            auth_service = app.get_auth_service()
            user = auth_service.get_user(access_token)
            if not user:
                raise APIError("유효하지 않은 토큰입니다.", status_code=401)
            
            data = request.get_json()
            if not data or 'revision' not in data:
                raise APIError("revision이 필요합니다.", status_code=400)
            
            revision_text = data['revision']
            
            # 세션 조회
            session = session_model.get_session(session_id, user['id'])
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)
            
            # 세션 내 질문 인덱스 검증
            if not session.questions or question_index < 0 or question_index >= len(session.questions):
                raise APIError("질문을 찾을 수 없습니다.", status_code=404)
            
            # 세션 내 해당 인덱스의 질문 가져오기 (안전한 접근)
            question = session.questions[question_index]
            
            
            # 현재 답변을 히스토리에 추가
            current_answer = question.answer_history
            if current_answer:
                try:
                    history_list = json.loads(current_answer) if isinstance(current_answer, str) else current_answer
                except (json.JSONDecodeError, TypeError):
                    history_list = []
            else:
                history_list = []
            
            # 현재 답변을 히스토리에 추가
            if question.current_version_index < len(history_list):
                current_answer_text = history_list[question.current_version_index]
                history_list.append(current_answer_text)
            else:
                history_list.append("")
            
            # 개별 필드들을 조합하여 JD 텍스트 생성
            jd_text = f"""
회사명: {session.company_name or ''}
직무: {session.job_title or ''}

주요업무:
{session.main_responsibilities or ''}

자격요건:
{session.requirements or ''}

우대사항:
{session.preferred_qualifications or ''}
            """.strip()
            
            # 답변 수정
            revised_answer = app.get_ai_service().revise_cover_letter(
                question=question.question,
                jd_text=jd_text,
                resume_text=session.resume_text or "",
                original_answer=current_answer_text if 'current_answer_text' in locals() else "",
                user_edit_prompt=revision_text,
                company_info="",  # 회사 정보 사용 비활성화
                company_name=session.company_name or "",
                job_title=session.job_title or "",
                answer_history=history_list
            )
            
            # 새로운 답변을 히스토리에 추가
            history_list.append(revised_answer)
            
            # 데이터베이스 업데이트
            question.answer_history = json.dumps(history_list)
            question.current_version_index = len(history_list) - 1
            
            session_model.update_session(session_id, user['id'], session.to_dict())
            
            app.logger.info(f"답변 수정 완료 - 세션: {session_id}, 질문 인덱스: {question_index}")
            
            return jsonify({
                'success': True,
                'revised_answer': revised_answer,
                'message': '답변이 수정되었습니다.'
            }), 200
            
        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"답변 수정 중 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"답변 수정에 실패했습니다: {str(e)}", status_code=500)

    @app.route('/api/v1/feedback', methods=['POST'])
    @app.get_limiter().limit("5 per minute, 20 per hour")  # Rate Limiting 적용
    def submit_feedback():
        """피드백 제출 및 메일 전송"""
        try:
            app.logger.info("피드백 제출 요청 시작")
            
            # 인증 확인 (선택사항 - 비로그인 사용자도 피드백 가능)
            user_id = None
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    access_token = auth_header.split(' ')[1]
                    auth_service = app.get_auth_service()
                    user = auth_service.get_user(access_token)
                    if user:
                        user_id = user['id']
                        app.logger.info(f"인증된 사용자: {user['email']}")
                except Exception as e:
                    app.logger.warning(f"인증 실패 (비로그인 사용자로 처리): {str(e)}")
            
            # 요청 데이터 검증
            data = request.get_json()
            if not data:
                raise APIError("요청 데이터가 없습니다.", status_code=400)
            
            email = data.get('email', '').strip()
            message = data.get('message', '').strip()
            
            # 필수 필드 검증
            if not email:
                raise APIError("이메일은 필수입니다.", status_code=400)
            
            if not message:
                raise APIError("메시지는 필수입니다.", status_code=400)
            
            # 이메일 형식 검증 (강화된 검증)
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise APIError("올바른 이메일 형식이 아닙니다.", status_code=400)
            
            # 이메일 길이 제한
            if len(email) > 254:  # RFC 5321 표준
                raise APIError("이메일 주소가 너무 깁니다.", status_code=400)
            
            # 메시지 길이 검증
            if len(message) < 5:
                raise APIError("메시지는 최소 5자 이상이어야 합니다.", status_code=400)
            
            if len(message) > 2000:
                raise APIError("메시지는 최대 2000자까지 입력 가능합니다.", status_code=400)
            
            app.logger.info(f"피드백 데이터 검증 완료: {email}, 메시지 길이: {len(message)}자, IP: {request.remote_addr}")
            
            # Supabase에 피드백 저장
            feedback_model = get_feedback_model()
            feedback_data = {
                'user_id': user_id,
                'email': email,
                'message': message
            }
            
            feedback = feedback_model.create_feedback(feedback_data)
            if not feedback:
                raise APIError("피드백 저장에 실패했습니다.", status_code=500)
            
            app.logger.info(f"피드백 저장 성공: {feedback['id']}")
            
            # 메일 전송
            mail_service = app.get_mail_service()
            mail_result = mail_service.send_feedback_email({
                'email': email,
                'message': message,
                'created_at': feedback.get('created_at', 'N/A')
            })
            
            # 메일 전송 결과에 따라 상태 업데이트
            if mail_result['success']:
                feedback_model.update_feedback_status(feedback['id'], 'sent')
                app.logger.info(f"피드백 메일 전송 성공: {feedback['id']}")
                
                return jsonify({
                    'success': True,
                    'message': '피드백이 성공적으로 전송되었습니다.',
                    'feedbackId': feedback['id']
                }), 200
            else:
                # 메일 전송 실패 시 상태 업데이트
                feedback_model.update_feedback_status(
                    feedback['id'], 
                    'failed', 
                    mail_result.get('error', '알 수 없는 오류')
                )
                
                app.logger.error(f"피드백 메일 전송 실패: {feedback['id']}, 오류: {mail_result.get('error')}")
                
                # 메일 전송 실패해도 피드백은 저장되었으므로 부분 성공으로 처리
                return jsonify({
                    'success': False,
                    'message': '피드백은 저장되었지만 메일 전송에 실패했습니다. 나중에 다시 시도해주세요.',
                    'feedbackId': feedback['id'],
                    'error': mail_result.get('error')
                }), 200
            
        except APIError:
            raise
        except Exception as e:
            app.logger.error(f"피드백 제출 처리 중 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"피드백 제출에 실패했습니다: {str(e)}", status_code=500)

    @app.route('/api/v1/feedback/test', methods=['GET'])
    @app.get_limiter().limit("2 per minute, 10 per hour")  # 테스트용 Rate Limiting
    def test_mail_service():
        """메일 서비스 연결 테스트"""
        try:
            mail_service = app.get_mail_service()
            result = mail_service.test_connection()
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': '메일 서비스 연결 테스트 성공'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': result['message']
                }), 500
                
        except Exception as e:
            app.logger.error(f"메일 서비스 테스트 중 오류: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'메일 서비스 테스트 실패: {str(e)}'
            }), 500


# Flask 앱 생성
app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 
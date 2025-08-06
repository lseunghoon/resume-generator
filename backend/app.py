"""
iloveresume 백엔드 메인 애플리케이션 (리팩토링 버전)
분리된 모듈들을 사용하여 깔끔하게 정리된 Flask 애플리케이션
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import json
import werkzeug
import uuid
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 설정 및 유틸리티 모듈
from config import get_cors_config, validate_settings
from config.settings import get_database_config, get_vertex_ai_config
from utils import (
    setup_flask_logger, get_logger,
    validate_session_data, validate_question_data, validate_revision_request,
    validate_session_id, validate_question_index, ValidationError,
    FileProcessingError
)
# FileProcessingError는 이제 서비스에서 처리됨

# 새로운 서비스 모듈들
from services import AIService, OCRService, FileService
from services.auth_service import AuthService
from supabase_models import get_session_model, get_question_model, get_user_model




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
    
    # 서비스 접근자 등록
    app.get_ai_service = get_ai_service
    app.get_ocr_service = get_ocr_service
    app.get_file_service = get_file_service
    app.get_auth_service = get_auth_service
    
    # API 라우트 등록
    register_routes(app)
    
    # 에러 핸들러 등록
    register_error_handlers(app)
    
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
        response = jsonify({'message': '업로드된 파일의 크기가 너무 큽니다. (최대 50MB)'})
        response.status_code = 413
        return response
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        app.logger.error(f"내부 서버 오류: {str(error)}")
        response = jsonify({'message': '서버 내부 오류가 발생했습니다.'})
        response.status_code = 500
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
                return jsonify({'message': '업로드된 파일의 크기가 너무 큽니다. (최대 50MB)'}), 413
            
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
                
                # 파일에서 추출한 텍스트와 사용자 입력 텍스트를 결합
                if resume_text and file_resume_text:
                    resume_text = f"{resume_text}\n\n=== 파일에서 추출한 내용 ===\n{file_resume_text}"
                    app.logger.info(f"사용자 입력과 파일 내용 결합: {len(resume_text)}자")
                elif file_resume_text:
                    resume_text = file_resume_text
                    app.logger.info("파일에서 추출한 텍스트만 사용")
            else:
                app.logger.info("파일이 없어서 사용자 입력 텍스트만 사용")

            # 세션 생성 (Supabase 사용)
            # 채용정보에서 회사명과 직무 추출 시도
            company_name = ""
            job_title = ""
            
            # 개선된 파싱 로직
            company_name = ""
            job_title = ""
            main_responsibilities = ""
            requirements = ""
            preferred_qualifications = ""
            
            # 전체 텍스트를 한 줄로 처리
            full_text = job_description.replace('\n', ' ').strip()
            
            # 회사명과 직무 추출 (예: "김나라테크 - 제조 엔지니어")
            if ' - ' in full_text:
                parts = full_text.split(' - ', 1)
                company_name = parts[0].strip()
                remaining_text = parts[1].strip()
                
                # 직무 추출 (첫 번째 공백까지)
                if ' ' in remaining_text:
                    job_title = remaining_text.split(' ', 1)[0].strip()
                    remaining_text = remaining_text.split(' ', 1)[1].strip()
                else:
                    job_title = remaining_text
                    remaining_text = ""
            else:
                remaining_text = full_text
            
            # 섹션별 내용 파싱
            current_section = None
            current_content = ""
            
            # 주요업무, 자격요건, 우대사항 섹션 찾기
            sections = {
                'main_responsibilities': ['주요업무:', '담당업무:', '업무내용:'],
                'requirements': ['자격요건:', '요구사항:', '필수요건:'],
                'preferred_qualifications': ['우대사항:', '선호사항:', '가산점:']
            }
            
            # 각 섹션의 시작 위치 찾기
            section_positions = {}
            for section_name, keywords in sections.items():
                for keyword in keywords:
                    pos = remaining_text.find(keyword)
                    if pos != -1:
                        section_positions[section_name] = pos
                        break
            
            # 섹션별로 내용 추출
            if section_positions:
                # 섹션을 위치 순으로 정렬
                sorted_sections = sorted(section_positions.items(), key=lambda x: x[1])
                
                for i, (section_name, start_pos) in enumerate(sorted_sections):
                    # 다음 섹션의 시작 위치 찾기
                    if i + 1 < len(sorted_sections):
                        end_pos = sorted_sections[i + 1][1]
                    else:
                        end_pos = len(remaining_text)
                    
                    # 섹션 내용 추출
                    section_content = remaining_text[start_pos:end_pos].strip()
                    
                    # 키워드 제거하고 내용만 추출
                    for keyword in sections[section_name]:
                        if keyword in section_content:
                            section_content = section_content.replace(keyword, '').strip()
                            break
                    
                    # 해당 섹션에 내용 할당
                    if section_name == 'main_responsibilities':
                        main_responsibilities = section_content
                    elif section_name == 'requirements':
                        requirements = section_content
                    elif section_name == 'preferred_qualifications':
                        preferred_qualifications = section_content
            else:
                # 섹션 구분이 없는 경우 전체를 주요업무로 처리
                main_responsibilities = remaining_text
            
            # 디버깅을 위한 로그 추가
            app.logger.info(f"파싱 결과:")
            app.logger.info(f"  - 회사명: '{company_name}'")
            app.logger.info(f"  - 직무: '{job_title}'")
            app.logger.info(f"  - 주요업무: '{main_responsibilities}'")
            app.logger.info(f"  - 자격요건: '{requirements}'")
            app.logger.info(f"  - 우대사항: '{preferred_qualifications}'")
            
            # Supabase에 세션 생성
            session_data = {
                'company_name': company_name,
                'job_title': job_title,
                'main_responsibilities': main_responsibilities,
                'requirements': requirements,
                'preferred_qualifications': preferred_qualifications,
                'jd_text': job_description,  # 기존 호환성을 위해 유지
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
                'jd_text': job_description,
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
            if not questions or question_index > len(questions):
                raise APIError("질문을 찾을 수 없습니다.", status_code=404)

            # question_index는 1부터 시작하므로 0부터 시작하는 배열 인덱스로 변환
            question = questions[question_index - 1]
            history = question.get('answer_history', [])
            
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
                
                revised_text = app.get_ai_service().revise_cover_letter(
                    question=question['question'],
                    jd_text=session.get('jd_text', ''),
                    resume_text=session.get('resume_text', ''),
                    original_answer=history[current_version_index],
                    user_edit_prompt=revision_request,
                    company_info="",  # 회사 정보 사용 비활성화
                    company_name=session.get('company_name', ''),
                    job_title=session.get('job_title', ''),
                    answer_history=history
                )
                
                history.append(revised_text)
                question['answer_history'] = history
                question['current_version_index'] = len(history) - 1
            
            else:
                raise APIError(f"알 수 없는 액션입니다: {action}", status_code=400)

            # 질문 업데이트
            question_model.update_question(question['id'], question)
            
            return jsonify({
                'revisedAnswer': history[question['current_version_index']],
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
                current_answer = question['answer_history'][question['current_version_index']] if question['answer_history'] else ''
                questions_with_answers.append({
                    'id': question['id'],
                    'question': question['question'],
                    'answer': current_answer,
                    'answer_history': question['answer_history'],
                    'current_version_index': question['current_version_index'],
                    'length': len(current_answer),
                    'question_number': question['question_number']
                })

            return jsonify({
                'questions': questions_with_answers,
                'jobDescription': session['jd_text'] or '',
                'companyName': session['company_name'] or '',
                'jobTitle': session['job_title'] or '',
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
            if not session['resume_text'] or not session['jd_text']:
                raise APIError("이력서나 채용공고 정보가 없어 답변을 생성할 수 없습니다.", status_code=400)
            
            # AI 답변 생성
            result = app.get_ai_service().generate_cover_letter(
                question=validated_question['question'],
                jd_text=session['jd_text'],
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
            
            # 데이터 유효성 검증
            if not session.get('resume_text') or not session.get('jd_text'):
                raise APIError("이력서나 채용공고 정보가 없어 답변을 생성할 수 없습니다.", status_code=400)
            
            # AI 답변 생성
            generated_answer, company_info = app.get_ai_service().generate_cover_letter(
                question=validated_question['question'],
                jd_text=session.get('jd_text'),
                resume_text=session.get('resume_text'),
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
                raise APIError("이메일을 입력해주세요.")
            
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
            
            data = request.get_json()
            if not data or 'revision' not in data:
                raise APIError("revision이 필요합니다.", status_code=400)
            
            revision_text = data['revision']
            
            # 세션 조회
            session = session_model.get_session(session_id, user['id'])
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)
            
            # 세션 내 질문 인덱스 검증
            if question_index < 0 or question_index >= len(session.questions):
                raise APIError("질문을 찾을 수 없습니다.", status_code=404)
            
            # 세션 내 해당 인덱스의 질문 가져오기 (안전한 접근)
            question = session.questions[question_index]
            
            app.logger.info(f"질문 번호: {question.question_number} (세션 내 인덱스: {question_index})")
            
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
            
            # 답변 수정
            revised_answer = app.get_ai_service().revise_cover_letter(
                question=question.question,
                jd_text=session.jd_text,
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


# Flask 앱 생성
app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 
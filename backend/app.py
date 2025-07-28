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

# 기존 모듈들
from models import Session, Question, get_db, init_db, _parse_answer_history

# 새로운 서비스 모듈들
from services import AIService, OCRService, FileService




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
    
    # 데이터베이스 초기화
    init_db()
    
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
    
    # 서비스 접근자 등록
    app.get_ai_service = get_ai_service
    app.get_ocr_service = get_ocr_service
    app.get_file_service = get_file_service
    
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
        db = next(get_db())
        
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

            # 세션 생성 (새로운 필드 구조 사용)
            # 채용정보에서 회사명과 직무 추출 시도
            company_name = ""
            job_title = ""
            
            # 간단한 파싱 로직 (기본적인 형태만 지원)
            lines = job_description.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('회사명:'):
                    company_name = line.replace('회사명:', '').strip()
                elif line.startswith('직무:'):
                    job_title = line.replace('직무:', '').strip()
            
            new_session = Session(
                id=str(uuid.uuid4()),
                company_name=company_name,
                job_title=job_title,
                main_responsibilities="",  # 추후 개선 가능
                requirements="",           # 추후 개선 가능
                preferred_qualifications="", # 추후 개선 가능
                jd_text=job_description,  # 기존 호환성을 위해 유지
                resume_text=resume_text
            )

            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            
            app.logger.info(f"세션 생성 성공: {new_session.id}")
            
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
                            
                            # 질문과 답변을 데이터베이스에 저장
                            new_question = Question(
                                session_id=new_session.id,
                                question=question_text.strip(),
                                answer_history=json.dumps([answer]),
                                current_version_index=0,
                                length=len(answer),
                                question_number=i+1  # 세션 내 질문 번호
                            )
                            
                            db.add(new_question)
                    
                    db.commit()
                    app.logger.info("자기소개서 생성 완료")
                    
                except Exception as e:
                    app.logger.error(f"자기소개서 생성 중 오류: {str(e)}")
                    # 자기소개서 생성 실패해도 세션은 성공으로 처리
                    pass
            else:
                app.logger.info("질문이 없어서 자기소개서 생성 건너뜀")
            
            return jsonify({
                'sessionId': new_session.id,
                'message': 'Files uploaded and session created successfully'
            }), 201

        except (APIError, ValidationError, FileProcessingError):
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            app.logger.error(f"업로드 처리 중 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"세션 생성에 실패했습니다: {str(e)}", status_code=500)
        finally:
            db.close()

    @app.route('/api/v1/job-info', methods=['POST'])
    def job_info():
        """채용정보 직접 입력 API"""
        try:
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
            
            # 세션 생성 (새로운 필드 구조 사용)
            new_session = Session(
                id=str(uuid.uuid4()),
                company_name=data['companyName'].strip(),
                job_title=data['jobTitle'].strip(),
                main_responsibilities=data['mainResponsibilities'].strip(),
                requirements=data['requirements'].strip(),
                preferred_qualifications=preferred_qualifications,
                jd_text=job_description,  # 기존 호환성을 위해 유지
                resume_text=""  # 이력서는 별도로 입력받음
            )
            
            db = next(get_db())
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            db.close()
            
            return jsonify({
                'success': True,
                'sessionId': new_session.id,
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
        db = next(get_db())
        
        try:
            app.logger.info("자기소개서 수정 요청 시작")
            data = request.get_json()
            
            session_id = validate_session_id(data.get('sessionId'))
            question_index = validate_question_index(data.get('questionIndex'))
            action = data.get('action', 'revise')
            
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
                revision_request = validate_revision_request(data.get('revisionRequest'))
                
                # 현재 버전 이후의 히스토리 삭제
                history = history[:question.current_version_index + 1]
                
                revised_text = app.get_ai_service().revise_cover_letter(
                    question=question.question,
                    jd_text=session.jd_text,
                    resume_text=session.resume_text,
                    original_answer=history[question.current_version_index],
                    user_edit_prompt=revision_request,
                    company_info="",  # 회사 정보 사용 비활성화
                    company_name=session.company_name or "",
                    job_title=session.job_title or ""
                )
                
                history.append(revised_text)
                question.answer_history = json.dumps(history)
                question.current_version_index = len(history) - 1
            
            else:
                raise APIError(f"알 수 없는 액션입니다: {action}", status_code=400)

            db.commit()
            db.refresh(question)
            
            return jsonify({
                'revised_answer': question.to_dict()['answer']
            }), 200

        except (APIError, ValidationError):
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            app.logger.error(f"자기소개서 수정 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"자기소개서 수정에 실패했습니다: {str(e)}", status_code=500)
        finally:
            db.close()

    @app.route('/api/v1/session/<string:id>', methods=['DELETE'])
    def delete_session(id):
        """세션 삭제 및 관련 데이터 정리"""
        try:
            session_id = validate_session_id(id)
            app.logger.info(f"세션 삭제 요청: {session_id}")
            
            db = next(get_db())
            session = db.query(Session).filter_by(id=session_id).first()
            
            if not session:
                raise APIError("Session not found", status_code=404)

            try:
                # 1. 세션과 관련된 모든 질문들 삭제 (CASCADE로 자동 삭제됨)
                app.logger.info(f"세션 관련 질문들 삭제: {len(session.questions)}개")
                
                # 2. 세션 삭제
                db.delete(session)
                db.commit()
                
                # 3. 메모리 정리 (프리로딩된 콘텐츠가 있다면 정리)
                # preloaded_content_store는 세션별로 관리되지 않으므로 별도 정리 불필요
                
                # 4. 파일 정리 (업로드된 파일이 있다면 정리)
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

            except Exception as e:
                db.rollback()
                raise APIError(f"Failed to delete session: {str(e)}", status_code=500)
            finally:
                db.close()

        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"세션 삭제 오류: {str(e)}")
            raise APIError(f"Deletion failed: {str(e)}", status_code=500)

    @app.route('/api/v1/session/<string:id>', methods=['GET'])
    def get_session(id):
        """세션 조회"""
        db = next(get_db())
        
        try:
            session_id = validate_session_id(id)
            session = db.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)

            questions_with_answers = [q.to_dict() for q in session.questions]
            
            # 직무 정보는 이제 프론트엔드에서 직접 전달받으므로, 여기서 추출할 필요가 없습니다.
            selected_job = ''

            return jsonify({
                'questions': questions_with_answers,
                'jobDescription': session.jd_text or '',
                'companyName': session.company_name or '',
                'jobTitle': session.job_title or '',
                'message': '자기소개서 조회에 성공했습니다.'
            }), 200

        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"세션 조회 오류: {str(e)}")
            raise APIError(f"세션 조회에 실패했습니다: {str(e)}", status_code=500)
        finally:
            db.close()







    @app.route('/api/v1/add-question', methods=['POST'])
    def add_question():
        """기존 세션에 새로운 질문 추가"""
        db = next(get_db())
        
        try:
            app.logger.info("새 질문 추가 요청 시작")
            
            data = request.get_json()
            session_id = validate_session_id(data.get('sessionId'))
            question_text = data.get('question')
            
            # 질문 검증
            validated_question = validate_question_data(question_text)
            
            # 세션 조회
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)
            
            # 최대 질문 수 제한
            if len(session.questions) >= 3:
                raise APIError("최대 3개의 질문까지만 추가할 수 있습니다.", status_code=400)
            
            # 데이터 유효성 검증
            if not session.resume_text or not session.jd_text:
                raise APIError("이력서나 채용공고 정보가 없어 답변을 생성할 수 없습니다.", status_code=400)
            
            # AI 답변 생성
            result = app.get_ai_service().generate_cover_letter(
                question=validated_question['question'],
                jd_text=session.jd_text,
                resume_text=session.resume_text,
                company_name=session.company_name or "",
                job_title=session.job_title or ""
            )
            
            # 튜플에서 답변과 회사 정보 추출
            generated_answer, company_info = result
            
            if not generated_answer:
                raise APIError("답변 생성에 실패했습니다.", status_code=500)
            
            # 세션 내 질문 번호 계산
            existing_questions_count = len(session.questions)
            question_number = existing_questions_count + 1
            
            # 새 질문 저장
            new_question_obj = Question(
                question=validated_question['question'],
                length=len(generated_answer),
                question_number=question_number,
                answer_history=json.dumps([generated_answer]),
                current_version_index=0,
                session_id=session_id
            )
            
            db.add(new_question_obj)
            db.commit()
            db.refresh(new_question_obj)
            
            app.logger.info(f"새 질문 저장 완료 - 세션 내 번호: {new_question_obj.question_number}")
            
            return jsonify({
                'questionId': new_question_obj.id,
                'question': validated_question['question'],
                'answer': generated_answer,
                'length': len(generated_answer),
                'message': '새로운 질문과 답변이 생성되었습니다.'
            }), 200
            
        except (APIError, ValidationError):
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            app.logger.error(f"새 질문 추가 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"새 질문 추가에 실패했습니다: {str(e)}", status_code=500)
        finally:
            db.close()

    @app.route('/api/v1/sessions/<string:session_id>/questions', methods=['POST'])
    def add_question_to_session(session_id):
        """특정 세션에 새로운 질문 추가 (RESTful 엔드포인트)"""
        db = next(get_db())
        
        try:
            app.logger.info(f"새 질문 추가 요청 시작 - 세션: {session_id}")
            
            data = request.get_json()
            if not data or 'question' not in data:
                raise APIError("question이 필요합니다.", status_code=400)
            
            question_text = data.get('question')
            
            # 질문 검증
            validated_question = validate_question_data(question_text)
            
            # 세션 조회
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)
            
            # 최대 질문 수 제한
            if len(session.questions) >= 3:
                raise APIError("최대 3개의 질문까지만 추가할 수 있습니다.", status_code=400)
            
            # 데이터 유효성 검증
            if not session.resume_text or not session.jd_text:
                raise APIError("이력서나 채용공고 정보가 없어 답변을 생성할 수 없습니다.", status_code=400)
            
            # AI 답변 생성
            generated_answer, company_info = app.get_ai_service().generate_cover_letter(
                question=validated_question['question'],
                jd_text=session.jd_text,
                resume_text=session.resume_text,
                company_name=session.company_name or "",
                job_title=session.job_title or ""
            )
            
            # 회사 정보가 있으면 세션에 저장 (현재 비활성화)
            # if company_info and not session.company_info:
            #     session.company_info = company_info
            
            if not generated_answer:
                raise APIError("답변 생성에 실패했습니다.", status_code=500)
            
            # 세션 내 질문 번호 계산
            existing_questions_count = len(session.questions)
            question_number = existing_questions_count + 1
            
            # 새 질문 저장
            new_question_obj = Question(
                question=validated_question['question'],
                length=len(generated_answer),
                question_number=question_number,
                answer_history=json.dumps([generated_answer]),
                current_version_index=0,
                session_id=session_id
            )
            
            db.add(new_question_obj)
            db.commit()
            db.refresh(new_question_obj)
            
            app.logger.info(f"새 질문 저장 완료 - 세션 내 번호: {new_question_obj.question_number}")
            
            return jsonify({
                'questionId': new_question_obj.id,
                'question': validated_question['question'],
                'answer': generated_answer,
                'length': len(generated_answer),
                'message': '새로운 질문과 답변이 생성되었습니다.'
            }), 200
            
        except (APIError, ValidationError):
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            app.logger.error(f"새 질문 추가 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"새 질문 추가에 실패했습니다: {str(e)}", status_code=500)
        finally:
            db.close()

    @app.route('/api/v1/sessions/<string:session_id>/questions/<int:question_index>/revise', methods=['POST'])
    def revise_answer(session_id, question_index):
        """특정 질문의 답변 수정 (세션 내 인덱스 기반)"""
        db = next(get_db())
        
        try:
            app.logger.info(f"답변 수정 요청 시작 - 세션: {session_id}, 질문 인덱스: {question_index}")
            
            data = request.get_json()
            if not data or 'revision' not in data:
                raise APIError("revision이 필요합니다.", status_code=400)
            
            revision_text = data['revision']
            
            # 세션 조회
            session = db.query(Session).filter(Session.id == session_id).first()
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
                job_title=session.job_title or ""
            )
            
            # 새로운 답변을 히스토리에 추가
            history_list.append(revised_answer)
            
            # 데이터베이스 업데이트
            question.answer_history = json.dumps(history_list)
            question.current_version_index = len(history_list) - 1
            
            db.commit()
            
            app.logger.info(f"답변 수정 완료 - 세션: {session_id}, 질문 인덱스: {question_index}")
            
            return jsonify({
                'success': True,
                'revised_answer': revised_answer,
                'message': '답변이 수정되었습니다.'
            }), 200
            
        except (APIError, ValidationError):
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            app.logger.error(f"답변 수정 중 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"답변 수정에 실패했습니다: {str(e)}", status_code=500)
        finally:
            db.close()


# Flask 앱 생성
app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 
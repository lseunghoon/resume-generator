"""
iloveresume 백엔드 메인 애플리케이션 (리팩토링 버전)
분리된 모듈들을 사용하여 깔끔하게 정리된 Flask 애플리케이션
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import traceback
import json
import werkzeug
import time

# 설정 및 유틸리티 모듈
from config import get_cors_config, validate_settings
from config.settings import get_database_config, get_vertex_ai_config
from utils import (
    setup_flask_logger, get_logger,
    validate_session_data, validate_question_data, validate_revision_request,
    validate_session_id, validate_question_index, ValidationError,
    validate_job_posting_url, check_robots_txt_permission, FileProcessingError
)
# FileProcessingError는 이제 서비스에서 처리됨

# 기존 모듈들
from models import Session, Question, get_db, init_db, _parse_answer_history

# 새로운 서비스 모듈들
from services import AIService, CrawlingService, OCRService, FileService

# 프리로딩된 콘텐츠 임시 저장소 (메모리 기반)
preloaded_content_store = {}


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
    
    def get_crawling_service():
        if not hasattr(app, '_crawling_service'):
            app._crawling_service = CrawlingService()
        return app._crawling_service
    
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
    app.get_crawling_service = get_crawling_service
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
            
            job_description_url = validated_data['jobDescriptionUrl']
            questions_data = validated_data['questions']
            lengths_data = validated_data.get('lengths', [])
            html_content = validated_data.get('htmlContent') # 프론트에서 전달받을 HTML
            preloaded_content = validated_data.get('preloadedContent') # 프리로딩된 콘텐츠
            content_id = validated_data.get('contentId') # 프리로딩된 콘텐츠 ID

            # 디버깅: contentId 확인
            app.logger.info(f"받은 contentId: {content_id}")
            app.logger.info(f"preloaded_content_store 키 목록: {list(preloaded_content_store.keys())}")

            job_description = ""
            if content_id:
                # contentId로 저장된 콘텐츠 조회 (우선순위 1)
                app.logger.info(f"contentId로 저장된 콘텐츠 조회: {content_id}")
                if content_id in preloaded_content_store:
                    content_data = preloaded_content_store[content_id]
                    job_description = content_data['content']
                    # 사용 후 삭제
                    del preloaded_content_store[content_id]
                    app.logger.info(f"저장된 콘텐츠 사용 후 삭제: {content_id}")
                else:
                    app.logger.warning(f"저장된 콘텐츠를 찾을 수 없음: {content_id}")
                    # contentId가 있지만 저장소에 없으면 크롤링 수행
                    app.logger.info("contentId가 유효하지 않으므로 직접 크롤링 수행")
                    try:
                        crawling_service = app.get_crawling_service()
                        job_titles, html_content = crawling_service.extract_job_quick(job_description_url)
                        job_description = crawling_service.extract_content_from_html(html_content, job_description_url)
                        app.logger.info("직접 크롤링 완료")
                    except Exception as e:
                        app.logger.error(f"크롤링 실패: {str(e)}")
                        job_description = ""
            elif preloaded_content:
                # 프리로딩된 콘텐츠가 있으면 사용 (우선순위 2)
                app.logger.info("프리로딩된 콘텐츠 사용")
                job_description = preloaded_content
            elif html_content:
                app.logger.info("미리 받아온 HTML 소스로 전체 콘텐츠 추출 시작")
                job_description = app.get_crawling_service().extract_content_from_html(
                    html_content, job_description_url
                )
                app.logger.info("전체 콘텐츠 추출 완료")
            else:
                # htmlContent가 없는 경우 직접 크롤링 수행
                app.logger.info("HTML 콘텐츠가 없습니다. 직접 크롤링을 수행합니다.")
                try:
                    crawling_service = app.get_crawling_service()
                    job_titles, html_content = crawling_service.extract_job_quick(job_description_url)
                    job_description = crawling_service.extract_content_from_html(html_content, job_description_url)
                    app.logger.info("직접 크롤링 완료")
                except Exception as e:
                    app.logger.error(f"크롤링 실패: {str(e)}")
                    # 크롤링 실패 시에도 계속 진행 (빈 job_description으로)
                    job_description = ""


            # 파일 텍스트 추출 (파일이 없으면 빈 텍스트)
            if files:
                file_result = app.get_file_service().process_uploaded_files(files)
                if not file_result['success']:
                    raise APIError(file_result['message'], status_code=400)
                
                resume_text = file_result['extracted_text']
                app.logger.info(f"이력서 텍스트 추출 완료: {len(resume_text)}자")
            else:
                resume_text = ""  # 파일이 없으면 빈 텍스트
                app.logger.info("파일이 없어서 이력서 텍스트를 빈 문자열로 설정")

            # 세션 생성
            new_session = Session(
                id=str(uuid.uuid4()),
                jd_url=job_description_url,
                jd_text=job_description,
                resume_text=resume_text
            )

            # 질문 생성
            for i, q_text in enumerate(questions_data):
                validated_question = validate_question_data(
                    q_text, 
                    lengths_data[i] if i < len(lengths_data) else None
                )
                
                new_question = Question(
                    question=validated_question['question'],
                    length=validated_question['length'],
                    question_number=i + 1,  # 세션 내 질문 번호 (1, 2, 3...)
                    session_id=new_session.id
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

    @app.route('/api/v1/generate', methods=['POST'])
    def generate():
        """세션 ID를 받아 자기소개서 생성 (배치 처리)"""
        db = next(get_db())
        
        try:
            app.logger.info("자기소개서 생성 요청 시작")
            data = request.get_json()
            session_id = validate_session_id(data.get('sessionId'))

            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                raise APIError("세션을 찾을 수 없습니다.", status_code=404)

            # 단일 처리
            app.logger.info(f"자기소개서 생성 시작: {len(session.questions)}개 질문")
            
            # 각 질문에 대해 개별적으로 AI 답변 생성
            for question in session.questions:
                answer = app.get_ai_service().generate_cover_letter(
                    question=question.question,
                    jd_text=session.jd_text,
                    resume_text=session.resume_text
                )
                
                if answer:
                    question.answer_history = json.dumps([answer])
                    question.current_version_index = 0
                else:
                    raise APIError(f"질문 '{question.question[:50]}...'에 대한 답변 생성에 실패했습니다.", status_code=500)
            
            db.commit()
            app.logger.info("자기소개서 생성 완료")

            questions_with_answers = [q.to_dict() for q in session.questions]
            
            return jsonify({
                'questions': questions_with_answers,
                'message': f'자기소개서 생성 완료 ({len(session.questions)}개 문항)'
            }), 200

        except (APIError, ValidationError):
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            app.logger.error(f"자기소개서 생성 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"자기소개서 생성에 실패했습니다: {str(e)}", status_code=500)
        finally:
            db.close()

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
                    user_edit_prompt=revision_request
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
                'jobDescriptionUrl': session.jd_url or '',
                'selectedJob': selected_job,
                'message': '자기소개서 조회에 성공했습니다.'
            }), 200

        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"세션 조회 오류: {str(e)}")
            raise APIError(f"세션 조회에 실패했습니다: {str(e)}", status_code=500)
        finally:
            db.close()

    @app.route('/api/v1/extract-job-quick', methods=['POST'])
    def extract_job_quick():
        """
        채용공고 URL에서 직무 제목과 전체 HTML 소스를 추출합니다.
        """
        try:
            data = request.get_json()
            if not data or 'jobPostingUrl' not in data:
                raise APIError("jobPostingUrl이 필요합니다.", 400)
            
            job_posting_url = data['jobPostingUrl']
            
            # 책임감 있는 robots.txt 검증
            can_crawl, delay = check_robots_txt_permission(job_posting_url)
            if not can_crawl:
                raise APIError("로봇이 읽지 못하는 링크입니다 :( 다른 채용공고를 입력해보세요.", 403)
            
            if not validate_job_posting_url(job_posting_url):
                raise APIError("유효하지 않은 채용공고 URL입니다.", 400)
            
            crawling_service = app.get_crawling_service()
            job_titles, html_content = crawling_service.extract_job_quick(job_posting_url)
            
            return jsonify({
                'success': True,
                'positions': job_titles,
                'htmlContent': html_content  # 최종 콘텐츠 대신 HTML 소스 반환
            })
            
        except ValueError as e:
            raise APIError(str(e), 400)
        except Exception as e:
            app.logger.error(f"빠른 직무 정보 추출 실패: {str(e)}")
            raise APIError("직무 정보 추출에 실패했습니다.", 500)

    # @app.route('/api/v1/extract-job', methods=['POST'])
    # def extract_job(): ... -> 이 엔드포인트는 이제 extract-job-quick으로 통합되어 삭제합니다.

    @app.route('/api/v1/preload-content', methods=['POST'])
    def preload_content():
        """백그라운드에서 콘텐츠 프리로딩"""
        try:
            app.logger.info("콘텐츠 프리로딩 요청 시작")
            data = request.get_json()
            
            job_description_url = data.get('jobPostingUrl')
            html_content = data.get('htmlContent', '')
            
            # URL 유효성 검증
            if not validate_job_posting_url(job_description_url):
                raise APIError("올바른 채용공고 URL이 아닙니다.", status_code=400)
            
            # 책임감 있는 robots.txt 검증
            can_crawl, delay = check_robots_txt_permission(job_description_url)
            if not can_crawl:
                raise APIError("로봇이 읽지 못하는 링크입니다 :( 다른 채용공고를 입력해보세요.", status_code=403)
            
            app.logger.info("백그라운드 콘텐츠 추출 시작")
            
            if html_content:
                # 미리 받아온 HTML 소스로 전체 콘텐츠 추출
                app.logger.info("미리 받아온 HTML 소스로 전체 콘텐츠 추출 시작")
                job_description = app.get_crawling_service().extract_content_from_html(
                    html_content, job_description_url
                )
                app.logger.info("백그라운드 전체 콘텐츠 추출 완료")
            else:
                # htmlContent가 없는 경우 직접 크롤링 수행
                app.logger.info("백그라운드 직접 크롤링 수행")
                try:
                    crawling_service = app.get_crawling_service()
                    job_titles, html_content = crawling_service.extract_job_quick(job_description_url)
                    job_description = crawling_service.extract_content_from_html(html_content, job_description_url)
                    app.logger.info("백그라운드 직접 크롤링 완료")
                except Exception as e:
                    app.logger.error(f"백그라운드 크롤링 실패: {str(e)}")
                    job_description = ""
            
            # 콘텐츠 크기 확인
            content_size = len(job_description.encode('utf-8'))
            app.logger.info(f"프리로딩된 콘텐츠 크기: {content_size} bytes ({content_size / 1024 / 1024:.2f} MB)")
            if content_size > 1024 * 1024:  # 1MB 이상
                app.logger.warning(f"프리로딩된 콘텐츠가 매우 큽니다: {content_size / 1024 / 1024:.2f} MB")
            
            # 콘텐츠가 너무 크면 임시 저장소에 저장하고 ID 반환
            content_size = len(job_description.encode('utf-8'))
            if content_size > 1 * 1024:  # 1KB 이상 (모든 프리로딩 콘텐츠를 contentId로 처리)
                # 임시 저장소에 저장
                content_id = str(uuid.uuid4())
                preloaded_content_store[content_id] = {
                    'content': job_description,
                    'timestamp': time.time(),
                    'url': job_description_url
                }
                app.logger.info(f"대용량 콘텐츠를 임시 저장소에 저장: {content_id}")
                
                return jsonify({
                    'contentId': content_id,
                    'contentSize': content_size,
                    'message': '대용량 콘텐츠가 임시 저장되었습니다. contentId를 사용하여 세션 생성 시 참조하세요.'
                }), 200
            else:
                # 작은 콘텐츠는 직접 반환
                return jsonify({
                    'jobDescription': job_description,
                    'contentSize': content_size,
                    'message': '콘텐츠 프리로딩 완료'
                }), 200
            
        except (APIError, ValidationError):
            raise
        except Exception as e:
            app.logger.error(f"프리로딩 처리 중 오류: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise APIError(f"콘텐츠 프리로딩에 실패했습니다: {str(e)}", status_code=500)

    @app.route('/api/v1/get-preloaded-content/<string:content_id>', methods=['GET'])
    def get_preloaded_content(content_id):
        """임시 저장된 프리로딩 콘텐츠 조회"""
        try:
            if content_id not in preloaded_content_store:
                raise APIError("저장된 콘텐츠를 찾을 수 없습니다.", status_code=404)
            
            content_data = preloaded_content_store[content_id]
            
            # 30분 이상 된 콘텐츠는 자동 삭제
            if time.time() - content_data['timestamp'] > 1800:  # 30분
                del preloaded_content_store[content_id]
                raise APIError("저장된 콘텐츠가 만료되었습니다.", status_code=410)
            
            return jsonify({
                'jobDescription': content_data['content'],
                'contentSize': len(content_data['content'].encode('utf-8')),
                'message': '저장된 콘텐츠 조회 완료'
            }), 200
            
        except APIError:
            raise
        except Exception as e:
            app.logger.error(f"저장된 콘텐츠 조회 중 오류: {str(e)}")
            raise APIError(f"콘텐츠 조회에 실패했습니다: {str(e)}", status_code=500)

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
            generated_answer = app.get_ai_service().generate_cover_letter(
                question=validated_question['question'],
                jd_text=session.jd_text,
                resume_text=session.resume_text
            )
            
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
            generated_answer = app.get_ai_service().generate_cover_letter(
                question=validated_question['question'],
                jd_text=session.jd_text,
                resume_text=session.resume_text
            )
            
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
                user_edit_prompt=revision_text
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
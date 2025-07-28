"""
파일 서비스 - 파일 업로드, 처리, 관리 서비스
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from werkzeug.datastructures import FileStorage

from utils.file_processor import (
    extract_text_from_file, get_file_info, validate_file_type, 
    FileProcessingError
)
from utils.logger import LoggerMixin
from config.settings import get_file_config

logger = logging.getLogger(__name__)


class FileService(LoggerMixin):
    """파일 업로드, 처리, 관리 서비스"""
    
    def __init__(self):
        """파일 서비스 초기화"""
        self.config = get_file_config()
        self.logger.info("파일 서비스 초기화 완료")
    
    def process_uploaded_files(self, files: List[FileStorage]) -> Dict:
        """
        업로드된 파일들을 처리하고 텍스트 추출 (OCR 최적화)
        
        Args:
            files: 업로드된 파일 목록
            
        Returns:
            Dict: 처리 결과 정보
        """
        try:
            self.logger.info(f"파일 처리 시작: {len(files)}개 파일")
            
            if not files or not any(f.filename for f in files):
                raise FileProcessingError("유효한 파일이 없습니다.")
            
            # 첫 번째 유효한 파일 사용 (비용 최적화)
            main_file = None
            for file in files:
                if file.filename:
                    main_file = file
                    break
            
            if not main_file:
                raise FileProcessingError("유효한 파일이 없습니다.")
            
            # 파일 정보 확인
            file_info = get_file_info(main_file)
            self.logger.info(f"파일 정보: {file_info}")
            
            # 파일 유효성 검사
            self._validate_file(file_info)
            
            # 텍스트 추출 (OCR 비용 최적화)
            extracted_text = extract_text_from_file(main_file)
            self.logger.info(f"텍스트 추출 완료: {len(extracted_text)}자")
            
            # 텍스트 길이 검증 (너무 짧으면 경고)
            if len(extracted_text.strip()) < 10:
                self.logger.warning("추출된 텍스트가 너무 짧습니다. OCR 품질을 확인해주세요.")
            
            return {
                'success': True,
                'file_info': file_info,
                'extracted_text': extracted_text,
                'text_length': len(extracted_text),
                'message': '파일 처리가 성공적으로 완료되었습니다.'
            }
            
        except FileProcessingError as e:
            self.logger.error(f"파일 처리 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '파일 처리에 실패했습니다.'
            }
        except Exception as e:
            self.logger.error(f"파일 처리 중 예상치 못한 오류: {e}")
            return {
                'success': False,
                'error': f'파일 처리 중 오류 발생: {str(e)}',
                'message': '파일 처리 중 오류가 발생했습니다.'
            }
    
    def _validate_file(self, file_info: Dict) -> None:
        """파일 유효성 검사"""
        if not file_info:
            raise FileProcessingError("파일 정보를 가져올 수 없습니다.")
        
        if not file_info['is_valid_type']:
            raise FileProcessingError(
                f"지원하지 않는 파일 형식입니다: {file_info['extension']}"
            )
        
        if not file_info['is_valid_size']:
            max_size_mb = self.config['max_file_size'] / 1024 / 1024
            raise FileProcessingError(
                f"파일 크기가 제한을 초과합니다. "
                f"현재: {file_info['size_mb']}MB, 최대: {max_size_mb:.1f}MB"
            )
    
    def save_file(self, file: FileStorage, upload_dir: str = None) -> Dict:
        """
        파일을 서버에 저장
        
        Args:
            file: 저장할 파일
            upload_dir: 업로드 디렉토리 (기본값: config에서 가져옴)
            
        Returns:
            Dict: 저장 결과 정보
        """
        try:
            if not upload_dir:
                upload_dir = self.config['uploads_dir']
            
            # 업로드 디렉토리 생성
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                self.logger.info(f"업로드 디렉토리 생성: {upload_dir}")
            
            # 파일명 안전화
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            
            # 중복 파일명 처리
            file_path = os.path.join(upload_dir, filename)
            counter = 1
            base_name, ext = os.path.splitext(filename)
            
            while os.path.exists(file_path):
                new_filename = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(upload_dir, new_filename)
                counter += 1
            
            # 파일 저장
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            self.logger.info(f"파일 저장 완료: {file_path}")
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'size': file_size,
                'message': '파일이 성공적으로 저장되었습니다.'
            }
            
        except Exception as e:
            self.logger.error(f"파일 저장 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '파일 저장에 실패했습니다.'
            }
    
    def delete_file(self, file_path: str) -> Dict:
        """
        저장된 파일 삭제
        
        Args:
            file_path: 삭제할 파일 경로
            
        Returns:
            Dict: 삭제 결과 정보
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"파일 삭제 완료: {file_path}")
                return {
                    'success': True,
                    'message': '파일이 성공적으로 삭제되었습니다.'
                }
            else:
                return {
                    'success': False,
                    'error': '파일을 찾을 수 없습니다.',
                    'message': '삭제할 파일이 존재하지 않습니다.'
                }
        except Exception as e:
            self.logger.error(f"파일 삭제 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '파일 삭제에 실패했습니다.'
            }
    
    def get_upload_directory_info(self, upload_dir: str = None) -> Dict:
        """
        업로드 디렉토리 정보 조회
        
        Args:
            upload_dir: 조회할 디렉토리 (기본값: config에서 가져옴)
            
        Returns:
            Dict: 디렉토리 정보
        """
        try:
            if not upload_dir:
                upload_dir = self.config['uploads_dir']
            
            if not os.path.exists(upload_dir):
                return {
                    'exists': False,
                    'file_count': 0,
                    'total_size': 0,
                    'files': []
                }
            
            files = []
            total_size = 0
            
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_stat = os.stat(file_path)
                    
                    files.append({
                        'filename': filename,
                        'size': file_size,
                        'size_mb': round(file_size / 1024 / 1024, 2),
                        'created_time': file_stat.st_ctime,
                        'modified_time': file_stat.st_mtime
                    })
                    total_size += file_size
            
            return {
                'exists': True,
                'directory': upload_dir,
                'file_count': len(files),
                'total_size': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'files': files
            }
            
        except Exception as e:
            self.logger.error(f"디렉토리 정보 조회 실패: {e}")
            return {
                'exists': False,
                'error': str(e)
            }
    
    def cleanup_old_files(self, upload_dir: str = None, max_age_days: int = 7) -> Dict:
        """
        오래된 파일들 정리
        
        Args:
            upload_dir: 정리할 디렉토리
            max_age_days: 최대 보관 기간 (일)
            
        Returns:
            Dict: 정리 결과
        """
        try:
            if not upload_dir:
                upload_dir = self.config['uploads_dir']
            
            if not os.path.exists(upload_dir):
                return {
                    'success': True,
                    'deleted_count': 0,
                    'message': '정리할 디렉토리가 존재하지 않습니다.'
                }
            
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            deleted_files = []
            deleted_size = 0
            
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    
                    if file_age > max_age_seconds:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        
                        deleted_files.append({
                            'filename': filename,
                            'size': file_size,
                            'age_days': round(file_age / (24 * 60 * 60), 1)
                        })
                        deleted_size += file_size
            
            self.logger.info(f"파일 정리 완료: {len(deleted_files)}개 파일 삭제")
            
            return {
                'success': True,
                'deleted_count': len(deleted_files),
                'deleted_size': deleted_size,
                'deleted_size_mb': round(deleted_size / 1024 / 1024, 2),
                'deleted_files': deleted_files,
                'message': f'{len(deleted_files)}개의 오래된 파일이 삭제되었습니다.'
            }
            
        except Exception as e:
            self.logger.error(f"파일 정리 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '파일 정리 중 오류가 발생했습니다.'
            }
    
    def validate_upload_request(self, files: List[FileStorage]) -> Tuple[bool, str]:
        """
        파일 업로드 요청 유효성 검사
        
        Args:
            files: 업로드할 파일 목록
            
        Returns:
            Tuple[bool, str]: (유효성, 오류 메시지)
        """
        try:
            if not files:
                return False, "파일이 제공되지 않았습니다."
            
            valid_files = [f for f in files if f.filename]
            if not valid_files:
                return False, "유효한 파일이 없습니다."
            
            if len(valid_files) > 1:
                return False, "한 번에 하나의 파일만 업로드할 수 있습니다."
            
            file = valid_files[0]
            
            # 파일명 검사
            if not file.filename.strip():
                return False, "파일명이 유효하지 않습니다."
            
            # 확장자 검사
            try:
                validate_file_type(file.filename)
            except FileProcessingError as e:
                return False, str(e)
            
            # 파일 크기 검사 (대략적)
            file.seek(0, 2)  # 파일 끝으로 이동
            file_size = file.tell()
            file.seek(0)  # 처음으로 되돌리기
            
            if file_size > self.config['max_file_size']:
                max_size_mb = self.config['max_file_size'] / 1024 / 1024
                current_size_mb = file_size / 1024 / 1024
                return False, (
                    f"파일 크기가 제한을 초과합니다. "
                    f"현재: {current_size_mb:.1f}MB, 최대: {max_size_mb:.1f}MB"
                )
            
            if file_size == 0:
                return False, "빈 파일은 업로드할 수 없습니다."
            
            return True, "유효한 파일입니다."
            
        except Exception as e:
            self.logger.error(f"파일 업로드 검사 실패: {e}")
            return False, f"파일 검사 중 오류 발생: {str(e)}"
    
    def get_supported_formats(self) -> Dict:
        """지원되는 파일 형식 정보 반환"""
        return {
            'allowed_extensions': list(self.config['allowed_extensions']),
            'max_file_size': self.config['max_file_size'],
            'max_file_size_mb': round(self.config['max_file_size'] / 1024 / 1024, 1),
            'description': {
                '.pdf': 'PDF 문서',
                '.docx': 'Microsoft Word 문서'
            }
        }
    
    def test_file_operations(self) -> Tuple[bool, str]:
        """파일 서비스 기능 테스트"""
        try:
            # 임시 테스트 디렉토리 생성
            test_dir = os.path.join(self.config['uploads_dir'], 'test')
            
            if not os.path.exists(test_dir):
                os.makedirs(test_dir)
            
            # 테스트 파일 생성
            test_file_path = os.path.join(test_dir, 'test.txt')
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write('테스트 파일입니다.')
            
            # 파일 존재 확인
            if not os.path.exists(test_file_path):
                return False, "테스트 파일 생성 실패"
            
            # 파일 삭제
            os.remove(test_file_path)
            
            # 테스트 디렉토리 삭제
            os.rmdir(test_dir)
            
            self.logger.info("파일 서비스 테스트 성공")
            return True, "파일 서비스가 정상적으로 작동합니다."
            
        except Exception as e:
            self.logger.error(f"파일 서비스 테스트 실패: {e}")
            return False, f"파일 서비스 테스트 실패: {str(e)}" 
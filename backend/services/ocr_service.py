"""
OCR 서비스 - Google Cloud Vision AI 기반 이미지 텍스트 추출 서비스
"""

import logging
import io
import base64
import requests
from typing import List, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageFile
from google.cloud import vision
from urllib.parse import urljoin

from utils.chrome_driver import safe_create_chrome_driver
from utils.logger import LoggerMixin

# DecompressionBombWarning을 처리하기 위한 설정
# 한계를 넉넉하게 늘려주어 경고가 발생하지 않도록 함
Image.MAX_IMAGE_PIXELS = None
ImageFile.LOAD_TRUNCATED_IMAGES = True # 손상된 이미지도 최대한 로드 시도

logger = logging.getLogger(__name__)


class OCRService(LoggerMixin):
    """Google Cloud Vision AI 기반 OCR 처리 서비스"""
    
    def __init__(self):
        """OCR 서비스 초기화"""
        try:
            # GCP Vision AI 클라이언트 초기화
            self.client = vision.ImageAnnotatorClient()
            self.logger.info("GCP Vision AI 클라이언트 초기화 완료")
        except Exception as e:
            self.logger.error(f"GCP Vision AI 클라이언트 초기화 실패: {e}")
            self.client = None

    def _preprocess_image_bytes(self, content: bytes, max_width: int = 2048) -> bytes:
        """
        이미지 바이트를 받아 리사이징하고 최적화하여 새로운 바이트를 반환합니다.
        """
        try:
            image = Image.open(io.BytesIO(content))
            
            # 이미지 포맷이 지원되는지 확인 (e.g., JPEG, PNG)
            if image.format not in ['JPEG', 'PNG', 'WEBP']:
                self.logger.warning(f"지원되지 않는 이미지 포맷({image.format}), 변환 시도.")
                # RGBA(PNG) -> RGB(JPEG) 변환
                if image.mode == 'RGBA':
                    image = image.convert('RGB')

            # 이미지 너비가 최대 너비보다 크면 리사이징
            if image.width > max_width:
                self.logger.info(f"이미지가 너무 커서 리사이징합니다. (원본 너비: {image.width}px)")
                aspect_ratio = image.height / image.width
                new_height = int(max_width * aspect_ratio)
                image = image.resize((max_width, new_height), Image.LANCZOS)

            # 리사이징된 이미지를 다시 바이트로 변환
            output_byte_io = io.BytesIO()
            image.save(output_byte_io, format='JPEG', quality=85) # JPEG로 저장하여 용량 최적화
            
            return output_byte_io.getvalue()
            
        except Exception as e:
            self.logger.error(f"이미지 전처리 실패: {e}")
            # 전처리 실패 시 원본 바이트라도 반환 시도
            return content

    def extract_text_from_image_bytes(self, content: bytes) -> str:
        """이미지 바이트에서 텍스트를 추출합니다. (전처리 단계 추가)"""
        if not self.client:
            self.logger.error("Vision AI 클라이언트가 초기화되지 않았습니다.")
            return ""
        
        if not content:
            self.logger.warning("OCR을 위한 이미지 내용(bytes)이 없습니다.")
            return ""

        try:
            self.logger.info(f"이미지 바이트({len(content)} bytes)에서 텍스트 추출 시작 (전처리 포함)")
            
            # === 핵심 수정 ===
            # Vision API로 보내기 전에 이미지를 전처리(리사이징 및 최적화)
            preprocessed_content = self._preprocess_image_bytes(content)
            
            self.logger.info(f"전처리 후 이미지 크기: {len(preprocessed_content)} bytes")
            
            image = vision.Image(content=preprocessed_content)
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API 오류: {response.error.message}")
            
            return response.full_text_annotation.text if response.full_text_annotation else ""

        except Exception as e:
            self.logger.error(f"이미지 바이트 OCR 실패: {e}")
            return "" 
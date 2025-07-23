import logging
import io
import base64
import requests
from typing import List, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter
from google.cloud import vision
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

logger = logging.getLogger(__name__)

class OCRProcessor:
    """이미지에서 텍스트를 추출하는 GCP Vision AI 기반 OCR 처리 클래스"""
    
    def __init__(self):
        """OCR 프로세서 초기화 (GCP Vision AI)"""
        try:
            # GCP Vision AI 클라이언트 초기화
            self.client = vision.ImageAnnotatorClient()
            logger.info("GCP Vision AI 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"GCP Vision AI 클라이언트 초기화 실패: {e}")
            self.client = None
    
    def detect_images_in_webpage(self, url: str) -> List[str]:
        """웹페이지에서 채용공고 관련 이미지들을 감지하고 URL 목록 반환"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.get(url)
            time.sleep(3)  # 페이지 로딩 대기
            
            # 이미지 요소들 찾기
            image_elements = driver.find_elements(By.TAG_NAME, "img")
            
            image_urls = []
            for img_element in image_elements:
                try:
                    img_src = img_element.get_attribute("src")
                    img_alt = img_element.get_attribute("alt") or ""
                    img_class = img_element.get_attribute("class") or ""
                    img_id = img_element.get_attribute("id") or ""
                    
                    # 채용공고 관련 이미지 필터링
                    if self._is_job_posting_image(img_src, img_alt, img_class, img_id):
                        # 상대 경로인 경우 절대 경로로 변환
                        if img_src.startswith('/'):
                            from urllib.parse import urljoin
                            img_src = urljoin(url, img_src)
                        elif img_src.startswith('data:'):
                            # Base64 인코딩된 이미지는 별도 처리
                            continue
                        
                        image_urls.append(img_src)
                        
                except Exception as e:
                    logger.warning(f"이미지 요소 처리 중 오류: {e}")
                    continue
            
            driver.quit()
            
            logger.info(f"발견된 채용공고 관련 이미지 개수: {len(image_urls)}")
            return image_urls
            
        except Exception as e:
            logger.error(f"웹페이지 이미지 감지 실패: {e}")
            if 'driver' in locals():
                driver.quit()
            return []
    
    def _is_job_posting_image(self, src: str, alt: str, class_name: str, img_id: str) -> bool:
        """이미지가 채용공고 관련인지 판단 (링커리어 특화 포함)"""
        if not src:
            return False
        
        # 링커리어 특화 처리
        if 'linkareer.com' in src:
            # 링커리어의 경우 se2editor 이미지는 대부분 채용공고 관련
            if 'se2editor/image' in src:
                logger.info(f"링커리어 se2editor 이미지 발견: {src[:50]}...")
                return True
            
            # 링커리어 미디어 CDN 이미지도 처리
            if 'media-cdn.linkareer.com' in src:
                return True
        
        # 너무 작은 이미지 제외 (로고, 아이콘 등)
        if any(keyword in src.lower() for keyword in ['icon', 'logo', 'avatar', 'thumb']):
            return False
        
        # 채용공고 관련 키워드 체크 (확장된 키워드)
        text_to_check = f"{alt} {class_name} {img_id} {src}".lower()
        job_keywords = [
            'job', 'recruit', 'career', 'position', 'employment', 'hiring',
            '채용', '모집', '직무', '구인', '취업', '입사', '면접', '공고',
            '인턴', '신입', '경력', '지원', '전환형', '체험형', '인턴십',
            'bd', 'business', 'development', '개발', '마케팅', '기획'
        ]
        
        # 크기가 충분한 이미지인지 확인
        size_indicators = ['large', 'big', 'detail', 'content', 'main', 'body', 'max-width']
        has_size_indicator = any(indicator in text_to_check for indicator in size_indicators)
        
        # 채용공고 키워드가 있거나 크기가 충분한 이미지
        has_job_keyword = any(keyword in text_to_check for keyword in job_keywords)
        
        # 링커리어의 경우 더 관대하게 처리
        if 'linkareer.com' in src:
            return has_job_keyword or has_size_indicator or len(alt) > 10
        
        return has_job_keyword or has_size_indicator
    
    def extract_text_from_image_url(self, image_url: str) -> Optional[str]:
        """이미지 URL에서 텍스트 추출"""
        try:
            # 이미지 다운로드
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # PIL 이미지로 변환
            image = Image.open(io.BytesIO(response.content))
            
            # 이미지 전처리 및 OCR
            extracted_text = self.extract_text_from_image(image)
            
            if extracted_text and len(extracted_text.strip()) > 50:
                logger.info(f"이미지에서 텍스트 추출 성공: {image_url[:50]}...")
                return extracted_text
            else:
                logger.warning(f"이미지에서 충분한 텍스트를 추출하지 못함: {image_url[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"이미지 URL에서 텍스트 추출 실패 ({image_url}): {e}")
            return None
    
    def extract_text_from_image(self, image: Image.Image) -> Optional[str]:
        """PIL 이미지에서 GCP Vision AI로 텍스트 추출"""
        try:
            if not self.client:
                logger.error("GCP Vision AI 클라이언트가 초기화되지 않았습니다")
                return None
            
            # 이미지 전처리
            processed_image = self._preprocess_image(image)
            
            # PIL 이미지를 바이트로 변환
            img_byte_array = io.BytesIO()
            processed_image.save(img_byte_array, format='PNG')
            img_byte_array = img_byte_array.getvalue()
            
            # GCP Vision AI 이미지 객체 생성
            vision_image = vision.Image(content=img_byte_array)
            
            # 텍스트 감지 실행 (한국어 + 영어 자동 감지)
            response = self.client.text_detection(image=vision_image)
            
            if response.error.message:
                logger.error(f"GCP Vision AI 오류: {response.error.message}")
                return None
            
            # 텍스트 추출
            texts = response.text_annotations
            if not texts:
                logger.info("이미지에서 텍스트를 찾을 수 없습니다")
                return None
            
            # 첫 번째 결과가 전체 텍스트
            extracted_text = texts[0].description
            
            # 후처리
            cleaned_text = self._postprocess_ocr_text(extracted_text)
            
            logger.info(f"GCP Vision AI 텍스트 추출 완료: {len(cleaned_text)}자")
            return cleaned_text if len(cleaned_text.strip()) > 20 else None
            
        except Exception as e:
            logger.error(f"GCP Vision AI OCR 처리 실패: {e}")
            return None
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """OCR 정확도 향상을 위한 이미지 전처리"""
        try:
            # RGB 모드로 변환
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 이미지 크기 확인 및 리사이즈
            width, height = image.size
            if width < 800:  # 너무 작은 이미지는 확대
                scale_factor = 800 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 대비 향상
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # 선명도 향상
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # 노이즈 제거
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
            
        except Exception as e:
            logger.warning(f"이미지 전처리 중 오류: {e}")
            return image  # 전처리 실패시 원본 반환
    
    def _postprocess_ocr_text(self, text: str) -> str:
        """OCR 결과 텍스트 후처리"""
        import re
        
        # 기본 정리
        text = text.strip()
        
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 연속된 줄바꿈 정리
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # OCR 오류로 발생한 이상한 문자들 제거
        text = re.sub(r'[^\w\s가-힣.,!?()[\]{}:;-]', ' ', text)
        
        # 너무 짧은 줄들 제거
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
        
        return '\n'.join(lines)
    
    def process_webpage_images(self, url: str) -> Optional[str]:
        """웹페이지의 모든 채용공고 관련 이미지에서 텍스트 추출 및 통합"""
        try:
            # 이미지 URL 목록 가져오기
            image_urls = self.detect_images_in_webpage(url)
            
            if not image_urls:
                logger.info("채용공고 관련 이미지가 발견되지 않음")
                return None
            
            all_extracted_texts = []
            
            # 각 이미지에서 텍스트 추출 (최대 5개까지만 처리)
            for i, img_url in enumerate(image_urls[:5]):
                logger.info(f"이미지 처리 중 ({i+1}/{min(len(image_urls), 5)}): {img_url[:50]}...")
                
                extracted_text = self.extract_text_from_image_url(img_url)
                if extracted_text:
                    all_extracted_texts.append(extracted_text)
            
            # 추출된 텍스트들 통합
            if all_extracted_texts:
                combined_text = '\n\n'.join(all_extracted_texts)
                logger.info(f"총 {len(all_extracted_texts)}개 이미지에서 텍스트 추출 완료")
                return combined_text
            else:
                logger.warning("이미지에서 의미있는 텍스트를 추출하지 못함")
                return None
                
        except Exception as e:
            logger.error(f"웹페이지 이미지 처리 실패: {e}")
            return None
    
    def test_ocr_setup(self) -> Tuple[bool, str]:
        """GCP Vision AI 설정이 정상적으로 작동하는지 테스트"""
        try:
            if not self.client:
                return False, "GCP Vision AI 클라이언트가 초기화되지 않았습니다. 서비스 계정 키 파일을 확인하세요."
            
            # 간단한 테스트 이미지 생성 (흰색 배경에 검은 텍스트)
            test_image = Image.new('RGB', (300, 100), color='white')
            
            # PIL 이미지를 바이트로 변환
            img_byte_array = io.BytesIO()
            test_image.save(img_byte_array, format='PNG')
            img_byte_array = img_byte_array.getvalue()
            
            # GCP Vision AI 테스트
            vision_image = vision.Image(content=img_byte_array)
            response = self.client.text_detection(image=vision_image)
            
            if response.error.message:
                return False, f"GCP Vision AI 오류: {response.error.message}"
            
            return True, "GCP Vision AI 설정이 정상적으로 작동합니다"
            
        except Exception as e:
            error_msg = f"GCP Vision AI 설정 오류: {e}"
            
            if "credentials" in str(e).lower():
                error_msg += "\n\n인증 문제가 발생했습니다."
                error_msg += "\n해결방법:"
                error_msg += "\n1. GOOGLE_APPLICATION_CREDENTIALS 환경 변수 설정"
                error_msg += "\n2. 서비스 계정 키 파일 경로 확인"
                error_msg += "\n3. Vision API가 활성화되어 있는지 확인"
            elif "permission" in str(e).lower():
                error_msg += "\n\nAPI 권한 문제가 발생했습니다."
                error_msg += "\n해결방법:"
                error_msg += "\n1. GCP 프로젝트에서 Vision API 활성화"
                error_msg += "\n2. 서비스 계정에 필요한 권한 부여"
            
            return False, error_msg 
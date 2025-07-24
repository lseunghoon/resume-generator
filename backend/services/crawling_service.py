"""
크롤링 서비스 - 웹페이지 크롤링 및 데이터 추출 서비스
"""

import re
import logging
from typing import Tuple, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import requests
from utils.chrome_driver import create_chrome_driver, ChromeDriverError
from utils.validators import analyze_job_posting_content
from utils.logger import LoggerMixin


logger = logging.getLogger(__name__)


class CrawlingService(LoggerMixin):
    def __init__(self):
        super().__init__()

    def extract_job_quick(self, url: str) -> Tuple[List[str], str]:
        """
        빠른 직무 추출. Selenium으로 페이지를 한번 로드하여
        직무 제목과 전체 페이지 HTML 소스를 반환합니다.
        """
        self.logger.info(f"빠른 직무 추출 및 페이지 소스 가져오기 시작: {url}")
        
        try:
            # 1. 단 한 번의 페이지 로드
            html_content = self._load_dynamic_page(url)
            self.logger.info("1단계: 동적 페이지 로드 완료")
            
            # 2. 채용공고 검증
            content_analysis = analyze_job_posting_content(html_content)
            if not content_analysis['is_job_posting']:
                raise ValueError("해당 URL은 채용공고가 아닐 수 있습니다.")
            self.logger.info(f"2단계: 채용공고 검증 완료 (신뢰도: {content_analysis['confidence_score']})")

            # 3. 직무 제목 추출
            job_titles = self._extract_job_title_from_tags(html_content)
            self.logger.info(f"3단계: 직무 제목 추출 완료 - {job_titles}")

            return job_titles, html_content
            
        except Exception as e:
            self.logger.error(f"빠른 직무 추출 실패: {str(e)}")
            raise
            
    def extract_content_from_html(self, html_content: str, base_url: str) -> str:
        """
        미리 받아온 HTML 소스에서 전체 콘텐츠(텍스트 + OCR)를 추출합니다.
        이 함수는 Selenium을 실행하지 않습니다.
        """
        self.logger.info("HTML 소스에서 전체 콘텐츠 추출 시작...")
        try:
            # 1. 전체 텍스트 콘텐츠 추출
            clean_text = self._parse_and_clean_html(html_content)
            self.logger.info(f"1단계: HTML 텍스트 정제 완료")
            
            # 크롤링 결과 디버깅 로그 추가
            self.logger.info(f"크롤링된 텍스트 길이: {len(clean_text)}자")
            self.logger.info(f"크롤링된 텍스트 전체:")
            self.logger.info(f"=== 크롤링된 텍스트 시작 ===")
            self.logger.info(clean_text)
            self.logger.info(f"=== 크롤링된 텍스트 끝 ===")
            
            # 키워드 매칭 디버깅
            text_lower = clean_text.lower()
            role_keywords = ['주요업무', '담당업무', '업무내용', 'job description', 'responsibilities', '역할']
            req_keywords = ['자격요건', '지원자격', 'requirements', 'qualifications', '경험']
            pref_keywords = ['우대사항', '선호사항', 'preferred', 'nice to have']
            process_keywords = ['채용절차', '전형절차', 'process']
            
            found_role = [kw for kw in role_keywords if kw in text_lower]
            found_req = [kw for kw in req_keywords if kw in text_lower]
            found_pref = [kw for kw in pref_keywords if kw in text_lower]
            found_process = [kw for kw in process_keywords if kw in text_lower]
            
            self.logger.info(f"발견된 키워드 - 주요업무: {found_role}, 자격요건: {found_req}, 우대사항: {found_pref}, 채용절차: {found_process}")

            # 2. OCR 실행 여부 판단 및 실행
            ocr_text = ""
            if not self._analyze_text_sufficiency(clean_text):
                self.logger.info("텍스트 정보 불충분, OCR 실행 시작...")
                ocr_text = self._conditional_ocr_extraction(html_content, base_url)
            else:
                self.logger.info("텍스트 정보 충분, OCR 건너뜀")

            # 3. 최종 콘텐츠 통합
            final_content = self._integrate_content(clean_text, ocr_text)
            self.logger.info("3단계: 최종 콘텐츠 통합 완료")

            return final_content
            
        except Exception as e:
            self.logger.error(f"HTML 기반 콘텐츠 추출 실패: {str(e)}")
            return "" # 실패 시 빈 문자열 반환

    def _load_dynamic_page(self, url: str) -> str:
        """1단계: Selenium을 사용한 동적 페이지 로드"""
        driver = None
        try:
            driver = create_chrome_driver()
            driver.get(url)
            
            # 페이지 로드 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            return driver.page_source
            
        except Exception as e:
            self.logger.warning(f"Selenium 크롤링 실패, requests로 대체: {e}")
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except Exception as fallback_error:
                raise Exception(f"모든 크롤링 방법 실패: {fallback_error}")
        finally:
            if driver:
                driver.quit()

    def _parse_and_clean_html(self, html_content: str) -> str:
        """3단계: BeautifulSoup을 사용한 HTML 파싱 및 정제"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 불필요한 요소 제거
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # 텍스트 추출 및 정제
            text = soup.get_text(separator=' ', strip=True)
            
            # 중복 공백 제거
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"HTML 파싱 실패: {e}")
            return html_content

    def _analyze_text_sufficiency(self, text: str) -> bool:
        """구조적 완성도 기반으로 텍스트의 '품질'을 분석하여 OCR 실행 여부를 결정합니다."""
        self.logger.info("구조적 완성도 기반 텍스트 품질 분석 시작...")
        
        if len(text) < 200:
            self.logger.info(f"품질 분석: 텍스트 길이가 절대적으로 부족({len(text)} < 200자). OCR 필요.")
            return False

        role_keywords = ['주요업무', '담당업무', '업무내용', 'job description', 'responsibilities', '역할']
        req_keywords = ['자격요건', '지원자격', 'requirements', 'qualifications', '경험']
        pref_keywords = ['우대사항', '선호사항', 'preferred', 'nice to have']
        process_keywords = ['채용절차', '전형절차', 'process']
        
        text_lower = text.lower()
        quality_score = 0
        matched_keywords = []
        
        has_role = any(keyword in text_lower for keyword in role_keywords)
        has_req = any(keyword in text_lower for keyword in req_keywords)
        
        if has_role and has_req:
            quality_score += 2
            matched_keywords.extend([kw for kw in role_keywords if kw in text_lower])
            matched_keywords.extend([kw for kw in req_keywords if kw in text_lower])
        elif has_role or has_req:
            quality_score += 1
            if has_role:
                matched_keywords.extend([kw for kw in role_keywords if kw in text_lower])
            if has_req:
                matched_keywords.extend([kw for kw in req_keywords if kw in text_lower])
            
        if any(keyword in text_lower for keyword in pref_keywords):
            quality_score += 1
            matched_keywords.extend([kw for kw in pref_keywords if kw in text_lower])
        if any(keyword in text_lower for keyword in process_keywords):
            quality_score += 1
            matched_keywords.extend([kw for kw in process_keywords if kw in text_lower])

        SCORE_THRESHOLD = 3
        self.logger.info(f"콘텐츠 품질 점수: {quality_score} / {SCORE_THRESHOLD}")
        if matched_keywords:
            self.logger.info(f"매칭된 키워드: {', '.join(set(matched_keywords))}")
        else:
            self.logger.info("매칭된 키워드 없음")

        if quality_score >= SCORE_THRESHOLD:
            self.logger.info("텍스트가 구조적으로 충분하다고 판단. OCR을 건너뜁니다.")
            return True
        else:
            self.logger.info("텍스트에 핵심 섹션 조합이 부족. OCR을 실행합니다.")
            return False

    def _conditional_ocr_extraction(self, html_content: str, base_url: str) -> str:
        """
        고도화된 점수 시스템을 사용하여 가장 관련성 높은 단일 이미지를 선택하고 OCR을 실행합니다.
        """
        self.logger.info("고도화된 점수 기반 OCR 이미지 선택 시작...")
        try:
            from services.ocr_service import OCRService
            from urllib.parse import urljoin
            soup = BeautifulSoup(html_content, 'html.parser')
            images = soup.find_all('img')

            self.logger.info(f"페이지에서 발견된 이미지 수: {len(images)}")

            if not images:
                self.logger.info("페이지에 이미지가 없어 OCR을 건너뜁니다.")
                return ""

            best_image = None
            max_score = -1

            for img in images:
                src = img.get('src', '')
                if not src or src.startswith('data:image'): # data URI 스킵
                    continue

                score = 0
                details = []

                # 1. 크기 점수 (가장 중요한 요소)
                width = img.get('width') or img.get('data-width') or 0
                height = img.get('height') or img.get('data-height') or 0
                try:
                    w = int(re.sub(r'\D', '', str(width)))
                    h = int(re.sub(r'\D', '', str(height)))
                    area = w * h
                    
                    if area < 20000:
                        details.append(f"크기 점수: 0 (너무 작음: {w}x{h})")
                        score = -999 # 즉시 탈락
                    elif 20000 <= area <= 2500000:
                        size_score = int(area / 10000)
                        score += size_score
                        details.append(f"크기 점수: +{size_score} ({w}x{h})")
                    else:
                        score += 10
                        details.append(f"크기 점수: +10 (너무 큼: {w}x{h})")

                except (ValueError, TypeError):
                    details.append("크기 정보 없음")
                    pass

                if score < 0:
                    self.logger.debug(f"이미지 건너뜀 (너무 작음): {src[:70]}")
                    continue

                # 2. 키워드 점수 (alt, class, id)
                alt_text = img.get('alt', '').lower()
                class_name = ' '.join(img.get('class', [])).lower()
                
                positive_keywords = ['recruit', 'job', 'career', 'hire', 'position', 'vacancy', '채용', '모집', '구인', '직무', '업무', '자격', '요건', '상세', 'detail', 'posting', '공고']
                if any(kw in alt_text or kw in class_name for kw in positive_keywords):
                    score += 50
                    details.append("긍정 키워드: +50")

                negative_keywords = ['logo', 'icon', 'avatar', 'profile', 'thumb', 'banner', 'ad', 'advertisement', '로고', '아이콘', '배너', 'ci', 'bi', 'sprite']
                if any(kw in src.lower() or kw in alt_text or kw in class_name for kw in negative_keywords):
                    score -= 60
                    details.append("부정 키워드: -60")

                # 3. DOM 위치 점수
                parent = img.parent
                if parent:
                    parent_class = ' '.join(parent.get('class', [])).lower()
                    if any(kw in parent_class for kw in ['content', 'main', 'body', 'article', 'detail', 'view']):
                        score += 20
                        details.append("중요 DOM 위치: +20")

                # 4. 이미지 소스(src) URL 패턴 점수
                if any(p in src.lower() for p in ['job', 'posting', 'recruit', 'view']):
                    score += 15
                    details.append("URL 패턴: +15")
                
                self.logger.info(f"이미지 후보: '{src[:70]}...' | 점수: {score} | 상세: {', '.join(details)}")

                if score > max_score:
                    max_score = score
                    best_image = img

            MIN_SCORE_THRESHOLD = 5  # 임계값을 낮춤 (10 → 5)
            if best_image and max_score >= MIN_SCORE_THRESHOLD:
                image_url = best_image.get('src')
                if not image_url.startswith('http'):
                     image_url = urljoin(base_url, image_url)
                
                self.logger.info(f"--- 최종 OCR 이미지 선택 ---")
                self.logger.info(f"URL: {image_url}")
                self.logger.info(f"최고 점수: {max_score}")
                self.logger.info(f"--------------------------")
                
                # === 핵심 수정 ===
                # 이미지를 직접 다운로드
                image_bytes = self._download_image_with_headers(image_url, base_url)

                if image_bytes:
                    self.logger.info(f"이미지 다운로드 성공 ({len(image_bytes)} bytes), OCR 실행")
                    ocr_service = OCRService()
                    # URL 대신 이미지의 '내용(content)'을 직접 전달
                    return ocr_service.extract_text_from_image_bytes(image_bytes)
                else:
                    self.logger.warning(f"이미지 다운로드 실패: {image_url}")
                    return ""
            else:
                self.logger.warning(f"유효한 OCR 이미지를 찾지 못했습니다. 최고 점수: {max_score} (기준: {MIN_SCORE_THRESHOLD})")
                return ""

        except Exception as e:
            self.logger.warning(f"OCR 이미지 추출 중 예외 발생: {e}")
            return ""
    
    def _download_image_with_headers(self, image_url: str, referer_url: str) -> Optional[bytes]:
        """
        Referer 헤더를 포함하여 이미지를 다운로드하고, 그 내용을 바이트로 반환합니다.
        """
        try:
            # referer_url 유효성 검사
            if not referer_url or not isinstance(referer_url, str):
                self.logger.warning(f"유효하지 않은 referer_url: {referer_url}")
                referer_url = "https://www.google.com"  # 기본값 설정
            
            headers = {
                # "나는 일반적인 최신 Chrome 브라우저다"
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                # "나는 이 페이지(referer_url)를 보다가 이미지를 요청하는 것이다"
                'Referer': referer_url
            }
            
            response = requests.get(image_url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()
            
            # 이미지 내용을 바이트 형태로 반환
            return response.content
            
        except requests.RequestException as e:
            self.logger.error(f"헤더 포함 이미지 다운로드 실패: {e}")
            return None

    def _integrate_content(self, crawled_text: str, ocr_text: str) -> str:
        """크롤링 텍스트와 OCR 텍스트 통합"""
        return f"{crawled_text}\n\n{ocr_text}" if ocr_text else crawled_text

    def _extract_job_title_from_tags(self, html_content: str) -> List[str]:
        """
        h1, h2, h3, h4, title 태그를 대상으로 점수 모델을 적용하여 최적의 직무 제목을 추출합니다.
        클래스 이름에 'title' 등이 포함된 경우 추가 점수를 부여합니다.
        """
        self.logger.info("핵심 태그(h1~h4, title) 및 클래스 기반 직무 제목 추출 시작...")
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            candidates = []

            # 1. 후보군 수집 (h1, h2, h3, h4, title로 확장)
            potential_elements = soup.find_all(['h1', 'h2', 'h3', 'h4'], limit=10)
            if soup.title:
                potential_elements.append(soup.title)
            
            if not potential_elements:
                self.logger.warning("h1-h4, title 태그를 찾을 수 없습니다.")
                return ["직무 정보 없음"]

            # 2. 각 후보에 대해 '품질 점수' 계산
            for element in potential_elements:
                text = element.get_text().strip()
                if not text or len(text) < 5 or len(text) > 150:
                    continue
                
                score = 0
                class_name = ' '.join(element.get('class', [])).lower()
                
                # a) 구조 점수: 태그 이름
                if element.name == 'h1': score += 60
                elif element.name == 'title': score += 30
                elif element.name == 'h2': score += 20
                elif element.name == 'h3': score += 15
                elif element.name == 'h4': score += 10

                # b) 구조 점수: 클래스 이름 보너스
                if any(cls_kw in class_name for cls_kw in ['title', 'head', 'job', 'position', 'name']):
                    score += 35

                # c) 내용 점수: 긍정 키워드
                positive_keywords = ['developer', '개발', 'engineer', 'designer', 'planner', 'manager', 'marketing', 'intern', '인턴', '신입', '경력', 'corporate', 'development']
                if any(pos_kw in text.lower() for pos_kw in positive_keywords):
                    score += 40

                # d) 페널티 점수: 부정 키워드
                negative_keywords = ['careers', '채용정보', '채용 안내', 'cookie', '©', 'corp.', '목록', 'filter', '안내', '절차']
                if any(neg_kw in text.lower() for neg_kw in negative_keywords):
                    score -= 100

                candidates.append({'text': text, 'score': score})
                self.logger.info(f"후보: '{text[:40]}...' (태그: {element.name}, 클래스: '{class_name}', 점수: {score})")

            if not candidates:
                return ["직무 정보 없음"]
            
            # 3. 최고점 후보 선정
            best_candidate = max(candidates, key=lambda x: x['score'])
            
            # 4. 최종 결과 반환
            MINIMUM_SCORE = 25
            if best_candidate['score'] >= MINIMUM_SCORE:
                cleaned_title = self._clean_job_title(best_candidate['text'])
                self.logger.info(f"최종 선택: '{cleaned_title}' (최고 점수: {best_candidate['score']})")
                return [cleaned_title]
            else:
                self.logger.warning(f"모든 후보가 최소 점수({MINIMUM_SCORE}) 미달. 최고점 후보: '{best_candidate['text']}' (점수: {best_candidate['score']})")
                return ["직무 정보 없음"]
                
        except Exception as e:
            self.logger.error(f"페이지 제목 추출 중 예외 발생: {e}")
            return ["직무 정보 없음"]

    def _clean_job_title(self, title: str) -> str:
        """기존보다 강화된 직무 제목 정제 함수"""
        try:
            title = re.sub(r'\s*([-|–])\s*([a-zA-Z\s]+(corp|inc)?\.?)$', '', title, flags=re.I)
            title = re.sub(r'\s*job\s*details$', '', title, flags=re.I)
            title = re.sub(r'^\[.*?\]\s*', '', title)
            title = re.sub(r'\([^)]{30,}\)', '', title)
            return title.strip()
        except Exception:
            return ""

    def test_crawling(self, url: str = "https://www.google.com") -> Tuple[bool, str]:
        """크롤링 기능 테스트"""
        try:
            html_content = self._load_dynamic_page(url)
            if html_content and len(html_content) > 100:
                self.logger.info("크롤링 테스트 성공")
                return True, f"크롤링 성공: {len(html_content)}자 추출"
            else:
                return False, "크롤링 실패: 내용 추출 불가"
        except Exception as e:
            self.logger.error(f"크롤링 테스트 실패: {e}")
            return False, f"크롤링 테스트 실패: {str(e)}" 
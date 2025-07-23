from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging
import time
from job_posting_filter import JobPostingFilter
from ocr_processor import OCRProcessor

logger = logging.getLogger(__name__)

def crawl_job_description(url):
    """채용공고 크롤링 메인 함수 (필터링 + OCR + 검증 포함)"""
    try:
        logger.info(f"채용공고 크롤링 시작: {url}")
        
        # 1단계: 텍스트 기반 크롤링
        text_content = _crawl_text_content(url)
        logger.info(f"텍스트 크롤링 완료: {'성공' if text_content else '실패'}")
        
        # 링커리어 특화 결과이거나 이미 이미지 OCR이 포함된 경우 별도 이미지 크롤링 건너뛰기
        if isinstance(text_content, dict) and text_content.get('needs_ocr'):
            logger.info("텍스트 크롤링에서 이미지 OCR 정보 포함됨 - 별도 이미지 크롤링 건너뛰기")
            ocr_content = None
        else:
            # 2단계: 이미지 기반 OCR 크롤링 (일반적인 경우만)
            ocr_content = _crawl_image_content(url)
            logger.info(f"이미지 OCR 크롤링 완료: {'성공' if ocr_content else '실패'}")
        
        # 3단계: 콘텐츠 통합
        combined_content = _combine_content(text_content, ocr_content)
        
        if not combined_content:
            logger.warning("크롤링된 콘텐츠가 없음")
            return None
        
        # 4단계: 채용공고 필터링
        from job_posting_filter import JobPostingFilter
        filtered_content = JobPostingFilter.filter_job_posting_content(combined_content)
        
        if not filtered_content:
            logger.warning("채용공고 필터링 실패")
            return None
        
        # 5단계: 최종 검증
        is_valid, score, status = JobPostingFilter.validate_job_posting(filtered_content)
        
        if not is_valid:
            logger.warning(f"채용공고 검증 실패: {status}")
            return None
        
        logger.info(f"채용공고 크롤링 및 검증 완료 (점수: {score:.2f})")
        return filtered_content
        
    except Exception as e:
        logger.error(f"채용공고 크롤링 중 오류: {str(e)}")
        return None

def _crawl_text_content(url):
    """기존 텍스트 기반 크롤링 로직 (링커리어 특화 포함)"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)
        time.sleep(3)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # 웹페이지 제목 추출
        page_title = ""
        title_tag = soup.find('title')
        if title_tag:
            page_title = title_tag.get_text(strip=True)
            logger.info(f"웹페이지 제목 추출: {page_title[:100]}...")
        
        driver.quit()

        # 링커리어 특화 크롤링 (다른 일반 크롤링 대신 우선 실행)
        if url.startswith("https://linkareer.com/activity/"):
            logger.info("링커리어 특화 크롤링 시작 - 일반 크롤링 건너뛰기")
            linkareer_content = _extract_linkareer_content(soup, url)
            if linkareer_content:
                logger.info("링커리어 특화 크롤링 성공 - 다른 크롤링 방식 건너뛰기")
                
                # 제목 정보 추가
                if isinstance(linkareer_content, dict):
                    linkareer_content['page_title'] = page_title
                    return linkareer_content
                else:
                    # 일반 텍스트인 경우 제목을 앞에 추가
                    if page_title:
                        return f"=== 제목 ===\n{page_title}\n\n=== 내용 ===\n{linkareer_content}"
                    return linkareer_content
            else:
                logger.warning("링커리어 특화 크롤링 실패 - 일반 크롤링으로 fallback")

        # 일반적인 채용공고 컨테이너 선택자들
        common_selectors = [
            'main[role="main"]',
            '.job-description',
            '.job-content',
            '.post-content',
            '.content',
            'article',
            '.detail-content',
            '.job-detail',
            '#content',
            '.main-content'
        ]

        # 선택자로 텍스트 추출 시도
        for selector in common_selectors:
            content = soup.select_one(selector)
            if content:
                # 이미지가 있는지 먼저 확인
                images = content.find_all('img')
                
                for tag in content.find_all(['button', 'a', 'form', 'input']):
                    tag.decompose()
                    
                text = content.get_text(strip=True, separator='\n')
                
                # 이미지가 있으면 OCR 처리 필요한 형태로 반환
                if images and len(text) > 50:
                    image_urls = [img.get('src') for img in images if img.get('src')]
                    if image_urls:
                        logger.info(f"일반 크롤링에서 이미지 발견 - 선택자: {selector}, 이미지 {len(image_urls)}개")
                        result = {
                            'text': text,
                            'images': image_urls,
                            'needs_ocr': True,
                            'source_url': url,
                            'page_title': page_title
                        }
                        return result
                
                # 이미지가 없으면 텍스트만 반환 (제목 포함)
                if len(text) > 100:
                    logger.info(f"텍스트 콘텐츠 추출 성공 - 선택자: {selector}")
                    if page_title:
                        return f"=== 제목 ===\n{page_title}\n\n=== 내용 ===\n{text}"
                    return text

        # 선택자로 찾지 못한 경우 전체 텍스트 추출
        # 먼저 이미지가 있는지 확인
        all_images = soup.find_all('img')
        
        text = soup.get_text(strip=True, separator='\n')
        blocks = [block for block in text.split('\n') if len(block) > 100]
        
        if blocks:
            result = '\n'.join(blocks)
            
            # 이미지가 있으면 OCR 처리 필요한 형태로 반환
            if all_images:
                image_urls = [img.get('src') for img in all_images if img.get('src')]
                if image_urls:
                    logger.info(f"전체 텍스트에서 이미지 발견 - 이미지 {len(image_urls)}개")
                    return {
                        'text': result,
                        'images': image_urls,
                        'needs_ocr': True,
                        'source_url': url,
                        'page_title': page_title
                    }
            
            logger.info("텍스트 콘텐츠 추출 성공 (전체 텍스트)")
            if page_title:
                return f"=== 제목 ===\n{page_title}\n\n=== 내용 ===\n{result}"
            return result

        return None
        
    except Exception as e:
        logger.error(f"텍스트 크롤링 실패: {str(e)}")
        if 'driver' in locals() and driver:
            driver.quit()
        return None

def _extract_linkareer_content(soup, source_url):
    """링커리어 활동 페이지에서 '상세내용' 섹션만 정확히 추출 (엄격한 버전)"""
    try:
        logger.info("링커리어 상세내용 섹션 정확한 추출 시작")
        
        # 1단계: 정확한 '상세내용' 섹션 찾기
        activity_sections = soup.find_all('section', class_=lambda x: x and 'ActivityDetailTabContent' in x)
        logger.info(f"ActivityDetailTabContent 섹션 {len(activity_sections)}개 발견")
        
        for i, section in enumerate(activity_sections):
            # '상세내용' h2 태그가 있는 섹션 찾기
            h2_tag = section.find('h2')
            if h2_tag and '상세내용' in h2_tag.get_text():
                logger.info(f"섹션 {i+1}에서 '상세내용' h2 태그 발견")
                
                # 정확히 h2 다음의 div만 추출 (형제 요소)
                next_div = h2_tag.find_next_sibling('div')
                if next_div:
                    logger.info("h2 다음 div 발견 - 정확한 상세내용 컨테이너")
                    
                    # 이 div 안의 이미지만 확인 (다른 섹션 이미지 제외)
                    images = next_div.find_all('img')
                    text_content = next_div.get_text(strip=True, separator='\n')
                    
                    logger.info(f"상세내용 div: 텍스트 {len(text_content)}자, 이미지 {len(images)}개")
                    
                    if images:
                        # se2editor 이미지만 필터링 (링커리어 채용공고 이미지)
                        job_images = []
                        for img in images:
                            src = img.get('src', '')
                            if 'se2editor' in src or 'media-cdn.linkareer.com' in src:
                                job_images.append(src)
                                logger.info(f"채용공고 이미지 발견: {src[:60]}...")
                        
                        if job_images:
                            result = {
                                'text': text_content,
                                'images': job_images,
                                'needs_ocr': True,
                                'source_url': source_url
                            }
                            logger.info(f"링커리어 정확한 상세내용 추출 성공: 텍스트 {len(text_content)}자, 채용공고 이미지 {len(job_images)}개")
                            return result
                        else:
                            logger.info("이미지가 있지만 채용공고 관련 이미지가 아님")
                    
                    # 이미지가 없거나 채용공고 이미지가 아닌 경우 텍스트만 반환
                    if len(text_content) > 50:
                        logger.info(f"링커리어 상세내용 텍스트만 추출: {len(text_content)}자")
                        return text_content
                
                # h2 다음 div가 없으면 responsive-element 찾기
                else:
                    logger.info("h2 다음 div 없음, responsive-element 찾기")
                    content_div = section.find('div', class_='responsive-element')
                    if content_div:
                        images = content_div.find_all('img')
                        text_content = content_div.get_text(strip=True, separator='\n')
                        
                        # se2editor 이미지만 필터링
                        job_images = []
                        for img in images:
                            src = img.get('src', '')
                            if 'se2editor' in src or 'media-cdn.linkareer.com' in src:
                                job_images.append(src)
                        
                        if job_images:
                            result = {
                                'text': text_content,
                                'images': job_images,
                                'needs_ocr': True,
                                'source_url': source_url
                            }
                            logger.info(f"링커리어 responsive-element 추출 성공: 텍스트 {len(text_content)}자, 채용공고 이미지 {len(job_images)}개")
                            return result
                        elif len(text_content) > 50:
                            return text_content
        
        logger.warning("링커리어 상세내용 섹션을 찾지 못함")
        return None
        
    except Exception as e:
        logger.error(f"링커리어 컨텐츠 추출 실패: {e}")
        return None

def _crawl_image_content(url):
    """이미지 OCR 기반 크롤링"""
    try:
        logger.info("이미지 OCR 처리 시작")
        ocr_processor = OCRProcessor()
        
        # OCR 설정 테스트
        is_setup_ok, setup_message = ocr_processor.test_ocr_setup()
        if not is_setup_ok:
            logger.warning(f"OCR 설정 문제: {setup_message}")
            return None
        
        # 웹페이지에서 이미지 처리
        image_text = ocr_processor.process_webpage_images(url)
        
        if image_text:
            logger.info("이미지 OCR 처리 성공")
            return image_text
        else:
            logger.info("이미지에서 추출된 텍스트 없음")
            return None
            
    except Exception as e:
        logger.error(f"이미지 OCR 처리 실패: {str(e)}")
        return None

def _combine_content(text_content, ocr_content):
    """텍스트와 이미지에서 추출한 내용을 통합 (새로운 형태 지원)"""
    try:
        combined_parts = []
        
        # text_content가 딕셔너리 형태인 경우 (이미지 OCR 필요)
        if isinstance(text_content, dict) and text_content.get('needs_ocr'):
            logger.info("특별한 형태의 텍스트 콘텐츠 - 내장 이미지 OCR 처리")
            
            # 제목 정보 추가
            page_title = text_content.get('page_title', '')
            if page_title:
                combined_parts.append("=== 제목 ===")
                combined_parts.append(page_title)
            
            # 텍스트 부분 추가
            if text_content.get('text') and len(text_content['text'].strip()) > 50:
                combined_parts.append("=== 텍스트 콘텐츠 ===")
                combined_parts.append(text_content['text'])
            
            # 내장 이미지들에 대해 OCR 실행
            image_urls = text_content.get('images', [])
            if image_urls:
                logger.info(f"내장 이미지 {len(image_urls)}개에 대해 OCR 실행")
                
                from ocr_processor import OCRProcessor
                ocr_processor = OCRProcessor()
                
                all_ocr_texts = []
                for i, img_url in enumerate(image_urls[:5]):  # 최대 5개까지
                    logger.info(f"내장 이미지 OCR 처리 ({i+1}/{min(len(image_urls), 5)}): {img_url[:50]}...")
                    
                    try:
                        # 상대 경로인 경우 절대 경로로 변환
                        if img_url.startswith('/'):
                            from urllib.parse import urljoin, urlparse
                            source_url = text_content.get('source_url', '')
                            if source_url:
                                parsed_url = urlparse(source_url)
                                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                img_url = urljoin(base_url, img_url)
                        
                        ocr_text = ocr_processor.extract_text_from_image_url(img_url)
                        if ocr_text and len(ocr_text.strip()) > 20:
                            all_ocr_texts.append(f"[이미지 {i+1}]\n{ocr_text}")
                            logger.info(f"내장 이미지 {i+1} OCR 성공: {len(ocr_text)}자")
                        else:
                            logger.warning(f"내장 이미지 {i+1} OCR 실패 또는 텍스트 부족")
                    except Exception as e:
                        logger.error(f"내장 이미지 {i+1} OCR 처리 중 오류: {e}")
                
                if all_ocr_texts:
                    combined_parts.append("=== 이미지에서 추출된 콘텐츠 ===")
                    combined_parts.extend(all_ocr_texts)
                    logger.info(f"내장 이미지 OCR 완료: {len(all_ocr_texts)}개 이미지에서 텍스트 추출")
                else:
                    logger.warning("내장 이미지들에서 의미있는 텍스트를 추출하지 못함")
            
            # 딕셔너리 형태의 경우 별도 OCR 콘텐츠는 무시 (중복 방지)
            if ocr_content:
                logger.info("내장 이미지 OCR이 있으므로 별도 OCR 콘텐츠 무시 (중복 방지)")
        
        # 일반적인 텍스트 콘텐츠 처리
        elif text_content and len(str(text_content).strip()) > 50:
            combined_parts.append(str(text_content))
            
            # 별도 OCR 콘텐츠 처리 (일반 텍스트인 경우만)
            if ocr_content and len(ocr_content.strip()) > 50:
                combined_parts.append("=== 이미지에서 추출된 콘텐츠 ===")
                combined_parts.append(ocr_content)
        
        if combined_parts:
            result = '\n\n'.join(combined_parts)
            has_text = bool(text_content)
            has_ocr = bool(ocr_content) or (isinstance(text_content, dict) and text_content.get('images'))
            logger.info(f"콘텐츠 통합 완료 (텍스트: {'있음' if has_text else '없음'}, 이미지: {'있음' if has_ocr else '없음'})")
            return result
        else:
            logger.warning("통합할 콘텐츠가 없음")
            return None
            
    except Exception as e:
        logger.error(f"콘텐츠 통합 실패: {str(e)}")
        # 실패 시 텍스트 콘텐츠라도 반환
        if isinstance(text_content, dict):
            return text_content.get('text', '')
        return text_content if text_content else ocr_content 
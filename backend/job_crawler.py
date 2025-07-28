from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import logging
import time
import requests
import re
from job_posting_filter import JobPostingFilter
from ocr_processor import OCRProcessor
from utils.chrome_driver import safe_create_chrome_driver

logger = logging.getLogger(__name__)

def crawl_job_description(url):
    """채용공고 크롤링 메인 함수 - 새로운 구조화된 추출 방식"""
    try:
        logger.info(f"새로운 구조화된 채용공고 크롤링 시작: {url}")
        
        # 1단계: Selenium으로 동적 페이지 로드 및 HTML 확보
        html_content = _get_dynamic_html(url)
        if not html_content:
            logger.warning("HTML 확보 실패")
            return None
        
        # 2단계: BeautifulSoup으로 파싱 및 1차 구조적 클리닝
        soup = _parse_and_clean_html(html_content)
        
        # 3단계: 2차 콘텐츠 클리닝 및 텍스트 데이터 추출
        crawled_text = _extract_clean_text(soup)
        logger.info(f"텍스트 추출 완료: {len(crawled_text)}자")
        
        # 4단계: 텍스트 유효성 분석 (OCR 실행 여부 결정)
        is_text_insufficient = _analyze_text_sufficiency(crawled_text)
        logger.info(f"텍스트 충분성 분석: {'부족' if is_text_insufficient else '충분'}")
        
        # 5단계: OCR 대상 이미지 분석 및 '최고 후보' 선정
        best_image_url = None
        if is_text_insufficient:
            best_image_url = _select_best_image_candidate(soup, url)
            logger.info(f"최고 후보 이미지: {best_image_url[:50] if best_image_url else '없음'}...")
        
        # 6단계: 조건부 단일 이미지 OCR 실행
        ocr_text = ""
        if is_text_insufficient and best_image_url:
            logger.info("텍스트 부족으로 OCR 실행")
            ocr_text = _execute_single_image_ocr(best_image_url)
            logger.info(f"OCR 결과: {len(ocr_text)}자")
        else:
            logger.info("텍스트 충분 또는 이미지 없음 - OCR 건너뛰기")
        
        # 7단계: 최종 콘텐츠 통합 및 정제
        final_content = _integrate_and_refine_content(crawled_text, ocr_text)
        
        if not final_content or len(final_content) < 100:
            logger.warning("최종 콘텐츠 부족")
            return None
        
        # 8단계: 구조화된 데이터 추출
        structured_data = _extract_structured_data(final_content)
        
        logger.info(f"구조화된 데이터 추출 완료: {len(structured_data)}자")
        return structured_data
        
    except Exception as e:
        logger.error(f"채용공고 크롤링 중 오류: {str(e)}")
        return None

def _get_dynamic_html(url):
    """1단계: Selenium으로 동적 페이지 로드 및 HTML 확보"""
    try:
        # 새로운 안전한 ChromeDriver 사용
        driver = safe_create_chrome_driver()
        
        if driver is not None:
            try:
                driver.get(url)
                time.sleep(3)  # JavaScript 렌더링 대기
                
                html_content = driver.page_source
                driver.quit()
                
                logger.info("Selenium으로 HTML 확보 성공")
                return html_content
                
            except Exception as selenium_error:
                if driver:
                    driver.quit()
                logger.warning(f"Selenium 실행 중 오류: {selenium_error}")
        else:
            logger.warning("ChromeDriver 초기화 실패")
        
        # 대안: requests 사용
        logger.info("requests로 fallback")
        return _get_html_with_requests(url)
            
    except Exception as e:
        logger.error(f"HTML 확보 실패: {str(e)}")
        return None

def _get_html_with_requests(url):
    """대안: requests로 HTML 확보"""
    try:
        logger.info("requests로 HTML 확보 시도")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        logger.info("requests로 HTML 확보 성공")
        return response.text
        
    except Exception as e:
        logger.error(f"requests HTML 확보 실패: {str(e)}")
        return None

def _parse_and_clean_html(html_content):
    """2단계: BeautifulSoup으로 파싱 및 1차 구조적 클리닝"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 직무와 전혀 관련 없는 구조적 요소 제거
    unwanted_tags = ['header', 'footer', 'nav', 'script', 'style', 'aside', 'iframe']
    for tag_name in unwanted_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    
    # 광고 및 불필요한 클래스 제거
    unwanted_classes = ['ad', 'advertisement', 'banner', 'popup', 'modal', 'cookie', 'gdpr']
    for class_name in unwanted_classes:
        for tag in soup.find_all(class_=lambda x: x and any(unwanted in str(x).lower() for unwanted in unwanted_classes)):
            tag.decompose()
    
    logger.info("1차 구조적 클리닝 완료")
    return soup

def _extract_clean_text(soup):
    """3단계: 2차 콘텐츠 클리닝 및 텍스트 데이터 추출"""
    # 불필요한 버튼/링크 영역 제거
    unwanted_texts = ['지원하기', '공유하기', '스크랩', '신고하기', '목록보기', '이전글', '다음글']
    for text in unwanted_texts:
        for element in soup.find_all(text=re.compile(text, re.IGNORECASE)):
            parent = element.parent
            if parent and parent.name in ['button', 'a', 'span']:
                parent.decompose()
    
    # 핵심 본문 영역 탐색 (우선순위 순)
    main_selectors = [
        'main',
        'article', 
        'div#content',
        'div.content',
        '.job-description',
        '.job-detail',
        '.post-content',
        '.detail-content'
    ]
    
    main_content = None
    for selector in main_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            logger.info(f"핵심 본문 영역 발견: {selector}")
            break
    
    # 핵심 영역을 찾지 못한 경우 body 전체 사용
    if not main_content:
        main_content = soup.find('body') or soup
        logger.info("핵심 영역 미발견 - body 전체 사용")
    
    # 텍스트 추출 및 정제
    raw_text = main_content.get_text(separator='\n', strip=True)
    
    # 불필요한 단어 제거
    noise_words = ['jd', '직무정보', '채용정보', '상세보기', '더보기', '접기']
    for word in noise_words:
        raw_text = re.sub(rf'\b{word}\b', '', raw_text, flags=re.IGNORECASE)
    
    # 과도한 공백 정리
    raw_text = re.sub(r'\n\s*\n', '\n', raw_text)
    raw_text = re.sub(r'\s+', ' ', raw_text)
    
    return raw_text.strip()

def _analyze_text_sufficiency(text):
    """4단계: 텍스트 유효성 분석 (OCR 실행 여부 결정)"""
    if len(text) < 200:
        logger.info("텍스트 길이 부족 (200자 미만)")
        return True
    
    # 필수 키워드 체크
    essential_keywords = [
        '주요업무', '담당업무', '업무내용', '자격요건', '우대사항',
        '주요 업무', '담당 업무', '업무 내용', '자격 요건', '우대 사항',
        '채용', '모집', 'job', 'work', 'responsibility', 'requirement'
    ]
    
    text_lower = text.lower()
    found_keywords = sum(1 for keyword in essential_keywords if keyword.lower() in text_lower)
    
    if found_keywords < 2:
        logger.info(f"필수 키워드 부족 ({found_keywords}/2)")
        return True
    
    logger.info("텍스트 충분성 확인")
    return False

def _select_best_image_candidate(soup, base_url):
    """5단계: OCR 대상 이미지 분석 및 '최고 후보' 선정"""
    images = soup.find_all('img')
    if not images:
        logger.info("이미지 없음")
        return None
    
    candidates = []
    
    for img in images:
        src = img.get('src')
        if not src:
            continue
        
        # 상대 경로를 절대 경로로 변환
        if src.startswith('/'):
            from urllib.parse import urljoin
            src = urljoin(base_url, src)
        elif src.startswith('data:'):
            continue  # Base64 이미지 제외
        
        # 기본 점수: 이미지 크기 (추정)
        width = img.get('width', '0')
        height = img.get('height', '0')
        try:
            area = int(width) * int(height) if width.isdigit() and height.isdigit() else 1000
        except:
            area = 1000
        
        score = area
        
        # 보너스 점수: 관련 키워드
        bonus_keywords = ['채용', 'job', 'recruit', 'description', 'detail', 'info']
        alt_text = (img.get('alt') or '').lower()
        src_lower = src.lower()
        
        for keyword in bonus_keywords:
            if keyword in alt_text or keyword in src_lower:
                score += 10000  # 매우 큰 보너스
        
        candidates.append((src, score))
        logger.debug(f"이미지 후보: {src[:50]}... (점수: {score})")
    
    if not candidates:
        return None

    # 최고 점수 이미지 선정
    best_candidate = max(candidates, key=lambda x: x[1])
    logger.info(f"최고 후보 이미지 선정 (점수: {best_candidate[1]})")
    
    return best_candidate[0]

def _execute_single_image_ocr(image_url):
    """6단계: 조건부 단일 이미지 OCR 실행"""
    try:
        ocr_processor = OCRProcessor()
        result = ocr_processor.extract_text_from_image_url(image_url)
        
        if result and len(result) > 50:
            logger.info("OCR 실행 성공")
            return result
        else:
            logger.warning("OCR 결과 부족")
            return ""
            
    except Exception as e:
        logger.error(f"OCR 실행 실패: {str(e)}")
        return ""

def _integrate_and_refine_content(crawled_text, ocr_text):
    """7단계: 최종 콘텐츠 통합 및 정제"""
    # 콘텐츠 통합
    final_content = crawled_text
    if ocr_text:
        final_content += f"\n\n=== 이미지에서 추출된 내용 ===\n{ocr_text}"
    
    # 최종 정제
    final_content = re.sub(r'\n\s*\n+', '\n\n', final_content)
    final_content = re.sub(r'\s+', ' ', final_content)
    
    return final_content.strip()

def _extract_structured_data(content):
    """8단계: 구조화된 데이터 추출"""
    try:
        # 섹션별 패턴 정의
        section_patterns = {
            '주요업무': [
                r'주요\s*업무[:\s]*(.+?)(?=\n(?:자격|우대|조건|혜택|기타|\Z))',
                r'담당\s*업무[:\s]*(.+?)(?=\n(?:자격|우대|조건|혜택|기타|\Z))',
                r'업무\s*내용[:\s]*(.+?)(?=\n(?:자격|우대|조건|혜택|기타|\Z))',
                r'job\s*description[:\s]*(.+?)(?=\n(?:requirement|qualification|benefit|\Z))',
            ],
            '자격요건': [
                r'자격\s*요건[:\s]*(.+?)(?=\n(?:우대|조건|혜택|기타|\Z))',
                r'지원\s*자격[:\s]*(.+?)(?=\n(?:우대|조건|혜택|기타|\Z))',
                r'requirement[:\s]*(.+?)(?=\n(?:preferred|benefit|other|\Z))',
            ],
            '우대사항': [
                r'우대\s*사항[:\s]*(.+?)(?=\n(?:조건|혜택|기타|\Z))',
                r'우대\s*조건[:\s]*(.+?)(?=\n(?:조건|혜택|기타|\Z))',
                r'preferred[:\s]*(.+?)(?=\n(?:benefit|other|\Z))',
            ],
            '근무조건': [
                r'근무\s*조건[:\s]*(.+?)(?=\n(?:혜택|기타|\Z))',
                r'근무\s*환경[:\s]*(.+?)(?=\n(?:혜택|기타|\Z))',
                r'working\s*condition[:\s]*(.+?)(?=\n(?:benefit|other|\Z))',
            ],
            '복리혜택': [
                r'복리\s*혜택[:\s]*(.+?)(?=\n(?:기타|\Z))',
                r'혜택[:\s]*(.+?)(?=\n(?:기타|\Z))',
                r'benefit[:\s]*(.+?)(?=\n(?:other|\Z))',
            ]
        }
        
        structured_result = {}
        
        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    section_content = match.group(1).strip()
                    if len(section_content) > 10:  # 최소 길이 체크
                        structured_result[section_name] = section_content[:500]  # 최대 500자
                        logger.info(f"{section_name} 섹션 추출 성공: {len(section_content)}자")
                        break
        
        # 구조화된 데이터가 없으면 원본 텍스트 반환
        if not structured_result:
            logger.warning("구조화된 데이터 추출 실패 - 원본 텍스트 반환")
            return content[:1000]  # 최대 1000자
        
        # 구조화된 데이터를 텍스트로 변환
        formatted_result = []
        for section, content in structured_result.items():
            formatted_result.append(f"=== {section} ===\n{content}")
        
        return "\n\n".join(formatted_result)
            
    except Exception as e:
        logger.error(f"구조화된 데이터 추출 실패: {str(e)}")
        return content[:1000]  # 실패 시 원본 텍스트 반환

# 기존 함수들은 유지 (하위 호환성)
def _crawl_text_content(url):
    """기존 호환성을 위한 래퍼 함수"""
    return crawl_job_description(url)

def _crawl_image_content(url):
    """이미지 크롤링 - 새로운 방식에서는 사용하지 않음"""
    logger.info("새로운 방식에서는 별도 이미지 크롤링을 사용하지 않음")
        return None

def _combine_content(text_content, ocr_content):
    """콘텐츠 통합 - 새로운 방식에서는 내부적으로 처리됨"""
    if isinstance(text_content, str):
        return text_content
    return text_content if text_content else ocr_content


def _extract_job_positions_from_structured_data(structured_content):
    """구조화된 데이터에서 직무 정보 추출"""
    try:
        logger.info("구조화된 데이터에서 직무 정보 추출 시작")
        
        # 구조화된 데이터에서 직무 키워드 추출
        job_keywords = []
        
        # 섹션별로 직무 관련 키워드 추출
        sections_to_check = ['주요업무', '담당업무', '업무내용']
        
        for section in sections_to_check:
            if f"=== {section} ===" in structured_content:
                # 해당 섹션 내용 추출
                section_start = structured_content.find(f"=== {section} ===")
                section_end = structured_content.find("===", section_start + 10)
                if section_end == -1:
                    section_content = structured_content[section_start:]
                else:
                    section_content = structured_content[section_start:section_end]
                
                # 직무 관련 키워드 패턴
                job_patterns = [
                    r'([가-힣]+)\s*(?:담당|업무|개발|기획|분석|설계)',
                    r'(?:담당|업무):\s*([가-힣\s]+)',
                    r'([A-Za-z\s]+)\s*(?:development|analysis|design|management)',
                ]
                
                for pattern in job_patterns:
                    matches = re.findall(pattern, section_content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]
                        clean_match = match.strip()
                        if len(clean_match) > 2 and clean_match not in job_keywords:
                            job_keywords.append(clean_match)
        
        # 키워드가 없으면 기본 추론
        if not job_keywords:
            # 전체 텍스트에서 일반적인 직무 키워드 찾기
            common_jobs = [
                'Research Assistant', 'RA', '리서치 어시스턴트', '연구 보조',
                '인턴', '인턴십', 'Intern', 'Internship',
                '개발자', 'Developer', '기획자', 'Planner',
                '분석가', 'Analyst', '매니저', 'Manager'
            ]
            
            content_lower = structured_content.lower()
            for job in common_jobs:
                if job.lower() in content_lower:
                    job_keywords.append(job)
                    break
        
        # 결과 정리
        if job_keywords:
            logger.info(f"구조화된 데이터에서 직무 키워드 추출 성공: {job_keywords}")
            return job_keywords[:3]
        else:
            logger.info("구조화된 데이터에서 직무 키워드 미발견 - 기본값 반환")
            return ['인턴']
            
    except Exception as e:
        logger.error(f"구조화된 데이터 직무 추출 실패: {e}")
        return ['인턴'] 
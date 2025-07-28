"""
데이터 검증 유틸리티 함수들
"""

import re
import json
from typing import List, Dict, Any
from urllib.parse import urlparse
import logging
from urllib.parse import urljoin
import requests
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


def check_robots_txt_permission(url: str) -> bool:
    """robots.txt를 확인하여 크롤링이 허용되는지 검증"""
    try:
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        logger.info(f"robots.txt 확인: {robots_url}")
        
        # RobotFileParser 사용
        rp = RobotFileParser()
        rp.set_url(robots_url)
        
        # robots.txt 읽기 (타임아웃 설정)
        try:
            rp.read()
        except Exception as e:
            logger.warning(f"robots.txt 읽기 실패: {e}. 허용으로 간주합니다.")
            return True  # robots.txt가 없거나 읽을 수 없으면 허용으로 간주
        
        # User-agent '*'에 대해 해당 URL 접근 가능 여부 확인
        try:
            can_fetch = rp.can_fetch('*', url)
        except Exception as e:
            logger.warning(f"robots.txt can_fetch 실패: {e}. 허용으로 간주합니다.")
            return True  # can_fetch 실패 시 허용으로 간주
        
        logger.info(f"robots.txt 검증 결과: {can_fetch} (URL: {url})")
        return can_fetch
        
    except Exception as e:
        logger.error(f"robots.txt 검증 중 오류: {e}")
        return True  # 오류 시 허용으로 간주


class ValidationError(Exception):
    """데이터 검증 관련 예외"""
    pass


def validate_url(url: str) -> bool:
    """
    URL 유효성 검증
    
    Args:
        url (str): 검증할 URL
        
    Returns:
        bool: 유효한 URL인지 여부
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_job_posting_url(url: str) -> bool:
    """
    하이브리드 방식으로 채용공고 URL 검증
    
    1단계: 주요 플랫폼 URL 패턴 검사
    2단계: 일반 키워드 URL 패턴 검사  
    3단계: 웹 크롤링 및 콘텐츠 분석 (필요시)
    """
    if not url or not isinstance(url, str):
        return False
    
    # URL 앞뒤 공백 제거
    url = url.strip()
    
    # 기본 URL 형식 검증
    if not url.startswith(('http://', 'https://')):
        return False
    
    # 링커리어 차단
    if url.startswith(('https://linkareer.com/', 'http://linkareer.com/')):
        return False
    
    # 1단계: 주요 플랫폼 URL 패턴 검사
    if _check_major_platform_patterns(url):
        return True
    
    # 2단계: 일반 키워드 URL 패턴 검사
    if _check_general_keyword_patterns(url):
        return True
    
    # 3단계: 웹 크롤링 및 콘텐츠 분석 (비동기로 처리)
    # 실제 크롤링은 별도 함수에서 처리하므로 여기서는 기본적으로 True 반환
    return True


def _check_major_platform_patterns(url: str) -> bool:
    """1단계: 주요 채용 플랫폼 URL 패턴 검사"""
    import re
    
    # 주요 플랫폼 패턴 정의
    platform_patterns = [
        # 원티드
        r'wanted\.co\.kr/wd/\d+',
        r'wanted\.co\.kr/company/\d+/jobs/\d+',
        
        # 사람인
        r'saramin\.co\.kr/zf_user/jobs/view\?rec_idx=\d+',
        r'saramin\.co\.kr/zf_user/jobs/relay/view\?rec_idx=\d+',
        
        # 프로그래머스
        r'career\.programmers\.co\.kr/job_positions/\d+',
        r'programmers\.co\.kr/job_positions/\d+',
        
        # 점핏
        r'jumpit\.co\.kr/position/\d+',
        r'jumpit\.co\.kr/position/[^/]+',
        
        # 잡코리아
        r'jobkorea\.co\.kr/Recruit/GI_Read/\d+',
        r'jobkorea\.co\.kr/Recruit/Co_Read/\d+',
        
        # 인크루트
        r'incruit\.com/jobdb_info/job_post\.asp\?job=\d+',
        r'incruit\.com/jobdb_info/job_post\.asp\?job_id=\d+',
        
        # 잡플래닛
        r'jobplanet\.co\.kr/job_postings/\d+',
        r'jobplanet\.co\.kr/companies/\d+/jobs/\d+',
        
        # 로켓펀치
        r'rocketpunch\.com/jobs/\d+',
        r'rocketpunch\.com/companies/[^/]+/jobs/\d+',
        
        # 슈퍼루키
        r'superrookie\.co\.kr/job/\d+',
        r'superrookie\.co\.kr/company/[^/]+/job/\d+',
        
        # 크래프톤
        r'krafton\.com/careers/job/\d+',
        
        # 네이버
        r'naver\.com/recruit/\d+',
        
        # 카카오
        r'kakao\.com/careers/\d+',
        r'kakao\.com/jobs/\d+',
        
        # 토스
        r'toss\.careers/jobs/\d+',
        r'toss\.careers/positions/\d+',
        
        # 쿠팡
        r'coupang\.com/careers/jobs/\d+',
        
        # 배달의민족
        r'woowahan\.com/careers/\d+',
        r'woowahan\.com/jobs/\d+',
        
        # 당근마켓
        r'daangn\.com/careers/\d+',
        r'daangn\.com/jobs/\d+',
        
        # 스타트업 관련
        r'startup\.kr/jobs/\d+',
        r'startup\.kr/recruit/\d+',
    ]
    
    for pattern in platform_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False


def _check_general_keyword_patterns(url: str) -> bool:
    """2단계: 일반 키워드 URL 패턴 검사"""
    import re
    
    # URL 경로에서 채용 관련 키워드 검사
    url_lower = url.lower()
    
    # 채용 관련 키워드들
    job_keywords = [
        'recruit', 'recruitment', 'hiring', 'careers', 'jobs', 'job',
        'position', 'opportunity', 'vacancy', 'opening',
        '채용', '모집', '구인', '채용정보', '채용공고',
        'career', 'employment', 'work', 'apply', 'application'
    ]
    
    # URL 경로에 키워드가 포함되어 있는지 확인
    for keyword in job_keywords:
        if keyword in url_lower:
            # 단순 키워드 매칭이 아닌 경로 기반 매칭
            path_pattern = rf'[/\-_]({keyword})[/\-_]'
            if re.search(path_pattern, url_lower):
                return True
    
    return False


def analyze_job_posting_content(html_content: str) -> dict:
    """
    3단계: 웹 페이지 콘텐츠 분석
    HTML 내용을 분석하여 채용공고 여부를 판단
    """
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html_content, 'html.parser')
    analysis_result = {
        'is_job_posting': False,
        'confidence_score': 0,
        'detected_features': []
    }
    
    score = 0
    features = []
    
    # 1. JSON-LD 스키마 확인 (가장 확실한 신호)
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                score += 100
                features.append('JSON-LD JobPosting schema')
                break
        except:
            continue
    
    # 2. HTML title 태그 확인
    title = soup.find('title')
    if title:
        title_text = title.get_text().lower()
        title_keywords = ['채용', '모집', 'recruit', 'hiring', 'careers', 'jobs', 'position']
        for keyword in title_keywords:
            if keyword in title_text:
                score += 20
                features.append(f'Title contains "{keyword}"')
                break
    
    # 3. Meta 태그 확인 (Open Graph, Twitter Card)
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        content = meta.get('content', '').lower()
        property_name = meta.get('property', '').lower()
        
        # Open Graph 태그
        if 'og:title' in property_name or 'og:description' in property_name:
            og_keywords = ['채용', '모집', 'recruit', 'hiring', 'careers', 'jobs']
            for keyword in og_keywords:
                if keyword in content:
                    score += 15
                    features.append(f'OG meta contains "{keyword}"')
                    break
        
        # 일반 meta description
        if meta.get('name') == 'description':
            desc_keywords = ['채용', '모집', 'recruit', 'hiring', 'careers', 'jobs', '지원']
            for keyword in desc_keywords:
                if keyword in content:
                    score += 10
                    features.append(f'Meta description contains "{keyword}"')
                    break
    
    # 4. 본문 키워드 분석
    body_text = soup.get_text().lower()
    
    # 채용공고 특유의 키워드들
    job_specific_keywords = [
        '주요업무', '담당업무', '업무내용', '업무', 'job description',
        '자격요건', '지원자격', '자격', 'qualification', 'requirement',
        '우대사항', '우대조건', '우대', 'preferred', 'bonus',
        '근무조건', '근무환경', '근무', 'work environment',
        '복리혜택', '복지', 'benefit', 'welfare',
        '지원하기', '지원', 'apply', 'application',
        '마감일', '마감', 'deadline', 'closing',
        '경력', '신입', 'experience', 'entry level',
        '연봉', '급여', 'salary', 'compensation'
    ]
    
    keyword_count = 0
    for keyword in job_specific_keywords:
        if keyword in body_text:
            keyword_count += 1
    
    # 키워드 개수에 따른 점수 부여
    if keyword_count >= 8:
        score += 40
        features.append(f'High keyword density ({keyword_count} job-related keywords)')
    elif keyword_count >= 5:
        score += 25
        features.append(f'Medium keyword density ({keyword_count} job-related keywords)')
    elif keyword_count >= 3:
        score += 15
        features.append(f'Low keyword density ({keyword_count} job-related keywords)')
    
    # 5. 폼 요소 확인 (지원 버튼, 입력 폼 등)
    forms = soup.find_all('form')
    for form in forms:
        form_text = form.get_text().lower()
        if any(keyword in form_text for keyword in ['지원', 'apply', 'submit', '신청']):
            score += 15
            features.append('Application form detected')
            break
    
    # 6. 버튼 텍스트 확인
    buttons = soup.find_all(['button', 'a'], class_=re.compile(r'btn|button', re.I))
    for button in buttons:
        button_text = button.get_text().lower()
        if any(keyword in button_text for keyword in ['지원', 'apply', '신청', '지원하기']):
            score += 10
            features.append('Apply button detected')
            break
    
    # 최종 판정
    analysis_result['confidence_score'] = score
    analysis_result['detected_features'] = features
    
    # 점수 기준으로 채용공고 여부 판정
    if score >= 50:  # 높은 신뢰도
        analysis_result['is_job_posting'] = True
    elif score >= 30:  # 중간 신뢰도
        analysis_result['is_job_posting'] = True
    elif score >= 20:  # 낮은 신뢰도 (추가 검증 필요)
        analysis_result['is_job_posting'] = True
    
    return analysis_result


def validate_session_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    세션 생성 데이터 검증
    """
    if not isinstance(data, dict):
        raise ValidationError("세션 데이터는 딕셔너리 형태여야 합니다.")
    
    # 필수 필드 검증 (jobDescriptionUrl, questions만 필수로)
    required_fields = ['jobDescriptionUrl', 'questions']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValidationError(f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}")
    
    # URL 검증
    job_url = data.get('jobDescriptionUrl', '').strip()
    if not validate_job_posting_url(job_url):
        raise ValidationError(f"유효하지 않은 채용공고 URL입니다: {job_url}")
    
    # 질문 데이터 검증
    questions = data.get('questions', [])
    if not isinstance(questions, list) or len(questions) == 0:
        raise ValidationError("최소 1개 이상의 질문이 필요합니다.")
    
    if len(questions) > 3:
        raise ValidationError("질문은 최대 3개까지만 허용됩니다.")
    
    # 각 질문 검증
    for i, question in enumerate(questions):
        if not isinstance(question, str) or not question.strip():
            raise ValidationError(f"질문 {i+1}이 유효하지 않습니다.")
        
        if len(question.strip()) < 5:
            raise ValidationError(f"질문 {i+1}이 너무 짧습니다. (최소 5자)")
        
        if len(question.strip()) > 500:
            raise ValidationError(f"질문 {i+1}이 너무 깁니다. (최대 500자)")
    
    # 길이 데이터 검증
    lengths = data.get('lengths', [])
    if lengths:
        if len(lengths) != len(questions):
            raise ValidationError("질문과 길이 데이터의 개수가 일치하지 않습니다.")
        
        for i, length in enumerate(lengths):
            try:
                length_int = int(length) if length else 1000
                if length_int < 100 or length_int > 2000:
                    raise ValidationError(f"질문 {i+1}의 답변 길이가 유효하지 않습니다. (100-2000자)")
            except (ValueError, TypeError):
                raise ValidationError(f"질문 {i+1}의 답변 길이가 숫자가 아닙니다.")
    
    return data


def validate_question_data(question: str, length: int = None) -> Dict[str, Any]:
    """
    질문 데이터 검증
    
    Args:
        question (str): 검증할 질문
        length (int): 답변 길이 제한
        
    Returns:
        dict: 검증된 질문 데이터
        
    Raises:
        ValidationError: 데이터가 유효하지 않은 경우
    """
    if not isinstance(question, str) or not question.strip():
        raise ValidationError("유효하지 않은 질문입니다.")
    
    question = question.strip()
    
    if len(question) < 5:
        raise ValidationError("질문이 너무 짧습니다. (최소 5자)")
    
    if len(question) > 500:
        raise ValidationError("질문이 너무 깁니다. (최대 500자)")
    
    # 부적절한 내용 체크
    inappropriate_keywords = ['욕설', '비하', '차별']  # 실제로는 더 많은 키워드 필요
    if any(keyword in question.lower() for keyword in inappropriate_keywords):
        raise ValidationError("부적절한 내용이 포함된 질문입니다.")
    
    # 길이 검증
    if length is not None:
        try:
            length = int(length)
            if length < 100 or length > 2000:
                raise ValidationError("답변 길이는 100자에서 2000자 사이여야 합니다.")
        except (ValueError, TypeError):
            raise ValidationError("답변 길이는 숫자여야 합니다.")
    
    return {
        'question': question,
        'length': length or 500
    }


def validate_revision_request(revision_text: str) -> str:
    """
    수정 요청 텍스트 검증
    
    Args:
        revision_text (str): 수정 요청 내용
        
    Returns:
        str: 검증된 수정 요청 텍스트
        
    Raises:
        ValidationError: 텍스트가 유효하지 않은 경우
    """
    if not isinstance(revision_text, str) or not revision_text.strip():
        raise ValidationError("수정 요청 내용이 필요합니다.")
    
    revision_text = revision_text.strip()
    
    if len(revision_text) < 5:
        raise ValidationError("수정 요청이 너무 짧습니다. (최소 5자)")
    
    if len(revision_text) > 1000:
        raise ValidationError("수정 요청이 너무 깁니다. (최대 1000자)")
    
    return revision_text


def validate_json_data(json_string: str) -> Dict[str, Any]:
    """
    JSON 문자열 검증 및 파싱
    
    Args:
        json_string (str): JSON 문자열
        
    Returns:
        dict: 파싱된 데이터
        
    Raises:
        ValidationError: JSON이 유효하지 않은 경우
    """
    if not isinstance(json_string, str) or not json_string.strip():
        raise ValidationError("JSON 데이터가 필요합니다.")
    
    try:
        data = json.loads(json_string)
        return data
    except json.JSONDecodeError as e:
        raise ValidationError(f"유효하지 않은 JSON 형식입니다: {str(e)}")


def validate_session_id(session_id: str) -> str:
    """
    세션 ID 검증
    
    Args:
        session_id (str): 검증할 세션 ID
        
    Returns:
        str: 검증된 세션 ID
        
    Raises:
        ValidationError: 세션 ID가 유효하지 않은 경우
    """
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValidationError("세션 ID가 필요합니다.")
    
    session_id = session_id.strip()
    
    # UUID 형식 검증 (간단한 형태)
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    if not uuid_pattern.match(session_id):
        raise ValidationError("유효하지 않은 세션 ID 형식입니다.")
    
    return session_id


def validate_question_index(index: Any, max_questions: int = 3) -> int:
    """
    질문 인덱스 검증
    
    Args:
        index: 검증할 인덱스
        max_questions (int): 최대 질문 수
        
    Returns:
        int: 검증된 인덱스
        
    Raises:
        ValidationError: 인덱스가 유효하지 않은 경우
    """
    try:
        index = int(index)
    except (ValueError, TypeError):
        raise ValidationError("질문 인덱스는 숫자여야 합니다.")
    
    if index < 0:
        raise ValidationError("질문 인덱스는 0 이상이어야 합니다.")
    
    if index >= max_questions:
        raise ValidationError(f"질문 인덱스는 {max_questions-1} 이하여야 합니다.")
    
    return index


def sanitize_text(text: str) -> str:
    """
    텍스트 정리 및 안전화
    
    Args:
        text (str): 정리할 텍스트
        
    Returns:
        str: 정리된 텍스트
    """
    if not isinstance(text, str):
        return ""
    
    # 기본 정리
    text = text.strip()
    
    # 연속된 공백을 하나로 변경
    text = re.sub(r'\s+', ' ', text)
    
    # 특수 문자 제거 (필요에 따라 조정)
    text = re.sub(r'[^\w\s가-힣.,!?()[\]{}":;-]', '', text)
    
    return text 
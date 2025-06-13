from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging
import time

logger = logging.getLogger(__name__)

def crawl_job_description(url):
    """채용공고 URL에서 JD 텍스트 크롤링 (Selenium으로 동적 컨텐츠 처리)"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 브라우저 창을 띄우지 않음
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # 웹 드라이버 설정
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)
        # 페이지 로딩 대기 (필요에 따라 시간 조절)
        time.sleep(3) 

        # 페이지 소스 가져오기
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        driver.quit()

        # 일반적인 채용공고 컨테이너 선택자들
        common_selectors = [
            # 직무 설명 관련
            'div.job-description', 'div.job_description', 'div.job-detail',
            'div.job-detail-content', 'div.job-detail-body', 'div.job-detail-desc',
            'div.recruit-detail', 'div.recruit-content', 'div.recruit-body',
            'div.position-detail', 'div.position-content', 'div.position-body',
            'div.career-detail', 'div.career-content', 'div.career-body',
            'div.employment-detail', 'div.employment-content', 'div.employment-body',
            'div.hire-detail', 'div.hire-content', 'div.hire-body',
            'div.recruit-info', 'div.recruit-desc', 'div.recruit-text',
            'div.job-info', 'div.job-desc', 'div.job-text',
            'div.position-info', 'div.position-desc', 'div.position-text',
            'div.career-info', 'div.career-desc', 'div.career-text',
            'div.employment-info', 'div.employment-desc', 'div.employment-text',
            'div.hire-info', 'div.hire-desc', 'div.hire-text',
            # 메인 컨텐츠 영역
            'main', 'article', 'section',
            # 일반적인 컨텐츠 영역
            'div.content', 'div.contents', 'div.container',
            'div.main', 'div.main-content', 'div.main-body',
            'div.detail', 'div.detail-content', 'div.detail-body',
            'div.info', 'div.info-content', 'div.info-body'
        ]
        
        # 불필요한 요소들 제거
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
            
        # 선택자로 텍스트 추출 시도
        for selector in common_selectors:
            content = soup.select_one(selector)
            if content:
                # 불필요한 요소들 추가 제거
                for tag in content.find_all(['button', 'a', 'form', 'input']):
                    tag.decompose()
                    
                text = content.get_text(strip=True, separator='\n')
                # 텍스트가 충분히 긴 경우에만 반환
                if len(text) > 100:
                    logger.info(f"채용공고 추출 성공 - URL: {url}, 선택자: {selector}")
                    return text
        
        # 선택자로 찾지 못한 경우, 전체 텍스트에서 의미있는 부분 추출
        text = soup.get_text(strip=True, separator='\n')
        # 줄바꿈으로 분리하여 긴 텍스트 블록만 추출
        blocks = [block for block in text.split('\n') if len(block) > 100]
        if blocks:
            result = '\n'.join(blocks)
            logger.info(f"채용공고 추출 성공 (전체 텍스트) - URL: {url}")
            return result
            
        logger.warning(f"채용공고 추출 실패 - URL: {url}")
        return None
        
    except Exception as e:
        logger.error(f"채용공고 크롤링 실패 (Selenium): {str(e)}")
        # Selenium 오류 시 driver가 살아있을 수 있으므로 종료 처리
        if 'driver' in locals() and driver:
            driver.quit()
        return None 
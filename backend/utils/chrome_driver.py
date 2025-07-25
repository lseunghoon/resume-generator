"""
ChromeDriver 유틸리티 - 안전한 ChromeDriver 초기화 및 관리
"""

import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from config.settings import CHROME_DRIVER_PATH # 설정 파일 대신 직접 경로를 사용

logger = logging.getLogger(__name__)


class ChromeDriverError(Exception):
    """ChromeDriver 관련 예외"""
    pass


def get_chrome_options(headless=True, user_agent=None):
    """봇 탐지를 우회하는 옵션이 강화된 Chrome 옵션 설정"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    # --- 봇 탐지 우회 및 안정성을 위한 핵심 옵션들 ---
    # User-Agent 설정 (우선순위: 전달받은 user_agent > 기본값)
    if user_agent:
        chrome_options.add_argument(f"user-agent={user_agent}")
    else:
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    
    # 자동화 제어 기능을 비활성화하여 Selenium임을 숨김
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 그래픽 가속 및 샌드박스 관련 옵션 (서버 환경 안정성)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # 기타 옵션
    chrome_options.add_argument("--window-size=1920x1080") # 헤드리스 모드에서 실제 화면 크기를 지정해주는 것이 좋음
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    return chrome_options


def create_chrome_driver(user_agent=None):
    """ChromeDriver 인스턴스 생성 - 신뢰도 높은 순서로 재배치"""
    
    logger.info("ChromeDriver 초기화 시작...")
    
    # ==============================================================================
    # 방법 1: backend 폴더에 위치한 수동 다운로드 드라이버 (가장 확실한 방법)
    # ==============================================================================
    # 64비트용 chromedriver.exe를 backend 폴더에 위치시켰습니다.
    manual_driver_path = './chromedriver.exe' # backend 폴더 기준
    
    if os.path.exists(manual_driver_path):
        logger.info(f"방법 1 시도: 수동 지정 경로 ({manual_driver_path})")
        try:
            options = get_chrome_options(user_agent=user_agent)
            service = Service(executable_path=manual_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            logger.info("성공: 프로젝트 내 수동 지정된 ChromeDriver를 사용합니다.")
            return driver
        except Exception as e:
            logger.error(f"수동 지정 경로({manual_driver_path}) ChromeDriver 실패: {str(e)}")
            logger.error(f"예외 타입: {type(e).__name__}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
    else:
        logger.warning(f"정보: 프로젝트 내 수동 지정된 ChromeDriver가 없습니다. ({manual_driver_path})")

    # ==============================================================================
    # 방법 2: 시스템 PATH에서 찾기 (수동으로 드라이버 경로를 PATH에 등록한 경우)
    # ==============================================================================
    logger.info("방법 2 시도: 시스템 PATH에서 ChromeDriver 찾기")
    try:
        options = get_chrome_options(user_agent=user_agent)
        # Service 객체를 명시적으로 사용하지 않으면 Selenium이 PATH에서 chromedriver를 찾습니다.
        driver = webdriver.Chrome(options=options)
        logger.info("성공: 시스템 PATH에 등록된 ChromeDriver를 사용합니다.")
        return driver
    except Exception as e:
        logger.error(f"시스템 PATH에서 ChromeDriver 찾기 실패: {str(e)}")
        logger.error(f"예외 타입: {type(e).__name__}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")

    # ==============================================================================
    # 방법 3: webdriver-manager (최후의 수단)
    # ==============================================================================
    logger.info("방법 3 시도: webdriver-manager 사용")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        options = get_chrome_options(user_agent=user_agent)
        # webdriver-manager의 최신 버전은 캐시 관리 기능이 개선되었습니다.
        # 명시적으로 버전을 지정하지 않고 자동으로 찾게 합니다.
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("성공: webdriver-manager로 ChromeDriver를 생성했습니다.")
        return driver
    except Exception as e:
        logger.error(f"webdriver-manager를 사용한 ChromeDriver 생성 실패: {str(e)}")
        logger.error(f"예외 타입: {type(e).__name__}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
    
    # 모든 방법이 실패한 경우
    error_msg = "모든 ChromeDriver 초기화 방법이 실패했습니다. 수동으로 chromedriver.exe를 설치해주세요."
    logger.error(error_msg)
    raise ChromeDriverError(error_msg)


def safe_create_chrome_driver():
    """안전한 ChromeDriver 생성 (예외 처리 포함)"""
    try:
        return create_chrome_driver()
    except Exception as e:
        logger.error(f"ChromeDriver 생성 실패: {e}")
        raise ChromeDriverError(f"ChromeDriver 초기화 실패: {e}")


def test_chrome_driver():
    """ChromeDriver 테스트 함수"""
    try:
        driver = safe_create_chrome_driver()
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        logger.info(f"ChromeDriver 테스트 성공: {title}")
        return True
    except Exception as e:
        logger.error(f"ChromeDriver 테스트 실패: {e}")
        return False 
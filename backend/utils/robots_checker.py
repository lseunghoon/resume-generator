"""
책임감 있는 Robots.txt 검증 서비스
크롤링의 4대 원칙을 준수하는 안전한 robots.txt 검증 로직
"""

import logging
from urllib.parse import urlparse
from urllib import robotparser
import requests
import time

# === 1. 나는 누구인지 밝힌다 ===
# 우리 서비스의 크롤러를 위한 고유 User-Agent를 정의합니다.
# 문제가 생겼을 때 사이트 관리자가 이 이름을 보고 우리 서비스임을 알 수 있게 합니다.
CUSTOM_USER_AGENT = "IloveresumeBot/1.0 (+https://github.com/iloveresume)" 
REQUEST_TIMEOUT = 5  # robots.txt 요청 시 타임아웃 (초)

logger = logging.getLogger(__name__)

def check_robots_txt_permission(url: str) -> tuple[bool, int]:
    """
    책임감 있는 방식으로 robots.txt를 검사하여 크롤링 허용 여부와 지연 시간을 반환합니다.

    Args:
        url: 크롤링할 대상 URL

    Returns:
        tuple[bool, int]: (크롤링 허용 여부, 권장 지연 시간(초))
    """
    try:
        # URL 앞뒤 공백 제거
        url = url.strip()
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        # === 2. 규칙을 엄격하게 따른다 (안전한 기본값) ===
        # 기본적으로는 허용하지 않음
        can_crawl = False
        crawl_delay = 1  # 기본 지연 시간 1초

        # === 3. 상대방을 배려한다 (타임아웃 설정) ===
        try:
            response = requests.get(robots_url, timeout=REQUEST_TIMEOUT, headers={'User-Agent': CUSTOM_USER_AGENT})
            
            # robots.txt가 존재하지 않거나 접근이 금지된 경우 -> 크롤링 허용 (명시적 금지 규칙이 없음)
            if response.status_code in [401, 403, 404]:
                logger.info(f"robots.txt를 찾을 수 없음 ({response.status_code}). 크롤링을 허용합니다.")
                return True, crawl_delay
            
            response.raise_for_status()  # 다른 HTTP 오류는 예외 발생
            
            # === 4. User-Agent 통일 및 규칙 해석 ===
            rp = robotparser.RobotFileParser()
            rp.parse(response.text.splitlines())
            
            # Crawl-Delay 준수
            delay_from_robots = rp.crawl_delay(CUSTOM_USER_AGENT)
            if delay_from_robots:
                crawl_delay = max(crawl_delay, delay_from_robots)  # robots.txt 권장 시간과 기본값 중 더 긴 시간을 선택

            # 우리 봇의 User-Agent로 먼저 검사하고, 없으면 '*'로 검사
            can_crawl = rp.can_fetch(CUSTOM_USER_AGENT, url)
            
            logger.info(f"robots.txt 분석 완료: URL='{url}', User-Agent='{CUSTOM_USER_AGENT}', 허용여부={can_crawl}, 지연시간={crawl_delay}초")

            return can_crawl, crawl_delay

        # === 5. 실패를 현명하게 처리한다 (엄격한 예외 처리) ===
        except requests.RequestException as e:
            logger.error(f"robots.txt 다운로드 실패: {e}. 안전을 위해 크롤링을 거부합니다.")
            return False, crawl_delay  # 다운로드 실패 시 거부
        except Exception as e:
            logger.error(f"robots.txt 처리 중 알 수 없는 오류: {e}. 안전을 위해 크롤링을 거부합니다.")
            return False, crawl_delay  # 기타 모든 예외 발생 시 거부

    except Exception as e:
        logger.error(f"URL 파싱 오류: {e}. 크롤링을 거부합니다.")
        return False, 1


def get_custom_user_agent() -> str:
    """우리 봇의 User-Agent를 반환합니다."""
    return CUSTOM_USER_AGENT 
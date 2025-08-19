/**
 * 스크롤 관련 유틸리티 함수들
 */

/**
 * 특정 요소로 부드럽게 스크롤하는 함수
 * @param {string} elementId - 스크롤할 요소의 ID
 * @param {number} maxRetries - 최대 재시도 횟수 (기본값: 3)
 * @param {number} retryDelay - 재시도 간격 (기본값: 200ms)
 * @returns {Promise<boolean>} - 스크롤 성공 여부
 */
export const scrollToElement = async (elementId, maxRetries = 3, retryDelay = 200) => {
  return new Promise((resolve) => {
    let retryCount = 0;
    
    const attemptScroll = () => {
      const element = document.getElementById(elementId);
      
      if (!element) {
        if (retryCount < maxRetries) {
          retryCount++;
          setTimeout(attemptScroll, retryDelay);
        } else {
          console.warn(`요소를 찾을 수 없습니다: ${elementId}`);
          resolve(false);
        }
        return;
      }
      
      try {
        // 요소가 화면에 보이는지 확인
        const rect = element.getBoundingClientRect();
        const isVisible = rect.top >= 0 && rect.bottom <= window.innerHeight;
        
        if (isVisible) {
          // 이미 화면에 보이는 경우
          resolve(true);
          return;
        }
        
        // 부드러운 스크롤 실행
        element.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        });
        
        // 스크롤 완료 확인
        let scrollCompleted = false;
        let scrollTimeout;
        
        const checkScrollComplete = () => {
          if (scrollCompleted) return;
          
          const currentRect = element.getBoundingClientRect();
          const isAtTop = Math.abs(currentRect.top) < 10; // 10px 이내면 완료로 간주
          
          if (isAtTop) {
            scrollCompleted = true;
            clearTimeout(scrollTimeout);
            resolve(true);
          } else {
            // 스크롤이 아직 진행 중
            requestAnimationFrame(checkScrollComplete);
          }
        };
        
        // 스크롤 시작
        setTimeout(() => {
          checkScrollComplete();
        }, 100);
        
        // 최대 대기 시간 (5초)
        scrollTimeout = setTimeout(() => {
          if (!scrollCompleted) {
            scrollCompleted = true;
            console.warn(`스크롤 시간 초과: ${elementId}`);
            resolve(false);
          }
        }, 5000);
        
      } catch (error) {
        console.error(`스크롤 중 오류 발생: ${error.message}`);
        resolve(false);
      }
    };
    
    // 첫 번째 시도
    attemptScroll();
  });
};

/**
 * 페이지 최상단으로 스크롤하는 함수
 * @param {boolean} smooth - 부드러운 스크롤 여부 (기본값: true)
 * @returns {Promise<void>}
 */
export const scrollToTop = async (smooth = true) => {
  return new Promise((resolve) => {
    try {
      if (smooth) {
        window.scrollTo({ 
          top: 0, 
          left: 0, 
          behavior: 'smooth' 
        });
        
        // 스크롤 완료 확인
        const checkComplete = () => {
          if (window.pageYOffset === 0) {
            resolve();
          } else {
            requestAnimationFrame(checkComplete);
          }
        };
        
        setTimeout(checkComplete, 100);
      } else {
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
        resolve();
      }
    } catch (error) {
      console.error('최상단 스크롤 중 오류:', error);
      resolve();
    }
  });
};

/**
 * 특정 섹션으로 스크롤하는 함수 (Header 메뉴용)
 * @param {string} sectionId - 섹션 ID
 * @param {string} currentPath - 현재 페이지 경로
 * @param {Function} navigate - React Router navigate 함수
 * @returns {Promise<boolean>} - 스크롤 성공 여부
 */
export const scrollToSection = async (sectionId, currentPath, navigate) => {
  if (currentPath !== '/') {
    // 다른 페이지에서 온 경우 랜딩페이지로 이동 후 스크롤
    navigate('/', { 
      state: { scrollTo: sectionId },
      replace: false  // false로 변경하여 히스토리 누적 방지
    });
    return true;
  } else {
    // 랜딩페이지에서는 바로 스크롤
    return await scrollToElement(sectionId);
  }
};

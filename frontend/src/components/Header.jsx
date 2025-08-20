import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import LoginButton from './LoginButton';
import { scrollToSection, scrollToTop } from '../utils/scrollUtils';
import './Header.css';

const Header = ({ user, onLogout, sidebarOpen, onSidebarToggle, currentStep, onLogoClick, onLoginSuccess }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  // 단계별 인디케이터 계산
  const getProgressWidth = () => {
    const path = location.pathname;
    
    // 단계별 진행률 계산 (7단계)
    if (path === '/job-info') {
      // 회사명, 직무, 주요업무, 자격요건, 우대사항 입력 페이지 (1-5단계)
      if (currentStep !== undefined) {
        const progress = ((currentStep + 1) / 7) * 100;
        console.log('JobInfoInputPage 진행률:', currentStep + 1, '/', 7, '=', progress + '%');
        return `${progress}%`;
      }
      console.log('JobInfoInputPage currentStep undefined, 기본값 사용');
      return '14.28%'; // 기본값 (1/7 단계)
    } else if (path === '/file-upload') {
      console.log('FileUploadPage 진행률: 6/7 = 85.71%');
      return '85.71%'; // 6/7 단계 (파일 업로드)
    } else if (path === '/question') {
      console.log('QuestionPage 진행률: 7/7 = 100%');
      return '100%'; // 7/7 단계 (문항 입력)
    } else if (path === '/result') {
      console.log('ResultPage 진행률: 완료 = 100%');
      return '100%'; // 완료
    }
    
    console.log('알 수 없는 경로:', path, '진행률: 0%');
    return '0%';
  };

  console.log('Header 컴포넌트 렌더링됨:', {
    user: user?.email,
    pathname: location.pathname,
    currentStep: currentStep,
    progressWidth: getProgressWidth()
  });

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleProfileClick = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleLogoClick = async () => {
    console.log('로고 클릭됨!');
    console.log('현재 경로:', location.pathname);
    
    // localStorage에서 모든 입력 관련 데이터 삭제
    console.log('로고 클릭 - localStorage 클리어 실행');
    localStorage.removeItem('resultPageActiveTab');
    localStorage.removeItem('pendingSessionDelete');
    localStorage.removeItem('mockJobDataFilled');
    localStorage.removeItem('useMockApi');
    localStorage.removeItem('auth_redirect_path'); // 인증 관련 리다이렉트 경로도 클리어
    
    // App.js의 currentStep 초기화 호출
    if (onLogoClick) {
      onLogoClick();
    }
    
    // 현재 페이지가 랜딩페이지가 아닌 경우에만 navigate
    if (location.pathname !== '/') {
      console.log('로고 클릭 - state 정보 초기화하여 홈페이지로 이동');
      // 완전한 새로고침으로 모든 상태 초기화
      window.location.href = '/';
      return;
    }
    
    // 스크롤 유틸리티 함수 사용하여 최상단으로 이동
    try {
      await scrollToTop(true);
      console.log('로고 클릭 - 스크롤 최상단 이동 완료');
    } catch (error) {
      console.error('스크롤 이동 중 오류:', error);
    }
  };

  const handleLogoutClick = () => {
    setIsDropdownOpen(false);
    onLogout();
  };

  const handleLoginSuccess = () => {
    // 로그인 성공 시 사용자 상태를 업데이트하는 로직을 여기에 추가
    // 예: 사용자 정보를 다시 가져오거나, 로그인 상태를 확인하는 함수를 호출
    console.log('로그인 성공!');
    // 사용자 상태 업데이트 로직
    if (onLoginSuccess) {
      onLoginSuccess();
    }
  };

  const handleMenuClick = async (sectionId) => {
    try {
      console.log(`메뉴 클릭: ${sectionId}, 현재 경로: ${location.pathname}`);
      
      // 스크롤 유틸리티 함수 사용
      const success = await scrollToSection(sectionId, location.pathname, navigate);
      
      if (success) {
        console.log(`${sectionId} 섹션으로 스크롤 완료`);
      } else {
        console.warn(`${sectionId} 섹션으로 스크롤 실패`);
      }
    } catch (error) {
      console.error('메뉴 클릭 처리 중 오류:', error);
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left-section">
          <div 
            className="logo-section" 
            onClick={handleLogoClick}
            style={{ cursor: 'pointer', pointerEvents: 'auto' }}
          >
            <img 
              src="/assets/logo_sseojum.svg" 
              alt="서줌 로고" 
              className="logo-image"
            />
          </div>
          
          {/* 헤더 메뉴들 - 로고 오른쪽 (모든 페이지에서 표시) */}
          <div className="header-menu-section">
            <button className="header-menu-btn" onClick={() => handleMenuClick('service-intro')}>서비스 소개</button>
            <button className="header-menu-btn" onClick={() => handleMenuClick('feedback')}>피드백</button>
          </div>
        </div>
        
        <div className="header-right-section">
          {user ? (
            // 로그인된 사용자: 사이드바 토글 버튼과 프로필 섹션
            <>
              {/* 사이드바 토글 버튼 */}
              <button className="header-sidebar-toggle-btn" onClick={onSidebarToggle}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 6H20M4 12H20M4 18H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              
              {/* 프로필 섹션 */}
              <div className="profile-section" ref={dropdownRef}>
                <div 
                  className="profile-icon"
                  onClick={handleProfileClick}
                >
                  {user.picture ? (
                    <img 
                      src={user.picture} 
                      alt="프로필" 
                      className="profile-image"
                    />
                  ) : (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="8" r="5" fill="#9CA3AF"/>
                      <path d="M20 21C20 16.5817 16.4183 13 12 13C13 7.58172 4 16.5817 4 21" stroke="#9CA3AF" strokeWidth="2"/>
                    </svg>
                  )}
                </div>
                
                {isDropdownOpen && (
                  <div className="dropdown-menu">
                    <div 
                      className="dropdown-item"
                      onClick={handleLogoutClick}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M16 17L21 12L16 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M21 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      로그아웃
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            // 로그인 안된 사용자: 로그인 페이지가 아닐 때만 로그인 버튼 표시
            location.pathname !== '/login' && (
              <LoginButton onLoginSuccess={handleLoginSuccess} />
            )
          )}
        </div>
      </div>
      {['/job-info', '/file-upload', '/question', '/result'].includes(location.pathname) && (
        <div 
          className="active-indicator" 
          style={{ width: getProgressWidth() }}
        ></div>
      )}
    </header>
  );
};

export default Header; 
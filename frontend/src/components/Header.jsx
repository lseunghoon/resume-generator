import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Header.css';

const Header = ({ user, onLogout, sidebarOpen, onSidebarToggle, currentStep, onLogoClick }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  // 단계별 인디케이터 계산
  const getProgressWidth = () => {
    const path = location.pathname;
    const search = location.search;
    
    // 단계별 진행률 계산 (7단계)
    if (path === '/') {
      // 회사명, 직무, 주요업무, 자격요건, 우대사항 입력 페이지 (5단계)
      if (currentStep !== undefined) {
        return `${((currentStep + 1) / 7) * 100}%`;
      }
      return '14.28%'; // 기본값 (1/7 단계)
    } else if (path === '/file-upload') {
      return '85.71%'; // 6/7 단계 (파일 업로드)
    } else if (path === '/question') {
      return '100%'; // 7/7 단계 (문항 입력)
    } else if (path === '/result') {
      return '100%'; // 완료
    }
    
    return '0%';
  };

  console.log('Header 컴포넌트 렌더링됨, 사용자:', user?.email);

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



  const handleLogoClick = () => {
    console.log('로고 클릭됨!');
    console.log('현재 경로:', location.pathname);
    
    // localStorage에서 모든 입력 관련 데이터 삭제
    console.log('로고 클릭 - localStorage 클리어 실행');
    localStorage.removeItem('resultPageActiveTab');
    localStorage.removeItem('pendingSessionDelete');
    localStorage.removeItem('mockJobDataFilled');
    localStorage.removeItem('useMockApi');
    
    // 완전한 새로고침으로 홈페이지로 이동 (모든 페이지에서 동일하게 작동)
    console.log('로고 클릭 - 완전한 새로고침으로 홈페이지로 이동');
    window.location.href = '/';
  };

  const handleLogoutClick = () => {
    setIsDropdownOpen(false);
    onLogout();
  };

  return (
    <header className="header">
      <div className="header-content">
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
        
        {user && (
          <div className="header-right-section">
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
                    <path d="M20 21C20 16.5817 16.4183 13 12 13C7.58172 13 4 16.5817 4 21" stroke="#9CA3AF" strokeWidth="2"/>
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
          </div>
        )}
      </div>
      {location.pathname !== '/' && (
        <div 
          className="active-indicator" 
          style={{ width: getProgressWidth() }}
        ></div>
      )}
    </header>
  );
};

export default Header; 
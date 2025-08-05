import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Header.css';

const Header = ({ user, onLogout }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

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

  const handleSessionListClick = () => {
    setIsDropdownOpen(false);
    navigate('/');
  };

  const handleLogoClick = () => {
    console.log('로고 클릭됨!');
    console.log('현재 경로:', location.pathname);
    
    // 현재 경로가 / 이면 새로고침, 아니면 홈으로 이동
    if (location.pathname === '/') {
      console.log('홈페이지에서 새로고침 실행 - 첫 번째 단계로 초기화됨');
      window.location.reload();
    } else {
      console.log('다른 페이지에서 홈으로 이동');
      navigate('/', { replace: true });
    }
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
            src="/assets/logo_test.svg" 
            alt="로고" 
            className="logo-image"
          />
          <div className="active-indicator"></div>
        </div>
        
        {user && (
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
                  onClick={handleSessionListClick}
                >
                  자기소개서 목록
                </div>
                <div 
                  className="dropdown-item"
                  onClick={handleLogoutClick}
                >
                  로그아웃
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

export default Header; 
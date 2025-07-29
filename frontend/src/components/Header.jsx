import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Header.css';

const Header = ({ 
  progress = 0, 
  showRestartButton = false, 
  onRestart,
  currentStep = 0 // 현재 단계 정보 추가
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogoClick = () => {
    console.log('Header - 로고 클릭됨');
    console.log('Header - 현재 경로:', location.pathname);
    
    // 링크입력페이지에서 로고 클릭 시 홈으로 이동
    if (location.pathname === '/link-upload') {
      console.log('Header - 홈으로 이동');
      navigate('/');
    } else {
      // 모든 페이지에서 로고 클릭 시 홈으로 이동 후 새로고침
      console.log('Header - 홈으로 이동 후 새로고침');
      navigate('/', { replace: true });
      // 약간의 지연 후 새로고침 실행
      setTimeout(() => {
        window.location.reload();
      }, 100);
    }
  };

  return (
    <div className="header">
      <div className="header-content">
        <div 
          className="logo-area" 
          onClick={handleLogoClick} 
          style={{cursor: 'pointer'}}
          onMouseDown={(e) => e.preventDefault()} // 더블클릭 선택 방지
        >
          <img 
            src="/assets/logo_test.svg" 
            alt="로고" 
            className="logo-image"
            draggable={false} // 드래그 방지
            onError={(e) => {
              // SVG 파일이 없는 경우 폴백 텍스트 표시
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'inline';
            }}
          />
          <span className="logo-fallback" style={{display: 'none'}}>
            Logo area
          </span>
        </div>

        <div className="header-right">
          {showRestartButton && (
            <button className="restart-button" onClick={onRestart}>
              다시 시작
            </button>
          )}
        </div>
      </div>
      <div className="progress-container">
        <div className="progress-bar" style={{ width: `${progress}%` }}></div>
      </div>
    </div>
  );
};

export default Header; 
import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Header.css';

const Header = ({ 
  progress = 0, 
  showRestartButton = false, 
  onRestart
}) => {
  const navigate = useNavigate();

  const handleLogoClick = () => {
    navigate('/');
  };

  return (
    <div className="header">
      <div className="header-content">
        <div className="logo-area" onClick={handleLogoClick} style={{cursor: 'pointer'}}>
          <img 
            src="/assets/logo_test.svg" 
            alt="로고" 
            className="logo-image"
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
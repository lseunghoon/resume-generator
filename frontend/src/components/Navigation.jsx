import React from 'react';
import './Navigation.css';

const Navigation = ({ 
  canGoBack = false,
  onGoBack
}) => {
  return (
    <div className="navigation-container">
      {/* 좌측 뒤로가기 화살표 */}
      <div className="navigation-left">
        {canGoBack && (
          <button 
            className="nav-arrow-button back"
            onClick={onGoBack}
            title="이전 단계"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 18L9 12L15 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        )}
      </div>

      {/* 우측 빈 공간 (균형을 위해) */}
      <div className="navigation-right">
      </div>
    </div>
  );
};

export default Navigation; 
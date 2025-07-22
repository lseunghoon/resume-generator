import React from 'react';
import './Header.css';

const Header = ({ progress = 0, showRestartButton = false, onRestart }) => {
  return (
    <div className="header">
      <div className="header-content">
        <div className="logo-area">
          Logo area
        </div>
        {showRestartButton && (
          <button className="restart-button" onClick={onRestart}>
            다시 시작
          </button>
        )}
      </div>
      <div className="progress-container">
        <div className="progress-bar" style={{ width: `${progress}%` }}></div>
      </div>
    </div>
  );
};

export default Header; 
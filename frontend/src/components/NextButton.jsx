import React from 'react';
import './NextButton.css';

const NextButton = ({ 
  text = '다음',
  disabled = false,
  loading = false,
  onClick
}) => {
  return (
    <div className="next-button-container">
      <button 
        className={`next-button ${disabled || loading ? 'disabled' : 'active'}`}
        onClick={onClick}
        disabled={disabled || loading}
      >
        {loading ? (
          <>
            <div className="spinner"></div>
            <span>처리 중...</span>
          </>
        ) : (
          text
        )}
      </button>
    </div>
  );
};

export default NextButton; 
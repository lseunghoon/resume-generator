import React from 'react';
import './NextButton.css';

const NextButton = ({ 
  text = '다음',
  disabled = false,
  onClick
}) => {
  return (
    <div className="next-button-container">
      <button 
        className={`next-button ${disabled ? 'disabled' : 'active'}`}
        onClick={onClick}
        disabled={disabled}
      >
        {text}
      </button>
    </div>
  );
};

export default NextButton; 
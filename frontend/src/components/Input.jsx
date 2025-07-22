import React from 'react';
import './Input.css';

const Input = ({ 
  placeholder, 
  value, 
  onChange, 
  disabled = false,
  error,
  hasIcon = false,
  iconType = 'send',
  onIconClick,
  className = ''
}) => {
  return (
    <div className={`input-container ${className}`}>
      <div className={`input-wrapper ${error ? 'input-error' : ''} ${disabled ? 'input-disabled' : ''}`}>
        <div className="input-content">
          <input
            type="text"
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            disabled={disabled}
            className="input-field"
          />
          {hasIcon && (
            <button 
              className={`input-icon ${disabled ? 'input-icon-disabled' : ''}`}
              onClick={onIconClick}
              disabled={disabled}
            >
              {iconType === 'send' && '→'}
            </button>
          )}
        </div>
      </div>
      {error && <div className="input-error-message">{error}</div>}
    </div>
  );
};

export default Input; 
import React, { forwardRef } from 'react';
import './Input.css';

const Input = forwardRef(({ 
  placeholder, 
  value, 
  onChange, 
  onKeyPress,
  disabled = false,
  error,
  hasIcon = false,
  iconType = 'send',
  onIconClick,
  className = ''
}, ref) => {
  return (
    <div className={`input-container ${className}`}>
      <div className={`input-wrapper ${error ? 'input-error' : ''} ${disabled ? 'input-disabled' : ''}`}>
        <div className="input-content">
          <input
            ref={ref}
            type="text"
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            onKeyPress={onKeyPress}
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
});

export default Input; 
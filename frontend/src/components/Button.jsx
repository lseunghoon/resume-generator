import React from 'react';
import './Button.css';

const Button = ({ 
  children, 
  variant = 'primary', 
  disabled = false, 
  onClick, 
  className = '',
  type = 'button',
  loading = false
}) => {
  const getButtonClass = () => {
    const baseClass = 'btn';
    const variantClass = `btn-${variant}`;
    const disabledClass = (disabled || loading) ? 'btn-disabled' : '';
    return `${baseClass} ${variantClass} ${disabledClass} ${className}`.trim();
  };

  return (
    <button
      type={type}
      className={getButtonClass()}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading && <div className="btn-loading-spinner"></div>}
      {children}
    </button>
  );
};

export default Button; 
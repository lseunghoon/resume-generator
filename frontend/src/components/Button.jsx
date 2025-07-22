import React from 'react';
import './Button.css';

const Button = ({ 
  children, 
  variant = 'primary', 
  disabled = false, 
  onClick, 
  className = '',
  type = 'button'
}) => {
  const getButtonClass = () => {
    const baseClass = 'btn';
    const variantClass = `btn-${variant}`;
    const disabledClass = disabled ? 'btn-disabled' : '';
    return `${baseClass} ${variantClass} ${disabledClass} ${className}`.trim();
  };

  return (
    <button
      type={type}
      className={getButtonClass()}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

export default Button; 
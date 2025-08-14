import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginButton.css';

const LoginButton = () => {
  const navigate = useNavigate();

  const handleLoginClick = () => {
    navigate('/login');
  };

  return (
    <button 
      className="login-button" 
      onClick={handleLoginClick}
      type="button"
    >
      로그인
    </button>
  );
};

export default LoginButton;

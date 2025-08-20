import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { checkGoogleSession, handleAutoGoogleSignIn } from '../services/api';
import './LoginButton.css';

const LoginButton = ({ onLoginSuccess }) => {
  const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(false);

  const handleLoginClick = async () => {
    if (isProcessing) return; // 중복 클릭 방지
    
    setIsProcessing(true);
    
    try {
      console.log('로그인 버튼 클릭 - Google 세션 확인 중...');
      
      // 1. Google OAuth 세션 확인
      const hasSession = await checkGoogleSession();
      
      if (hasSession) {
        console.log('Google 세션 발견 - 자동 로그인 시도...');
        
        // 2. 세션이 있으면 자동 로그인 처리
        const result = await handleAutoGoogleSignIn();
        
        if (result && result.success) {
          console.log('자동 로그인 성공!');
          // 로그인 성공 시 콜백 호출
          if (onLoginSuccess) {
            onLoginSuccess(result.user);
          }
        } else {
          throw new Error('자동 로그인 실패');
        }
      } else {
        console.log('Google 세션 없음 - 로그인 페이지로 이동...');
        
        // 3. 세션이 없으면 로그인 페이지로 이동
        navigate('/login');
      }
    } catch (error) {
      console.error('로그인 처리 중 오류:', error);
      
      // 오류 발생 시 로그인 페이지로 이동
      navigate('/login');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <button 
      className="login-button" 
      onClick={handleLoginClick}
      type="button"
      disabled={isProcessing}
    >
      {isProcessing ? '로그인 중...' : '로그인'}
    </button>
  );
};

export default LoginButton;

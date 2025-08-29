import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { signInWithGoogle, signInWithKakao } from '../services/api';
import './Login.css';

const Login = () => {
  const [googleLoading, setGoogleLoading] = useState(false);
  const [kakaoLoading, setKakaoLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    setError('');

    try {
      await signInWithGoogle();
      // Google OAuth 페이지로 리다이렉트되므로 여기서는 아무것도 하지 않음
    } catch (error) {
      setError(error.message);
      setGoogleLoading(false);
    }
  };

  const handleKakaoLogin = async () => {
    setKakaoLoading(true);
    setError('');

    try {
      await signInWithKakao();
      // Kakao OAuth 페이지로 리다이렉트되므로 여기서는 아무것도 하지 않음
    } catch (error) {
      setError(error.message);
      setKakaoLoading(false);
    }
  };

  const handleSignUp = () => {
    // 회원가입 페이지로 이동 (추후 구현)
    console.log('Sign up clicked');
  };

  return (
    <div className="login-container">
      {/* 메인 콘텐츠 */}
      <div className="login-main">
        <div className="login-content">
          <h1 className="welcome-title">자소서 퀄리티 200% 향상,<br/>바로 시작해 보세요!</h1>
          
                     <p className="login-subtitle">별도의 가입 절차 없이<br/>기존 계정으로 이용할 수 있습니다.</p>
          
          <div className="social-login-buttons">
            <button 
              className="social-login-btn google-btn"
              onClick={handleGoogleLogin}
              disabled={googleLoading || kakaoLoading}
            >
              {googleLoading && (
                <div className="login-spinner">
                  <div className="spinner"></div>
                </div>
              )}
              <svg className="google-icon" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Google로 계속하기
            </button>
          
            <button 
              className="social-login-btn kakao-btn"
              onClick={handleKakaoLogin}
              disabled={kakaoLoading || googleLoading}
            >
              {kakaoLoading && (
                <div className="login-spinner">
                  <div className="spinner"></div>
                </div>
              )}
              <svg className="kakao-icon" viewBox="0 0 24 24" width="18" height="18">
                <path fill="#3C1E1E" d="M12 3C7.03 3 3 6.25 3 10.25c0 2.57 1.68 4.83 4.19 6.16l-.87 3.19c-.08.3.23.53.49.36l3.77-2.51c.47.07.96.11 1.42.11 4.97 0 9-3.25 9-7.25S16.97 3 12 3z"/>
              </svg>
              카카오로 계속하기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login; 
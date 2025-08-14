import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { signInWithGoogle } from '../services/api';
import Navigation from './Navigation';
import './Login.css';

const Login = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError('');

    try {
      await signInWithGoogle();
      // Google OAuth 페이지로 리다이렉트되므로 여기서는 아무것도 하지 않음
    } catch (error) {
      setError(error.message);
      setLoading(false);
    }
  };

  const handleKakaoLogin = () => {
    // Kakao 로그인 기능은 추후 구현 예정
    console.log('Kakao login clicked');
  };

  const handleSignUp = () => {
    // 회원가입 페이지로 이동 (추후 구현)
    console.log('Sign up clicked');
  };

  const handleGoBack = () => {
    navigate(-1); // 이전 페이지로 이동
  };

  return (
    <div className="login-container">
      {/* Navigation */}
      <Navigation 
        canGoBack={true}
        onGoBack={handleGoBack}
      />
      
      {/* 메인 콘텐츠 */}
      <div className="login-main">
        <div className="login-content">
          <h1 className="welcome-title">다시 오신 것을 환영합니다</h1>
          
          <p className="continue-text">또는 다음으로 계속하기</p>
          
          <div className="social-login-buttons">
            <button 
              className="social-login-btn google-btn"
              onClick={handleGoogleLogin}
              disabled={loading}
            >
              {loading && <div className="login-btn-spinner"></div>}
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
            >
              <svg className="kakao-icon" viewBox="0 0 24 24" width="18" height="18">
                <path fill="#FEE500" d="M12 3C6.48 3 2 6.48 2 12c0 4.41 2.87 8.14 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.82.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.14 22 16.41 22 12c0-5.52-4.48-10-10-10z"/>
              </svg>
              카카오로 계속하기
            </button>
          </div>
          
          <p className="signup-text">
            계정이 없으신가요? <span className="signup-link" onClick={handleSignUp}>회원가입</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login; 
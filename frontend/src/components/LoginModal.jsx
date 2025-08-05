import React from 'react';
import { createPortal } from 'react-dom';
import { signInWithGoogle } from '../services/api';
import './LoginModal.css';

const LoginModal = ({ onClose }) => {
  const handleGoogleLogin = async () => {
    try {
      await signInWithGoogle();
      // 로그인 성공 시 모달은 자동으로 닫힘 (페이지 새로고침으로 인해)
    } catch (error) {
      console.error('Google 로그인 오류:', error);
    }
  };

  const handleOverlayClick = (e) => {
    // 오버레이 클릭 시에만 모달 닫기
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

    return createPortal(
    <div className="login-modal-overlay" onClick={handleOverlayClick}>
      <div 
        className="login-modal" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="login-modal-header">
          <h2>로그인이 필요합니다</h2>
          <p>자기소개서 생성을 위해 Google 계정으로 로그인해주세요</p>
        </div>
        
        <div className="login-modal-content">
          <button 
            className="google-login-btn"
            onClick={handleGoogleLogin}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Google로 로그인
          </button>
        </div>
        
 
      </div>
    </div>,
    document.body
  );
};

export default LoginModal; 
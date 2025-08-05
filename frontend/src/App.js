import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import './App.css';

// Pages
import JobInfoInputPage from './pages/JobInfoInputPage';
import FileUploadPage from './pages/FileUploadPage';
import QuestionPage from './pages/QuestionPage';
import ResultPage from './pages/ResultPage';

// Components
import DevTools from './components/DevTools';
import Header from './components/Header';
import OAuthCallback from './components/OAuthCallback';

// API
import { getAuthToken, getCurrentUser } from './services/api';

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // 앱 시작 시 인증 상태 확인
    const checkAuth = async () => {
      // URL에서 Google OAuth 콜백 코드 확인
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      
      // URL 해시에서 access_token 확인 (Supabase OAuth 방식)
      const hash = window.location.hash.substring(1);
      const hashParams = new URLSearchParams(hash);
      const accessToken = hashParams.get('access_token');
      
      if (accessToken) {
        console.log('Google OAuth access_token 발견:', accessToken.substring(0, 20) + '...');
        try {
          // 토큰 저장
          localStorage.setItem('authToken', accessToken);
          
          // 사용자 정보 조회
          const response = await fetch('http://localhost:5000/api/v1/auth/user', {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
            },
          });
          
          const data = await response.json();
          console.log('사용자 정보 조회 응답:', data);
          
                               if (data.success && data.user) {
            setUser(data.user);
            
            // URL에서 해시 파라미터 제거하고 루트 경로로 리다이렉트 (JobInfoInputPage)
            window.history.replaceState({}, document.title, '/');
           } else {
            console.error('사용자 정보 조회 실패:', data);
          }
        } catch (error) {
          console.error('Google OAuth 토큰 처리 오류:', error);
        }
      } else if (code) {
        console.log('Google OAuth 콜백 코드 발견:', code);
        try {
          // Google OAuth 콜백 처리
          const response = await fetch('http://localhost:5000/api/v1/auth/google/callback', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code }),
          });
          
          const data = await response.json();
          console.log('Google OAuth 콜백 응답:', data);
          
          if (data.success && data.session && data.session.access_token) {
            // 토큰 저장
            localStorage.setItem('authToken', data.session.access_token);
            setUser(data.user);
            
            // URL에서 코드 파라미터 제거
            window.history.replaceState({}, document.title, window.location.pathname);
          } else {
            console.error('Google OAuth 콜백 실패:', data);
          }
        } catch (error) {
          console.error('Google OAuth 콜백 처리 오류:', error);
        }
      } else {
        // 일반적인 토큰 확인
        const token = getAuthToken();
        if (token) {
          try {
            const userData = await getCurrentUser();
            setUser(userData.user);
          } catch (error) {
            console.error('인증 확인 실패:', error);
            // 토큰이 유효하지 않으면 제거
            localStorage.removeItem('authToken');
          }
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  // handleLoginSuccess 함수는 현재 사용되지 않으므로 제거

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('authToken');
    setShowLoginModal(false); // 모달 상태 초기화
    
    // 로그아웃 후 홈페이지로 이동 (새로고침 없이)
    navigate('/', { replace: true });
  };

  const handleShowLoginModal = () => {
    setShowLoginModal(true);
  };

  const handleCloseLoginModal = () => {
    setShowLoginModal(false);
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '16px',
        color: '#666'
      }}>
        로딩 중...
      </div>
    );
  }

  // 로그인되지 않은 경우에도 JobInfoInputPage를 표시하되, 로그인 모달을 함께 표시
  // JobInfoInputPage 내부에서 로그인 상태를 확인하여 모달을 표시할 예정

  return (
    <div className={`App ${showLoginModal ? 'modal-open' : ''}`}>
      <Header user={user} onLogout={handleLogout} />
      <Routes>
        <Route path="/" element={<JobInfoInputPage onShowLoginModal={handleShowLoginModal} onCloseLoginModal={handleCloseLoginModal} showLoginModal={showLoginModal} />} />
        <Route path="/auth/callback" element={<OAuthCallback />} />
        <Route path="/file-upload" element={<FileUploadPage />} />
        <Route path="/question" element={<QuestionPage />} />
        <Route path="/result" element={<ResultPage />} />
      </Routes>
      
      {/* 개발자 도구 (개발 환경에서만 표시) */}
      <DevTools />
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;

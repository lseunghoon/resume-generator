import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import './App.css';

// Pages
import JobInfoInputPage from './pages/JobInfoInputPage';
import FileUploadPage from './pages/FileUploadPage';
import QuestionPage from './pages/QuestionPage';
import ResultPage from './pages/ResultPage';
import PrivacyPage from './pages/PrivacyPage';

// Components
import DevTools from './components/DevTools';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import OAuthCallback from './components/OAuthCallback';
import LoginModal from './components/LoginModal';

// API
import { getCurrentUser } from './services/api';
import { supabase } from './services/supabaseClient';

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [sidebarRefreshTrigger, setSidebarRefreshTrigger] = useState(0);
  const navigate = useNavigate();

  // 인증 상태 확인
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // 1) Supabase 세션 확인
        const { data: { session }, error } = await supabase.auth.getSession();

        if (error) {
          console.error('세션 확인 오류:', error);
        }

        // 2) 세션 없으면 로그인 모달 표시
        if (!session) {
          setShowLoginModal(true);
          setUser(null);
          setLoading(false);
          return;
        }

        // 3) 토큰 발급처(iss) 검증 – 기대값: `${REACT_APP_SUPABASE_URL}/auth/v1`
        const expectedIss = `${(process.env.REACT_APP_SUPABASE_URL || '').replace(/\/$/, '')}/auth/v1`;
        let isIssuerValid = false;
        try {
          const token = session.access_token;
          const payload = JSON.parse(atob(token.split('.')[1] || '')) || {};
          isIssuerValid = payload.iss === expectedIss;
        } catch (e) {
          isIssuerValid = false;
        }

        if (!isIssuerValid) {
          // 비파괴 모드: 즉시 로그아웃하지 않고 원인 파악을 위해 로그만 남기고 모달 표시
          const tokenIss = (function(){
            try { return JSON.parse(atob((session.access_token || '').split('.')[1] || ''))?.iss || null; } catch(_) { return null; }
          })();
          console.warn('[Auth] ISS mismatch detected. Keeping session for inspection', {
            tokenIss,
            expectedIss,
            href: typeof window !== 'undefined' ? window.location.href : ''
          });
          // 디버깅 편의를 위해 전역으로 노출
          if (typeof window !== 'undefined') {
            window.__AUTH_DEBUG__ = { tokenIss, expectedIss };
          }
          // 여기서는 반환하지 않고, 서버에 사용자 정보 요청을 이어갑니다.
        }

        // 4) 서버에 현재 사용자 요청
        try {
          const userData = await getCurrentUser();
          if (userData && userData.user) {
            setUser(userData.user);
          } else {
            setShowLoginModal(true);
          }
        } catch (error) {
          console.error('사용자 정보 조회 실패:', error);
          setShowLoginModal(true);
        }
      } catch (error) {
        console.error('인증 확인 실패:', error);
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  // handleLoginSuccess 함수는 현재 사용되지 않으므로 제거

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut();
    } catch (error) {
      console.error('로그아웃 오류:', error);
    }
    
    setUser(null);
    setShowLoginModal(false); // 모달 상태 초기화
    setSidebarOpen(false); // 사이드바 닫기
    
    // 로그아웃 후 홈페이지로 이동 (새로고침 없이)
    navigate('/', { replace: true });
  };

  const handleShowLoginModal = () => {
    setShowLoginModal(true);
  };

  const handleCloseLoginModal = () => {
    setShowLoginModal(false);
  };

  const handleSidebarToggle = () => {
    console.log('토글 버튼 클릭됨, 현재 상태:', sidebarOpen);
    setSidebarOpen(!sidebarOpen);
  };

  const handleLogoClick = () => {
    console.log('App.js: 로고 클릭됨, currentStep 초기화');
    setCurrentStep(0); // currentStep을 0으로 초기화
  };

  if (loading) {
    return (
      <div className="app-loading-container">
        <div className="app-loading-spinner"></div>
      </div>
    );
  }

  // 로그인되지 않은 경우에도 JobInfoInputPage를 표시하되, 로그인 모달을 함께 표시
  // JobInfoInputPage 내부에서 로그인 상태를 확인하여 모달을 표시할 예정

  return (
    <div className={`App ${showLoginModal ? 'modal-open' : ''}`}>
      <Header 
        user={user} 
        onLogout={handleLogout} 
        sidebarOpen={sidebarOpen}
        onSidebarToggle={handleSidebarToggle}
        currentStep={currentStep}
        onLogoClick={handleLogoClick}
      />
      
      {/* 사이드바 (로그인된 사용자만 표시) */}
      {user && (
        <Sidebar 
          user={user} 
          isOpen={sidebarOpen} 
          onToggle={handleSidebarToggle}
          refreshTrigger={sidebarRefreshTrigger}
        />
      )}
      
      {/* 메인 콘텐츠 영역 */}
      <div className={`main-content ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
                       <Routes>
                 <Route path="/" element={<JobInfoInputPage onShowLoginModal={handleShowLoginModal} onCloseLoginModal={handleCloseLoginModal} showLoginModal={showLoginModal} currentStep={currentStep} setCurrentStep={setCurrentStep} onSidebarRefresh={() => setSidebarRefreshTrigger(prev => prev + 1)} />} />
                 <Route path="/auth/callback" element={<OAuthCallback />} />
                 <Route path="/file-upload" element={<FileUploadPage />} />
                 <Route path="/question" element={<QuestionPage onSidebarRefresh={() => setSidebarRefreshTrigger(prev => prev + 1)} />} />
                 <Route path="/result" element={<ResultPage onSidebarRefresh={() => setSidebarRefreshTrigger(prev => prev + 1)} />} />
                 <Route path="/privacy" element={<PrivacyPage />} />
               </Routes>
      </div>
      
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

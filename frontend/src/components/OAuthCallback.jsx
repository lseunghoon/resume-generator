import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const OAuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // OAuth 콜백 처리 로직은 App.js에서 이미 처리되므로
    // 여기서는 단순히 홈페이지로 리다이렉트
    console.log('OAuth 콜백 페이지 로드됨');
    
    // 잠시 후 홈페이지로 이동 (App.js에서 토큰 처리가 완료될 시간을 줌)
    const timer = setTimeout(() => {
      navigate('/', { replace: true });
    }, 100);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      fontSize: '16px',
      color: '#666'
    }}>
      로그인 처리 중...
    </div>
  );
};

export default OAuthCallback; 
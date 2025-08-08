import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../services/supabaseClient';

const OAuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    console.log('OAuth 콜백 페이지 로드됨');
    let cleanedUp = false;
    let navigated = false;

    const goHome = () => {
      if (!navigated) {
        navigated = true;
        navigate('/', { replace: true });
      }
    };

    // 1) 즉시 세션이 이미 존재하면 바로 이동
    (async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session && !cleanedUp) {
          goHome();
        }
      } catch (_) {}
    })();

    // 2) auth 상태 변화를 구독하여 SIGNED_IN 시점에 이동 (Edge 대응)
    const { data: subscription } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN' && !cleanedUp) {
        goHome();
      }
    });

    // 3) 폴백: 짧은 폴링으로 최대 5초까지 대기
    const startedAt = Date.now();
    const interval = setInterval(async () => {
      if (cleanedUp || navigated) return;
      if (Date.now() - startedAt > 5000) {
        // 타임아웃: 홈으로 보내 UI가 멈추지 않도록 함
        goHome();
        return;
      }
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          goHome();
        }
      } catch (_) {}
    }, 300);

    return () => {
      cleanedUp = true;
      clearInterval(interval);
      subscription?.subscription?.unsubscribe?.();
    };
  }, [navigate]);

  // 로그인 모달과 어울리는 가벼운 오버레이 스피너만 표시
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(255,255,255,0.6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 2000
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: '50%',
        border: '3px solid #e1e5e9', borderTopColor: '#3b82f6',
        animation: 'spin 1s linear infinite'
      }} />
    </div>
  );
};

export default OAuthCallback; 
import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '../services/supabaseClient';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    console.log('OAuth 콜백 페이지 로드됨');
    let cleanedUp = false;
    let navigated = false;

    // next 파라미터 확인 및 정규화
    const rawLocal = localStorage.getItem('auth_redirect_path');
    const rawQuery = searchParams.get('next');
    const normalizeNext = (value) => {
      let v = value || '/';
      try {
        if (v.startsWith('/login')) {
          const url = new URL(v, window.location.origin);
          v = url.searchParams.get('next') || '/';
        }
      } catch (_) {}
      // 화이트리스트 체크
      const allowed = ['/', '/job-info', '/file-upload', '/question', '/result'];
      if (!allowed.some((p) => v.startsWith(p))) {
        v = '/';
      }
      return v;
    };

    const nextPath = normalizeNext(rawLocal || rawQuery || '/');
    console.log('OAuthCallback - localStorage의 auth_redirect_path:', rawLocal);
    console.log('OAuthCallback - URL의 next 파라미터:', rawQuery);
    console.log('OAuthCallback - 최종 이동할 경로:', nextPath);
    console.log('OAuthCallback - 전체 URL:', window.location.href);

    const goToNext = () => {
      if (!navigated) {
        navigated = true;
        console.log('OAuthCallback - 이동할 경로:', nextPath);
        
        // localStorage에서 next 경로를 사용했다면 제거
        if (rawLocal) {
          localStorage.removeItem('auth_redirect_path');
          console.log('OAuthCallback - localStorage에서 auth_redirect_path 제거됨');
        }
        
        navigate(nextPath, { replace: true });
      }
    };

    // 1) 즉시 세션이 이미 존재하면 바로 이동
    (async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session && !cleanedUp) {
          goToNext();
        }
      } catch (_) {}
    })();

    // 2) auth 상태 변화를 구독하여 SIGNED_IN 시점에 이동 (Edge 대응)
    const { data: subscription } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN' && !cleanedUp) {
        goToNext();
      }
    });

    // 3) 폴백: 짧은 폴링으로 최대 5초까지 대기
    const startedAt = Date.now();
    const interval = setInterval(async () => {
      if (cleanedUp || navigated) return;
      if (Date.now() - startedAt > 5000) {
        // 타임아웃: next 페이지로 보내 UI가 멈추지 않도록 함
        goToNext();
        return;
      }
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          goToNext();
        }
      } catch (_) {}
    }, 300);

    return () => {
      cleanedUp = true;
      clearInterval(interval);
      subscription?.subscription?.unsubscribe?.();
    };
  }, [navigate, searchParams]);

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
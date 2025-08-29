import { mockApi, enableMockApi, disableMockApi, isMockApiEnabled } from './mockApi';
import { supabase } from './supabaseClient';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Mock API 모드 확인 (런타임에 확인)
const checkMockMode = () => isMockApiEnabled();

// API 호출을 위한 래퍼(wrapper) 함수
const fetchWithAuth = async (url, options = {}) => {
  // 1. API를 호출하기 '직전에' 현재 세션 정보를 가져옵니다.
  //    이 과정에서 supabase-js가 토큰이 만료되었다면 자동으로 갱신해줍니다.
  const { data: { session }, error } = await supabase.auth.getSession();

  if (error || !session) {
    console.log('세션이 없거나 오류가 발생했습니다:', error);
    try {
      const currentPath = window.location.pathname + window.location.search;
      const existing = localStorage.getItem('auth_redirect_path');

      const extractNext = (pathWithQuery) => {
        try {
          const url = new URL(pathWithQuery, window.location.origin);
          return url.searchParams.get('next') || url.pathname;
        } catch (_) {
          return pathWithQuery;
        }
      };

      let intended = currentPath;

      // 로그인/콜백 화면에서는 기존 intended를 보존
      if (currentPath.startsWith('/login') || currentPath.startsWith('/auth/callback')) {
        intended = existing || '/';
      }

      // 의도 경로가 로그인 URL 형태라면 next를 추출
      if (intended && intended.startsWith('/login')) {
        intended = extractNext(intended) || '/';
      }

      // 화이트리스트 이외 경로는 루트로 폴백
      const allowedPrefixes = ['/', '/job-info', '/file-upload', '/question', '/result'];
      if (!allowedPrefixes.some((p) => intended.startsWith(p))) {
        intended = '/';
      }

      localStorage.setItem('auth_redirect_path', intended);
      window.location.href = `/login?next=${encodeURIComponent(intended)}`;
    } catch (_) {
      window.location.href = '/login';
    }
    throw new Error('인증되지 않았습니다.');
  }

  // 2. '방금 받은' 최신 토큰을 헤더에 담습니다.
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}`,
    ...options.headers,
  };

  // 3. 요청을 보냅니다.
  const response = await fetch(url, { ...options, headers });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `API 호출 실패: ${response.status}`);
  }

  // 4. 응답을 JSON으로 파싱
  try {
    const jsonData = await response.json();
    return jsonData;
  } catch (parseError) {
    console.error('JSON 파싱 오류:', {
      url,
      status: response.status,
      parseError: parseError.message
    });
    throw new Error(`응답 파싱 실패: ${parseError.message}`);
  }
};

// 공통 API 호출 함수
const apiCall = async (endpoint, options = {}) => {
  if (checkMockMode()) {
    console.log('Mock API 모드 사용 중');
    return mockApi[endpoint] || (() => Promise.reject(new Error('Mock API not found')));
  }

  const url = `${API_BASE_URL}${endpoint}`;
  return fetchWithAuth(url, options);
};



// Google OAuth 로그인
export const signInWithGoogle = async () => {
  try {
    console.debug('Google OAuth 로그인 시작 (supabase-js)');
    const redirectTo = `${window.location.origin}/auth/callback`;
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo }
    });
    if (error) throw error;
    // 일부 환경에서 자동 리다이렉트가 되지 않으면 수동으로 이동
    if (data?.url) {
      window.location.href = data.url;
    }
  } catch (error) {
    console.error('Google OAuth 오류:', error);
    throw error;
  }
};

// Kakao OAuth 로그인
export const signInWithKakao = async () => {
  try {
    console.debug('Kakao OAuth 로그인 시작 (supabase-js)');
    const redirectTo = `${window.location.origin}/auth/callback`;
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'kakao',
      options: { redirectTo }
    });
    if (error) throw error;
    // 일부 환경에서 자동 리다이렉트가 되지 않으면 수동으로 이동
    if (data?.url) {
      window.location.href = data.url;
    }
  } catch (error) {
    console.error('Kakao OAuth 오류:', error);
    throw error;
  }
};

// 로그아웃
export const signOut = async () => {
  try {
    await supabase.auth.signOut();
  } catch (error) {
    console.error('로그아웃 오류:', error);
  }
};

// 사용자 정보 조회
export const getCurrentUser = async () => {
  return fetchWithAuth(`${API_BASE_URL}/api/v1/auth/user`);
};

// 사용자별 자기소개서 세션 목록 조회
export const getUserSessions = async () => {
  // 재시도 로직 추가
  const maxRetries = 3;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/user/sessions`);
      console.log('getUserSessions 응답:', response);
      return response;
    } catch (error) {
      console.log(`getUserSessions 시도 ${attempt}/${maxRetries} 실패:`, error.message);
      
      // 에러 메시지 분석 및 사용자 친화적 메시지 생성
      let userFriendlyMessage = '세션 목록을 불러오는데 실패했습니다.';
      
      if (error.message.includes('Server disconnected')) {
        userFriendlyMessage = '데이터베이스 연결이 일시적으로 끊어졌습니다. 잠시 후 다시 시도해주세요.';
      } else if (error.message.includes('timeout')) {
        userFriendlyMessage = '요청 시간이 초과되었습니다. 네트워크 상태를 확인하고 다시 시도해주세요.';
      } else if (error.message.includes('500')) {
        userFriendlyMessage = '서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
      } else if (error.message.includes('인증')) {
        userFriendlyMessage = '로그인이 필요합니다. 다시 로그인해주세요.';
      }
      
      // 사용자에게 에러 메시지 표시 (선택사항)
      if (attempt === maxRetries) {
        // 마지막 시도에서 실패한 경우에만 사용자에게 알림
        console.error('최종 실패:', userFriendlyMessage);
        // 여기에 사용자 알림 로직을 추가할 수 있습니다 (예: toast, alert 등)
      }
      
      if (attempt === maxRetries) {
        // 마지막 시도에서도 실패하면 사용자 친화적 에러 메시지와 함께 에러 던지기
        const enhancedError = new Error(userFriendlyMessage);
        enhancedError.originalError = error;
        enhancedError.attempts = attempt;
        throw enhancedError;
      }
      
      // 1초 대기 후 재시도
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
};

// 채용정보 직접 입력 (새로운 방식)
export const submitJobInfo = async (jobInfo) => {
  if (checkMockMode()) {
    return mockApi.submitJobInfo(jobInfo);
  }

  return fetchWithAuth(`${API_BASE_URL}/api/v1/job-info`, {
    method: 'POST',
    body: JSON.stringify(jobInfo),
  });
};

// 세션 생성 (자기소개서 생성)
export const createSession = async (data) => {
  if (checkMockMode()) {
    return mockApi.createSession(data);
  }

  const formData = new FormData();
  
  // 파일들 추가
  if (data.uploadedFiles && data.uploadedFiles.length > 0) {
    data.uploadedFiles.forEach((file, index) => {
      formData.append('files', file);
    });
  }

  // JSON 데이터 추가 (사용자가 입력한 개별 필드들 포함)
  const jsonData = {
    jobDescription: data.jobDescription || '',
    resumeText: data.resumeText || '',
    questions: data.questions || [],
    // 사용자가 직접 입력한 개별 필드들 추가
    companyName: data.companyName || '',
    jobTitle: data.jobTitle || '',
    mainResponsibilities: data.mainResponsibilities || '',
    requirements: data.requirements || '',
    preferredQualifications: data.preferredQualifications || ''
  };
  
  formData.append('data', JSON.stringify(jsonData));

  // FormData를 사용하는 경우를 위한 특별한 fetchWithAuth 호출
  const { data: { session }, error } = await supabase.auth.getSession();

  if (error || !session) {
    console.log('세션이 없거나 오류가 발생했습니다:', error);
    window.location.href = '/';
    throw new Error('인증되지 않았습니다.');
  }

  const headers = {
    'Authorization': `Bearer ${session.access_token}`,
    // FormData를 사용할 때는 Content-Type을 설정하지 않음 (브라우저가 자동으로 설정)
  };
  
  console.log('createSession 요청 헤더:', headers);

  const response = await fetch(`${API_BASE_URL}/api/v1/upload`, {
    method: 'POST',
    headers: headers,
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    // 백엔드에서 413 또는 명시 메시지를 내려줄 때 사용자 친화적으로 노출
    const msg = errorData.message || (response.status === 413 ? '첨부파일의 용량이 50mb를 초과했습니다.' : '자기소개서 생성에 실패했습니다');
    throw new Error(msg);
  }

  return response.json();
};

// 자기소개서 결과 조회
export const getCoverLetter = async (sessionId) => {
  if (checkMockMode()) {
    return mockApi.getCoverLetter(sessionId);
  }

  console.log('API: getCoverLetter 호출 - sessionId:', sessionId);
  
  // 재시도 로직 추가
  const maxRetries = 3;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await apiCall(`/api/v1/session/${sessionId}`);
      console.log('API: getCoverLetter 응답:', response);
      return response;
    } catch (error) {
      console.log(`getCoverLetter 시도 ${attempt}/${maxRetries} 실패:`, error.message);
      
      if (attempt === maxRetries) {
        throw error; // 마지막 시도에서도 실패하면 에러 던지기
      }
      
      // 1초 대기 후 재시도
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
};

// 자기소개서 생성 (AI 모델 호출)
export const generate = async ({ sessionId }) => {
  if (checkMockMode()) {
    return mockApi.generate({ sessionId });
  }

  return apiCall(`/api/v1/generate`, {
    method: 'POST',
    body: JSON.stringify({ sessionId }),
  });
};

// 문항 추가
export const addQuestion = async (sessionId, question) => {
  if (checkMockMode()) {
    return mockApi.addQuestion(sessionId, question);
  }

  return apiCall(`/api/v1/sessions/${sessionId}/questions`, {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
};

// 답변 수정
export const reviseAnswer = async (sessionId, questionIndex, revision) => {
  if (checkMockMode()) {
    return mockApi.reviseAnswer(sessionId, questionIndex, revision);
  }

  return apiCall(`/api/v1/revise`, {
    method: 'POST',
    body: JSON.stringify({ 
      sessionId, 
      questionIndex, 
      revisionRequest: revision 
    }),
  });
};



// 세션 삭제
export const deleteSession = async (sessionId) => {
  if (checkMockMode()) {
    return mockApi.deleteSession(sessionId);
  }

  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/session/${sessionId}`, {
    method: 'DELETE',
  });

  console.log('deleteSession 응답:', response);
  return response;
};

// 피드백 제출 API
export const submitFeedback = async (email, message) => {
  try {
    // Mock API 모드 확인
    if (checkMockMode()) {
      console.log('Mock API 모드: 피드백 제출 시뮬레이션');
      // Mock 응답 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 1000));
      return {
        success: true,
        message: '피드백이 성공적으로 전송되었습니다. (Mock)',
        feedbackId: 'mock-feedback-id'
      };
    }

    // 실제 API 호출
    const response = await fetch(`${API_BASE_URL}/api/v1/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, message })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `피드백 제출 실패: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('피드백 제출 오류:', error);
    throw error;
  }
};

// Mock API 모드 제어 함수들
export { enableMockApi, disableMockApi, isMockApiEnabled } from './mockApi';

// Google OAuth 세션 확인
export const checkGoogleSession = () => {
  return new Promise((resolve) => {
    // Google Identity Services가 로드되었는지 확인
    if (window.google && window.google.accounts && window.google.accounts.oauth2) {
      try {
        // 현재 토큰이 있는지 확인
        const token = localStorage.getItem('google_access_token');
        if (token) {
          // 토큰 유효성 검증 (간단한 검증)
          resolve(true);
        } else {
          resolve(false);
        }
      } catch (error) {
        console.log('Google 세션 확인 중 오류:', error);
        resolve(false);
      }
    } else {
      resolve(false);
    }
  });
};

// 자동 Google 로그인 처리
export const handleAutoGoogleSignIn = async () => {
  try {
    // Google Identity Services 초기화
    if (!window.google || !window.google.accounts) {
      throw new Error('Google Identity Services not loaded');
    }

    // Google OAuth 클라이언트 초기화
    const client = window.google.accounts.oauth2.initTokenClient({
      client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID,
      scope: 'openid profile email',
      callback: async (tokenResponse) => {
        if (tokenResponse.access_token) {
          try {
            // 액세스 토큰을 localStorage에 저장
            localStorage.setItem('google_access_token', tokenResponse.access_token);
            
            // 사용자 정보 가져오기
            const userInfo = await fetchGoogleUserInfo(tokenResponse.access_token);
            
            // Supabase에 로그인 처리
            const { data, error } = await supabase.auth.signInWithOAuth({
              provider: 'google',
              options: {
                access_token: tokenResponse.access_token,
                id_token: tokenResponse.id_token,
              }
            });

            if (error) {
              throw error;
            }

            console.log('자동 Google 로그인 성공:', data);
            return { success: true, user: userInfo };
          } catch (error) {
            console.error('자동 Google 로그인 실패:', error);
            throw error;
          }
        }
      },
    });

    // 토큰 요청
    client.requestAccessToken();
  } catch (error) {
    console.error('자동 Google 로그인 초기화 실패:', error);
    throw error;
  }
};

// Google 사용자 정보 가져오기
const fetchGoogleUserInfo = async (accessToken) => {
  try {
    const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user info');
    }

    const userInfo = await response.json();
    return userInfo;
  } catch (error) {
    console.error('Google 사용자 정보 가져오기 실패:', error);
    throw error;
  }
};

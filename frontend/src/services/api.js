import { mockApi, isMockApiEnabled } from './mockApi';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Mock API 모드 확인 (런타임에 확인)
const checkMockMode = () => isMockApiEnabled();

// 공통 API 호출 함수
const apiCall = async (endpoint, options = {}) => {
  if (checkMockMode()) {
    console.log('Mock API 모드 사용 중');
    return mockApi[endpoint] || (() => Promise.reject(new Error('Mock API not found')));
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `API 호출 실패: ${response.status}`);
  }

  return response.json();
};



// 인증 토큰 관리
let authToken = localStorage.getItem('authToken');

export const setAuthToken = (token) => {
  authToken = token;
  localStorage.setItem('authToken', token);
};

export const getAuthToken = () => {
  return authToken || localStorage.getItem('authToken');
};

export const clearAuthToken = () => {
  authToken = null;
  localStorage.removeItem('authToken');
};

// 인증 헤더 생성
const getAuthHeaders = () => {
  const token = getAuthToken();
  console.log('인증 토큰 확인:', token ? '토큰 있음' : '토큰 없음');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

// Google OAuth 로그인
export const signInWithGoogle = async () => {
  try {
    console.log('Google OAuth 로그인 시작');
    
    // 1. Google OAuth URL 가져오기
    console.log('Google OAuth URL 요청 중...');
    const urlResponse = await fetch(`${API_BASE_URL}/api/v1/auth/google/url`);
    console.log('Google OAuth URL 응답 상태:', urlResponse.status);
    
    const urlData = await urlResponse.json();
    console.log('Google OAuth URL 응답 데이터:', urlData);
    
    if (!urlData.success) {
      throw new Error(urlData.message || 'Google OAuth URL 생성에 실패했습니다');
    }
    
    // 2. Google OAuth 페이지로 리다이렉트
    console.log('Google OAuth 페이지로 리다이렉트:', urlData.auth_url);
    window.location.href = urlData.auth_url;
    
  } catch (error) {
    console.error('Google OAuth 오류:', error);
    throw error;
  }
};

// 로그아웃
export const signOut = async () => {
  const token = getAuthToken();
  if (token) {
    try {
      await fetch(`${API_BASE_URL}/api/v1/auth/signout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error('로그아웃 오류:', error);
    }
  }
  
  clearAuthToken();
};

// 사용자 정보 조회
export const getCurrentUser = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error('인증 토큰이 없습니다');
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/user`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || '사용자 정보 조회에 실패했습니다');
  }

  return data;
};

// 사용자별 자기소개서 세션 목록 조회
export const getUserSessions = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error('인증 토큰이 없습니다');
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/user/sessions`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || '세션 목록 조회에 실패했습니다');
  }

  return data;
};

// 채용정보 직접 입력 (새로운 방식)
export const submitJobInfo = async (jobInfo) => {
  if (checkMockMode()) {
    return mockApi.submitJobInfo(jobInfo);
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/job-info`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(jobInfo),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || '채용정보 입력에 실패했습니다');
  }

  return response.json();
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

  // JSON 데이터 추가 (새로운 채용정보 입력 방식 지원)
  const jsonData = {
    jobDescription: data.jobDescription || '',
    resumeText: data.resumeText || '',
    questions: data.questions || []
  };
  
  formData.append('data', JSON.stringify(jsonData));

  const headers = {
    ...getAuthHeaders(),
    // FormData를 사용할 때는 Content-Type을 설정하지 않음 (브라우저가 자동으로 설정)
  };
  
  console.log('createSession 요청 헤더:', headers);

  const response = await fetch(`${API_BASE_URL}/api/v1/upload`, {
    method: 'POST',
    headers: headers,
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
          throw new Error(errorData.message || '자기소개서 생성에 실패했습니다');
  }

  return response.json();
};

// 자기소개서 결과 조회
export const getCoverLetter = async (sessionId) => {
  if (checkMockMode()) {
    return mockApi.getCoverLetter(sessionId);
  }

  console.log('API: getCoverLetter 호출 - sessionId:', sessionId);
  const response = await apiCall(`/api/v1/session/${sessionId}`);
  console.log('API: getCoverLetter 응답:', response);
  return response;
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

  return apiCall(`/api/v1/session/${sessionId}`, {
    method: 'DELETE',
  });
};

// Mock API 모드 제어 함수들
export { enableMockApi, disableMockApi, isMockApiEnabled } from './mockApi';

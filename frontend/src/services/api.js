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
    // 세션이 없거나 오류 발생 시 로그인 페이지로 리다이렉트 또는 에러 처리
    console.log('세션이 없거나 오류가 발생했습니다:', error);
    window.location.href = '/';
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

  return response.json();
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
      
      if (attempt === maxRetries) {
        throw error; // 마지막 시도에서도 실패하면 에러 던지기
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

// Mock API 모드 제어 함수들
export { enableMockApi, disableMockApi, isMockApiEnabled } from './mockApi';

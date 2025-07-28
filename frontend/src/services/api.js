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



// 채용정보 직접 입력 (새로운 방식)
export const submitJobInfo = async (jobInfo) => {
  if (checkMockMode()) {
    return mockApi.submitJobInfo(jobInfo);
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/job-info`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(jobInfo),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || '채용정보 입력에 실패했습니다.');
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

  const response = await fetch(`${API_BASE_URL}/api/v1/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || '자기소개서 생성에 실패했습니다.');
  }

  return response.json();
};

// 자기소개서 결과 조회
export const getCoverLetter = async (sessionId) => {
  if (checkMockMode()) {
    return mockApi.getCoverLetter(sessionId);
  }

  return apiCall(`/api/v1/session/${sessionId}`);
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

  return apiCall(`/api/v1/sessions/${sessionId}/questions/${questionIndex}/revise`, {
    method: 'POST',
    body: JSON.stringify({ revision }),
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
export { useMockApi, disableMockApi, isMockApiEnabled } from './mockApi';

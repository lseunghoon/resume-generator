import { mockApi, isMockApiEnabled } from './mockApi';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Mock API 모드 확인
const useMock = isMockApiEnabled();

// 공통 API 호출 함수
const apiCall = async (endpoint, options = {}) => {
  if (useMock) {
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
    throw new Error(`API 호출 실패: ${response.status}`);
  }

  return response.json();
};

// 직무 정보 추출
export const extractJobInfo = async (url) => {
  if (useMock) {
    return mockApi.extractJobInfo(url);
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/extract-job`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '직무 정보 추출에 실패했습니다.');
  }

  return response.json();
};

// 세션 생성 (자기소개서 생성)
export const createSession = async (data) => {
  if (useMock) {
    return mockApi.createSession(data);
  }

  const formData = new FormData();
  
  // 파일들 추가
  if (data.uploadedFiles && data.uploadedFiles.length > 0) {
    data.uploadedFiles.forEach((file, index) => {
      formData.append('files', file);
    });
  }

  // JSON 데이터 추가
  const jsonData = {
    job_posting_url: data.jobPostingUrl,
    selected_job: data.selectedJob,
    questions: data.questions,
    job_description: data.jobDescription
  };
  
  formData.append('data', JSON.stringify(jsonData));

  const response = await fetch(`${API_BASE_URL}/api/v1/sessions`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '자기소개서 생성에 실패했습니다.');
  }

  return response.json();
};

// 자기소개서 결과 조회
export const getCoverLetter = async (sessionId) => {
  if (useMock) {
    return mockApi.getCoverLetter(sessionId);
  }

  return apiCall(`/api/v1/sessions/${sessionId}/cover-letter`);
};

// 문항 추가
export const addQuestion = async (sessionId, question) => {
  if (useMock) {
    return mockApi.addQuestion(sessionId, question);
  }

  return apiCall(`/api/v1/sessions/${sessionId}/questions`, {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
};

// 답변 수정
export const reviseAnswer = async (sessionId, questionId, revision) => {
  if (useMock) {
    return mockApi.reviseAnswer(sessionId, questionId, revision);
  }

  return apiCall(`/api/v1/sessions/${sessionId}/questions/${questionId}/revise`, {
    method: 'POST',
    body: JSON.stringify({ revision }),
  });
};

// Mock API 모드 제어 함수들
export { useMockApi, disableMockApi, isMockApiEnabled } from './mockApi';

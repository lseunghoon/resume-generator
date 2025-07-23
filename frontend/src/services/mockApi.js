// Mock API for frontend testing without backend
const MOCK_DELAY = 1000; // 1초 지연

// 지연 함수
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Mock 직무 추출 응답
const mockJobExtraction = {
  positions: [
    "프론트엔드 개발자",
    "백엔드 개발자", 
    "풀스택 개발자"
  ],
  jobDescription: "카카오에서 함께 성장할 개발자를 모집합니다. React, Node.js, Python 등 다양한 기술 스택을 활용하여 혁신적인 서비스를 만들어갑니다."
};

// Mock 세션 생성 응답
const mockSessionResponse = {
  session_id: "mock-session-123",
  message: "자기소개서 생성이 완료되었습니다."
};

// Mock 자기소개서 응답
const mockCoverLetterResponse = {
  session_id: "mock-session-123",
  answers: [
    {
      question: "사용자가 선택한 문항",
      answer: "저는 어린 시절부터 컴퓨터에 관심이 많았습니다. 중학교 때 처음 프로그래밍을 접하게 되었고, 그때부터 개발자의 꿈을 키워왔습니다. 고등학교에서는 정보올림피아드에 참가하여 전국 대회에서 입상하는 성과를 거두었고, 대학교에서는 컴퓨터공학을 전공하며 더욱 깊이 있는 지식을 쌓았습니다. 특히 웹 개발에 관심을 가지고 React, Node.js 등의 기술을 학습하며 실무 프로젝트에도 참여했습니다. 이러한 경험들을 통해 저는 지속적인 학습과 도전 정신의 중요성을 깨달았고, 이를 바탕으로 더 나은 개발자가 되기 위해 노력하고 있습니다."
    }
  ]
};

// Mock API 함수들
export const mockApi = {
  // 직무 정보 추출
  extractJobInfo: async (url) => {
    console.log('Mock: 직무 정보 추출 중...', url);
    await delay(MOCK_DELAY);
    
    if (!url || url.trim() === '') {
      throw new Error('URL을 입력해주세요.');
    }
    
    if (!url.includes('http')) {
      throw new Error('올바른 URL 형식을 입력해주세요.');
    }
    
    return mockJobExtraction;
  },

  // 세션 생성 (자기소개서 생성)
  createSession: async (data) => {
    console.log('Mock: 자기소개서 생성 중...', data);
    await delay(MOCK_DELAY * 2); // 생성은 더 오래 걸림
    
    return mockSessionResponse;
  },

  // 자기소개서 결과 조회
  getCoverLetter: async (sessionId) => {
    console.log('Mock: 자기소개서 조회 중...', sessionId);
    await delay(MOCK_DELAY);
    
    return mockCoverLetterResponse;
  },

  // 문항 추가
  addQuestion: async (sessionId, question) => {
    console.log('Mock: 문항 추가 중...', { sessionId, question });
    await delay(MOCK_DELAY);
    
    return {
      session_id: sessionId,
      message: "문항이 추가되었습니다.",
      new_answer: {
        question: question,
        answer: `새로 추가된 문항 "${question}"에 대한 답변입니다. 이는 Mock 데이터로 생성된 예시 답변입니다. 실제로는 AI 모델이 생성한 답변이 표시됩니다.`
      }
    };
  },

  // 답변 수정
  reviseAnswer: async (sessionId, questionId, revision) => {
    console.log('Mock: 답변 수정 중...', { sessionId, questionId, revision });
    await delay(MOCK_DELAY);
    
    return {
      session_id: sessionId,
      message: "답변이 수정되었습니다.",
      revised_answer: {
        question: "수정된 문항",
        answer: `수정 요청: "${revision}"에 따라 수정된 답변입니다. 이는 Mock 데이터로 생성된 예시 답변입니다.`
      }
    };
  }
};

// Mock API 사용을 위한 설정
export const useMockApi = () => {
  // localStorage에 mock 모드 저장
  localStorage.setItem('useMockApi', 'true');
  console.log('Mock API 모드가 활성화되었습니다.');
};

export const disableMockApi = () => {
  localStorage.removeItem('useMockApi');
  console.log('Mock API 모드가 비활성화되었습니다.');
};

export const isMockApiEnabled = () => {
  return localStorage.getItem('useMockApi') === 'true';
}; 
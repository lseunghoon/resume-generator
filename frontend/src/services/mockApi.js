// Mock API for frontend testing without backend
const MOCK_DELAY = 1000; // 1초 지연

// 지연 함수
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Mock 직무 추출 응답
const mockJobExtraction = {
  success: true,
  positions: [
    "프론트엔드 개발자",
    "백엔드 개발자", 
    "풀스택 개발자"
  ],
  htmlContent: "<html><body><h1>Mock 채용공고</h1><p>카카오에서 함께 성장할 개발자를 모집합니다. React, Node.js, Python 등 다양한 기술 스택을 활용하여 혁신적인 서비스를 만들어갑니다.</p></body></html>"
};

// Mock 세션 생성 응답
const mockSessionResponse = {
  sessionId: "mock-session-123",
  message: "자기소개서 생성이 완료되었습니다."
};

// Mock 자기소개서 응답
const mockCoverLetterResponse = {
  session_id: "mock-session-123",
  questions: [
    {
      id: 1,
      question: "사용자가 선택한 문항",
      answer: "저는 어린 시절부터 컴퓨터에 관심이 많았습니다. 중학교 때 처음 프로그래밍을 접하게 되었고, 그때부터 개발자의 꿈을 키워왔습니다. 고등학교에서는 정보올림피아드에 참가하여 전국 대회에서 입상하는 성과를 거두었고, 대학교에서는 컴퓨터공학을 전공하며 더욱 깊이 있는 지식을 쌓았습니다. 특히 웹 개발에 관심을 가지고 React, Node.js 등의 기술을 학습하며 실무 프로젝트에도 참여했습니다. 이러한 경험들을 통해 저는 지속적인 학습과 도전 정신의 중요성을 깨달았고, 이를 바탕으로 더 나은 개발자가 되기 위해 노력하고 있습니다.",
      answer_history: JSON.stringify(["저는 어린 시절부터 컴퓨터에 관심이 많았습니다. 중학교 때 처음 프로그래밍을 접하게 되었고, 그때부터 개발자의 꿈을 키워왔습니다. 고등학교에서는 정보올림피아드에 참가하여 전국 대회에서 입상하는 성과를 거두었고, 대학교에서는 컴퓨터공학을 전공하며 더욱 깊이 있는 지식을 쌓았습니다. 특히 웹 개발에 관심을 가지고 React, Node.js 등의 기술을 학습하며 실무 프로젝트에도 참여했습니다. 이러한 경험들을 통해 저는 지속적인 학습과 도전 정신의 중요성을 깨달았고, 이를 바탕으로 더 나은 개발자가 되기 위해 노력하고 있습니다."]),
      current_version_index: 0,
      length: 500
    }
  ]
};

// Mock API 함수들
let mockUserQuestion = "지원 동기는 무엇인가요?"; // 기본 질문

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
    
    // 사용자가 입력한 질문 저장
    if (data.questions && data.questions.length > 0) {
      mockUserQuestion = data.questions[0];
    }
    
    // Mock API에서는 세션 생성과 동시에 자기소개서도 생성됨
    console.log('Mock: 자기소개서 생성 완료');
    
    return mockSessionResponse;
  },

  // 자기소개서 생성 (AI 모델 호출) - Mock에서는 이미 생성됨
  generate: async ({ sessionId }) => {
    console.log('Mock: generate 함수 호출됨 (이미 생성됨)', sessionId);
    await delay(MOCK_DELAY);
    
    return {
      success: true,
      message: "자기소개서가 이미 생성되었습니다."
    };
  },

  // 자기소개서 결과 조회
  getCoverLetter: async (sessionId) => {
    console.log('Mock: 자기소개서 조회 중...', sessionId);
    await delay(MOCK_DELAY);
    
    // Mock 응답에서 저장된 질문 사용
    const mockResponse = {
      session_id: "mock-session-123",
      questions: [
        {
          id: 1,
          question: mockUserQuestion, // 사용자가 입력한 질문 사용
          answer: "저는 어린 시절부터 컴퓨터에 관심이 많았습니다. 중학교 때 처음 프로그래밍을 접하게 되었고, 그때부터 개발자의 꿈을 키워왔습니다. 고등학교에서는 정보올림피아드에 참가하여 전국 대회에서 입상하는 성과를 거두었고, 대학교에서는 컴퓨터공학을 전공하며 더욱 깊이 있는 지식을 쌓았습니다. 특히 웹 개발에 관심을 가지고 React, Node.js 등의 기술을 학습하며 실무 프로젝트에도 참여했습니다. 이러한 경험들을 통해 저는 지속적인 학습과 도전 정신의 중요성을 깨달았고, 이를 바탕으로 더 나은 개발자가 되기 위해 노력하고 있습니다.",
          answer_history: JSON.stringify(["저는 어린 시절부터 컴퓨터에 관심이 많았습니다. 중학교 때 처음 프로그래밍을 접하게 되었고, 그때부터 개발자의 꿈을 키워왔습니다. 고등학교에서는 정보올림피아드에 참가하여 전국 대회에서 입상하는 성과를 거두었고, 대학교에서는 컴퓨터공학을 전공하며 더욱 깊이 있는 지식을 쌓았습니다. 특히 웹 개발에 관심을 가지고 React, Node.js 등의 기술을 학습하며 실무 프로젝트에도 참여했습니다. 이러한 경험들을 통해 저는 지속적인 학습과 도전 정신의 중요성을 깨달았고, 이를 바탕으로 더 나은 개발자가 되기 위해 노력하고 있습니다."]),
          current_version_index: 0,
          length: 500
        }
      ]
    };
    
    return mockResponse;
  },

  // 문항 추가
  addQuestion: async (sessionId, question) => {
    console.log('Mock: 문항 추가 중...', { sessionId, question });
    await delay(MOCK_DELAY);
    
    return {
      sessionId: sessionId,
      message: "문항이 추가되었습니다.",
      new_answer: {
        question: question,
        answer: `새로 추가된 문항 "${question}"에 대한 답변입니다. 이는 Mock 데이터로 생성된 예시 답변입니다. 실제로는 AI 모델이 생성한 답변이 표시됩니다.`
      }
    };
  },

  // 답변 수정
  reviseAnswer: async (sessionId, questionIndex, revision) => {
    console.log('Mock: 답변 수정 중...', { sessionId, questionIndex, revision });
    await delay(MOCK_DELAY);
    
    return {
      sessionId: sessionId,
      message: "답변이 수정되었습니다.",
      revised_answer: {
        question: "수정된 문항",
        answer: `수정 요청: "${revision}"에 따라 수정된 답변입니다. 이는 Mock 데이터로 생성된 예시 답변입니다.`
      }
    };
  },

  // 콘텐츠 프리로딩
  preloadContent: async (data) => {
    console.log('Mock: 콘텐츠 프리로딩 중...', data);
    await delay(MOCK_DELAY);
    
    // 대용량 콘텐츠 시뮬레이션 (contentId 반환)
    if (Math.random() > 0.5) {
      return {
        contentId: 'mock-content-id-' + Date.now(),
        contentSize: 1024 * 1024, // 1MB
        message: '대용량 콘텐츠가 임시 저장되었습니다. contentId를 사용하여 세션 생성 시 참조하세요.'
      };
    } else {
      // 작은 콘텐츠 시뮬레이션 (직접 반환)
      return {
        jobDescription: 'Mock 채용공고 내용입니다. 이는 프리로딩된 콘텐츠입니다. 실제로는 크롤링과 OCR을 통해 추출된 채용공고 내용이 여기에 들어갑니다.',
        contentSize: 1024, // 1KB
        message: '콘텐츠 프리로딩 완료'
      };
    }
  },

  // 저장된 프리로딩 콘텐츠 조회
  getPreloadedContent: async (contentId) => {
    console.log('Mock: 저장된 콘텐츠 조회 중...', contentId);
    await delay(MOCK_DELAY);
    
    return {
      jobDescription: 'Mock 저장된 대용량 채용공고 내용입니다. 이는 프리로딩된 콘텐츠입니다. 실제로는 크롤링과 OCR을 통해 추출된 채용공고 내용이 여기에 들어갑니다.',
      contentSize: 1024 * 1024, // 1MB
      message: '저장된 콘텐츠 조회 완료'
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
  // localStorage에서 Mock API 사용 여부 확인
  return localStorage.getItem('useMockApi') === 'true';
}; 
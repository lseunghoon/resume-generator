import axios from 'axios';

// baseURL을 localhost:5000으로 수정
const api = axios.create({
  baseURL: 'http://localhost:5000/api/v1',
  // baseURL: 'https://90fd-125-143-163-25.ngrok-free.app//api/v1'
});

// 직무 정보 추출을 위한 새로운 API 함수
export const extractJobInfo = async (jobPostingUrl) => {
  try {
    const response = await api.post('/extract-job', { 
      jobPostingUrl 
    });
    return response.data;
  } catch (err) {
    console.error('직무 정보 추출 오류:', err);
    throw err;
  }
};

// 세션 생성 및 파일 업로드 (기존 upload 함수 개선)
export const createSession = async (jobPostingUrl, selectedJob, uploadedFiles, question, jobDescription, selectedQuestions = []) => {
  try {
    const formData = new FormData();
    
    // 다중 파일 처리
    if (uploadedFiles && uploadedFiles.length > 0) {
      uploadedFiles.forEach(file => {
        formData.append('files', file);
      });
    } else {
      // 파일이 없으면 더미 파일 생성
      const dummyFile = new File([''], 'no-file.txt', { type: 'text/plain' });
      formData.append('files', dummyFile);
    }
    
    // 사용자가 선택한 문항들을 사용, 없으면 기본값 사용
    const defaultQuestions = ['성장과정', '성격의 장단점', '지원동기 및 포부'];
    const questionsToUse = selectedQuestions.length > 0 ? selectedQuestions : defaultQuestions;
    
    const jsonData = {
      jobDescriptionUrl: jobPostingUrl,
      questions: questionsToUse, // 선택된 질문들 사용
      lengths: Array(questionsToUse.length).fill('500'), // 문항 수에 맞춰 길이 배열 생성
      selectedJob,
      additionalQuestion: question,
      jobDescription // 이미 크롤링된 데이터를 전달하여 중복 크롤링 방지
    };
    formData.append('data', JSON.stringify(jsonData));
    
    const response = await api.post('/upload', formData);
    return response.data;
  } catch (err) {
    console.error('세션 생성 오류:', err);
    throw err;
  }
};

export const upload = async (formData) => {
  console.log('API: /upload 호출 시도');
  try {
    const response = await api.post('/upload', formData);
    console.log('API: /upload 응답 받음');
    return response.data;
  } catch (err) {
    console.error('🔴 API 서비스 내부에서 오류가 발생했습니다!');
    if (axios.isAxiosError(err)) {
      console.error('Axios 오류 상세 정보 (services/api.js):', {
        message: err.message,
        code: err.code,
        response: err.response ? {
          status: err.response.status,
          data: err.response.data,
        } : '응답 없음',
      });
    } else {
      console.error('일반 오류 상세 정보 (services/api.js):', err);
    }
    throw err;
  }
};

export const generate = async (data) => {
  try {
    const response = await api.post('/generate', data);
    return response.data;
  } catch (err) {
    console.error('API /generate 호출 오류:', err);
    throw err;
  }
};

// 자기소개서 수정
export const revise = async (data) => {
  try {
    const response = await api.post('/revise', {
      sessionId: data.sessionId,
      questionIndex: data.questionIndex, // q_idx에서 questionIndex로 변경
      action: data.action || 'revise',
      revisionRequest: data.revisionRequest // prompt에서 revisionRequest로 변경
    });
    return response.data;
  } catch (err) {
    console.error('자기소개서 수정 오류:', err);
    throw err;
  }
};

export const getSession = async (sessionId) => {
  try {
    const response = await api.get(`/session/${sessionId}`);
    return response.data;
  } catch (err) {
    console.error('API /session/:id 호출 오류:', err);
    throw err;
  }
}

export default api;

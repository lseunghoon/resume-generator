import axios from 'axios';

// baseURL을 localhost:5000으로 수정
const api = axios.create({
  baseURL: 'http://localhost:5000/api/v1',
  // baseURL: 'https://90fd-125-143-163-25.ngrok-free.app//api/v1'
});

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

export const revise = async (data) => {
  try {
    // data: { sessionId, q_idx, action, prompt? }
    const response = await api.post('/revise', data);
    return response.data;
  } catch (err) {
    console.error('API /revise 호출 오류:', err);
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

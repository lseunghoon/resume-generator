import axios from 'axios';

const baseURL = typeof window !== 'undefined' 
  ? window.location.origin + '/api/v1'
  : 'http://localhost:5000/api/v1';

const api = axios.create({
  baseURL,
});

// 응답 인터셉터 추가
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface UploadResponse {
  sessionId: string;
  message: string;
}

export interface GenerateResponse {
  answers: string[];
  message: string;
}

export interface ReviseResponse {
  revisedAnswer: string;
  message: string;
}

export const uploadFiles = async (formData: FormData): Promise<UploadResponse> => {
  try {
    console.log('FormData 확인');
    for (let [k, v] of formData.entries()) {
      console.log('entry', k, v);  // 여기에 files 항목이 찍혀야 정상
    }

    const response = await axios.post<UploadResponse>(
      'http://localhost:5000/api/v1/upload',
      formData
    );
    console.log('Upload successful:', response.data);
    return response.data;
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
};

export const generateCoverLetter = async (sessionId: string): Promise<GenerateResponse> => {
  try {
    const response = await api.post<GenerateResponse>('/generate', { sessionId });
    console.log('Generation successful:', response.data);
    return response.data;
  } catch (error) {
    console.error('Generation failed:', error);
    throw error;
  }
};

export const reviseCoverLetter = async (sessionId: string, questionIndex: number, revisionRequest: string): Promise<ReviseResponse> => {
  try {
    const response = await api.post<ReviseResponse>('/revise', { 
      sessionId, 
      questionIndex, 
      revisionRequest 
    });
    console.log('Revision successful:', response.data);
    return response.data;
  } catch (error) {
    console.error('Revision failed:', error);
    throw error;
  }
};

export const deleteSession = async (sessionId: string): Promise<void> => {
  try {
    await api.delete(`/session/${sessionId}`);
    console.log('Session deleted successfully');
  } catch (error) {
    console.error('Session deletion failed:', error);
    throw error;
  }
}; 
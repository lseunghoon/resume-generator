import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { upload, generate } from '../services/api';
import axios from 'axios';
import '../components/Button.css';
import './UploadPage.css';
import './LoadingIndicator.css';

const LoadingIndicator = () => (
  <div className="loading-popup-overlay">
    <div className="loading-popup-content">
      <div className="loading-spinner"></div>
      <p>자기소개서를 생성하고 있습니다.</p>
      <p>이 작업은 최대 1분 정도 소요될 수 있습니다.</p>
    </div>
  </div>
);

const UploadPage = () => {
  const navigate = useNavigate();
  const [jdUrl, setJdUrl] = useState('');
  const [questions, setQuestions] = useState(['']);
  const [lengths, setLengths] = useState(['']);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInput = useRef();

  const handleQuestionChipClick = (question) => {
    setQuestions([question]);
  };

  const handleQuestionChange = (index, value) => {
    const newQuestions = [...questions];
    newQuestions[index] = value;
    setQuestions(newQuestions);
  };

  const handleLengthChange = (index, value) => {
    const newLengths = [...lengths];
    newLengths[index] = value;
    setLengths(newLengths);
  };

  const addQuestion = () => {
    setQuestions([...questions, '']);
    setLengths([...lengths, '']);
  };

  const removeQuestion = (index) => {
    const newQuestions = questions.filter((_, i) => i !== index);
    const newLengths = lengths.filter((_, i) => i !== index);
    setQuestions(newQuestions);
    setLengths(newLengths);
  };

  const handleFileChange = (e) => {
    setFiles(e.target.files);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (questions.some(q => !q.trim())) throw new Error('자기소개서 문항을 입력해주세요.');
      if (!jdUrl) throw new Error('채용공고 URL을 입력해주세요.');
      if (files.length === 0) throw new Error('이력서 혹은 자기소개서 파일을 업로드해주세요.');

      const formData = new FormData();

      const jsonData = {
        jobDescriptionUrl: jdUrl,
        questions: questions,
        lengths: [],
      };
      formData.append('data', JSON.stringify(jsonData));
      
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      
      const uploadResponse = await upload(formData);
      const sessionId = uploadResponse.sessionId;
      if (!sessionId) {
        throw new Error('세션 ID를 받아오지 못했습니다.');
      }

      await generate({ sessionId });

      navigate(`/result?sessionId=${sessionId}`);

    } catch (err) {
      console.error('‼️ 업로드 및 생성 과정에서 오류가 발생했습니다.');
      if (axios.isAxiosError(err)) {
        console.error('Axios 오류 상세 정보:', err.response?.data || err.message);
        const serverMessage = err.response?.data?.message || '서버 응답을 확인해주세요.';
        setError(`업로드 실패: ${serverMessage}`);
      } else {
        console.error('일반 오류 상세 정보:', err);
        setError(err instanceof Error ? err.message : '파일 업로드 중 알 수 없는 오류가 발생했습니다.');
      }
      setLoading(false);
    }
  };

  return (
    <>
      {loading && <LoadingIndicator />}
      <div className="upload-page-container">
        <header className="upload-header">
          <div className="logo">Upstage</div>
        </header>
        <main className="upload-main">
          <form onSubmit={handleSubmit} className="upload-form">
            <div className="form-section">
              <label className="form-label">1. 자기소개서 문항을 직접 입력하거나 선택해주세요.</label>
              <input
                type="text"
                value={questions[0]}
                onChange={(e) => handleQuestionChange(0, e.target.value)}
                placeholder="실제 자기소개서 문항을 입력해주세요."
                className="form-input"
                required
              />
              <div className="chip-container">
                <button type="button" className="chip" onClick={() => handleQuestionChipClick('지원 동기는 무엇인가요?')}>
                  지원 동기는 무엇인가요?
                </button>
                <button type="button" className="chip" onClick={() => handleQuestionChipClick('성격의 장단점은 무엇인가요?')}>
                  성격의 장단점은 무엇인가요?
                </button>
              </div>
            </div>

            <div className="form-section">
              <label className="form-label">2. 채용공고 링크를 삽입해주세요.</label>
              <input
                type="url"
                value={jdUrl}
                onChange={(e) => setJdUrl(e.target.value)}
                placeholder="실제 지원하는 채용공고 링크를 삽입해주세요."
                className="form-input"
                required
              />
            </div>

            <div className="form-section">
              <label className="form-label">3. 이력서 혹은 자기소개서를 업로드해주세요.</label>
              <p className="form-description">이력서와 자기소개서가 함께 묶인 형태 파일 첨부하면 더 정확하게 할 수 있음</p>
              <div className="file-attach-wrapper">
                <button
                  type="button"
                  onClick={() => fileInput.current.click()}
                  className="file-attach-button"
                >
                  파일 첨부
                </button>
                <input
                  type="file"
                  ref={fileInput}
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                  multiple
                  accept=".pdf,.docx"
                />
                {files.length > 0 && <span className="file-count">{files.length}개 파일 선택됨</span>}
              </div>
              <p className="form-description-small">pdf 혹은 doxc 형식만 첨부 가능합니다.</p>
            </div>

            <div className="submit-section">
              {error && <p className="error-message">{error}</p>}
              <button
                type="submit"
                className="submit-button"
                disabled={loading || !jdUrl || !questions[0] || files.length === 0}
              >
                생성하기
              </button>
              <p className="form-description-small">입력해주신 정보 및 파일은 저장되지 않습니다.</p>
            </div>
          </form>
        </main>
      </div>
    </>
  );
};

export default UploadPage; 
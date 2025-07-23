import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import Input from '../components/Input';
import { createSession, generate } from '../services/api';
import './QuestionPage.css';

const QuestionPage = () => {
  const [question, setQuestion] = useState(''); // 직접 입력 질문
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobPostingUrl, setJobPostingUrl] = useState('');
  const [selectedJob, setSelectedJob] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [jobDescription, setJobDescription] = useState('');
  const [extractedJobs, setExtractedJobs] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.state) {
      setJobPostingUrl(location.state.jobPostingUrl || '');
      setSelectedJob(location.state.selectedJob || '');
      setUploadedFiles(location.state.uploadedFiles || []);
      setJobDescription(location.state.jobDescription || '');
      setExtractedJobs(location.state.extractedJobs || []);
      
      // 이전에 입력한 질문이 있으면 복원
      if (location.state.question) {
        setQuestion(location.state.question);
      }
    } else {
      // 상태가 없으면 홈으로 이동
      navigate('/');
    }
  }, [location.state, navigate]);

  // 추천 질문 chip 버튼들 (Figma 디자인 기준)
  const recommendedQuestions = [
    '성격의 장단점은 무엇인가요?',
    '입사 후 포부는 무엇인가요?',
    '직무와 관련된 경험을 설명해주세요',
    '실패 경험과 극복 과정에 대해 말해주세요'
  ];

  const handleQuestionChange = (e) => {
    setQuestion(e.target.value);
  };

  const handleChipClick = (chipQuestion) => {
    setQuestion(chipQuestion); // chip 클릭 시 입력창에 해당 질문 설정
  };

  const handleGenerate = async () => {
    if (!question.trim()) {
      alert('질문을 입력해주세요.');
      return;
    }

    setIsGenerating(true);

    try {
      // API 호출을 위한 데이터 준비
      const sessionData = {
        jobPostingUrl,
        selectedJob,
        uploadedFiles: uploadedFiles || [],
        questions: [question], // 사용자가 입력한 질문
        jobDescription
      };

      console.log('QuestionPage - Creating session with data:', sessionData);
      const response = await createSession(sessionData);
      console.log('QuestionPage - Session created:', response);
      
      // 세션 ID를 사용하여 결과 페이지로 이동
      console.log('QuestionPage - Navigating to result with sessionId:', response.session_id);
      navigate('/result', { 
        state: { 
          sessionId: response.session_id,
          jobPostingUrl,
          selectedJob,
          jobDescription,
          question // 입력한 질문도 함께 전달
        } 
      });
    } catch (error) {
      console.error('자기소개서 생성 오류:', error);
      alert(error.message || '자기소개서 생성에 실패했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRestart = () => {
    navigate('/');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isGenerating && question.trim()) {
      handleGenerate();
    }
  };

  const handleGoBack = () => {
    navigate('/file-upload', { 
      state: { 
        jobPostingUrl, 
        selectedJob,
        jobDescription,
        extractedJobs,
        uploadedFiles, // 업로드된 파일들 전달
        question // 입력한 질문 전달
      } 
    });
  };

  const handleGoForward = () => {
    if (question.trim()) {
      handleGenerate();
    }
  };

  return (
    <div className="question-page">
      <Header 
        progress={90} 
        showNavigation={true}
        canGoBack={true}
        canGoForward={!!question.trim() && !isGenerating}
        onGoBack={handleGoBack}
        onGoForward={handleGoForward}
        currentStep="4"
        totalSteps="4"
      />

      <div className="page-content">
        <div className="content-wrapper">
          <div className="form-section">
            {/* 질문 입력 섹션 - Figma 디자인 기준 */}
            <div className="question-input-section">
              <div className="form-header">
                <h1>생성하고자 하는 문항을<br/>선택하거나 직접 입력해주세요</h1>
                <p>자기소개서 문항 중 하나를 골라 입력해보세요.</p>
              </div>

              {/* 질문 직접 입력 */}
              <div className="question-input">
                <Input
                  placeholder="지원 동기는 무엇인가요?"
                  value={question}
                  onChange={handleQuestionChange}
                  onKeyPress={handleKeyPress}
                  disabled={isGenerating}
                />
              </div>

              {/* 추천 질문 chips */}
              <div className="recommendation-chips">
                {recommendedQuestions.map((chipQuestion, index) => (
                  <button
                    key={index}
                    className="recommendation-chip"
                    onClick={() => handleChipClick(chipQuestion)}
                    disabled={isGenerating}
                  >
                    {chipQuestion}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="action-section">
            <Button
              variant={question.trim() ? 'primary' : 'secondary'}
              disabled={isGenerating || !question.trim()}
              onClick={handleGenerate}
              className="generate-button"
            >
              {isGenerating ? '자기소개서 생성 중...' : '자기소개서 생성하기'}
            </Button>
          </div>

          {isGenerating && (
            <div className="generating-info">
              <div className="generating-spinner"></div>
              <p>AI가 맞춤형 자기소개서를 생성하고 있습니다...</p>
              <p className="generating-details">
                • 채용 공고 분석 중<br/>
                • 직무 정보 반영 중<br/>
                {uploadedFiles && uploadedFiles.length > 0 && '• 기존 자기소개서/이력서 분석 중'}<br/>
                • 맞춤형 답변 생성 중...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuestionPage; 
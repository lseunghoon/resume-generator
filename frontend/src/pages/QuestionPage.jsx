import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import Input from '../components/Input';
import { createSession, generate } from '../services/api';
import './QuestionPage.css';

const QuestionPage = () => {
  const [question, setQuestion] = useState('');
  const [selectedQuestions, setSelectedQuestions] = useState([
    '지원 동기는 무엇인가요?'
  ]); // 기본 선택된 문항
  const [isGenerating, setIsGenerating] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { jobPostingUrl, selectedJob, uploadedFiles, jobDescription } = location.state || {};

  // 추천 질문 chip 버튼들
  const recommendedQuestions = [
    '성장과정을 말씀해주세요',
    '성격의 장단점은 무엇인가요?',
    '학업이 관련된 경험을 설명해주세요',
    '실제 경험과 극복 과정에 대해 말씀해주세요'
  ];

  // 기본 자기소개서 문항들
  const defaultQuestions = [
    '지원 동기는 무엇인가요?',
    '성장과정을 말씀해주세요',
    '성격의 장단점은 무엇인가요?',
    '학업이 관련된 경험을 설명해주세요',
    '프로젝트 경험을 설명해주세요',
    '입사 후 포부를 말씀해주세요'
  ];

  const handleQuestionChange = (e) => {
    setQuestion(e.target.value);
  };

  const handleChipClick = (chipQuestion) => {
    if (question.trim() === '') {
      setQuestion(chipQuestion);
    } else {
      setQuestion(question + ' ' + chipQuestion);
    }
  };

  const handleQuestionSelect = (questionText) => {
    if (selectedQuestions.includes(questionText)) {
      // 이미 선택된 경우 제거 (단, 최소 1개는 유지)
      if (selectedQuestions.length > 1) {
        setSelectedQuestions(selectedQuestions.filter(q => q !== questionText));
      }
    } else {
      // 최대 3개까지만 선택 가능
      if (selectedQuestions.length < 3) {
        setSelectedQuestions([...selectedQuestions, questionText]);
      }
    }
  };

  const handleAddCustomQuestion = (customQuestion) => {
    if (customQuestion.trim() && selectedQuestions.length < 3) {
      setSelectedQuestions([...selectedQuestions, customQuestion.trim()]);
    }
    setShowQuestionModal(false);
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    
    try {
      // 선택된 문항들과 추가 질문을 함께 전달
      const sessionResponse = await createSession(
        jobPostingUrl, 
        selectedJob, 
        uploadedFiles,
        question.trim(),
        jobDescription,
        selectedQuestions // 선택된 자기소개서 문항들 추가
      );
      
      const sessionId = sessionResponse.sessionId;
      if (!sessionId) {
        throw new Error('세션 ID를 받아오지 못했습니다.');
      }
      
      await generate({ sessionId });
      
      navigate(`/result?sessionId=${sessionId}`);
      
    } catch (err) {
      console.error('자기소개서 생성 실패:', err);
      setIsGenerating(false);
      alert('자기소개서 생성 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
  };

  const handleBack = () => {
    navigate('/file-upload', { 
      state: { 
        jobPostingUrl, 
        selectedJob,
        jobDescription
      } 
    });
  };

  const handleRestart = () => {
    navigate('/');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isGenerating) {
      handleGenerate();
    }
  };

  return (
    <div className="question-page">
      <Header progress={90} showRestartButton={true} onRestart={handleRestart} />

      <div className="page-content">
        <div className="content-wrapper">
          <div className="form-section">
            <button className="back-button" onClick={() => navigate('/file-upload', {
              state: { jobPostingUrl, selectedJob, jobDescription }
            })}>
              ←
            </button>

            <div className="form-content">
              {/* 자기소개서 문항 선택 섹션 */}
              <div className="question-selection-section">
                <h2>생성하고자 하는 문항을<br/>선택하거나 직접 입력해주세요</h2>
                <p>자기소개서 문항 중 하나를 골라 입력해보세요.</p>

                <div className="question-chips">
                  {defaultQuestions.map((questionText, index) => (
                    <button
                      key={index}
                      className={`question-chip ${selectedQuestions.includes(questionText) ? 'selected' : ''}`}
                      onClick={() => handleQuestionSelect(questionText)}
                    >
                      {questionText}
                    </button>
                  ))}
                </div>

                {selectedQuestions.length < 3 && (
                  <button 
                    className="add-question-button"
                    onClick={() => setShowQuestionModal(true)}
                  >
                    + 질문 추가
                  </button>
                )}

                <div className="selected-questions">
                  <h3>선택된 문항 ({selectedQuestions.length}/3)</h3>
                  <ul>
                    {selectedQuestions.map((q, index) => (
                      <li key={index}>
                        {index + 1}. {q}
                        {selectedQuestions.length > 1 && (
                          <button 
                            className="remove-question"
                            onClick={() => handleQuestionSelect(q)}
                          >
                            ✕
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* 추가 질문 입력 섹션 */}
              <div className="form-header">
                <h1>추가로 궁금한 점이 있나요?</h1>
                <p>자기소개서 작성 시 추가로 고려했으면 하는 사항이나 궁금한 점을 자유롭게 작성해 주세요.<br/>
                <span className="optional-text">입력하지 않고 바로 생성할 수도 있습니다.</span></p>
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

              <div className="question-input">
                <Input
                  placeholder="예) 해당 회사의 핵심 가치를 반영해 주세요."
                  value={question}
                  onChange={handleQuestionChange}
                  onKeyPress={handleKeyPress}
                  disabled={isGenerating}
                />
              </div>
            </div>
          </div>

          <div className="action-section">
            <Button
              variant="primary"
              disabled={isGenerating}
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
                {uploadedFiles && uploadedFiles.length > 0 && '• 기존 자기소개서 분석 중'}<br/>
                • 맞춤형 답변 생성 중...
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 추가 질문 모달 */}
      {showQuestionModal && (
        <div className="modal-overlay">
          <div className="question-modal">
            <h3>추가로 생성하고자 하는<br/>문항을 입력해주세요</h3>
            <p>자기소개서 문항은 최대 3개까지 추가 가능합니다.</p>
            <input
              type="text"
              placeholder="예) 지원 동기는 무엇인가요?"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleAddCustomQuestion(e.target.value);
                }
              }}
            />
            <div className="modal-buttons">
              <Button 
                variant="primary" 
                onClick={(e) => {
                  const input = e.target.closest('.question-modal').querySelector('input');
                  handleAddCustomQuestion(input.value);
                }}
              >
                추가 생성하기
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setShowQuestionModal(false)}
              >
                다음에 할게요
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuestionPage; 
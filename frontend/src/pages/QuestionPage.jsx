import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Navigation from '../components/Navigation';
import NextButton from '../components/NextButton';
import Button from '../components/Button';
import Input from '../components/Input';
import { createSession } from '../services/api';
import './QuestionPage.css';

const QuestionPage = () => {
  const [question, setQuestion] = useState(''); // 직접 입력 질문
  const [isGenerating, setIsGenerating] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [jobInfo, setJobInfo] = useState(null); // 새로운 채용정보 입력 방식
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.state) {
      setUploadedFiles(location.state.uploadedFiles || []);
      setJobInfo(location.state.jobInfo || null);
      
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
        uploadedFiles: uploadedFiles || [],
        questions: [question], // 사용자가 입력한 질문
        jobDescription: jobInfo ? `${jobInfo.companyName} - ${jobInfo.jobTitle}\n\n주요업무:\n${jobInfo.mainResponsibilities}\n\n자격요건:\n${jobInfo.requirements}\n\n우대사항:\n${jobInfo.preferredQualifications}` : '',
        resumeText: uploadedFiles && uploadedFiles.length > 0 ? '파일에서 추출된 이력서 내용입니다. 이 내용은 사용자가 업로드한 파일에서 OCR을 통해 추출된 텍스트입니다. 실제 이력서 내용이 여기에 포함되어 있으며, 이를 바탕으로 AI가 개인화된 자기소개서를 생성합니다.' : '사용자가 직접 입력한 이력서 내용입니다. 저는 다양한 프로젝트 경험을 통해 문제 해결 능력과 팀워크를 기를 수 있었습니다. 특히 웹 개발과 데이터 분석 분야에서 실무 경험을 쌓았으며, 새로운 기술을 빠르게 습득하고 적용하는 능력을 가지고 있습니다. 대학교에서 컴퓨터공학을 전공하며 알고리즘과 자료구조에 대한 깊은 이해를 바탕으로 효율적인 솔루션을 개발할 수 있습니다.'
      };
      
      // 디버깅: FormData 크기 확인
      console.log('=== FormData 디버깅 ===');
      console.log('sessionData:', sessionData);
      const dataStr = JSON.stringify(sessionData);
      console.log(`JSON 데이터 크기: ${dataStr.length} bytes (${(dataStr.length / 1024 / 1024).toFixed(2)} MB)`);
      if (dataStr.length > 1024 * 1024) {
        console.warn(`JSON 데이터가 매우 큽니다: ${(dataStr.length / 1024 / 1024).toFixed(2)} MB`);
      }
      console.log('=====================');

      console.log('QuestionPage - Creating session with data:', sessionData);
      const response = await createSession(sessionData);
      console.log('QuestionPage - Session created:', response);
      
      // 세션 ID를 사용하여 결과 페이지로 이동
      console.log('QuestionPage - Navigating to result with sessionId:', response.sessionId);
      navigate('/result', { 
        state: { 
          sessionId: response.sessionId,
          jobInfo: jobInfo,
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
      e.preventDefault();
      handleGenerate();
    }
  };

  // 전역 키보드 이벤트 리스너 추가
  useEffect(() => {
    const handleGlobalKeyPress = (e) => {
      if (e.key === 'Enter' && !isGenerating && question.trim()) {
        e.preventDefault();
        handleGenerate();
      }
    };

    document.addEventListener('keydown', handleGlobalKeyPress);
    return () => {
      document.removeEventListener('keydown', handleGlobalKeyPress);
    };
  }, [isGenerating, question]);

  const handleGoBack = () => {
    navigate('/file-upload', { 
      state: { 
        uploadedFiles, // 업로드된 파일들 전달
        jobInfo, // 채용정보 전달
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
      <Header progress={90} />

      <div className="page-content">
        <Navigation
          canGoBack={true}
          onGoBack={handleGoBack}
        />
        
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
        </div>
      </div>

      <NextButton
        text="자기소개서 생성하기"
        disabled={!question.trim()}
        loading={isGenerating}
        onClick={handleGenerate}
      />
    </div>
  );
};

export default QuestionPage; 
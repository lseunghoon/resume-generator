import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDocumentMeta } from '../hooks/useDocumentMeta';
import Navigation from '../components/Navigation';
import Input from '../components/Input';
import { createSession, getCoverLetter } from '../services/api';
import { createSessionUrl } from '../utils/sessionUtils';
import { supabase } from '../services/supabaseClient';
import './QuestionPage.css';

const QuestionPage = ({ onSidebarRefresh }) => {
  const [question, setQuestion] = useState(''); // 직접 입력 질문
  const [isGenerating, setIsGenerating] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [manualText, setManualText] = useState(''); // 직접 입력 텍스트
  const [activeTab, setActiveTab] = useState('upload'); // 활성 탭
  const [jobInfo, setJobInfo] = useState(null); // 새로운 채용정보 입력 방식
  const [error, setError] = useState(''); // 에러 메시지
  const [errorKey, setErrorKey] = useState(0); // 에러 애니메이션을 위한 key
  const [skipResumeUpload, setSkipResumeUpload] = useState(false); // 이력서 업로드 건너뛰기 상태
  const navigate = useNavigate();
  const location = useLocation();

  // 인증 상태 확인 (리다이렉트 없이 상태만 체크)
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  useEffect(() => {
    const checkAuthStatus = async () => {
      const { data, error } = await supabase.auth.getSession();
      if (!error && data?.session) {
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    };
    checkAuthStatus();
  }, []);

  useEffect(() => {
    if (location.state) {
      setUploadedFiles(location.state.uploadedFiles || []);
      setJobInfo(location.state.jobInfo || null);
      setSkipResumeUpload(location.state.skipResumeUpload || false); // 건너뛰기 상태 설정
      
      // FileUploadPage에서 전달된 데이터 복원
      if (location.state.manualText) {
        setManualText(location.state.manualText);
      }
      if (location.state.activeTab) {
        setActiveTab(location.state.activeTab);
      }
      
      // 이전에 입력한 질문이 있으면 복원
      if (location.state.question) {
        setQuestion(location.state.question);
      }
    } else {
      // 로그인 후 임시 저장된 데이터 복원 시도
      try {
        const tempQuestion = localStorage.getItem('temp_question');
        if (tempQuestion && isAuthenticated) {
          const parsed = JSON.parse(tempQuestion);
          const now = Date.now();
          // 30분 이내의 데이터만 복원 (1800000ms = 30분)
          if (now - parsed.timestamp < 1800000) {
            console.log('로그인 후 질문 임시 데이터 복원');
            setQuestion(parsed.question);
            setJobInfo(parsed.jobInfo);
            
            // 파일 메타데이터가 있다면 안내 (실제 파일은 복원 불가)
            if (parsed.uploadedFiles && parsed.uploadedFiles.length > 0) {
              setError('로그인 전에 업로드한 파일은 보안상 다시 업로드해주세요.');
            }
            
            // 사용한 임시 데이터 삭제
            localStorage.removeItem('temp_question');
            return;
          } else {
            // 오래된 데이터 삭제
            localStorage.removeItem('temp_question');
          }
        }
      } catch (e) {
        console.error('질문 임시 데이터 복원 실패:', e);
        localStorage.removeItem('temp_question');
      }
      
      // 상태가 없어도 페이지를 표시 (SEO 최적화)
      // 비로그인 상태에서도 콘텐츠를 볼 수 있어야 함
    }
  }, [location.state, navigate, isAuthenticated]);

  // 추천 질문 chip 버튼들 (Figma 디자인 기준)
  const recommendedQuestions = [
    '성격의 장단점은 무엇인가요',
    '입사 후 포부는 무엇인가요',
    '직무와 관련된 경험을 설명해주세요',
    '실패 경험과 극복 과정에 대해 말해주세요',
    '지원 동기는 무엇인가요',
  ];

  const handleQuestionChange = (e) => {
    setQuestion(e.target.value);
    // 에러가 있으면 초기화
    if (error) {
      setError('');
    }
  };

  const handleChipClick = (chipQuestion) => {
    // 이미 선택된 chip을 다시 클릭하면 해제
    if (question === chipQuestion) {
      setQuestion(''); // 입력창 비우기
    } else {
      setQuestion(chipQuestion); // chip 클릭 시 입력창에 해당 질문 설정
    }
    // 에러가 있으면 초기화
    if (error) {
      setError('');
    }
  };

  // 현재 선택된 chip인지 확인하는 함수
  const isChipSelected = (chipQuestion) => {
    return question === chipQuestion;
  };

  const handleGenerate = async () => {
    // 로그인 체크
    if (!isAuthenticated) {
      // 현재 질문과 관련 데이터를 localStorage에 저장
      try {
        localStorage.setItem('auth_redirect_path', '/job-info');
        localStorage.setItem('temp_question', JSON.stringify({
          question: question,
          jobInfo: jobInfo,
          uploadedFiles: uploadedFiles ? uploadedFiles.map(f => ({
            name: f.name,
            size: f.size,
            type: f.type || 'application/pdf'
          })) : [],
          timestamp: Date.now()
        }));
      } catch (_) {}
      navigate('/login?next=/job-info', { replace: true });
      return;
    }

    if (!question.trim()) {
      setError('문항을 입력해 주세요');
      setErrorKey(prev => prev + 1);
      return;
    }

    if (question.trim().length < 5) {
      setError('문항은 최소 5자 이상 입력해 주세요');
      setErrorKey(prev => prev + 1);
      return;
    }

    // 에러가 있으면 초기화
    setError('');

    // 자기소개서 생성 유효성 검사 성공 시 GA 이벤트 발송
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      'event': 'generate_cover_letter_success'
    });

    setIsGenerating(true);

    try {
      // API 호출을 위한 데이터 준비
      const sessionData = {
        uploadedFiles: uploadedFiles || [],
        questions: [question], // 사용자가 입력한 질문
        jobDescription: jobInfo ? `${jobInfo.companyName} - ${jobInfo.jobTitle}\n\n주요업무:\n${jobInfo.mainResponsibilities}\n\n자격요건:\n${jobInfo.requirements}\n\n우대사항:\n${jobInfo.preferredQualifications}` : '',
        resumeText: (() => {
          const hasFiles = uploadedFiles && uploadedFiles.length > 0;
          const hasManualText = manualText && manualText.trim();
          
          // 파일과 직접 입력이 모두 있는 경우 (MX-001):
          // 프론트에서는 수동 입력만 담고, 실제 파일 텍스트는 백엔드에서 병합합니다.
          if (hasFiles && hasManualText) {
            return `사용자가 직접 입력한 이력서 내용입니다.\n\n${manualText.trim()}`;
          }
          // 파일만 있는 경우
          if (hasFiles) {
            return '파일에서 추출된 이력서 내용이 있습니다. 업로드된 파일에서 텍스트가 추출됩니다.';
          }
          // 직접 입력만 있는 경우
          if (hasManualText) {
            return `사용자가 직접 입력한 이력서 내용입니다.\n\n${manualText.trim()}`;
          }
          // 아무것도 없는 경우 (건너뛰기)
          return '사용자가 직접 입력한 이력서 내용입니다. 저는 다양한 프로젝트 경험을 통해 문제 해결 능력과 팀워크를 기를 수 있었습니다. 특히 웹 개발과 데이터 분석 분야에서 실무 경험을 쌓았으며, 새로운 기술을 빠르게 습득하고 적용하는 능력을 가지고 있습니다. 대학교에서 컴퓨터공학을 전공하며 알고리즘과 자료구조에 대한 깊은 이해를 바탕으로 효율적인 솔루션을 개발할 수 있습니다.';
        })(),
        // 사용자가 직접 입력한 개별 필드들 추가
        companyName: jobInfo ? jobInfo.companyName : '',
        jobTitle: jobInfo ? jobInfo.jobTitle : '',
        mainResponsibilities: jobInfo ? jobInfo.mainResponsibilities : '',
        requirements: jobInfo ? jobInfo.requirements : '',
        preferredQualifications: jobInfo ? jobInfo.preferredQualifications : '',
        // 이력서 업로드 건너뛰기 관련 추가 정보
        hasResume: (uploadedFiles && uploadedFiles.length > 0) || (manualText && manualText.trim()),
        resumeSource: (() => {
          if (uploadedFiles && uploadedFiles.length > 0) return 'file_upload';
          if (manualText && manualText.trim()) return 'manual_input';
          return 'none';
        })(),
        skipResumeUpload: skipResumeUpload
      };
      
      // 디버깅: FormData 크기 확인
      console.log('=== FormData 디버깅 ===');
      console.log('sessionData:', sessionData);
      console.log('파일 개수:', uploadedFiles ? uploadedFiles.length : 0);
      console.log('직접 입력 텍스트 길이:', manualText ? manualText.length : 0);
      console.log('resumeText 길이:', sessionData.resumeText.length);
      const dataStr = JSON.stringify(sessionData);
      console.log(`JSON 데이터 크기: ${dataStr.length} bytes (${(dataStr.length / 1024 / 1024).toFixed(2)} MB)`);
      if (dataStr.length > 1024 * 1024) {
        console.warn(`JSON 데이터가 매우 큽니다: ${(dataStr.length / 1024 / 1024).toFixed(2)} MB`);
      }
      console.log('=====================');

      console.log('QuestionPage - Creating session with data:', sessionData);
      const response = await createSession(sessionData);
      console.log('QuestionPage - Session created:', response);
      
      // 모든 모드에서 폴링을 통해 생성 완료를 기다림
      const sessionId = response.sessionId;
      let attempts = 0;
      const maxAttempts = 60; // 최대 2분 대기 (실제 API는 더 오래 걸릴 수 있음)
      
      while (attempts < maxAttempts) {
        try {
          console.log(`QuestionPage - Polling attempt ${attempts + 1}/${maxAttempts}`);
          const coverLetterResponse = await getCoverLetter(sessionId);
          console.log('QuestionPage - Polling response:', coverLetterResponse);
          console.log('QuestionPage - Response structure:', {
            hasQuestions: !!coverLetterResponse.questions,
            questionsLength: coverLetterResponse.questions?.length,
            questionsType: typeof coverLetterResponse.questions,
            fullResponse: coverLetterResponse
          });
          
          // questions 배열의 실제 내용 확인
          if (coverLetterResponse.questions && coverLetterResponse.questions.length > 0) {
            console.log('QuestionPage - 첫 번째 question 객체:', coverLetterResponse.questions[0]);
            console.log('QuestionPage - question 객체의 속성들:', {
              id: coverLetterResponse.questions[0]?.id,
              question: coverLetterResponse.questions[0]?.question,
              answer: coverLetterResponse.questions[0]?.answer,
              answer_history: coverLetterResponse.questions[0]?.answer_history,
              current_version_index: coverLetterResponse.questions[0]?.current_version_index,
              length: coverLetterResponse.questions[0]?.length
            });
          }
          
          // 더 유연한 조건으로 생성 완료 확인
          const isCompleted = (
            // 백엔드에서 status 필드를 제공하는 경우
            (coverLetterResponse.status === 'completed' || coverLetterResponse.is_completed === true) ||
            // 또는 questions 배열에 실제 답변이 있는 경우
            (coverLetterResponse.questions && 
             Array.isArray(coverLetterResponse.questions) && 
             coverLetterResponse.questions.length > 0 &&
             coverLetterResponse.questions[0].answer && 
             coverLetterResponse.questions[0].answer.trim().length > 0)
          );
          
          if (isCompleted) {
            console.log('QuestionPage - Cover letter generation completed');
            // 자소서 생성이 완료되면 결과 페이지로 이동 (완성된 데이터와 함께)
            navigate(createSessionUrl(sessionId), { 
              state: { 
                sessionId: sessionId,
                jobInfo: jobInfo,
                question, // 입력한 질문도 함께 전달
                completedData: coverLetterResponse // 완성된 데이터도 함께 전달
              } 
            });
            
            // 사이드바 목록 새로고침
            if (onSidebarRefresh) {
              onSidebarRefresh();
            }
            return;
          } else {
            console.log('QuestionPage - Questions not ready yet:', {
              hasQuestions: !!coverLetterResponse.questions,
              questionsLength: coverLetterResponse.questions?.length,
              hasAnswer: coverLetterResponse.questions?.[0]?.answer
            });
          }
        } catch (pollError) {
          console.log('QuestionPage - Polling error (expected during generation):', pollError.message);
          console.log('QuestionPage - Error details:', pollError);
        }
        
        // 2초 대기 후 다시 시도 (더 긴 간격)
        await new Promise(resolve => setTimeout(resolve, 2000));
        attempts++;
      }
      
      // 최대 시도 횟수를 초과한 경우
      console.error('QuestionPage - Cover letter generation timeout');
      alert('자기소개서 생성에 시간이 오래 걸리고 있습니다. 잠시 후 다시 시도해주세요');
      
    } catch (error) {
      console.error('자기소개서 생성 오류:', error);
      alert(error.message || '자기소개서 생성에 실패했습니다');
    } finally {
      setIsGenerating(false);
    }
  };

  // handleRestart 함수는 사용되지 않으므로 제거

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
        manualText, // 직접 입력 텍스트 전달
        activeTab, // 활성 탭 전달
        jobInfo, // 채용정보 전달
        question // 입력한 질문 전달
      } 
    });
  };

  // handleGoForward 함수는 사용되지 않으므로 제거

  // SEO 메타데이터 설정
  useDocumentMeta({
    title: "자기소개서 문항 입력 | 써줌 - AI 자기소개서 생성",
    description: "자기소개서 문항을 선택하거나 직접 입력하여 AI가 맞춤형 자기소개서를 생성하도록 하세요. 다양한 추천 문항 제공.",
    robots: "noindex, nofollow",
    ogTitle: "자기소개서 문항 입력 | 써줌 - AI 자기소개서 생성",
    ogDescription: "자기소개서 문항을 선택하거나 직접 입력하여 AI가 맞춤형 자기소개서를 생성하도록 하세요.",
    ogType: "website",
    ogUrl: "https://www.sseojum.com/question"
  });

  return (
    <div className="question-page">
      
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
                <h1>자기소개서 문항을 선택하거나<br/> 직접 입력해 주세요</h1>
                <p>자주 쓰는 문항 중 하나를 골라 입력해보세요</p>
              </div>

              {/* 질문 직접 입력 */}
              <div className="question-input">
                <Input
                  placeholder="예시) 직무 역량을 쌓기 위해 어떤 노력을 했나요"
                  value={question}
                  onChange={handleQuestionChange}
                  onKeyPress={handleKeyPress}
                  disabled={isGenerating}
                />
                {/* 에러 메시지 */}
                {error && (
                  <div key={`error-${errorKey}`} className="input-error-message">{error}</div>
                )}
              </div>

              {/* 추천 질문 chips */}
              <div className="recommendation-chips">
                {recommendedQuestions.map((chipQuestion, index) => (
                  <button
                    key={index}
                    className={`recommendation-chip ${isChipSelected(chipQuestion) ? 'selected' : ''}`}
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

      <div className="button-container">
        <button 
          id="generate-cover-letter-btn"
          className={`next-button ${isGenerating ? 'disabled' : 'active'}`}
          onClick={handleGenerate}
          disabled={isGenerating}
        >
          {isGenerating ? (
            <>
              <div className="next-button-spinner"></div>
              <span>자기소개서 작성 중</span>
            </>
          ) : (
            '자기소개서 생성하기'
          )}
        </button>
      </div>
    </div>
  );
};

export default QuestionPage; 
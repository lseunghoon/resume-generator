import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import { preloadContent } from '../services/api';
import './JobSelectPage.css';

const JobSelectPage = () => {
  const [selectedJob, setSelectedJob] = useState('');
  const [isCustomInput, setIsCustomInput] = useState(false);
  const [customJob, setCustomJob] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [extractedJobs, setExtractedJobs] = useState([]);
  const [jobPostingUrl, setJobPostingUrl] = useState('');
  const [htmlContent, setHtmlContent] = useState(''); // jobDescription -> htmlContent
  const [preloadedContent, setPreloadedContent] = useState(null); // 프리로딩된 콘텐츠
  const [contentId, setContentId] = useState(null); // 프리로딩된 콘텐츠 ID
  const hasStartedPreloading = useRef(false); // 프리로딩 시작 여부 추적
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    console.log('JobSelectPage - location.state:', location.state);
    console.log('JobSelectPage - jobPostingUrl from state:', location.state?.jobPostingUrl);
    
    if (location.state) {
      setJobPostingUrl(location.state.jobPostingUrl || '');
      setExtractedJobs(location.state.extractedJobs || []);
      setHtmlContent(location.state.htmlContent || ''); // htmlContent 받기
      
      // 이전에 선택한 직무가 있으면 복원
      if (location.state.selectedJob) {
        setSelectedJob(location.state.selectedJob);
      }
      
      // 이전에 직접 입력한 직무가 있으면 복원
      if (location.state.customJob) {
        setCustomJob(location.state.customJob);
        setIsCustomInput(true);
      }
      
      console.log('JobSelectPage - Setting jobPostingUrl to:', location.state.jobPostingUrl || '');
      setIsLoading(false);
    } else {
      // 상태가 없으면 홈으로 이동
      console.log('JobSelectPage - No state, redirecting to home');
      navigate('/');
    }
  }, [location.state, navigate]);

  // 프리로딩 함수 (백그라운드에서 조용히 실행)
  const startPreloading = useCallback(async () => {
    if (!jobPostingUrl || hasStartedPreloading.current) return;
    
    hasStartedPreloading.current = true;
    console.log('JobSelectPage - 백그라운드 프리로딩 시작');
    
    try {
      const response = await preloadContent({
        jobPostingUrl,
        htmlContent
      });
      
      console.log('JobSelectPage - 백그라운드 프리로딩 완료');
      
      if (response.contentId) {
        // 대용량 콘텐츠인 경우 contentId 저장
        console.log('JobSelectPage - 대용량 콘텐츠, contentId 저장:', response.contentId);
        setContentId(response.contentId);
        setPreloadedContent(null);
      } else {
        // 작은 콘텐츠인 경우 직접 저장
        console.log('JobSelectPage - 작은 콘텐츠, 직접 저장');
        setPreloadedContent(response.jobDescription);
        setContentId(null);
      }
    } catch (error) {
      console.error('JobSelectPage - 백그라운드 프리로딩 실패:', error);
      // 프리로딩 실패해도 계속 진행
    }
  }, [jobPostingUrl, htmlContent]);

  // jobPostingUrl이 설정된 후 백그라운드 프리로딩 시작
  useEffect(() => {
    console.log('JobSelectPage - 백그라운드 프리로딩 useEffect 실행:', { jobPostingUrl, isLoading });
    if (jobPostingUrl && !isLoading) {
      console.log('JobSelectPage - 백그라운드 프리로딩 조건 만족, 시작');
      startPreloading();
    }
  }, [jobPostingUrl, isLoading, startPreloading]);

  const handleJobSelect = (job) => {
    setSelectedJob(job);
    setIsCustomInput(false);
    setCustomJob('');
  };

  const handleCustomInputSelect = () => {
    setSelectedJob('');
    setIsCustomInput(true);
  };

  const handleCustomJobChange = (e) => {
    setCustomJob(e.target.value);
  };

  const handleNext = () => {
    const finalJob = isCustomInput ? customJob : selectedJob;
    if (finalJob && finalJob.trim()) {
      navigate('/file-upload', { 
        state: { 
          jobPostingUrl, 
          selectedJob: finalJob,
          htmlContent, // htmlContent 전달
          extractedJobs,
          preloadedContent, // 프리로딩된 콘텐츠 전달
          contentId, // contentId 전달
          customJob: isCustomInput ? customJob : null // 직접 입력한 직무도 전달
        } 
      });
    }
  };

  const handleGoBack = () => {
    console.log('JobSelectPage - Going back with state:', { jobPostingUrl });
    navigate('/', { 
      state: { 
        jobPostingUrl,
        fromJobSelect: true // 뒤로가기 표시
      } 
    });
  };

  const handleGoForward = () => {
    const finalJob = isCustomInput ? customJob : selectedJob;
    if (finalJob && finalJob.trim()) {
      handleNext();
    }
  };

  const isNextEnabled = isCustomInput ? customJob.trim() !== '' : selectedJob !== '';

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && isNextEnabled) {
      e.preventDefault();
      handleNext();
    }
  };

  // 페이지 로드 시 포커스 설정
  useEffect(() => {
    const handleGlobalKeyPress = (e) => {
      if (e.key === 'Enter' && isNextEnabled) {
        e.preventDefault();
        handleNext();
      }
    };

    document.addEventListener('keydown', handleGlobalKeyPress);
    return () => {
      document.removeEventListener('keydown', handleGlobalKeyPress);
    };
  }, [isNextEnabled]);

  if (isLoading) {
    return (
      <div className="job-select-page">
        <Header progress={50} />
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>직무 정보를 분석하고 있습니다...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="job-select-page" onKeyPress={handleKeyPress} tabIndex={0}>
      <Header 
        progress={50} 
        showNavigation={true}
        canGoBack={true}
        canGoForward={isNextEnabled}
        onGoBack={handleGoBack}
        onGoForward={handleGoForward}
        currentStep="2"
        totalSteps="4"
      />
      
      <div className="page-content">
        <div className="content-wrapper">
          <div className="form-section">
            
            <div className="form-content">
              <div className="form-header">
                <h1>추출된 직무 중,<br/>원하는 직무를 선택해주세요.</h1>
                <p>원하는 직무가 없다면 '직접 입력'을 선택해 입력해주세요.</p>
              </div>
              
              <div className="job-options">
                <div className="job-list">
                  {extractedJobs.map((job, index) => (
                    <div 
                      key={index}
                      className={`job-option ${selectedJob === job ? 'selected' : ''}`}
                      onClick={() => handleJobSelect(job)}
                    >
                      <div className="radio-button">
                        <div className={`radio-circle ${selectedJob === job ? 'selected' : ''}`}>
                          {selectedJob === job && <div className="radio-dot"></div>}
                        </div>
                      </div>
                      <span className="job-title">{job}</span>
                    </div>
                  ))}
                  
                  <div 
                    className={`job-option ${isCustomInput ? 'selected' : ''}`}
                    onClick={handleCustomInputSelect}
                  >
                    <div className="radio-button">
                      <div className={`radio-circle ${isCustomInput ? 'selected' : ''}`}>
                        {isCustomInput && <div className="radio-dot"></div>}
                      </div>
                    </div>
                    <span className="job-title">직접 입력</span>
                  </div>
                </div>
                
                <div className={`custom-input-container ${isCustomInput ? 'active' : ''}`}>
                  <input
                    type="text"
                    className="custom-input"
                    placeholder="원하는 직무명을 입력해주세요"
                    value={customJob}
                    onChange={handleCustomJobChange}
                    disabled={!isCustomInput}
                    onKeyPress={handleKeyPress}
                  />
                </div>
              </div>
            </div>
          </div>
          
          <div className="action-section">
            <Button
              variant={isNextEnabled ? 'primary' : 'secondary'}
              disabled={!isNextEnabled}
              onClick={handleNext}
              className="next-button"
            >
              다음
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobSelectPage;


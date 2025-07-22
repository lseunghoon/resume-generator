import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import './JobSelectPage.css';

const JobSelectPage = () => {
  const [selectedJob, setSelectedJob] = useState('');
  const [customJob, setCustomJob] = useState('');
  const [isCustomInput, setIsCustomInput] = useState(false);
  const [extractedJobs, setExtractedJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { jobPostingUrl, extractedJobs: receivedJobs, jobDescription } = location.state || {};

  useEffect(() => {
    // 전달받은 추출된 직무 정보가 있으면 사용
    if (receivedJobs && receivedJobs.length > 0) {
      setExtractedJobs(receivedJobs);
      setIsLoading(false);
    } else {
      // 백업으로 이전 페이지로 리다이렉트
      navigate('/', { replace: true });
    }
  }, [receivedJobs, navigate]);

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
    const finalJob = isCustomInput ? customJob.trim() : selectedJob;
    if (finalJob) {
      navigate('/file-upload', { 
        state: { 
          jobPostingUrl, 
          selectedJob: finalJob,
          jobDescription
        } 
      });
    }
  };

  const handleBack = () => {
    navigate('/');
  };

  const isNextEnabled = isCustomInput ? customJob.trim() !== '' : selectedJob !== '';

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
    <div className="job-select-page">
      <Header progress={50} />
      
      <div className="page-content">
        <div className="content-wrapper">
          <div className="form-section">
            <button className="back-button" onClick={handleBack}>
              ←
            </button>
            
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
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && isNextEnabled) {
                        handleNext();
                      }
                    }}
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
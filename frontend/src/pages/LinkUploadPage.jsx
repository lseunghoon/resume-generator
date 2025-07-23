import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import Input from '../components/Input';
import { extractJobInfo } from '../services/api';
import './LinkUploadPage.css';

const LinkUploadPage = () => {
  const [jobPostingUrl, setJobPostingUrl] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState('');
  const [isValidUrl, setIsValidUrl] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    console.log('LinkUploadPage - location.state:', location.state);
    console.log('LinkUploadPage - jobPostingUrl from state:', location.state?.jobPostingUrl);
    
    // 이전에 입력한 URL이 있으면 복원
    if (location.state?.jobPostingUrl) {
      console.log('Restoring jobPostingUrl:', location.state.jobPostingUrl);
      setJobPostingUrl(location.state.jobPostingUrl);
      setIsValidUrl(validateUrl(location.state.jobPostingUrl));
    }
  }, [location.state]);

  const validateUrl = (url) => {
    try {
      const urlObj = new URL(url);
      // 유효한 URL인지 확인 (http 또는 https)
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handleUrlChange = (e) => {
    const url = e.target.value;
    setJobPostingUrl(url);
    
    if (url.trim() === '') {
      setIsValidUrl(false);
      setError('');
      return;
    }

    const valid = validateUrl(url);
    setIsValidUrl(valid);
    setError(valid ? '' : '올바른 URL 형식을 입력해주세요. (예: https://example.com)');
  };

  const handleExtractJobInfo = async () => {
    if (!jobPostingUrl.trim()) {
      setError('URL을 입력해주세요.');
      return;
    }

    setIsExtracting(true);
    setError('');

    try {
      const response = await extractJobInfo(jobPostingUrl);
      
      // 응답 구조에 맞게 수정
      const extractedJobs = response.positions || [];
      const jobDescription = response.jobDescription || '';
      
      console.log('LinkUploadPage - Navigating to job-select with state:', { 
        jobPostingUrl, 
        extractedJobs,
        jobDescription
      });
      
      navigate('/job-select', { 
        state: { 
          jobPostingUrl, 
          extractedJobs,
          jobDescription
        } 
      });
    } catch (error) {
      console.error('직무 정보 추출 오류:', error);
      setError(error.message || '직무 정보 추출에 실패했습니다.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && isValidUrl && !isExtracting) {
      handleExtractJobInfo();
    }
  };

  const handleGoBack = () => {
    // 첫 번째 페이지이므로 뒤로가기 없음
    console.log('LinkUploadPage - Back button clicked (no action)');
  };

  const handleGoForward = () => {
    if (isValidUrl && !isExtracting) {
      handleExtractJobInfo();
    }
  };

  return (
    <div className="link-upload-page">
      <Header 
        progress={25} 
        showNavigation={true}
        canGoBack={false} // 첫 번째 페이지이므로 뒤로가기 비활성화
        canGoForward={isValidUrl && !isExtracting} // 유효한 URL이 있을 때만 앞으로가기 활성화
        onGoBack={handleGoBack}
        onGoForward={handleGoForward}
        currentStep="1"
        totalSteps="4"
      />
      
      <div className="page-content">
        <div className="content-wrapper">
          <div className="form-section">
            <div className="form-content">
              <div className="form-header">
                <h1>지원하고자 하는 회사의 채용 공고를 첨부해주세요</h1>
                <p>채용 공고의 직무 정보를 분석해, 어떤 직무에 지원하시는지 정확히 이해하고 자기소개서를 도와드려요.<br/>
                </p>
              </div>
              
              <div className="form-input">
                <Input
                  placeholder="채용 공고 링크를 입력해주세요"
                  value={jobPostingUrl}
                  onChange={handleUrlChange}
                  onKeyPress={handleKeyPress}
                  error={error}
                  hasIcon={true}
                  iconType="send"
                  onIconClick={handleExtractJobInfo}
                  disabled={isExtracting}
                />
              </div>
            </div>
          </div>
          
          <div className="action-section">
            <Button
              variant={isValidUrl ? 'primary' : 'secondary'}
              disabled={!isValidUrl || isExtracting}
              onClick={handleExtractJobInfo}
              className="extract-button"
            >
              {isExtracting ? '직무 정보 추출 중...' : '직무 정보 추출'}
            </Button>
          </div>

          {isExtracting && (
            <div className="extracting-info">
              <div className="extracting-spinner"></div>
              <p>채용공고를 분석하고 있습니다...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LinkUploadPage; 
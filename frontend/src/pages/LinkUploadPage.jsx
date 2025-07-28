import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import NextButton from '../components/NextButton';
import Button from '../components/Button';
import Input from '../components/Input';
import { extractJobInfo } from '../services/api';
import './LinkUploadPage.css';

const LinkUploadPage = () => {
  const [jobPostingUrl, setJobPostingUrl] = useState('');
  const [htmlContent, setHtmlContent] = useState(''); // htmlContent 상태 추가
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState('');
  const [isValidUrl, setIsValidUrl] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    console.log('LinkUploadPage - location.state:', location.state);
    console.log('LinkUploadPage - jobPostingUrl from state:', location.state?.jobPostingUrl);
    
    // 이전에 입력한 URL이 있으면 복원
    if (location.state?.jobPostingUrl) {
      console.log('Restoring jobPostingUrl:', location.state.jobPostingUrl);
      setJobPostingUrl(location.state.jobPostingUrl);
      setHtmlContent(location.state.htmlContent || '');
      setIsValidUrl(validateUrl(location.state.jobPostingUrl));
    }
  }, [location.state]);

  const validateUrl = (url) => {
    try {
      // URL 앞뒤 공백 제거
      const trimmedUrl = url.trim();
      if (!trimmedUrl) return false;
      
      const urlObj = new URL(trimmedUrl);
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
      const response = await extractJobInfo(jobPostingUrl.trim());
      
      const extractedJobs = response.positions || [];
      const newHtmlContent = response.htmlContent || ''; // htmlContent 받기
      
      setHtmlContent(newHtmlContent); // 상태에 저장
      
      navigate('/job-select', { 
        state: { 
          jobPostingUrl: jobPostingUrl.trim(), 
          extractedJobs,
          htmlContent: newHtmlContent // 다음 페이지로 전달
        } 
      });
    } catch (error) {
      console.error('직무 정보 추출 오류:', error);
      
      // 크롤링 관련 오류인지 확인
      if (error.message && error.message.includes('로봇이 읽지 못하는 링크')) {
        // 알림 표시
        setNotificationMessage(error.message);
        setShowNotification(true);
        
        // 3초 후 알림 숨기기
        setTimeout(() => {
          setShowNotification(false);
          setNotificationMessage('');
        }, 3000);
      } else {
        setError(error.message || '직무 정보 추출에 실패했습니다.');
      }
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
      <Header progress={25} />
      
      {/* 알림 메시지 */}
      {showNotification && (
        <div className="notification-overlay">
          <div className="notification-message">
            <div className="notification-icon">⚠️</div>
            <div className="notification-content">
              <p className="notification-text">{notificationMessage}</p>
            </div>
          </div>
        </div>
      )}
      
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
                  hasIcon={false}
                  disabled={isExtracting}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <NextButton
        text="다음"
        disabled={!isValidUrl}
        loading={isExtracting}
        onClick={handleExtractJobInfo}
      />
    </div>
  );
};

export default LinkUploadPage; 
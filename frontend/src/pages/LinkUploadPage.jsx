import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import Input from '../components/Input';
import { extractJobInfo } from '../services/api';
import './LinkUploadPage.css';

const LinkUploadPage = () => {
  const [jobPostingUrl, setJobPostingUrl] = useState('');
  const [isValidUrl, setIsValidUrl] = useState(false);
  const [error, setError] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const navigate = useNavigate();

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
    if (!isValidUrl) return;
    
    setIsExtracting(true);
    setError('');
    
    try {
      const response = await extractJobInfo(jobPostingUrl);
      
      // 성공시 다음 페이지로 이동하며 추출된 직무 정보 전달
      navigate('/job-select', { 
        state: { 
          jobPostingUrl,
          extractedJobs: response.extractedJobs,
          jobDescription: response.jobDescription
        } 
      });
    } catch (err) {
      console.error('직무 정보 추출 실패:', err);
      setError('채용공고에서 직무 정보를 추출할 수 없습니다. URL을 확인해주세요.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && isValidUrl && !isExtracting) {
      handleExtractJobInfo();
    }
  };

  return (
    <div className="link-upload-page">
      <Header progress={25} />
      
      <div className="page-content">
        <div className="content-wrapper">
          <div className="form-section">
            <div className="form-content">
              <div className="form-header">
                <h1>지원하고자 하는 회사의 채용 공고를 첨부해주세요</h1>
                <p>채용 공고의 직무 정보를 분석해, 어떤 직무에 지원하시는지 정확히 이해하고 자기소개서를 도와드려요.<br/>
                <span className="supported-sites">모든 채용 사이트의 공고를 지원합니다.</span></p>
              </div>
              
              <div className="form-input">
                <Input
                  placeholder="채용 공고 링크를 첨부해주세요. (예: https://careers.kakao.com/jobs/P-14132)"
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
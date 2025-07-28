import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import NextButton from '../components/NextButton';
import Input from '../components/Input';
import './JobInfoInputPage.css';

const JobInfoInputPage = () => {
  const [formData, setFormData] = useState({
    companyName: '',
    jobTitle: '',
    mainResponsibilities: '',
    requirements: '',
    preferredQualifications: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // 이전에 입력한 데이터가 있으면 복원
  useEffect(() => {
    if (location.state?.jobInfo) {
      setFormData(location.state.jobInfo);
    }
  }, [location.state]);

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.companyName.trim()) {
      newErrors.companyName = '회사명을 입력해주세요.';
    } else if (formData.companyName.trim().length < 2) {
      newErrors.companyName = '회사명은 최소 2자 이상이어야 합니다.';
    }
    
    if (!formData.jobTitle.trim()) {
      newErrors.jobTitle = '직무를 입력해주세요.';
    } else if (formData.jobTitle.trim().length < 2) {
      newErrors.jobTitle = '직무는 최소 2자 이상이어야 합니다.';
    }
    
    if (!formData.mainResponsibilities.trim()) {
      newErrors.mainResponsibilities = '주요업무를 입력해주세요.';
    } else if (formData.mainResponsibilities.trim().length < 10) {
      newErrors.mainResponsibilities = '주요업무는 최소 10자 이상이어야 합니다.';
    }
    
    if (!formData.requirements.trim()) {
      newErrors.requirements = '자격요건을 입력해주세요.';
    } else if (formData.requirements.trim().length < 10) {
      newErrors.requirements = '자격요건은 최소 10자 이상이어야 합니다.';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // 실시간 유효성 검사 (에러가 있는 경우에만)
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // 채용정보를 다음 페이지로 전달
      navigate('/file-upload', {
        state: {
          jobInfo: formData
        }
      });
    } catch (error) {
      console.error('채용정보 처리 오류:', error);
      setErrors({ general: '채용정보 처리에 실패했습니다.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isSubmitting) {
      handleSubmit();
    }
  };

  return (
    <div className="job-info-input-page">
      <Header progress={25} />
      
      <div className="page-content">
        <div className="content-wrapper">
          <div className="form-section">
            <div className="form-content">
              <div className="form-header">
                <h1>지원하고자 하는 직무 정보를 입력해주세요</h1>
                <p>채용 공고의 정보를 직접 입력해주시면, 정확한 자기소개서를 도와드려요.</p>
              </div>
              
              <div className="form-inputs">
                <div className="input-group">
                  <label>회사명 *</label>
                  <Input
                    placeholder="예: 네이버, 카카오, 토스"
                    value={formData.companyName}
                    onChange={(e) => handleInputChange('companyName', e.target.value)}
                    onKeyPress={handleKeyPress}
                    error={errors.companyName}
                    hasIcon={false}
                    disabled={isSubmitting}
                  />
                </div>

                <div className="input-group">
                  <label>직무 *</label>
                  <Input
                    placeholder="예: 프론트엔드 개발자, 백엔드 개발자, 데이터 분석가"
                    value={formData.jobTitle}
                    onChange={(e) => handleInputChange('jobTitle', e.target.value)}
                    onKeyPress={handleKeyPress}
                    error={errors.jobTitle}
                    hasIcon={false}
                    disabled={isSubmitting}
                  />
                </div>

                <div className="input-group">
                  <label>주요업무 *</label>
                  <textarea
                    placeholder="담당하게 될 주요 업무 내용을 입력해주세요."
                    value={formData.mainResponsibilities}
                    onChange={(e) => handleInputChange('mainResponsibilities', e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isSubmitting}
                    className={errors.mainResponsibilities ? 'error' : ''}
                  />
                  {errors.mainResponsibilities && (
                    <div className="error-message">{errors.mainResponsibilities}</div>
                  )}
                </div>

                <div className="input-group">
                  <label>자격요건 *</label>
                  <textarea
                    placeholder="지원자격, 필수 경력, 기술 스택 등을 입력해주세요."
                    value={formData.requirements}
                    onChange={(e) => handleInputChange('requirements', e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isSubmitting}
                    className={errors.requirements ? 'error' : ''}
                  />
                  {errors.requirements && (
                    <div className="error-message">{errors.requirements}</div>
                  )}
                </div>

                <div className="input-group">
                  <label>우대사항 (선택)</label>
                  <textarea
                    placeholder="우대사항이 있다면 입력해주세요."
                    value={formData.preferredQualifications}
                    onChange={(e) => handleInputChange('preferredQualifications', e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isSubmitting}
                  />
                </div>

                {errors.general && (
                  <div className="error-message general">{errors.general}</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <NextButton
        text="다음"
        disabled={isSubmitting}
        loading={isSubmitting}
        onClick={handleSubmit}
      />
    </div>
  );
};

export default JobInfoInputPage; 
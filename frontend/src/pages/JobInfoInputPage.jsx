import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import NextButton from '../components/NextButton';
import Input from '../components/Input';
import './JobInfoInputPage.css';

// Mock 데이터 (보이저엑스 서비스기획 인턴)
const mockJobData = {
  companyName: "보이저엑스",
  jobTitle: "서비스기획",
  mainResponsibilities: `보이저엑스의 서비스 기획 인턴은 다음과 같은 활동을 통해 사용자들이 보이저엑스의 여러 서비스들을 더욱 즐겁고 편리하게 사용할 수 있도록 합니다.

**■ 주요 업무:**

a. 문제의 발견: 정량적, 정성적인 방법으로 사용자가 겪고 있는 문제를 발견합니다.

b. 문제의 정리: 발견한 문제를 논리적이고 체계적으로 잘 정리합니다.

c. 문제의 공유: 정리된 문제를 여러가지 방법으로 잘 공유합니다.

d. 해결책의 제시: 문제의 해결책을 제시합니다.

**■ 추가 업무:**

e. 그 외 사용자 응대 등 보이저엑스의 서비스 기획자가 하고 있는 모든 일의 보조`,
  requirements: `**■  필수 요건:**

1. 인턴 지원 자격에 해당하는 분
2. 성실하고 꼼꼼한 분
3. 정직하고 책임감이 강한 분
4. 공감하고 경청할 수 있는 분
5. 각종 소프트웨어를 잘 다루는 분
6. 글을 잘 읽고 잘 쓸 수 있는 분
7. 논리적이고 분석적인 분`,
  preferredQualifications: `**■ 우대 사항:** 

1. 영어 또는 일본어로 의사 소통이 가능한 분`
};

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

  // 이전에 입력한 데이터가 있으면 복원, Mock API 모드일 때는 자동 채우기
  useEffect(() => {
    if (location.state?.jobInfo) {
      setFormData(location.state.jobInfo);
    } else if (localStorage.getItem('useMockApi') === 'true' && localStorage.getItem('mockJobDataFilled') === 'true') {
      // Mock API 모드이고 Mock 데이터 채우기 플래그가 설정되어 있을 때 자동으로 데이터 채우기
      setFormData(mockJobData);
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
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Input from '../components/Input';
import Navigation from '../components/Navigation';
import { supabase } from '../services/supabaseClient';
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

// 단계별 설정
const STEPS = [
  { id: 'companyName', title: '지원하고자 하는 회사 이름을 입력해 주세요', placeholder: '예시) 삼성디스플레이, 아토머스, 보이저엑스' },
  { id: 'jobTitle', title: '직무를 입력해 주세요', placeholder: '예시) 사업개발, 서비스기획자' },
      { id: 'mainResponsibilities', title: '주요 업무를 입력해 주세요', placeholder: `예시)

■ 주요 업무:
a. 문제의 발견: 정량적, 정성적인 방법으로 사용자가 겪고 있는 문제를 발견합니다.
b. 문제의 정리: 발견한 문제를 논리적이고 체계적으로 잘 정리합니다.
c. 문제의 공유: 정리된 문제를 여러가지 방법으로 잘 공유합니다.
d. 해결책의 제시: 문제의 해결책을 제시합니다.

■ 추가 업무:
e. 그 외 사용자 응대 등 보이저엑스의 서비스 기획자가 하고 있는 모든 일의 보조` },
    { id: 'requirements', title: '자격요건을 입력해 주세요', placeholder: `예시)
      
■  필수 요건:
1. 인턴 지원 자격에 해당하는 분
2. 성실하고 꼼꼼한 분
3. 정직하고 책임감이 강한 분
4. 공감하고 경청할 수 있는 분
5. 각종 소프트웨어를 잘 다루는 분
6. 글을 잘 읽고 잘 쓸 수 있는 분
7. 논리적이고 분석적인 분` },
  { id: 'preferredQualifications', title: '우대사항을 입력해 주세요', placeholder: '예시) 영어 가능자, 일본어 가능자' }
];

const JobInfoInputPage = ({ currentStep, setCurrentStep }) => {
  const [formData, setFormData] = useState({
    companyName: '',
    jobTitle: '',
    mainResponsibilities: '',
    requirements: '',
    preferredQualifications: ''
  });
  // currentStep은 props로 받아옴
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorKey, setErrorKey] = useState(0); // 에러 애니메이션을 위한 key
  // showLoginModal은 props로 받아옴
  const navigate = useNavigate();
  const location = useLocation();
  
  // 각 입력 필드에 대한 ref 생성
  const inputRefs = {
    companyName: useRef(null),
    jobTitle: useRef(null),
    mainResponsibilities: useRef(null),
    requirements: useRef(null),
    preferredQualifications: useRef(null)
  };

  // 인증 상태 확인: 비로그인 시 로그인 페이지로 리다이렉트
  useEffect(() => {
    const checkAuthAndRedirect = async () => {
      const { data, error } = await supabase.auth.getSession();
      if (error || !data?.session) {
        try {
          localStorage.setItem('auth_redirect_path', '/job-info');
        } catch (_) {}
        navigate('/login?next=/job-info', { replace: true });
      }
    };
    checkAuthAndRedirect();
  }, [navigate]);

  // currentStep이 변경될 때마다 App.js의 currentStep 업데이트
  useEffect(() => {
    if (setCurrentStep) {
      setCurrentStep(currentStep);
    }
  }, [currentStep, setCurrentStep]);

  // 로그인 모달 제거에 따라 body overflow 제어 로직 삭제

  // 이전에 입력한 데이터가 있으면 복원, Mock API 모드일 때는 자동 채우기
  useEffect(() => {
    // location.state가 존재하고 jobInfo가 있으며 fromFileUpload가 true인 경우에만 데이터 복원
    if (location.state?.jobInfo && location.state?.fromFileUpload === true) {
      console.log('정상적인 뒤로가기 감지 - 데이터 복원');
      setFormData(location.state.jobInfo);
      
      // goToLastStep이 true인 경우, 마지막 단계로 이동
      if (location.state?.goToLastStep) {
        setCurrentStep(STEPS.length - 1); // 우대사항 단계(마지막 단계)로 설정
        console.log('파일업로드 페이지에서 돌아옴 - 우대사항 단계로 이동');
      }
    } else if (location.state?.scrollTo) {
      // 헤더 메뉴 클릭으로 인한 scrollTo state가 있는 경우 무시
      console.log('헤더 메뉴 클릭으로 인한 state 감지 - 첫 단계로 시작');
      setCurrentStep(0); // 명시적으로 첫 단계로 설정
    } else if (localStorage.getItem('useMockApi') === 'true' && localStorage.getItem('mockJobDataFilled') === 'true') {
      // Mock API 모드이고 Mock 데이터 채우기 플래그가 설정되어 있을 때 자동으로 데이터 채우기
      console.log('Mock API 모드 - 자동 데이터 채우기');
      setFormData(mockJobData);
    } else {
      // 일반적인 새 시작의 경우
      console.log('새로운 시작 - 첫 단계부터 시작');
      setCurrentStep(0);
    }
    
    console.log('JobInfoInputPage 진입:', {
      hasJobInfo: !!location.state?.jobInfo,
      fromFileUpload: location.state?.fromFileUpload,
      goToLastStep: location.state?.goToLastStep,
      scrollTo: location.state?.scrollTo,
      currentStep: currentStep
    });
  }, [location.state]);

  // 현재 단계의 입력 필드에 자동 포커스
  useEffect(() => {
    const currentField = STEPS[currentStep].id;
    const currentRef = inputRefs[currentField];
    
    // 페이지 로드 시나 단계 변경 시 해당 입력 필드에 포커스
    setTimeout(() => {
      if (currentRef && currentRef.current) {
        currentRef.current.focus();
      }
    }, 100);
  }, [currentStep]); // currentStep이 변경될 때마다 실행

  const currentStepData = STEPS[currentStep];
  const isRequirementsStep = currentStepData.id === 'requirements';
  const isPreferredQualificationsStep = currentStepData.id === 'preferredQualifications';
  
  // 현재 단계의 필수 입력값 확인
  const isCurrentStepValid = () => {
    // 자격요건과 우대사항은 선택항목이므로 항상 유효
    if (isRequirementsStep || isPreferredQualificationsStep) {
      return true;
    }
    
    // 모든 단계들은 버튼 클릭 시 검증하므로 항상 true 반환
    return true;
  };



  // validateCurrentStep 함수는 사용되지 않으므로 제거

  const handleInputChange = (value) => {
    const currentField = currentStepData.id;
    setFormData(prev => ({
      ...prev,
      [currentField]: value
    }));
    
    // 실시간 유효성 검사 (에러가 있는 경우에만)
    if (errors[currentField]) {
      setErrors(prev => ({
        ...prev,
        [currentField]: ''
      }));
    }
  };

  const handleNext = () => {
    const currentField = currentStepData.id;
    const currentValue = formData[currentField];
    
    // 모든 단계들은 버튼 클릭 시 검증
    const newErrors = {};
    
    if (!currentValue.trim()) {
      if (currentField === 'companyName') {
        newErrors[currentField] = '회사명을 입력해 주세요';
      } else if (currentField === 'jobTitle') {
        newErrors[currentField] = '직무를 입력해 주세요';
      } else if (currentField === 'mainResponsibilities') {
        newErrors[currentField] = '주요 업무를 입력해 주세요';
      }
    } else if (currentField === 'mainResponsibilities' && currentValue.trim().length < 10) {
      // 주요업무는 10자 이상 검증
      newErrors[currentField] = '주요 업무는 최소 10자 이상으로 입력해야 합니다';
    } else if (currentValue.trim().length < 2) {
      // 회사명과 직무는 2자 이상 검증
      if (currentField === 'companyName') {
        newErrors[currentField] = '회사명은 최소 2자 이상으로 입력해야 합니다';
      } else if (currentField === 'jobTitle') {
        newErrors[currentField] = '직무는 최소 2자 이상으로 입력해야 합니다';
      }
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setErrorKey(prev => prev + 1);
      
      // 에러가 발생한 필드에 포커스 이동
      setTimeout(() => {
        const currentRef = inputRefs[currentField];
        if (currentRef && currentRef.current) {
          currentRef.current.focus();
        }
      }, 100);
      return;
    }

    // 주요업무 단계 유효성 검사 성공 시 GA 이벤트 발송
    if (currentField === 'mainResponsibilities') {
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({
        'event': 'job_info_success'
      });
    }

    if (currentStep === STEPS.length - 1) {
      // 마지막 단계(우대사항)에서 다음을 누르면 파일업로드 페이지로 이동
      handleSubmit();
    } else {
      setCurrentStep(prev => prev + 1);
      setErrors({});
      
      // 다음 단계로 이동한 후 해당 입력 필드에 포커스
      setTimeout(() => {
        const nextField = STEPS[currentStep + 1].id;
        const nextRef = inputRefs[nextField];
        if (nextRef && nextRef.current) {
          nextRef.current.focus();
        }
      }, 100); // 상태 업데이트 후 포커스 이동
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
      setErrors({});
      
      // 이전 단계로 이동한 후 해당 입력 필드에 포커스
      setTimeout(() => {
        const prevField = STEPS[currentStep - 1].id;
        const prevRef = inputRefs[prevField];
        if (prevRef && prevRef.current) {
          prevRef.current.focus();
        }
      }, 100); // 상태 업데이트 후 포커스 이동
    } else {
      // 첫 번째 단계에서 뒤로가기를 누르면 랜딩페이지로 이동
      navigate('/', { replace: true });
    }
  };

  const handleSkip = () => {
    // 건너뛰기 시 다음 단계로 이동
    if (currentStep === STEPS.length - 1) {
      handleSubmit();
    } else {
      setCurrentStep(prev => prev + 1);
      setErrors({});
      
      // 다음 단계로 이동한 후 해당 입력 필드에 포커스
      setTimeout(() => {
        const nextField = STEPS[currentStep + 1].id;
        const nextRef = inputRefs[nextField];
        if (nextRef && nextRef.current) {
          nextRef.current.focus();
        }
      }, 100); // 상태 업데이트 후 포커스 이동
    }
  };

  const handleSubmit = async () => {
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
      setErrors({ general: '채용정보 처리에 실패했습니다' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyPress = (e) => {
    const currentField = currentStepData.id;
    const isTextarea = currentField === 'mainResponsibilities' || currentField === 'requirements' || currentField === 'preferredQualifications';
    
    // textarea가 아닌 경우에만 엔터 키로 다음 단계 이동
    if (e.key === 'Enter' && !isSubmitting && !isTextarea) {
      handleNext();
    }
  };

  const renderInput = () => {
    const currentField = currentStepData.id;
    const currentValue = formData[currentField];
    const isTextarea = currentField === 'mainResponsibilities' || currentField === 'requirements' || currentField === 'preferredQualifications';

    if (isTextarea) {
      return (
        <div className="textarea-container">
          <textarea
            ref={inputRefs[currentField]}
            placeholder={currentStepData.placeholder}
            value={currentValue}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isSubmitting}
            className={errors[currentField] ? 'error' : ''}
            rows={8}
          />
          {errors[currentField] && (
            <div key={`error-${currentField}-${errorKey}`} className="input-error-message">{errors[currentField]}</div>
          )}
        </div>
      );
    }

    return (
      <Input
        key={`input-${currentField}-${errorKey}`}
        ref={inputRefs[currentField]}
        placeholder={currentStepData.placeholder}
        value={currentValue}
        onChange={(e) => handleInputChange(e.target.value)}
        onKeyPress={handleKeyPress}
        error={errors[currentField]}
        hasIcon={false}
        disabled={isSubmitting}
        className="job-info-input"
      />
    );
  };

  return (
    <div className={`job-info-input-page`}>
      <Helmet>
        <title>채용정보 입력 | 써줌 - 맞춤형 자기소개서 생성</title>
        <meta name="description" content="지원하고자 하는 회사와 직무 정보를 입력하여 해당 포지션에 최적화된 자기소개서를 생성하세요. 회사명, 직무, 주요업무, 자격요건 입력 지원." />
        <meta name="robots" content="noindex, nofollow" />
        
        {/* Open Graph 태그 */}
        <meta property="og:title" content="채용정보 입력 | 써줌 - 맞춤형 자기소개서 생성" />
        <meta property="og:description" content="지원하고자 하는 회사와 직무 정보를 입력하여 해당 포지션에 최적화된 자기소개서를 생성하세요." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://www.sseojum.com/job-info" />
      </Helmet>
      
      <div className="page-content">
        <Navigation 
          canGoBack={true}
          onGoBack={handlePrevious}
        />
        
        <div className="content-wrapper">
          <div className="form-section">
            <div className="form-content">
              
              <div className="form-header">
                <h1>{currentStepData.title}</h1>
                <p>자세히 입력할수록 완성도 높은 자기소개서를 작성할 수 있어요</p>
              </div>
              
              <div className="form-inputs">
                <div className="input-container">
                  {renderInput()}
                </div>

                {errors.general && (
                  <div className="error-message general">{errors.general}</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="button-container">
        {(isRequirementsStep || isPreferredQualificationsStep) && (
          <button 
            className="skip-button"
            onClick={handleSkip}
            disabled={isSubmitting}
          >
            건너뛰기
          </button>
        )}
        <button 
          {...(STEPS[currentStep].id === 'mainResponsibilities' && { id: 'submit-job-info-btn' })}
          className={`next-button ${isCurrentStepValid() ? 'active' : 'disabled'}`}
          onClick={handleNext}
          disabled={isSubmitting || !isCurrentStepValid()}
        >
          다음
        </button>
      </div>
    </div>
  );
};

export default JobInfoInputPage; 
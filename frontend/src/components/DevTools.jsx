import React, { useState, useEffect } from 'react';
import { enableMockApi, disableMockApi, isMockApiEnabled } from '../services/mockApi';
import './DevTools.css';

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

const DevTools = () => {
  const [isMockEnabled, setIsMockEnabled] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsMockEnabled(isMockApiEnabled());
  }, []);

  const handleMockToggle = () => {
    if (isMockEnabled) {
      disableMockApi();
      setIsMockEnabled(false);
      // Mock 모드 비활성화 시 localStorage에서 Mock 데이터 관련 정보 제거
      localStorage.removeItem('mockJobDataFilled');
    } else {
      enableMockApi();
      setIsMockEnabled(true);
      // Mock 모드 활성화 시 Mock 데이터 자동 채우기 플래그 설정
      localStorage.setItem('mockJobDataFilled', 'true');
      // 페이지 새로고침하여 JobInfoInputPage에서 자동 채우기 적용
      window.location.reload();
    }
  };

  const toggleVisibility = () => {
    setIsVisible(!isVisible);
  };

  // 개발 환경에서만 표시
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className="dev-tools">
      <button 
        className="dev-tools-toggle"
        onClick={toggleVisibility}
        title="개발자 도구"
      >
        🔧
      </button>
      
      {isVisible && (
        <div className="dev-tools-panel">
          <h3>개발자 도구</h3>
          
          <div className="dev-tools-section">
            <h4>API 모드</h4>
            <div className="dev-tools-control">
              <label>
                <input
                  type="checkbox"
                  checked={isMockEnabled}
                  onChange={handleMockToggle}
                />
                Mock API 사용
              </label>
              <p className="dev-tools-description">
                {isMockEnabled 
                  ? "백엔드 없이 Mock 데이터로 테스트 중"
                  : "실제 백엔드 API 사용 중"
                }
              </p>
            </div>
          </div>

          <div className="dev-tools-section">
            <h4>테스트 가이드</h4>
            <div className="dev-tools-info">
              <p><strong>Mock 모드 활성화 시:</strong></p>
              <ul>
                <li>채용정보 입력: 보이저엑스 서비스기획 인턴 데이터 자동 채워짐</li>
                <li>직무 정보 추출: 아무 URL이나 입력하면 Mock 데이터 반환</li>
                <li>자기소개서 생성: 2초 후 Mock 결과 반환</li>
                <li>문항 추가: 즉시 Mock 답변 생성</li>
                <li>답변 수정: Mock 수정 결과 반환</li>
              </ul>
              <p><strong>Mock 데이터:</strong></p>
              <ul>
                <li>회사명: 보이저엑스</li>
                <li>직무: 서비스기획</li>
                <li>주요업무, 자격요건, 우대사항 포함</li>
              </ul>
            </div>
          </div>

          <div className="dev-tools-section">
            <h4>현재 상태</h4>
            <div className="dev-tools-status">
              <p>환경: {process.env.NODE_ENV}</p>
              <p>API URL: {process.env.REACT_APP_API_URL || 'http://localhost:5000'}</p>
              <p>Mock 모드: {isMockEnabled ? '활성화' : '비활성화'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DevTools; 
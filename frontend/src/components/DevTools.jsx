import React, { useState, useEffect } from 'react';
import { useMockApi, disableMockApi, isMockApiEnabled } from '../services/mockApi';
import './DevTools.css';

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
    } else {
      useMockApi();
      setIsMockEnabled(true);
    }
    // 페이지 새로고침 없이 상태만 업데이트
    // window.location.reload();
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
                <li>직무 정보 추출: 아무 URL이나 입력하면 Mock 데이터 반환</li>
                <li>자기소개서 생성: 2초 후 Mock 결과 반환</li>
                <li>문항 추가: 즉시 Mock 답변 생성</li>
                <li>답변 수정: Mock 수정 결과 반환</li>
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
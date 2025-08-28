import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDocumentMeta } from '../hooks/useDocumentMeta';
import Navigation from '../components/Navigation';
import { supabase } from '../services/supabaseClient';
import './FileUploadPage.css';

const FileUploadPage = () => {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' 또는 'manual'
  const [uploadedFiles, setUploadedFiles] = useState([]); // 다중 파일을 배열로 관리
  const [manualText, setManualText] = useState(''); // 직접 입력 텍스트
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState('');
  const [jobInfo, setJobInfo] = useState(null); // 새로운 채용정보 입력 방식
  const [showSkipModal, setShowSkipModal] = useState(false); // 건너뛰기 확인 모달
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  // 인증 상태 확인 (리다이렉트 없이 상태만 체크)
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  useEffect(() => {
    const checkAuthStatus = async () => {
      const { data, error } = await supabase.auth.getSession();
      if (!error && data?.session) {
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    };
    checkAuthStatus();
  }, []);

  useEffect(() => {
    if (location.state) {
      // 새로운 채용정보 입력 방식 데이터
      setJobInfo(location.state.jobInfo || null);
      
      // 이전에 업로드한 파일들이 있으면 복원 (현재 세션에서만)
      if (location.state.uploadedFiles && location.state.uploadedFiles.length > 0) {
        const restoredFiles = location.state.uploadedFiles.map((file, index) => ({
          id: Date.now() + index + Math.random(),
          file: file,
          name: file.name,
          size: file.size
        }));
        setUploadedFiles(restoredFiles);
      }
      
      // 직접 입력 텍스트가 있다면 복원
      if (location.state.manualText) {
        setManualText(location.state.manualText);
      }
      
      // 활성 탭이 있다면 복원
      if (location.state.activeTab) {
        setActiveTab(location.state.activeTab);
      }
    } else {
      // 로그인 후 임시 저장된 데이터 복원 시도
      try {
        const tempFileUpload = localStorage.getItem('temp_file_upload');
        if (tempFileUpload) {
          const parsed = JSON.parse(tempFileUpload);
          const now = Date.now();
          // 30분 이내의 데이터만 복원 (1800000ms = 30분)
          if (now - parsed.timestamp < 1800000) {
            console.log('파일업로드 임시 데이터 복원');
            setJobInfo(parsed.jobInfo);
            
            // 활성 탭 복원
            if (parsed.activeTab) {
              setActiveTab(parsed.activeTab);
            }
            
            // 직접 입력 텍스트 복원
            if (parsed.manualText) {
              setManualText(parsed.manualText);
            }
            
            // 건너뛰기였다면 바로 다음 페이지로 이동
            if (parsed.skipped) {
              console.log('건너뛰기 복원 - 다음 페이지로 이동');
              localStorage.removeItem('temp_file_upload');
              navigate('/question', { 
                state: { 
                  uploadedFiles: [],
                  manualText: '',
                  jobInfo: parsed.jobInfo,
                  question: ''
                } 
              });
              return;
            }
            
            // 파일 메타데이터가 있다면 안내 메시지 표시 (실제 파일은 복원 불가)
            if (parsed.uploadedFiles && parsed.uploadedFiles.length > 0) {
              setError('로그인 전에 업로드한 파일은 보안상 다시 업로드해주세요.');
            }
            
            // 사용한 임시 데이터 삭제
            localStorage.removeItem('temp_file_upload');
            return;
          } else {
            // 오래된 데이터 삭제
            localStorage.removeItem('temp_file_upload');
          }
        }
      } catch (e) {
        console.error('파일업로드 임시 데이터 복원 실패:', e);
        localStorage.removeItem('temp_file_upload');
      }
      
      // 상태가 없어도 페이지를 표시 (SEO 최적화)
      // 비로그인 상태에서도 콘텐츠를 볼 수 있어야 함
    }
  }, [location.state, navigate, isAuthenticated]);

  const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  const maxFileSize = 50 * 1024 * 1024; // 단일 파일 50MB 허용
  const maxFiles = 3;
  const maxTotalSize = 50 * 1024 * 1024; // 3개 도합 50MB

  const validateFile = (file) => {
    if (!allowedTypes.includes(file.type)) {
      setError('PDF, DOC, DOCX 파일만 업로드 가능합니다');
      return false;
    }
    
    if (file.size > maxFileSize) {
      setError('첨부파일의 용량이 50mb를 초과했습니다.');
      return false;
    }
    
    // 중복 파일 검사
    if (uploadedFiles.some(f => f.name === file.name && f.size === file.size)) {
      setError('이미 업로드된 파일입니다');
      return false;
    }
    
    setError('');
    return true;
  };

  const handleFileSelect = (files) => {
    const fileArray = Array.from(files);
    const validFiles = [];
    
    // 디버깅: 파일 크기 로깅
    console.log('=== 파일 업로드 디버깅 ===');
    let totalSize = 0;
    
    for (const file of fileArray) {
      console.log(`파일: ${file.name}, 크기: ${file.size} bytes (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
      totalSize += file.size;
      
      if (uploadedFiles.length + validFiles.length >= maxFiles) {
        setError(`최대 ${maxFiles}개까지만 업로드 가능합니다.`);
        break;
      }
      
      if (validateFile(file)) {
        validFiles.push({
          id: Date.now() + Math.random(), // 고유 ID 생성
          file: file,
          name: file.name,
          size: file.size
        });
      }
    }
    
    console.log(`총 파일 크기: ${totalSize} bytes (${(totalSize / 1024 / 1024).toFixed(2)} MB)`);
    // 총합 50MB 제한 검사
    const newTotal = getTotalSize() + validFiles.reduce((sum, f) => sum + f.size, 0);
    if (newTotal > maxTotalSize) {
      setError('첨부파일의 용량이 50mb를 초과했습니다. (최대 3개, 총합 50MB)');
      return;
    }
    console.log('========================');
    
    if (validFiles.length > 0) {
      setUploadedFiles(prev => [...prev, ...validFiles]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files);
    }
  };

  const handleFileInputChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFileSelect(files);
    }
    // 입력 값 초기화 (같은 파일을 다시 선택할 수 있도록)
    e.target.value = '';
  };

  const handleFileInputClick = () => {
    if (uploadedFiles.length < maxFiles) {
      fileInputRef.current?.click();
    }
  };

  const handleRemoveFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
    setError('');
  };

  const handleNext = () => {
    // 데이터 유효성 체크
    const hasFiles = uploadedFiles.length > 0;
    const hasManualText = manualText.trim().length > 0;
    
    // 둘 다 없으면 건너뛰기 모달 표시
    if (!hasFiles && !hasManualText) {
      setShowSkipModal(true);
      return;
    }

    // method 판단 및 이벤트 발송
    const method = determineMethod();
    sendFileUploadEvent(method);

    // 로그인 체크
    if (!isAuthenticated) {
      // 현재 업로드 데이터와 채용정보를 localStorage에 저장
      try {
        localStorage.setItem('auth_redirect_path', '/job-info');
        localStorage.setItem('temp_file_upload', JSON.stringify({
          jobInfo: jobInfo,
          activeTab: activeTab,
          uploadedFiles: uploadedFiles.map(f => ({
            name: f.name,
            size: f.size,
            type: f.file?.type || 'application/pdf'
          })), // File 객체는 직렬화할 수 없으므로 메타데이터만 저장
          manualText: manualText,
          timestamp: Date.now()
        }));
      } catch (_) {}
      navigate('/login?next=/job-info', { replace: true });
      return;
    }

    // 업로드된 파일들의 실제 File 객체들을 전달
    const fileObjects = uploadedFiles.map(f => f.file);
    
    navigate('/question', { 
      state: { 
        uploadedFiles: fileObjects, // 다중 파일 배열로 전달
        manualText: manualText, // 직접 입력 텍스트 전달
        activeTab: activeTab, // 활성 탭 정보 전달
        jobInfo, // 새로운 채용정보 입력 방식 데이터 전달
        question: location.state?.question || '', // 이전에 입력한 질문 전달
        skipResumeUpload: !hasFiles && !hasManualText // 둘 다 없으면 건너뛰기 플래그 추가
      } 
    });
  };

  const handleSkip = () => {
    // 건너뛰기 확인 모달 표시
    setShowSkipModal(true);
  };

  const handleConfirmSkip = () => {
    // 건너뛰기 이벤트 발송
    sendFileUploadEvent('skip');

    // 로그인 체크
    if (!isAuthenticated) {
      // 현재 채용정보를 localStorage에 저장 (파일 없이 건너뛰기)
      try {
        localStorage.setItem('auth_redirect_path', '/job-info');
        localStorage.setItem('temp_file_upload', JSON.stringify({
          jobInfo: jobInfo,
          uploadedFiles: [], // 건너뛰기이므로 빈 배열
          skipped: true, // 건너뛰기 플래그
          timestamp: Date.now()
        }));
      } catch (_) {}
      navigate('/login?next=/job-info', { replace: true });
      return;
    }

    // 실제 건너뛰기 실행
    navigate('/question', { 
      state: { 
        uploadedFiles: [], // 빈 배열
        manualText: '', // 빈 문자열
        activeTab: activeTab, // 활성 탭 정보 전달
        jobInfo, // 새로운 채용정보 입력 방식 데이터 전달
        question: location.state?.question || '', // 이전에 입력한 질문 전달
        skipResumeUpload: true // 건너뛰기 플래그 추가
      } 
    });
  };

  const handleUploadFromModal = () => {
    // 모달 닫기
    setShowSkipModal(false);
    
    // 문서 업로드 탭일 때만 파일 업로드 실행
    if (activeTab === 'upload') {
      if (fileInputRef.current) {
        fileInputRef.current.click();
      }
    }
    // 직접 입력 탭일 때는 단순히 모달만 닫고 사용자가 직접 입력하도록 함
  };

  const handleGoBack = () => {
    // 현재 입력된 데이터를 localStorage에 저장
    try {
      localStorage.setItem('temp_file_upload', JSON.stringify({
        jobInfo: jobInfo,
        activeTab: activeTab,
        uploadedFiles: uploadedFiles.map(f => ({
          name: f.name,
          size: f.size,
          type: f.file?.type || 'application/pdf'
        })),
        manualText: manualText,
        timestamp: Date.now()
      }));
    } catch (_) {}

    // JobInfoInputPage의 우대사항 단계(마지막 단계)로 돌아가기
    navigate('/job-info', { 
      state: { 
        jobInfo: jobInfo,
        fromFileUpload: true,
        goToLastStep: true, // 우대사항 단계로 이동하기 위한 플래그
        // FileUploadPage 데이터 전달
        fileUploadData: {
          uploadedFiles: uploadedFiles,
          manualText: manualText,
          activeTab: activeTab
        },
        // QuestionPage 데이터 전달 (location.state에서 가져온 경우)
        questionData: location.state?.question ? {
          question: location.state.question
        } : null
      } 
    });
  };

  // handleGoForward 함수는 사용되지 않으므로 제거

  const handleKeyPress = (e) => {
    // textarea나 input이 포커스되어 있을 때는 전역 키보드 이벤트 무시
    if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') {
      return;
    }
    
    // Enter 키만 눌렀을 때는 다음 버튼 작동
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleNext();
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getTotalSize = () => {
    return uploadedFiles.reduce((total, file) => total + file.size, 0);
  };

    const canUploadMore = uploadedFiles.length < maxFiles;

  // Google Analytics 이벤트 발송 함수
  const sendFileUploadEvent = (method) => {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      'event': 'submit_file_upload',
      'method': method
    });
  };

  // method 판단 함수
  const determineMethod = () => {
    const hasFiles = uploadedFiles.length > 0;
    const hasManualText = manualText.trim().length > 0;
    
    if (hasFiles && hasManualText) return 'both';
    if (hasFiles) return 'file_upload';
    if (hasManualText) return 'manual_input';
    return 'skip';
  };

	// SEO 메타데이터 설정
	useDocumentMeta({
		title: "이력서 업로드 | 써줌 - 맞춤형 자기소개서 생성",
		description: "기존 이력서나 자기소개서를 업로드하여 더욱 개인화된 맞춤형 자기소개서를 생성하세요. PDF, DOC, DOCX 파일 지원.",
		robots: "noindex, nofollow",
		ogTitle: "이력서 업로드 | 써줌 - 맞춤형 자기소개서 생성",
		ogDescription: "기존 이력서나 자기소개서를 업로드하여 더욱 개인화된 맞춤형 자기소개서를 생성하세요.",
		ogType: "website",
		ogUrl: "https://www.sseojum.com/file-upload"
	});

	return (
		<div className="file-upload-page" onKeyPress={handleKeyPress} tabIndex={0}>
      
      <div className="page-content">
        <Navigation
          canGoBack={true}
          onGoBack={handleGoBack}
        />
        
        <div className="content-wrapper">
          <div className="form-section">
            
            <div className="form-content">
              {/* 탭 메뉴 */}
              <div className="tab-menu">
                <button 
                  className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
                  onClick={() => setActiveTab('upload')}
                >
                  문서 업로드
                </button>
                <button 
                  className={`tab-button ${activeTab === 'manual' ? 'active' : ''}`}
                  onClick={() => setActiveTab('manual')}
                >
                  직접 입력
                </button>
              </div>

              <div className="form-header">
                {activeTab === 'upload' ? (
                  <>
                    <h1>기존 자기소개서나 이력서를<br/>업로드해 주세요</h1>
                    <p>더욱 개인화된 자기소개서 작성을 위해 건너뛰지 않는 것을 추천해요<br/>
                    </p>
                  </>
                ) : (
                  <>
                    <h1>자기소개서 작성에 도움이 될<br/>경험을 입력해 주세요</h1>
                    <p>구체적이고 상세할수록 더 개인화된 자기소개서를 만들 수 있어요<br/>
                    </p>
                  </>
                )}
              </div>
              
              {/* 문서 업로드 탭 */}
              {activeTab === 'upload' && (
                <div className="upload-section">
                <div className="upload-stats">
                  <span className="file-count">{uploadedFiles.length}</span>
                  <span className="file-separator">/</span>
                  <span className="max-files">3개</span>
                  <span className="size-info">({formatFileSize(getTotalSize())} / 50MB)</span>
                </div>
                
                <div className="upload-content">
                  {/* 업로드된 파일 목록 */}
                  {uploadedFiles.map((fileItem) => (
                    <div key={fileItem.id} className="uploaded-file-item">
                      <div className="file-info">
                        <span className="file-name">{fileItem.name}</span>
                        <span className="file-size">({formatFileSize(fileItem.size)})</span>
                      </div>
                      <button 
                        className="remove-file-button" 
                        onClick={() => handleRemoveFile(fileItem.id)}
                        aria-label="파일 삭제"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  
                  {/* 업로드 영역 (파일이 3개 미만일 때만 표시) */}
                  {canUploadMore && (
                    <div 
                      className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      onClick={handleFileInputClick}
                    >
                      <div className="upload-content-inner">
                        <span className="upload-text">첨부 파일을 업로드해 주세요</span>
                      </div>
                      <div className="upload-icon">
                        <img 
                          src="/assets/upload_file.svg" 
                          alt="파일 업로드" 
                          className="upload-icon-svg"
                        />
                      </div>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.doc,.docx"
                        multiple
                        onChange={handleFileInputChange}
                        style={{ display: 'none' }}
                      />
                    </div>
                  )}
                </div>
                
                <div className="upload-notes">
                  <p>* 첨부 파일은 최대 3개, 총합 50MB 까지 업로드 가능합니다.</p>
                  <p>* pdf, docx 파일만 업로드 가능합니다.</p>
                </div>
                
                {/* 문서 업로드 탭에도 가이드 섹션 추가 */}
                <div className="manual-input-guide">
                  <h4>이런 내용을 포함하면 좋아요</h4>
                  <ul>
                    <li><strong>경험과 성과 :</strong> 인턴십, 프로젝트, 아르바이트에서 얻은 성과와 배운 점</li>
                    <li><strong>대외활동 :</strong> 동아리, 봉사활동, 공모전 참여 경험과 역할</li>
                    <li><strong>역량과 강점 :</strong> 문제해결력, 리더십, 커뮤니케이션 등 구체적인 사례</li>
                    <li><strong>학습과 성장 :</strong> 새로운 기술 습득, 어려움 극복 과정</li>
                    <li><strong>협업 경험 :</strong> 팀워크, 갈등 해결, 목표 달성 사례</li>
                  </ul>
                </div>
                
                {error && (
                  <div className="error-message">
                    {error}
                  </div>
                )}
                </div>
              )}

              {/* 직접 입력 탭 */}
              {activeTab === 'manual' && (
                <div className="manual-input-section">
                  <div className="manual-input-content">
                    <textarea
                      className="manual-text-input"
                      placeholder="자기소개서 작성에 도움이 될 경험이나 활동을 자유롭게 작성해 주세요"
                      value={manualText}
                      onChange={(e) => setManualText(e.target.value)}
                      onKeyDown={(e) => {
                        // Enter: 줄바꿈 허용 (기본 동작)
                        if (e.key === 'Enter') {
                          // 기본 동작 허용 (줄바꿈)
                        }
                      }}
                      rows={12}
                    />
                    
                    <div className="manual-input-guide">
                      <h4>이런 내용을 포함하면 좋아요</h4>
                      <ul>
                        <li><strong>경험과 성과 :</strong> 인턴십, 프로젝트, 아르바이트에서 얻은 성과와 배운 점</li>
                        <li><strong>대외활동 :</strong> 동아리, 봉사활동, 공모전 참여 경험과 역할</li>
                        <li><strong>역량과 강점 :</strong> 문제해결력, 리더십, 커뮤니케이션 등 구체적인 사례</li>
                        <li><strong>학습과 성장 :</strong> 새로운 기술 습득, 어려움 극복 과정</li>
                        <li><strong>협업 경험 :</strong> 팀워크, 갈등 해결, 목표 달성 사례</li>
                      </ul>
                    </div>
                  </div>
                  
                  {error && (
                    <div className="error-message">
                      {error}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="button-container">
        <button 
          className="skip-button"
          onClick={handleSkip}
        >
          건너뛰기
        </button>
        <button
          id="submit-file-upload-btn"
          className="next-button active"
          onClick={handleNext}
        >
          다음
        </button>
      </div>

      {/* 건너뛰기 확인 모달 */}
      {showSkipModal && (
        <div className="modal-overlay" onClick={() => setShowSkipModal(false)}>
          <div className="skip-confirmation-modal" onClick={(e) => e.stopPropagation()}>
            <h3>잠깐! 합격의 가장 중요한 재료가 빠졌어요</h3><p></p>
            <p>
              {activeTab === 'upload' 
                ? '문서 업로드 없이는 맞춤형 자기소개서 작성이 어려울 수 있어요'
                : '경험 입력 없이는 맞춤형 자기소개서 작성이 어려울 수 있어요'
              }
            </p>
            <div className="modal-buttons">
              <button 
                className="modal-button secondary"
                onClick={handleConfirmSkip}
              >
                그래도 건너뛰기
              </button>
              <button 
                className="modal-button primary"
                onClick={handleUploadFromModal}
              >
                {activeTab === 'upload' ? '문서 업로드' : '돌아가기'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploadPage;
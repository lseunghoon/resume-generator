import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Navigation from '../components/Navigation';
import { supabase } from '../services/supabaseClient';
import './FileUploadPage.css';

const FileUploadPage = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]); // 다중 파일을 배열로 관리
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState('');
  const [jobInfo, setJobInfo] = useState(null); // 새로운 채용정보 입력 방식
  const [showSkipModal, setShowSkipModal] = useState(false); // 건너뛰기 확인 모달
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  // 인증 상태 확인: 비로그인 시 랜딩페이지로 리다이렉트
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
    } else {
      // 상태가 없으면 홈으로 이동
      navigate('/');
    }
  }, [location.state, navigate]);

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
    // 업로드된 파일들의 실제 File 객체들을 전달
    const fileObjects = uploadedFiles.map(f => f.file);
    
    navigate('/question', { 
      state: { 
        uploadedFiles: fileObjects, // 다중 파일 배열로 전달
        jobInfo, // 새로운 채용정보 입력 방식 데이터 전달
        question: location.state?.question || '' // 이전에 입력한 질문 전달
      } 
    });
  };

  const handleSkip = () => {
    // 건너뛰기 확인 모달 표시
    setShowSkipModal(true);
  };

  const handleConfirmSkip = () => {
    // 실제 건너뛰기 실행
    navigate('/question', { 
      state: { 
        uploadedFiles: [], // 빈 배열
        jobInfo, // 새로운 채용정보 입력 방식 데이터 전달
        question: location.state?.question || '' // 이전에 입력한 질문 전달
      } 
    });
  };

  const handleUploadFromModal = () => {
    // 모달 닫고 파일 업로드 실행
    setShowSkipModal(false);
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleGoBack = () => {
    // JobInfoInputPage의 우대사항 단계(마지막 단계)로 돌아가기
    navigate('/job-info', { 
      state: { 
        jobInfo: jobInfo,
        fromFileUpload: true,
        goToLastStep: true // 우대사항 단계로 이동하기 위한 플래그
      } 
    });
  };

  // handleGoForward 함수는 사용되지 않으므로 제거

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
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

  return (
    <div className="file-upload-page" onKeyPress={handleKeyPress} tabIndex={0}>
      <Helmet>
        <title>이력서 업로드 | 써줌 - 맞춤형 자기소개서 생성</title>
        <meta name="description" content="기존 이력서나 자기소개서를 업로드하여 더욱 개인화된 맞춤형 자기소개서를 생성하세요. PDF, DOC, DOCX 파일 지원." />
        <meta name="robots" content="noindex, nofollow" />
        
        {/* Open Graph 태그 */}
        <meta property="og:title" content="이력서 업로드 | 써줌 - 맞춤형 자기소개서 생성" />
        <meta property="og:description" content="기존 이력서나 자기소개서를 업로드하여 더욱 개인화된 맞춤형 자기소개서를 생성하세요." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://www.sseojum.com/file-upload" />
      </Helmet>
      
      <div className="page-content">
        <Navigation
          canGoBack={true}
          onGoBack={handleGoBack}
        />
        
        <div className="content-wrapper">
          <div className="form-section">
            
            <div className="form-content">
              <div className="form-header">
                <h1>기존 자기소개서나 이력서를<br/>업로드해 주세요</h1>
                <p>더욱 개인화된 자기소개서 작성을 위해 건너뛰지 않는 것을 추천해요<br/>
                </p>
              </div>
              
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
                
                {error && (
                  <div className="error-message">
                    {error}
                  </div>
                )}
              </div>
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
            <p>문서 업로드 없이는 맞춤형 자기소개서 작성이 어려울 수 있어요</p>
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
                문서 업로드
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploadPage;
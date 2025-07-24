import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import './FileUploadPage.css';

const FileUploadPage = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]); // 다중 파일을 배열로 관리
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState('');
  const [jobPostingUrl, setJobPostingUrl] = useState('');
  const [selectedJob, setSelectedJob] = useState('');
  const [extractedJobs, setExtractedJobs] = useState([]);
  const [htmlContent, setHtmlContent] = useState(''); // htmlContent 추가
  const [preloadedContent, setPreloadedContent] = useState(null); // 프리로딩된 콘텐츠
  const [contentId, setContentId] = useState(null); // contentId 추가
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.state) {
      setJobPostingUrl(location.state.jobPostingUrl || '');
      setSelectedJob(location.state.selectedJob || '');
      setExtractedJobs(location.state.extractedJobs || []);
      setHtmlContent(location.state.htmlContent || ''); // htmlContent 설정
      setPreloadedContent(location.state.preloadedContent || null); // 프리로딩된 콘텐츠 설정
      setContentId(location.state.contentId || null); // contentId 설정
      
      // 이전에 업로드한 파일들이 있으면 복원
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
  const maxFileSize = 50 * 1024 * 1024; // 50MB (백엔드와 동일하게 설정)
  const maxFiles = 3;

  const validateFile = (file) => {
    if (!allowedTypes.includes(file.type)) {
      setError('PDF, DOC, DOCX 파일만 업로드 가능합니다.');
      return false;
    }
    
    if (file.size > maxFileSize) {
      setError('파일 크기는 50MB 이하여야 합니다.');
      return false;
    }
    
    // 중복 파일 검사
    if (uploadedFiles.some(f => f.name === file.name && f.size === file.size)) {
      setError('이미 업로드된 파일입니다.');
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
          jobPostingUrl, 
          selectedJob,
          uploadedFiles: fileObjects, // 다중 파일 배열로 전달
          extractedJobs,
          htmlContent, // htmlContent 전달
          preloadedContent, // 프리로딩된 콘텐츠 전달
          contentId, // contentId 전달
          question: location.state?.question || '' // 이전에 입력한 질문 전달
        } 
      });
  };

  const handleSkip = () => {
    navigate('/question', { 
      state: { 
        jobPostingUrl, 
        selectedJob,
        uploadedFiles: [], // 빈 배열
        extractedJobs,
        htmlContent, // htmlContent 전달
        preloadedContent, // 프리로딩된 콘텐츠 전달
        contentId, // contentId 전달
        question: location.state?.question || '' // 이전에 입력한 질문 전달
      } 
    });
  };

  const handleGoBack = () => {
    navigate('/job-select', { 
      state: { 
        jobPostingUrl,
        extractedJobs,
        htmlContent, // htmlContent 전달
        selectedJob, // 선택한 직무 전달
        customJob: null // 직접 입력한 직무는 null로 전달
      } 
    });
  };

  const handleGoForward = () => {
    handleNext();
  };

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
      <Header 
        progress={75} 
        showNavigation={true}
        canGoBack={true}
        canGoForward={true}
        onGoBack={handleGoBack}
        onGoForward={handleGoForward}
        currentStep="3"
        totalSteps="4"
      />
      
      <div className="page-content">
        <div className="content-wrapper">
          <div className="form-section">
            
            <div className="form-content">
              <div className="form-header">
                <h1>기존 자기소개서나 이력서를<br/>업로드해주세요</h1>
                <p>더욱 개인화된 자기소개서 작성을 위해 건너뛰지 않는 것을 추천드립니다.<br/>
                </p>
              </div>
              
              <div className="upload-section">
                <div className="upload-stats">
                  <span className="file-count">{uploadedFiles.length}</span>
                  <span className="file-separator">/</span>
                  <span className="max-files">3개</span>
                  <span className="size-info">({formatFileSize(getTotalSize())} / 10MB)</span>
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
                        <span className="upload-text">첨부 파일을 업로드해주세요.</span>
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
                        onChange={handleFileInputChange}
                        multiple
                        style={{ display: 'none' }}
                      />
                    </div>
                  )}
                </div>
                
                <div className="upload-notes">
                  <p>* 첨부 파일은 최대 3개, 10Mb 까지 업로드 가능합니다.</p>
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
          
          <div className="action-section">
            <div className="action-buttons">
              <Button
                variant="outline"
                onClick={handleSkip}
                className="skip-button"
              >
                건너뛰기
              </Button>
              <Button
                variant="primary"
                onClick={handleNext}
                className="next-button"
              >
                다음
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUploadPage; 
import React, { useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import './FileUploadPage.css';

const FileUploadPage = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]); // 다중 파일을 배열로 관리
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { jobPostingUrl, selectedJob, jobDescription } = location.state || {};

  const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  const maxFileSize = 10 * 1024 * 1024; // 10MB
  const maxFiles = 3;

  const validateFile = (file) => {
    if (!allowedTypes.includes(file.type)) {
      setError('PDF, DOC, DOCX 파일만 업로드 가능합니다.');
      return false;
    }
    
    if (file.size > maxFileSize) {
      setError('파일 크기는 10MB 이하여야 합니다.');
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
    
    for (const file of fileArray) {
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
        jobDescription
      } 
    });
  };

  const handleSkip = () => {
    navigate('/question', { 
      state: { 
        jobPostingUrl, 
        selectedJob,
        uploadedFiles: [], // 빈 배열
        jobDescription
      } 
    });
  };

  const handleBack = () => {
    navigate('/job-select', { 
      state: { 
        jobPostingUrl,
        extractedJobs: [],
        jobDescription
      } 
    });
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
    <div className="file-upload-page">
      <Header progress={75} />
      
      <div className="page-content">
        <div className="content-wrapper">
          <div className="form-section">
            <button className="back-button" onClick={handleBack}>
              ←
            </button>
            
            <div className="form-content">
              <div className="form-header">
                <h1>기존 이력서 혹은<br/>자기소개서를 첨부해주세요</h1>
                <p>파일을 첨부해주시면 합격률 높은<br/>자기소개서를 생성할 수 있어요</p>
              </div>
              
              <div className="upload-section">
                <div className="upload-stats">
                  <span className="file-count">{uploadedFiles.length}</span>
                  <span className="file-separator">/</span>
                  <span className="max-size">10Mb</span>
                </div>
                
                <div className="upload-content">
                  {/* 업로드된 파일 목록 */}
                  {uploadedFiles.map((fileItem) => (
                    <div key={fileItem.id} className="uploaded-file-item">
                      <div className="file-info">
                        <span className="file-name">{fileItem.name}</span>
                        <span className="file-count-label">({uploadedFiles.indexOf(fileItem) + 1}/3)</span>
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
                        <span className="upload-count">({uploadedFiles.length}/3)</span>
                      </div>
                      <div className="upload-icon">📄</div>
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
                  <p>* 첨부 및 입력해주신 정보는 저장되지 않습니다.</p>
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
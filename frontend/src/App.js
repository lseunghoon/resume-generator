import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Pages
import JobInfoInputPage from './pages/JobInfoInputPage';
import FileUploadPage from './pages/FileUploadPage';
import QuestionPage from './pages/QuestionPage';
import ResultPage from './pages/ResultPage';

// Components
import DevTools from './components/DevTools';

// API
import { deleteSession } from './services/api';

function App() {
  // 앱 시작 시 이전 세션 정리
  useEffect(() => {
    const pendingSessionDelete = localStorage.getItem('pendingSessionDelete');
    if (pendingSessionDelete) {
      console.log('앱 시작 시 이전 세션 정리 중:', pendingSessionDelete);
      deleteSession(pendingSessionDelete)
        .then(() => {
          console.log('이전 세션 정리 완료');
        })
        .catch(error => {
          console.error('이전 세션 정리 실패:', error);
        })
        .finally(() => {
          localStorage.removeItem('pendingSessionDelete');
        });
    }
  }, []);

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<JobInfoInputPage />} />
          <Route path="/job-info" element={<JobInfoInputPage />} />
          <Route path="/file-upload" element={<FileUploadPage />} />
          <Route path="/question" element={<QuestionPage />} />
          <Route path="/result" element={<ResultPage />} />
        </Routes>
        
        {/* 개발자 도구 (개발 환경에서만 표시) */}
        <DevTools />
      </div>
    </Router>
  );
}

export default App;

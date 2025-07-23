import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Pages
import LinkUploadPage from './pages/LinkUploadPage';
import JobSelectPage from './pages/JobSelectPage';
import FileUploadPage from './pages/FileUploadPage';
import QuestionPage from './pages/QuestionPage';
import ResultPage from './pages/ResultPage';

// Components
import DevTools from './components/DevTools';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<LinkUploadPage />} />
          <Route path="/job-select" element={<JobSelectPage />} />
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

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LinkUploadPage from './pages/LinkUploadPage';
import JobSelectPage from './pages/JobSelectPage';
import FileUploadPage from './pages/FileUploadPage';
import QuestionPage from './pages/QuestionPage';
import ResultPage from './pages/ResultPage';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LinkUploadPage />} />
        <Route path="/job-select" element={<JobSelectPage />} />
        <Route path="/file-upload" element={<FileUploadPage />} />
        <Route path="/question" element={<QuestionPage />} />
        <Route path="/result" element={<ResultPage />} />
      </Routes>
    </Router>
  );
}

export default App;

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserSessions } from '../services/api';
import './SessionList.css';

const SessionList = ({ onSessionSelect }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await getUserSessions();
      setSessions(response.sessions || []);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleSessionClick = (session) => {
    if (onSessionSelect) {
      onSessionSelect(session);
    }
  };

  const handleNewSessionClick = () => {
    navigate('/job-info');
  };

  if (loading) {
    return <div className="session-list-loading">자기소개서 목록을 불러오는 중...</div>;
  }

  if (error) {
    return <div className="session-list-error">오류: {error}</div>;
  }

  if (sessions.length === 0) {
    return (
      <div className="session-list-empty">
        <h3>아직 작성한 자기소개서가 없습니다</h3>
        <p>새로운 자기소개서를 작성해보세요!</p>
        <button 
          className="new-session-btn"
          onClick={handleNewSessionClick}
        >
          새 자기소개서 작성
        </button>
      </div>
    );
  }

  return (
    <div className="session-list">
      <div className="session-list-header">
        <h2>내 자기소개서 목록</h2>
        <button 
          className="new-session-btn"
          onClick={handleNewSessionClick}
        >
          새 자기소개서 작성
        </button>
      </div>
      <div className="session-grid">
        {sessions.map((session) => (
          <div 
            key={session.id} 
            className="session-card"
            onClick={() => handleSessionClick(session)}
          >
            <div className="session-header">
              <h3>{session.company_name || '회사명 없음'}</h3>
              <span className="session-date">{formatDate(session.created_at)}</span>
            </div>
            <div className="session-content">
              <p className="job-title">{session.job_title || '직무명 없음'}</p>
              {session.company_name && (
                <p className="company-name">{session.company_name}</p>
              )}
            </div>
            <div className="session-footer">
              <span className="session-id">ID: {session.id.substring(0, 8)}...</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SessionList; 
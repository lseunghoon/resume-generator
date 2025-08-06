import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getUserSessions, deleteSession } from '../services/api';
import { createSessionUrl, extractSessionIdFromUrl } from '../utils/sessionUtils';
import './Sidebar.css';

const Sidebar = ({ user, isOpen, onToggle, refreshTrigger }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  // 세션 목록 로드
  useEffect(() => {
    console.log('Sidebar useEffect - user:', user);
    if (user) {
      loadSessions();
    }
  }, [user, refreshTrigger]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await getUserSessions();
      console.log('세션 목록 로드 성공:', data);
      
      if (data.success) {
        setSessions(data.sessions || []);
      } else {
        throw new Error(data.message || '세션 목록을 불러오는데 실패했습니다');
      }
    } catch (err) {
      console.error('세션 목록 로드 오류:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSessionClick = (sessionId) => {
    navigate(createSessionUrl(sessionId));
    
    // 모바일에서 사이드바 자동 닫기
    if (window.innerWidth <= 768 && isOpen) {
      onToggle();
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
      return '오늘';
    } else if (diffDays === 2) {
      return '어제';
    } else if (diffDays <= 7) {
      return `${diffDays - 1}일 전`;
    } else {
      return date.toLocaleDateString('ko-KR', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  const getSessionTitle = (session) => {
    const company = session.company_name || '회사명 없음';
    const job = session.job_title || '직무 없음';
    return `${company} ${job}`;
  };

  if (!user) {
    return null;
  }

  return (
    <>
      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-content">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>목록을 불러오는 중...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <p>오류가 발생했습니다</p>
              <button onClick={loadSessions} className="retry-btn">
                다시 시도
              </button>
            </div>
          ) : sessions.length === 0 ? (
            <div className="empty-state">
              <p>아직 작성한 자기소개서가 없습니다</p>
            </div>
          ) : (
            <div className="sessions-list">
              {sessions.map((session) => (
                <SessionItem
                  key={session.id}
                  session={session}
                  isActive={location.pathname === '/result' && location.search.includes(createSessionUrl(session.id).split('=')[1])}
                  onClick={() => handleSessionClick(session.id)}
                  onRefresh={loadSessions}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

// 세션 아이템 컴포넌트
const SessionItem = ({ session, isActive, onClick, onRefresh }) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // 외부 클릭 시 메뉴 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showMenu && !event.target.closest('.session-item')) {
        setShowMenu(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showMenu]);

  const handleMenuClick = (e) => {
    e.stopPropagation();
    setShowMenu(!showMenu);
  };

  const handleDeleteClick = (e) => {
    e.stopPropagation();
    setShowDeleteModal(true);
    setShowMenu(false);
  };

  const handleDeleteConfirm = async () => {
    try {
      setIsDeleting(true);
      
      const result = await deleteSession(session.id);
      console.log('세션 삭제 성공:', result);
      
      if (result.success) {
        onRefresh(); // 목록 새로고침
      } else {
        throw new Error(result.message || '삭제에 실패했습니다');
      }
    } catch (error) {
      console.error('세션 삭제 오류:', error);
      alert('삭제 중 오류가 발생했습니다');
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(false);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteModal(false);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
      return '오늘';
    } else if (diffDays === 2) {
      return '어제';
    } else if (diffDays <= 7) {
      return `${diffDays - 1}일 전`;
    } else {
      return date.toLocaleDateString('ko-KR', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  const getSessionTitle = (session) => {
    const company = session.company_name || '회사명 없음';
    const job = session.job_title || '직무 없음';
    return `${company} ${job}`;
  };

  return (
    <>
      <div className={`session-item ${isActive ? 'active' : ''}`}>
        <div className="session-content" onClick={onClick}>
          <div className="session-info">
            <h4 className="session-title">{getSessionTitle(session)}</h4>
            <p className="session-date">{formatDate(session.created_at)}</p>
          </div>
          <button 
            className="session-menu-btn"
            onClick={handleMenuClick}
            disabled={isDeleting}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="1" fill="currentColor"/>
              <circle cx="19" cy="12" r="1" fill="currentColor"/>
              <circle cx="5" cy="12" r="1" fill="currentColor"/>
            </svg>
          </button>
        </div>
        
        {showMenu && (
          <div className="session-menu">
            <button 
              className="menu-item delete-btn"
              onClick={handleDeleteClick}
              disabled={isDeleting}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 6H5H21M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              {isDeleting ? '삭제 중...' : '삭제'}
            </button>
          </div>
        )}
      </div>

      {/* 삭제 확인 모달 */}
      {showDeleteModal && (
        <div className="modal-overlay" onClick={handleDeleteCancel}>
          <div className="delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h3>자기소개서 삭제</h3>
            <p>이 자기소개서를 삭제하시겠습니까?</p>
            <p className="session-title-preview">{getSessionTitle(session)}</p>
            <div className="modal-buttons">
              <button 
                className="delete-confirm-btn"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
              >
                {isDeleting ? '삭제 중...' : '삭제'}
              </button>
              <button 
                className="delete-cancel-btn"
                onClick={handleDeleteCancel}
                disabled={isDeleting}
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar; 
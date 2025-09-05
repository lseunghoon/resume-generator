import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getUserSessions, deleteSession } from '../services/api';
import { createSessionUrl, extractSessionIdFromUrl } from '../utils/sessionUtils';
import './Sidebar.css';

// 공통 날짜 포맷 함수
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  
  return `${year}년 ${month}월 ${day}일`;
};

const Sidebar = ({ user, isOpen, onToggle, refreshTrigger }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('sidebarWidth');
    const value = saved ? parseInt(saved, 10) : 280;
    // 저장된 값이 최소값보다 작으면 최소값으로 설정
    return Number.isFinite(value) ? Math.max(280, value) : 280;
  });
  const [isResizing, setIsResizing] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // 세션 목록 로드
  useEffect(() => {
    console.log('Sidebar useEffect - user:', user);
    if (user) {
      loadSessions();
    }
  }, [user, refreshTrigger]);

  // 화면 크기 변경 시 사이드바 상태 조정
  useEffect(() => {
    const handleResize = () => {
      // PC 환경(1200px 이상)에서 모바일/태블릿 환경으로 변경될 때 사이드바 자동 닫기
      if (window.innerWidth < 1200 && isOpen) {
        onToggle();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isOpen, onToggle]);

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

  // 사이드바 리사이즈 핸들러
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return;
      const minWidth = 280; // 최소 너비를 280px로 고정 (더 줄일 수 없음)
      const maxWidth = Math.min(640, window.innerWidth - 100); // 우측 패널 최대폭 제한
      const newWidth = Math.max(minWidth, Math.min(maxWidth, window.innerWidth - e.clientX));
      
      // 최소 너비에 도달했을 때 시각적 피드백
      if (newWidth <= minWidth) {
        document.body.style.cursor = 'not-allowed';
      } else {
        document.body.style.cursor = 'col-resize';
      }
      
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false);
        // 커서 상태 복원
        document.body.style.cursor = '';
        // 저장
        localStorage.setItem('sidebarWidth', String(sidebarWidth));
      }
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, [isResizing, sidebarWidth]);

  const handleSessionClick = (sessionId) => {
    navigate(createSessionUrl(sessionId));
    
    // 모바일/태블릿에서 사이드바 자동 닫기
    if (window.innerWidth <= 1199 && isOpen) {
      onToggle();
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
      {/* 모바일/태블릿 환경에서 사이드바 오버레이 */}
      {isOpen && window.innerWidth <= 1199 && (
        <div 
          className="sidebar-overlay"
          onClick={onToggle}
          aria-label="사이드바 닫기"
        />
      )}
      
      <div className={`sidebar ${isOpen ? 'open' : ''} ${isResizing ? 'resizing' : ''} ${sidebarWidth <= 280 ? 'min-width-reached' : ''}`} style={{ width: sidebarWidth }}>
        {/* 좌측 리사이저 핸들 */}
        <div
          className="sidebar-resizer"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizing(true);
          }}
          title="너비 조절 (최소 280px)"
        />
        <div className="sidebar-content">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
            </div>
          ) : error ? (
            <div className="error-state">
              <div className="error-icon">⚠️</div>
              <p className="error-message">{error}</p>
              <button onClick={loadSessions} className="retry-btn">
                🔄 다시 시도
              </button>
              <p className="error-hint">
                문제가 지속되면 페이지를 새로고침하거나 잠시 후 다시 시도해주세요.
              </p>
            </div>
          ) : sessions.length === 0 ? (
            <div className="empty-state">
              <p>아직 작성한 자기소개서가 없어요</p>
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
      await deleteSession(session.id);
      console.log('세션 삭제 성공');
      
      // 사이드바 새로고침
      if (onRefresh) {
        onRefresh();
      }
      
      setShowDeleteModal(false);
    } catch (error) {
      console.error('세션 삭제 실패:', error);
      alert('세션 삭제에 실패했습니다.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteModal(false);
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
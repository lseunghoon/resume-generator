import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Button from '../components/Button';
import Navigation from '../components/Navigation';
import { getCoverLetter, addQuestion, reviseAnswer, deleteSession } from '../services/api';
import { extractSessionIdFromUrl } from '../utils/sessionUtils';
import { supabase } from '../services/supabaseClient';
import './ResultPage.css';

function ResultPage({ onSidebarRefresh }) {
    const location = useLocation();
    const navigate = useNavigate();
    const [sessionId, setSessionId] = useState('');
    const [answers, setAnswers] = useState([]);
    const [isLoading, setIsLoading] = useState(true); // 로딩 상태 추가

    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState(() => {
        // localStorage에서 저장된 activeTab 복원
        const savedActiveTab = localStorage.getItem('resultPageActiveTab');
        return savedActiveTab ? parseInt(savedActiveTab, 10) : 0;
    });
  
    const [selectedJob, setSelectedJob] = useState('');
    const [jobInfo, setJobInfo] = useState(null); // 새로운 채용정보 입력 방식 데이터
    const [showAddQuestionModal, setShowAddQuestionModal] = useState(false);
    const [newQuestion, setNewQuestion] = useState('');
    const [isAddingQuestion, setIsAddingQuestion] = useState(false);
    const [revisionRequest, setRevisionRequest] = useState('');
    const [isRevising, setIsRevising] = useState(false);
    const [inputRef, setInputRef] = useState(null); // 입력창 포커스를 위한 ref

    // 인증 상태 확인: 비로그인 시 랜딩페이지로 리다이렉트
    useEffect(() => {
        const checkAuthAndRedirect = async () => {
            const { data, error } = await supabase.auth.getSession();
            if (error || !data?.session) {
                try {
                    localStorage.setItem('auth_redirect_path', '/result');
                } catch (_) {}
                navigate('/login?next=/result', { replace: true });
            }
        };
        checkAuthAndRedirect();
    }, [navigate]);

    // 세션 삭제 함수
    const handleDeleteSession = async () => {
        if (sessionId) {
            try {
                await deleteSession(sessionId);
                console.log('세션이 성공적으로 삭제되었습니다.');
            } catch (error) {
                console.error('세션 삭제 실패:', error);
            }
        }
    };

    // 다시 시작 함수 (세션 삭제 없이 홈페이지로 이동)
    const handleRestart = () => {
        // localStorage에서 activeTab 정보만 삭제
        localStorage.removeItem('resultPageActiveTab');
        // 완전한 새로고침으로 홈페이지로 이동
        window.location.href = '/';
    };

    // activeTab 변경 시 localStorage에 저장
    useEffect(() => {
        localStorage.setItem('resultPageActiveTab', activeTab.toString());
    }, [activeTab]);

    // 새로고침 시 세션 삭제 준비
    useEffect(() => {
        const handleBeforeUnload = () => {
            if (sessionId) {
                // 페이지를 떠날 때 세션 ID를 localStorage에 저장
                localStorage.setItem('pendingSessionDelete', sessionId);
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, [sessionId]);





    // 실제 텍스트 길이 계산 함수
    const calculateTextLength = (text) => {
        if (!text || typeof text !== 'string') return 0;
        const cleanText = removeMarkdownBold(text);
        return cleanText.length;
    };

    useEffect(() => {
        console.log('ResultPage - location.state:', location.state);
        console.log('ResultPage - location.search:', location.search);
        console.log('ResultPage - location.pathname:', location.pathname);
        
        // sessionId를 여러 소스에서 찾기
        let currentSessionId = '';
        
        // 1. location.state에서 찾기
        if (location.state?.sessionId) {
            currentSessionId = location.state.sessionId;
            console.log('ResultPage - sessionId from location.state:', currentSessionId);
        }
        // 2. 쿼리 파라미터에서 찾기 (암호화된 형태 지원)
        else if (location.search) {
            currentSessionId = extractSessionIdFromUrl(location.search);
            console.log('ResultPage - sessionId from query params (decoded):', currentSessionId);
        }
        
        console.log('ResultPage - Final sessionId:', currentSessionId);
        
        if (currentSessionId) {
            setSessionId(currentSessionId);
            
            // location.state에서 다른 데이터 가져오기
            if (location.state) {
                setJobInfo(location.state.jobInfo || null);
                setSelectedJob(location.state.selectedJob || '');
            }
            
            // 항상 최신 데이터를 가져오기 위해 API 호출
            fetchCoverLetter(currentSessionId);
        } else {
            // 세션 ID가 없으면 사용자의 가장 최근 세션을 가져와서 리다이렉트
            console.log('ResultPage - No sessionId found, fetching user sessions...');
            fetchLatestSession();
        }
    }, [location.state, location.search, location.pathname, navigate]);

    // 사용자의 가장 최근 세션을 가져와서 리다이렉트하는 함수
    const fetchLatestSession = useCallback(async () => {
        try {
            const { getUserSessions } = await import('../services/api');
            const response = await getUserSessions();
            
            if (response && response.sessions && response.sessions.length > 0) {
                // 가장 최근 세션 선택 (created_at 기준)
                const latestSession = response.sessions[0];
                console.log('ResultPage - Latest session found:', latestSession);
                
                // 해당 세션의 결과 페이지로 리다이렉트
                const sessionUrl = `/result?session=${latestSession.id}`;
                navigate(sessionUrl, { replace: true });
            } else {
                // 세션이 없으면 홈으로 이동
                console.log('ResultPage - No user sessions found, redirecting to home');
                setError('자기소개서 세션이 없습니다. 새로운 자기소개서를 작성해주세요.');
                setIsLoading(false);
            }
        } catch (error) {
            console.error('ResultPage - Error fetching user sessions:', error);
            setError('세션 정보를 가져오는데 실패했습니다. 다시 시도해주세요.');
            setIsLoading(false);
        }
    }, [navigate]);

    const fetchCoverLetter = async (currentSessionId) => {
        if (!currentSessionId) {
            console.error('세션 ID가 없습니다.');
            setError('세션 ID가 없습니다');
            setIsLoading(false);
            return;
        }

        try {
            console.log('ResultPage - fetchCoverLetter 호출, sessionId:', currentSessionId);
            console.log('ResultPage - Mock API 활성화 상태:', localStorage.getItem('useMockApi'));
            
            const response = await getCoverLetter(currentSessionId);
            console.log('ResultPage - getCoverLetter 응답:', response);
            
            if (response.questions && response.questions.length > 0) {
                console.log('ResultPage - questions 배열:', response.questions);
                console.log('ResultPage - 첫 번째 question 객체:', response.questions[0]);
                console.log('ResultPage - API 응답 전체:', response);
                console.log('ResultPage - question 객체의 속성들:', {
                    id: response.questions[0]?.id,
                    question: response.questions[0]?.question,
                    answer: response.questions[0]?.answer,
                    answer_history: response.questions[0]?.answer_history,
                    current_version_index: response.questions[0]?.current_version_index,
                    length: response.questions[0]?.length
                });
                
                // API 응답에서 회사명과 직무명 정보 가져오기
                if (response.companyName && response.jobTitle) {
                    setJobInfo({
                        companyName: response.companyName,
                        jobTitle: response.jobTitle
                    });
                    setSelectedJob(response.jobTitle);
                }
                
                // 실제 API 응답 구조에 맞게 수정
                const answers = response.questions.map((question, index) => {
                    let answerHistory = [];
                    let currentAnswer = question.answer || '';
                    
                    if (question.answer_history) {
                        try {
                            // answer_history가 문자열인 경우 JSON 파싱 시도
                            if (typeof question.answer_history === 'string') {
                                answerHistory = JSON.parse(question.answer_history);
                            } else if (Array.isArray(question.answer_history)) {
                                // 이미 배열인 경우 그대로 사용
                                answerHistory = question.answer_history;
                            } else {
                                // 기타 경우 빈 배열로 초기화
                                answerHistory = [];
                            }
                            
                            if (answerHistory.length > 0 && question.current_version_index !== undefined) {
                                currentAnswer = answerHistory[question.current_version_index] || answerHistory[0] || '';
                            }
                        } catch (e) {
                            console.error('답변 히스토리 파싱 오류:', e);
                            console.error('파싱 실패한 데이터:', question.answer_history);
                            // 파싱 실패 시 현재 답변을 히스토리의 첫 번째 항목으로 설정
                            currentAnswer = question.answer || '';
                            answerHistory = [currentAnswer];
                        }
                    }
                    
                    return {
                        id: question.id || index + 1,
                        question: question.question,
                        answer: currentAnswer,
                        answer_history: answerHistory,
                        current_version_index: question.current_version_index || 0,
                        // length는 DB에 저장하지 않고 프론트에서 계산
                        length: calculateTextLength(currentAnswer),
                        has_undo: (question.current_version_index || 0) > 0,
                        has_redo: answerHistory.length > (question.current_version_index || 0) + 1
                    };
                });
                
                console.log('ResultPage - 변환된 answers:', answers);
                setAnswers(answers);
                
                // 저장된 activeTab이 유효한지 확인하고 설정
                const savedActiveTab = parseInt(localStorage.getItem('resultPageActiveTab') || '0', 10);
                const validActiveTab = savedActiveTab < answers.length ? savedActiveTab : 0;
                setActiveTab(validActiveTab);
                
                setIsLoading(false); // 로딩 완료
            } else {
                console.error('ResultPage - questions 배열이 없거나 비어있음:', response);
                
                // questions가 비어있는 경우 (수동 삭제로 인한 경우)
                if (response.questions && response.questions.length === 0) {
                    setError('이 자기소개서의 질문이 삭제되었습니다. 홈으로 돌아가서 새로운 자기소개서를 작성해주세요.');
                } else {
                    setError('자기소개서 데이터를 불러올 수 없습니다');
                }
                
                setIsLoading(false); // 로딩 완료
            }
        } catch (error) {
            console.error('자기소개서 조회 오류:', error);
            
            // 세션이 삭제되었거나 찾을 수 없는 경우 홈으로 리다이렉트
            if (error.message && (
                error.message.includes('세션 조회에 실패했습니다') ||
                error.message.includes('세션을 찾을 수 없습니다') ||
                error.message.includes('세션 조회 실패')
            )) {
                console.log('세션이 삭제되었거나 찾을 수 없어 홈으로 이동합니다.');
                navigate('/');
                return;
            }
            
            setError(error.message || '자기소개서를 불러오는데 실패했습니다');
            setIsLoading(false); // 로딩 완료
        }
    };

    // 마크다운 볼드 표시 제거 함수
    const removeMarkdownBold = (text) => {
        if (!text || typeof text !== 'string') {
            console.warn('removeMarkdownBold: text is not a string:', text);
            return '';
        }
        // ** 으로 감싸진 텍스트를 일반 텍스트로 변환
        return text.replace(/\*\*(.*?)\*\*/g, '$1');
    };

    const handleRevisionRequestChange = (value) => {
        setRevisionRequest(value);
        
        // textarea 높이 자동 조절
        setTimeout(() => {
            if (inputRef) {
                inputRef.style.height = 'auto';
                inputRef.style.height = Math.min(inputRef.scrollHeight, 200) + 'px';
            }
        }, 0);
    };

    const handleSubmitRevision = async () => {
        if (!revisionRequest.trim()) return;
        
        setIsRevising(true);
        try {
            // 세션 내 질문 인덱스 사용 (1, 2, 3으로 변환)
            const questionIndex = activeTab + 1;
            console.log('수정 요청 - 현재 탭:', activeTab);
            console.log('수정 요청 - answers:', answers);
            console.log('수정 요청 - 선택된 질문:', answers[activeTab]);
            console.log('수정 요청 - 질문 인덱스:', questionIndex);
            
            if (questionIndex < 1 || questionIndex > answers.length) {
                console.error('유효하지 않은 질문 인덱스입니다.');
                return;
            }
            
            const response = await reviseAnswer(sessionId, questionIndex, revisionRequest);
            
            // API 응답 구조에 맞게 수정
            const revisedAnswerText = response.revisedAnswer || response.answer;
            
            if (revisedAnswerText) {
                // 수정 완료 후 최신 데이터를 다시 가져오기
                await fetchCoverLetter(sessionId);
                
                setRevisionRequest('');
                
                // textarea 높이 초기화
                if (inputRef) {
                    inputRef.style.height = 'auto';
                }
                
                // 새로운 메시지가 추가된 후 자동 스크롤
                setTimeout(() => {
                    scrollToBottom();
                    focusInput();
                }, 100);
            }
        } catch (err) {
            console.error('수정 요청 실패:', err);
        } finally {
            setIsRevising(false);
            // 에러 발생 시에도 textarea 높이 초기화
            if (inputRef) {
                inputRef.style.height = 'auto';
            }
        }
    };
    
    const handleCopy = async (index, isHistory = false, historyIndex = null) => {
        try {
            let textToCopy;
            if (isHistory && historyIndex !== null) {
                // 히스토리 버전 복사
                textToCopy = answers[index].answer_history[historyIndex];
            } else {
                // 현재 버전 복사
                textToCopy = answers[index].answer;
            }
            
            await navigator.clipboard.writeText(textToCopy);
        } catch (err) {
            console.error('복사 실패:', err);
        }
    };

    // 자동 스크롤 함수
    const scrollToBottom = () => {
        window.scrollTo({
            top: document.documentElement.scrollHeight,
            behavior: 'smooth'
        });
    };

    // 입력창 포커스 유지 함수
    const focusInput = () => {
        if (inputRef) {
            inputRef.focus();
        }
    };

    const handleAddQuestion = async () => {
        if (!newQuestion.trim()) {
            console.log('문항이 비어있습니다.');
            return;
        }
        
        if (answers.length >= 3) {
            console.log('문항은 최대 2개까지 추가 가능합니다.');
            return;
        }

        setIsAddingQuestion(true);
        try {
            console.log('문항 추가 요청:', { sessionId, newQuestion });
            const response = await addQuestion(sessionId, newQuestion);
            console.log('문항 추가 응답:', response);
            
            // mock API 응답 구조에 맞게 수정
            const newAnswerData = response.new_answer || response;
            
            if (newAnswerData.question) {
                // 문항 추가 완료 후 최신 데이터를 다시 가져오기
                await fetchCoverLetter(sessionId);
                
                // 새로 추가된 질문에 대한 상태 초기화
                setRevisionRequest('');
                setNewQuestion('');
                setShowAddQuestionModal(false);
                
                // 새로 추가된 탭으로 이동 (answers 배열이 업데이트된 후)
                setTimeout(() => {
                    setActiveTab(answers.length);
                }, 100);
                
                console.log('문항 추가 완료');
            } else {
                console.error('응답에 question이 없습니다:', response);
            }
        } catch (err) {
            console.error('질문 추가 실패:', err);
            alert('문항 추가에 실패했습니다. 다시 시도해주세요');
        } finally {
            setIsAddingQuestion(false);
        }
    };



    // 로딩 중일 때는 스피너 표시
    if (isLoading) {
        return (
            <div className="result-page">
                <div className="page-content">
                    <Navigation
                        canGoBack={true}
                        onGoBack={handleRestart}
                    />
                    <div className="loading-container">
                        <div className="loading-spinner"></div>
                    </div>
                </div>
            </div>
        );
    }

    // 로딩이 완료되었지만 에러가 있거나 데이터가 없을 때
    if (error || answers.length === 0) {
        return (
            <div className="result-page">
                <div className="page-content">
                    <Navigation
                        canGoBack={true}
                        onGoBack={handleRestart}
                    />
                    <div className="error-container">
                        <p>{error || '결과를 찾을 수 없습니다'}</p>
                        <Button onClick={handleRestart}>다시 시작</Button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="result-page">
            <Helmet>
                <title>자기소개서 결과 | 써줌 - AI 생성 완료</title>
                <meta name="description" content="AI가 생성한 맞춤형 자기소개서 결과를 확인하고 수정하세요. 실시간 수정 요청과 추가 문항 생성 기능 제공." />
                <meta name="robots" content="noindex, nofollow" />
                
                {/* Open Graph 태그 */}
                <meta property="og:title" content="자기소개서 결과 | 써줌 - AI 생성 완료" />
                <meta property="og:description" content="AI가 생성한 맞춤형 자기소개서 결과를 확인하고 수정하세요." />
                <meta property="og:type" content="website" />
                <meta property="og:url" content="https://www.sseojum.com/result" />
            </Helmet>
            
            <div className="page-content">
                <Navigation
                    canGoBack={true}
                    onGoBack={handleRestart}
                />
                <div className="content-wrapper">
                    {/* 채용공고 정보 섹션 */}
                    <div className="job-info-section">
                        <div className="job-company">
                            <img src="/assets/companyicon.svg" alt="회사" className="company-icon" />
                            <span>{jobInfo ? jobInfo.companyName : '회사명'}</span>
                        </div>
                        <div className="job-position">
                            <img src="/assets/jobicon.svg" alt="직무" className="briefcase-icon" />
                            <span>{jobInfo ? jobInfo.jobTitle : selectedJob}</span>
                        </div>
                    </div>

                    {/* 탭 네비게이션 */}
                    <div className="tab-navigation" role="tablist" aria-label="자기소개서 문항">
                        {answers.map((item, index) => (
                            <button
                                key={index}
                                role="tab"
                                aria-selected={activeTab === index}
                                className={`tab ${activeTab === index ? 'active' : ''} ${answers.length >= 2 ? 'multiple-tabs' : 'single-tab'}`}
                                onClick={() => setActiveTab(index)}
                                type="button"
                            >
                                {item.question}
                            </button>
                        ))}

                        <button 
                            className="add-tab"
                            onClick={() => setShowAddQuestionModal(true)}
                            title="새 문항 추가"
                            disabled={answers.length >= 3}
                            type="button"
                        >
                            + 문항 추가
                        </button>
                    </div>

                    {/* 대화창 형태의 콘텐츠 */}
                    {answers[activeTab] && (
                        <div className="chat-container">
                            {/* 과거 버전들 (가장 오래된 것부터) */}
                            {answers[activeTab].answer_history && answers[activeTab].answer_history.length > 0 && 
                             answers[activeTab].current_version_index > 0 &&
                             answers[activeTab].answer_history.slice(0, answers[activeTab].current_version_index).map((historyAnswer, historyIndex) => (
                                <div key={`history-${activeTab}-${historyIndex}`} className="message-item history-message">
                                    <div className="message-content">
                                        <div className="message-text">
                                            {removeMarkdownBold(historyAnswer).split('\n').map((line, i) => (
                                                <p key={i}>{line}</p>
                                            ))}
                                        </div>
                                        <div className="message-meta">
                                            <span className="message-character-count">공백포함 {calculateTextLength(historyAnswer)}자</span>
                                            <button 
                                                className="message-copy-button"
                                                onClick={() => handleCopy(activeTab, true, historyIndex)}
                                            >
                                                <img 
                                                    src="/assets/content_copy.svg" 
                                                    alt="복사" 
                                                    className="copy-icon"
                                                />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            
                            {/* 현재 버전 (가장 최신) */}
                            <div className="message-item current-message">
                                <div className="message-content">
                                    <div className="message-text">
                                        {removeMarkdownBold(answers[activeTab].answer).split('\n').map((line, i) => (
                                            <p key={i}>{line}</p>
                                        ))}
                                    </div>
                                    <div className="message-meta">
                                        <span className="message-character-count">공백포함 {calculateTextLength(answers[activeTab].answer)}자</span>
                                        <button 
                                            className="message-copy-button"
                                            onClick={() => handleCopy(activeTab)}
                                        >
                                            <img 
                                                src="/assets/content_copy.svg" 
                                                alt="복사" 
                                                className="copy-icon"
                                            />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 고정된 수정 입력창 */}
                    <div className="chat-input-section">
                        <div className="revision-input">
                            <textarea
                                placeholder="수정할 내용을 입력해 주세요"
                                value={revisionRequest || ''}
                                onChange={(e) => handleRevisionRequestChange(e.target.value)}
                                onInput={(e) => handleRevisionRequestChange(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSubmitRevision();
                                        // 엔터 키 후에도 포커스 유지
                                        setTimeout(() => {
                                            focusInput();
                                        }, 50);
                                    }
                                }}
                                disabled={isRevising}
                                ref={setInputRef}
                                rows={1}
                                style={{ minHeight: '40px', maxHeight: '200px' }}
                            />
                            <button 
                                className={`send-revision ${isRevising ? 'processing' : ''}`}
                                onClick={handleSubmitRevision}
                                disabled={isRevising || !revisionRequest.trim()}
                            >
                                {isRevising ? (
                                    <div className="spinner"></div>
                                ) : (
                                    '→'
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* 문항 추가 모달 */}
            {showAddQuestionModal && (
                <div className="modal-overlay" onClick={() => setShowAddQuestionModal(false)}>
                    <div className="add-question-modal" onClick={(e) => e.stopPropagation()}>
                        <h3>추가로 생성하고자 하는<br/>문항을 입력해 주세요</h3>
                        <p>자기소개서 문항은 최대 2개까지 추가 가능해요</p>
                        <input
                            type="text"
                            placeholder="예) 지원 동기는 무엇인가요?"
                            value={newQuestion}
                            onChange={(e) => setNewQuestion(e.target.value)}
                            onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                    handleAddQuestion();
                                }
                            }}
                        />
                        <div className="modal-buttons">
                            <Button 
                                variant="primary" 
                                onClick={handleAddQuestion}
                                disabled={!newQuestion.trim() || isAddingQuestion || answers.length >= 3}
                                loading={isAddingQuestion}
                            >
                                {isAddingQuestion ? '생성 중' : '문항 추가하기'}
                            </Button>
                            <Button 
                                variant="outline" 
                                onClick={() => setShowAddQuestionModal(false)}
                            >
                                다음에 할게요
                            </Button>
                        </div>
                    </div>
            </div>
            )}
        </div>
    );
}

export default ResultPage;
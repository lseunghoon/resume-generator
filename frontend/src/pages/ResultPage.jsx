import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import { getCoverLetter, addQuestion, reviseAnswer } from '../services/api';
import './ResultPage.css';

function ResultPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const [sessionId, setSessionId] = useState('');
    const [answers, setAnswers] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState(0);
    const [jobPostingUrl, setJobPostingUrl] = useState('');
    const [selectedJob, setSelectedJob] = useState('');
    const [jobDescription, setJobDescription] = useState('');
    const [userQuestion, setUserQuestion] = useState(''); // 사용자가 선택한 문항
    const [showAddQuestionModal, setShowAddQuestionModal] = useState(false);
    const [newQuestion, setNewQuestion] = useState('');
    const [isAddingQuestion, setIsAddingQuestion] = useState(false);
    const [revisionRequest, setRevisionRequest] = useState('');
    const [isRevising, setIsRevising] = useState(false);
    const [copiedIndex, setCopiedIndex] = useState(null);
    const [answerHistory, setAnswerHistory] = useState({}); // 각 문항별 히스토리: { questionIndex: [historyItems] }
    const [chatMessagesRef, setChatMessagesRef] = useState(null); // 스크롤을 위한 ref
    const [inputRef, setInputRef] = useState(null); // 입력창 포커스를 위한 ref



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
        // 2. 쿼리 파라미터에서 찾기
        else if (location.search) {
            const urlParams = new URLSearchParams(location.search);
            currentSessionId = urlParams.get('sessionId') || '';
            console.log('ResultPage - sessionId from query params:', currentSessionId);
        }
        
        console.log('ResultPage - Final sessionId:', currentSessionId);
        
        if (currentSessionId) {
            setSessionId(currentSessionId);
            
            // location.state에서 다른 데이터 가져오기
            if (location.state) {
                setJobPostingUrl(location.state.jobPostingUrl || '');
                setSelectedJob(location.state.selectedJob || '');
                setJobDescription(location.state.jobDescription || '');
                setUserQuestion(location.state.question || '');
            }
            
            // 자기소개서 데이터 가져오기
            fetchCoverLetter(currentSessionId);
        } else {
            // 세션 ID가 없으면 홈으로 이동
            console.log('ResultPage - No sessionId found, redirecting to home');
            navigate('/');
        }
    }, [location.state, location.search, navigate]);

    const fetchCoverLetter = async (currentSessionId) => {
        if (!currentSessionId) {
            console.error('세션 ID가 없습니다.');
            setError('세션 ID가 없습니다.');
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        try {
            const response = await getCoverLetter(currentSessionId);
            
            if (response.questions && response.questions.length > 0) {
                // 실제 API 응답 구조에 맞게 수정
                const answers = response.questions.map((question, index) => ({
                    id: question.id || index + 1,
                    question: question.question,
                    answer: question.answer_history ? JSON.parse(question.answer_history)[question.current_version_index || 0] : question.answer || '',
                    length: question.length || 500,
                    has_undo: (question.current_version_index || 0) > 0,
                    has_redo: question.answer_history ? JSON.parse(question.answer_history).length > (question.current_version_index || 0) + 1 : false
                }));
                
                setAnswers(answers);
                setActiveTab(0);
            } else {
                setError('자기소개서 데이터를 불러올 수 없습니다.');
            }
        } catch (error) {
            console.error('자기소개서 조회 오류:', error);
            setError(error.message || '자기소개서를 불러오는데 실패했습니다.');
        } finally {
            setIsLoading(false);
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
    };

    const handleSubmitRevision = async () => {
        if (!revisionRequest.trim()) return;
        
        setIsRevising(true);
        try {
            const response = await reviseAnswer(sessionId, activeTab, revisionRequest);
            
            // mock API 응답 구조에 맞게 수정
            const revisedAnswerText = response.revised_answer?.answer || response.revised_answer;
            
            if (revisedAnswerText) {
                // 현재 버전을 과거 버전으로 저장
                const currentAnswer = answers[activeTab];
                const newHistoryItem = {
                    id: Date.now(),
                    question: currentAnswer.question,
                    answer: currentAnswer.answer,
                    length: currentAnswer.length,
                    timestamp: new Date().toLocaleString()
                };
                
                setAnswerHistory(prev => ({
                    ...prev,
                    [activeTab]: [...(prev[activeTab] || []), newHistoryItem]
                }));
                
                // 새로운 버전으로 업데이트
                setAnswers(prev => prev.map((item, i) => 
                    i === activeTab 
                        ? { ...item, answer: revisedAnswerText, length: revisedAnswerText.length }
                        : item
                ));
                
                setRevisionRequest('');
                
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
        }
    };
    
    const handleCopy = async (index, isHistory = false, historyIndex = null) => {
        try {
            let textToCopy;
            if (isHistory && historyIndex !== null) {
                textToCopy = answerHistory[index] ? answerHistory[index][historyIndex].answer : answers[index].answer;
            } else {
                textToCopy = answers[index].answer;
            }
            
            await navigator.clipboard.writeText(textToCopy);
            setCopiedIndex(isHistory ? `history-${historyIndex}` : index);
            setTimeout(() => setCopiedIndex(null), 2000);
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
            console.log('문항은 최대 3개까지 추가 가능합니다.');
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
                const newAnswer = {
                    id: answers.length + 1,
                    question: newAnswerData.question,
                    length: newAnswerData.answer?.length || 0,
                    answer: newAnswerData.answer,
                    has_undo: false,
                    has_redo: false
                };
                
                const newIndex = answers.length;
                
                setAnswers(prev => [...prev, newAnswer]);
                
                // 새로 추가된 질문에 대한 히스토리 초기화
                setAnswerHistory(prev => ({
                    ...prev,
                    [newIndex]: [] // 새로운 문항의 히스토리는 빈 배열로 초기화
                }));
                
                // 새로 추가된 질문에 대한 상태 초기화
                setRevisionRequest('');
                setNewQuestion('');
                setShowAddQuestionModal(false);
                
                // 새로 추가된 탭으로 이동
                setActiveTab(newIndex);
                
                console.log('문항 추가 완료:', newAnswer);
            } else {
                console.error('응답에 question이 없습니다:', response);
            }
        } catch (err) {
            console.error('질문 추가 실패:', err);
            alert('문항 추가에 실패했습니다. 다시 시도해주세요.');
        } finally {
            setIsAddingQuestion(false);
        }
    };

    if (isLoading) {
        return (
            <div className="result-page">
                <Header progress={100} />
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>결과를 불러오고 있습니다...</p>
                </div>
            </div>
        );
    }

    if (error || answers.length === 0) {
        return (
            <div className="result-page">
                <Header progress={100} />
                <div className="error-container">
                    <p>{error || '결과를 찾을 수 없습니다.'}</p>
                    <Button onClick={() => navigate('/')}>다시 시작</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="result-page">
            <Header progress={100} showRestartButton={true} onRestart={() => navigate('/')} />
            
            <div className="page-content">
                <div className="content-wrapper">
                    {/* 채용공고 정보 섹션 */}
                    <div className="job-info-section">
                        <div className="job-link">
                            <span className="link-icon">🔗</span>
                            <a href={jobPostingUrl} target="_blank" rel="noopener noreferrer">
                                {jobPostingUrl}
                            </a>
                        </div>
                        <div className="job-position">
                            <span className="briefcase-icon">💼</span>
                            <span>{selectedJob}</span>
                        </div>
                    </div>

                    {/* 탭 네비게이션 */}
                    <div className="tab-navigation">
                        {answers.map((item, index) => (
                            <button
                                key={index}
                                className={`tab ${activeTab === index ? 'active' : ''}`}
                                onClick={() => setActiveTab(index)}
                            >
                                {item.question}
                            </button>
                        ))}
                        
                        <button 
                            className="add-tab"
                            onClick={() => setShowAddQuestionModal(true)}
                            title="새 문항 추가"
                            disabled={answers.length >= 3}
                        >
                            + 문항 추가
                        </button>
                    </div>

                    {/* 대화창 형태의 콘텐츠 */}
                    {answers[activeTab] && (
                        <div className="chat-container">
                            {/* 과거 버전들 (가장 오래된 것부터) */}
                            {answerHistory[activeTab] && answerHistory[activeTab].map((historyItem, historyIndex) => (
                                <div key={historyItem.id} className="message-item history-message">
                                    <div className="message-content">
                                        <div className="message-text">
                                            {removeMarkdownBold(historyItem.answer).split('\n').map((line, i) => (
                                                <p key={i}>{line}</p>
                                            ))}
                                        </div>
                                        <div className="message-meta">
                                            <span className="message-character-count">공백포함 {calculateTextLength(historyItem.answer)}자</span>
                                            <button 
                                                className="message-copy-button"
                                                onClick={() => handleCopy(activeTab, true, historyIndex)}
                                            >
                                                {copiedIndex === `history-${historyIndex}` ? (
                                                    <span>✅</span>
                                                ) : (
                                                    <img 
                                                        src="/assets/content_copy.svg" 
                                                        alt="복사" 
                                                        className="copy-icon"
                                                    />
                                                )}
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
                                            {copiedIndex === activeTab ? (
                                                <span>✅</span>
                                            ) : (
                                                <img 
                                                    src="/assets/content_copy.svg" 
                                                    alt="복사" 
                                                    className="copy-icon"
                                                />
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 고정된 수정 입력창 */}
                    <div className="chat-input-section">
                        <div className="revision-input">
                            <input
                                type="text"
                                placeholder="수정할 내용을 입력해주세요"
                                value={revisionRequest || ''}
                                onChange={(e) => handleRevisionRequestChange(e.target.value)}
                                onKeyPress={(e) => {
                                    if (e.key === 'Enter') {
                                        handleSubmitRevision();
                                        // 엔터 키 후에도 포커스 유지
                                        setTimeout(() => {
                                            focusInput();
                                        }, 50);
                                    }
                                }}
                                disabled={isRevising}
                                ref={setInputRef}
                            />
                            <button 
                                className="send-revision"
                                onClick={handleSubmitRevision}
                                disabled={isRevising || !revisionRequest.trim()}
                            >
                                {isRevising ? '⏳' : '→'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* 문항 추가 모달 */}
            {showAddQuestionModal && (
                <div className="modal-overlay">
                    <div className="add-question-modal">
                        <h3>추가로 생성하고자 하는<br/>문항을 입력해주세요</h3>
                        <p>자기소개서 문항은 최대 3개까지 추가 가능합니다.</p>
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
                            >
                                {isAddingQuestion ? '생성 중...' : '추가 생성하기'}
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
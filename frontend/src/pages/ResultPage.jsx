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

    // 드래그 시작 시 시각적 피드백
    const handleDragStart = (e) => {
        e.target.style.opacity = '0.5';
        e.dataTransfer.setData('text/plain', e.target.textContent);
    };

    const handleDragEnd = (e) => {
        e.target.style.opacity = '1';
    };

    useEffect(() => {
        console.log('ResultPage - location.state:', location.state);
        console.log('ResultPage - sessionId from state:', location.state?.sessionId);
        
        // location.state에서 데이터 가져오기
        if (location.state) {
            setSessionId(location.state.sessionId || '');
            setJobPostingUrl(location.state.jobPostingUrl || '');
            setSelectedJob(location.state.selectedJob || '');
            setJobDescription(location.state.jobDescription || '');
            setUserQuestion(location.state.question || ''); // 사용자가 선택한 문항
            
            // 사용자가 선택한 문항으로 초기 답변 생성
            if (location.state.question) {
                const initialAnswer = {
                    id: 1,
                    question: location.state.question,
                    answer: "저는 어린 시절부터 컴퓨터에 관심이 많았습니다. 중학교 때 처음 프로그래밍을 접하게 되었고, 그때부터 개발자의 꿈을 키워왔습니다. 고등학교에서는 정보올림피아드에 참가하여 전국 대회에서 입상하는 성과를 거두었고, 대학교에서는 컴퓨터공학을 전공하며 더욱 깊이 있는 지식을 쌓았습니다. 특히 웹 개발에 관심을 가지고 React, Node.js 등의 기술을 학습하며 실무 프로젝트에도 참여했습니다. 이러한 경험들을 통해 저는 지속적인 학습과 도전 정신의 중요성을 깨달았고, 이를 바탕으로 더 나은 개발자가 되기 위해 노력하고 있습니다.",
                    length: 300,
                    has_undo: false,
                    has_redo: false
                };
                setAnswers([initialAnswer]);
                setIsLoading(false);
                return;
            }
        }

        // 세션 ID가 있으면 자기소개서 데이터 가져오기
        if (location.state?.sessionId) {
            console.log('ResultPage - Fetching cover letter with sessionId:', location.state.sessionId);
            fetchCoverLetter();
        } else {
            // 세션 ID가 없으면 홈으로 이동
            console.log('ResultPage - No sessionId, redirecting to home');
            navigate('/');
        }
    }, [location.state, navigate]);

    const fetchCoverLetter = async () => {
        const currentSessionId = location.state?.sessionId;
        if (!currentSessionId) {
            console.error('세션 ID가 없습니다.');
            setError('세션 ID가 없습니다.');
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        try {
            const response = await getCoverLetter(currentSessionId);
            
            if (response.answers && response.answers.length > 0) {
                // Mock 환경에서는 사용자가 선택한 문항을 사용
                const mockAnswers = response.answers.map((answer, index) => ({
                    ...answer,
                    question: index === 0 ? userQuestion : answer.question // 첫 번째 문항은 사용자가 선택한 문항으로 교체
                }));
                
                setAnswers(mockAnswers);
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
                                        <div className="message-text" 
                                             draggable="true"
                                             onDragStart={handleDragStart}
                                             onDragEnd={handleDragEnd}
                                        >
                                            {removeMarkdownBold(historyItem.answer).split('\n').map((line, i) => (
                                                <p key={i}>{line}</p>
                                            ))}
                                        </div>
                                        <div className="message-meta">
                                            <span className="message-character-count">공백포함 {historyItem.length}자</span>
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
                                    <div className="message-text" 
                                         draggable="true"
                                         onDragStart={handleDragStart}
                                         onDragEnd={handleDragEnd}
                                    >
                                        {removeMarkdownBold(answers[activeTab].answer).split('\n').map((line, i) => (
                                            <p key={i}>{line}</p>
                                        ))}
                                    </div>
                                    <div className="message-meta">
                                        <span className="message-character-count">공백포함 {answers[activeTab].length}자</span>
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
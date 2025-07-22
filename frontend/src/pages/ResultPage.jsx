import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/Button';
import { getSession, revise } from '../services/api';
import './ResultPage.css';

function ResultPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const [sessionId, setSessionId] = useState('');
    const [qaData, setQaData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [editStates, setEditStates] = useState({});
    const [activeTab, setActiveTab] = useState(0);
    const [jobInfo, setJobInfo] = useState({ url: '', position: '' });
    const [showAddQuestionModal, setShowAddQuestionModal] = useState(false);
    const [newQuestion, setNewQuestion] = useState('');
    const [isGeneratingNewQuestion, setIsGeneratingNewQuestion] = useState(false);
    const [copiedIndex, setCopiedIndex] = useState(null);

    useEffect(() => {
        const searchParams = new URLSearchParams(location.search);
        const id = searchParams.get('sessionId');
        
        if (id) {
            setSessionId(id);
            fetchSessionData(id);
        } else if (location.state && location.state.jobPostingUrl) {
            // Mock 데이터 사용 (백엔드 연동 실패시 백업)
            setLoading(true);
            setTimeout(() => {
                const mockData = [
                    {
                        id: 1,
                        question: "지원 동기는 무엇인가요?",
                        length: 492,
                        answer: "국제는 정부의 동양이인 정부가 제품의 지속해서 강력한 글제를 충가하거나 새 비율을 설치할 수 있다. 국가는 농업 및 어업의 보조촉성하기 위하여 농 어촌을 위한어야 볼 수 있다. 발변이 중대한 설서화의 정제로 직무를 수행할 수 없을 때에는 변절이 정하는 바에 의하여 틱집하게 할 수 있다.",
                        has_undo: false,
                        has_redo: false
                    },
                    {
                        id: 2,
                        question: "성장과정을 말씀해주세요",
                        length: 450,
                        answer: "저는 어려서부터 창의적인 문제 해결에 관심이 많았습니다. 특히 디자인 분야에서 사용자의 니즈를 파악하고 이를 시각적으로 표현하는 것에 흥미를 느꼈습니다. 중학교 때부터 그래픽 디자인 프로그램을 독학으로 배우기 시작했고, 고등학교에서는 동아리 활동을 통해 학교 행사 포스터와 웹사이트 디자인을 담당하며 실무 경험을 쌓았습니다.",
                        has_undo: false,
                        has_redo: false
                    }
                ];
                
                setQaData(mockData);
                setJobInfo({ 
                    url: '[스케치업] [기주식] 콘텐츠 디자이너 채용 공고 | 원티드',
                    position: '프로덕트 디자이너'
                });
                setLoading(false);
            }, 1000);
        } else {
            navigate('/');
        }
    }, [location, navigate]);

    const fetchSessionData = async (id) => {
        try {
            const data = await getSession(id);
            
            if (data && data.questions) {
                const formattedData = data.questions.map((item, index) => ({
                    id: index + 1,
                    question: item.question,
                    length: item.answer?.length || 0,
                    answer: item.answer || '',
                    has_undo: false,
                    has_redo: false
                }));
                
                setQaData(formattedData);
                setJobInfo({
                    url: data.jobDescriptionUrl || '',
                    position: data.selectedJob || ''
                });
            }
        } catch (err) {
            console.error('세션 데이터 로드 실패:', err);
            setError('결과를 불러올 수 없습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (index) => {
        setEditStates(prev => ({
            ...prev,
            [index]: {
                isEditing: true,
                revisionRequest: ''
            }
        }));
    };

    const handleCancelEdit = (index) => {
        setEditStates(prev => ({
            ...prev,
            [index]: {
                isEditing: false,
                revisionRequest: ''
            }
        }));
    };

    const handleRevisionRequestChange = (index, value) => {
        setEditStates(prev => ({
            ...prev,
            [index]: {
                ...prev[index],
                revisionRequest: value
            }
        }));
    };

    const handleSubmitRevision = async (index) => {
        const editState = editStates[index];
        if (!editState?.revisionRequest.trim()) return;

        try {
            setEditStates(prev => ({
                ...prev,
                [index]: { ...prev[index], isLoading: true }
            }));

            const response = await revise({
                sessionId,
                questionIndex: index,
                revisionRequest: editState.revisionRequest
            });

            if (response.revised_answer) {
                setQaData(prev => prev.map((item, i) => 
                    i === index 
                        ? { ...item, answer: response.revised_answer, length: response.revised_answer.length }
                        : item
                ));
                
                setEditStates(prev => ({
                    ...prev,
                    [index]: {
                        isEditing: false,
                        revisionRequest: '',
                        isLoading: false
                    }
                }));
            }
        } catch (err) {
            console.error('수정 요청 실패:', err);
            setEditStates(prev => ({
                ...prev,
                [index]: { ...prev[index], isLoading: false }
            }));
        }
    };

    const handleCopy = async (index) => {
        try {
            await navigator.clipboard.writeText(qaData[index].answer);
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        } catch (err) {
            console.error('복사 실패:', err);
        }
    };

    const handleAddQuestion = async () => {
        if (!newQuestion.trim() || qaData.length >= 3) return;

        setIsGeneratingNewQuestion(true);
        try {
            // 새로운 질문 추가 API 호출 (구현 필요)
            // const response = await addQuestion({ sessionId, question: newQuestion });
            
            // Mock 응답으로 임시 구현
            const newAnswer = "새로운 질문에 대한 AI 생성 답변입니다. 실제로는 백엔드에서 생성된 답변이 여기에 표시됩니다.";
            
            const newQA = {
                id: qaData.length + 1,
                question: newQuestion,
                length: newAnswer.length,
                answer: newAnswer,
                has_undo: false,
                has_redo: false
            };
            
            setQaData(prev => [...prev, newQA]);
            setNewQuestion('');
            setShowAddQuestionModal(false);
        } catch (err) {
            console.error('질문 추가 실패:', err);
        } finally {
            setIsGeneratingNewQuestion(false);
        }
    };

    if (loading) {
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

    if (error || qaData.length === 0) {
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
                            <a href={jobInfo.url} target="_blank" rel="noopener noreferrer">
                                {jobInfo.url}
                            </a>
                        </div>
                        <div className="job-position">
                            <span className="building-icon">🏢</span>
                            <span>{jobInfo.position}</span>
                        </div>
                    </div>

                    {/* 탭 네비게이션 */}
                    <div className="tab-navigation">
                        {qaData.map((item, index) => (
                            <button
                                key={index}
                                className={`tab ${activeTab === index ? 'active' : ''}`}
                                onClick={() => setActiveTab(index)}
                            >
                                {item.question}
                            </button>
                        ))}
                        
                        {qaData.length < 3 && (
                            <button 
                                className="add-tab"
                                onClick={() => setShowAddQuestionModal(true)}
                            >
                                + 질문 추가
                            </button>
                        )}
                    </div>

                    {/* 활성 탭 콘텐츠 */}
                    {qaData[activeTab] && (
                        <div className="tab-content">
                            <div className="answer-header">
                                <h3>{qaData[activeTab].question}</h3>
                                <div className="answer-meta">
                                    <span className="character-count">글자수 {qaData[activeTab].length}자</span>
                                    <button 
                                        className="copy-button"
                                        onClick={() => handleCopy(activeTab)}
                                    >
                                        {copiedIndex === activeTab ? '복사됨!' : '복사'}
                                    </button>
                                </div>
                            </div>

                            <div className="answer-content">
                                <div className="answer-text">
                                    {qaData[activeTab].answer.split('\n').map((line, i) => (
                                        <p key={i}>{line}</p>
                                    ))}
                                </div>

                                {/* AI 수정 요청 인라인 입력 */}
                                {editStates[activeTab]?.isEditing ? (
                                    <div className="revision-input-section">
                                        <div className="revision-input">
                                            <input
                                                type="text"
                                                placeholder="어떤 내용을 수정할까요?"
                                                value={editStates[activeTab]?.revisionRequest || ''}
                                                onChange={(e) => handleRevisionRequestChange(activeTab, e.target.value)}
                                                onKeyPress={(e) => {
                                                    if (e.key === 'Enter') {
                                                        handleSubmitRevision(activeTab);
                                                    }
                                                }}
                                                disabled={editStates[activeTab]?.isLoading}
                                            />
                                            <button 
                                                className="send-revision"
                                                onClick={() => handleSubmitRevision(activeTab)}
                                                disabled={editStates[activeTab]?.isLoading || !editStates[activeTab]?.revisionRequest.trim()}
                                            >
                                                {editStates[activeTab]?.isLoading ? '⏳' : '→'}
                                            </button>
                                        </div>
                                        <button 
                                            className="cancel-revision"
                                            onClick={() => handleCancelEdit(activeTab)}
                                        >
                                            취소
                                        </button>
                                    </div>
                                ) : (
                                    <div className="answer-actions">
                                        <button 
                                            className="edit-button"
                                            onClick={() => handleEdit(activeTab)}
                                        >
                                            ✏️ 수정하기
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* 질문 추가 모달 */}
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
                                disabled={!newQuestion.trim() || isGeneratingNewQuestion}
                            >
                                {isGeneratingNewQuestion ? '생성 중...' : '추가 생성하기'}
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
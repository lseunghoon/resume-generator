import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { getSession, revise } from '../services/api';
import './ResultPage.css';

function ResultPage() {
    const location = useLocation();
    const [sessionId, setSessionId] = useState('');
    const [qaData, setQaData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [editStates, setEditStates] = useState({});

    useEffect(() => {
        const searchParams = new URLSearchParams(location.search);
        const id = searchParams.get('sessionId');
        if (id) {
            setSessionId(id);
        } else {
            setError('세션 ID가 없어 자기소개서를 조회할 수 없습니다.');
            setLoading(false);
        }
    }, [location.search]);

    useEffect(() => {
        if (!sessionId) return;

        const fetchInitialData = async () => {
            setLoading(true);
            try {
                const response = await getSession(sessionId);
                if (response.questions && response.questions.length > 0) {
                    setQaData(response.questions);
                    setEditStates(response.questions.reduce((acc, q) => ({
                        ...acc,
                        [q.id]: { prompt: '', isProcessing: false }
                    }), {}));
                } else {
                    setError('생성된 자기소개서가 없습니다.');
                }
            } catch (err) {
                console.error("세션 데이터 로딩 실패:", err);
                setError('자기소개서를 불러오는 데 실패했습니다. 다시 시도해 주세요.');
            } finally {
                setLoading(false);
            }
        };

        fetchInitialData();
    }, [sessionId]);

    const handleEditChange = (id, value) => {
        setEditStates(prev => ({ ...prev, [id]: { ...prev[id], prompt: value } }));
    };

    const handleVersionControl = async (q_idx, action, prompt = '') => {
        const questionId = qaData[q_idx].id;
        
        setEditStates(prev => ({ ...prev, [questionId]: { ...prev[questionId], isProcessing: true } }));

        try {
            const res = await revise({ sessionId, q_idx, action, prompt });
            if (res.updatedQuestion) {
                setQaData(prev => prev.map(q => q.id === res.updatedQuestion.id ? res.updatedQuestion : q));
                if (action === 'revise') {
                    handleEditChange(questionId, ''); // 수정 요청 후 프롬프트 창 비우기
                }
            }
        } catch (err) {
            console.error(`${action} 실패:`, err);
            alert(`${action} 중 오류가 발생했습니다.`);
        } finally {
            setEditStates(prev => ({ ...prev, [questionId]: { ...prev[questionId], isProcessing: false } }));
        }
    };
    
    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
    };

    if (loading) return <div className="loading-container">자기소개서를 불러오는 중입니다...</div>;
    if (error) return <div className="error-container">{error}</div>;

    return (
        <div className="result-page-container">
            <h1>자기소개서 생성 결과</h1>
            
            <div className="qa-list">
                {qaData.map((qa, index) => (
                    <div key={qa.id} className="qa-item">
                        <div className="question-header">
                            <h3>{qa.question} ({qa.length}자)</h3>
                            <div className="button-group">
                                <button 
                                    onClick={() => handleVersionControl(index, 'undo')} 
                                    disabled={!qa.has_undo || editStates[qa.id]?.isProcessing}
                                    title="되돌리기"
                                    className="version-btn"
                                >
                                    ⬅️
                                </button>
                                <button 
                                    onClick={() => handleVersionControl(index, 'redo')} 
                                    disabled={!qa.has_redo || editStates[qa.id]?.isProcessing}
                                    title="다시 실행"
                                    className="version-btn"
                                >
                                    ➡️
                                </button>
                                <button onClick={() => copyToClipboard(qa.answer)} disabled={editStates[qa.id]?.isProcessing}>복사</button>
                            </div>
                        </div>

                        <div className="answer-box">
                            {qa.answer ? qa.answer.split('\n').map((line, i) => (
                                <p key={i}>{line}</p>
                            )) : <p>답변이 없습니다.</p>}
                        </div>

                        <div className="edit-section">
                            <textarea
                                value={editStates[qa.id]?.prompt || ''}
                                onChange={(e) => handleEditChange(qa.id, e.target.value)}
                                placeholder="수정하고 싶은 내용을 자세히 입력해주세요. (예: '경험' 부분에 '~~ 프로젝트' 경험을 추가해서 다시 써줘)"
                                disabled={editStates[qa.id]?.isProcessing}
                            />
                            <div className="edit-actions">
                                <button 
                                    onClick={() => handleVersionControl(index, 'revise', editStates[qa.id].prompt)} 
                                    disabled={!editStates[qa.id]?.prompt.trim() || editStates[qa.id]?.isProcessing}
                                >
                                    {editStates[qa.id]?.isProcessing ? '수정 중...' : '수정 요청'}
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ResultPage; 
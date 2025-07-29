'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { generateCoverLetter, reviseCoverLetter, deleteSession } from '../../api';

export default function ResultPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('sessionId');

  const [answers, setAnswers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revisionPrompts, setRevisionPrompts] = useState<string[]>([]);
  const [revisingIndex, setRevisingIndex] = useState<number | null>(null);

  useEffect(() => {
    const generateAnswers = async () => {
      if (!sessionId) {
        setError('세션 ID가 없습니다.');
        setLoading(false);
        return;
      }

      try {
        const response = await generateCoverLetter(sessionId);
        console.log('Generation response:', response);
        setAnswers(response.answers);
        setRevisionPrompts(new Array(response.answers.length).fill(''));
      } catch (err) {
        console.error('Generation error:', err);
        setError(err instanceof Error ? err.message : '자기소개서 생성 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };

    generateAnswers();
  }, [sessionId]);

  const handleRevise = async (index: number) => {
    if (!revisionPrompts[index]?.trim()) {
      setError('수정 요청을 입력해주세요.');
      return;
    }

    if (!sessionId) {
      setError('세션 ID가 없습니다.');
      return;
    }

    setRevisingIndex(index);
    setError(null);

    try {
      const response = await reviseCoverLetter(sessionId, index, revisionPrompts[index]);
      console.log('Revision response:', response);
      
      const newAnswers = [...answers];
      newAnswers[index] = response.revisedAnswer;
      setAnswers(newAnswers);
      
      const newPrompts = [...revisionPrompts];
      newPrompts[index] = '';
      setRevisionPrompts(newPrompts);
    } catch (err) {
      console.error('Revision error:', err);
      setError(err instanceof Error ? err.message : '자기소개서 수정 중 오류가 발생했습니다.');
    } finally {
      setRevisingIndex(null);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        console.log('Text copied to clipboard');
      })
      .catch((err) => {
        console.error('Failed to copy text:', err);
        setError('텍스트 복사에 실패했습니다.');
      });
  };

  const handleDelete = async () => {
    if (!sessionId) return;

    try {
      await deleteSession(sessionId);
      console.log('Session deleted');
      window.location.href = '/';
    } catch (err) {
      console.error('Deletion error:', err);
      setError(err instanceof Error ? err.message : '세션 삭제 중 오류가 발생했습니다.');
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">자기소개서를 생성하고 있습니다...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">자기소개서 결과</h1>
        <button
          onClick={handleDelete}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          세션 삭제
        </button>
      </div>

      <div className="space-y-8">
        {answers.map((answer, index) => (
          <div key={index} className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-semibold">질문 {index + 1}</h2>
              <button
                onClick={() => handleCopy(answer)}
                className="px-3 py-1 text-blue-600 hover:text-blue-800"
              >
                복사
              </button>
            </div>
            
            <div className="prose max-w-none mb-4">
              {answer.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>

            <div className="mt-4">
              <textarea
                value={revisionPrompts[index] || ''}
                onChange={(e) => {
                  const newPrompts = [...revisionPrompts];
                  newPrompts[index] = e.target.value;
                  setRevisionPrompts(newPrompts);
                }}
                placeholder="수정 요청을 입력하세요..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md mb-2"
                rows={3}
              />
              <button
                onClick={() => handleRevise(index)}
                disabled={revisingIndex === index}
                className={`px-4 py-2 text-white rounded-md flex items-center justify-center ${
                  revisingIndex === index
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {revisingIndex === index ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    수정 중...
                  </>
                ) : (
                  '수정하기'
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 
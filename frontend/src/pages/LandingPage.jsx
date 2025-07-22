import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../components/Button.css';

const LandingPage = () => {
  const navigate = useNavigate();
  return (
    <div style={{ background: 'linear-gradient(180deg, #eaeffa 0%, #fff 100%)', minHeight: '100vh' }}>
      <header style={{ display: 'flex', alignItems: 'center', height: 111, padding: '0 2rem' }}>
        <img src="/logo192.png" alt="로고" style={{ height: 39 }} />
      </header>
      <main style={{ maxWidth: 900, margin: '0 auto', padding: '2rem 1rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: 64, fontWeight: 700, margin: '2rem 0 1rem', letterSpacing: -1 }}>어떠한 질문도 AI로 손 쉽게</h1>
        <p style={{ fontSize: 24, marginBottom: '2rem' }}>기업과 직무에 최적화된 자기소개서로 합격의 가능성을 더합니다.</p>
        <button className="main-cta" onClick={() => navigate('/upload')}>무료로 시작하기</button>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 32, marginTop: 64 }}>
          <div className="feature-card">
            <h2>빠르지만 정확한 답변을</h2>
            <p>불필요한 정보 없이 핵심만 뽑아내어 답변 퀄리티를 높입니다.</p>
          </div>
          <div className="feature-card">
            <h2>내 이야기를 복잡한 정보없이 한 번에</h2>
            <p>기존 자기소개서 첨부만으로 나의 이야기를 자연스럽게 녹입니다.</p>
          </div>
          <div className="feature-card">
            <h2>지원하는 기업과 직무에 딱 맞게</h2>
            <p>실제 채용 공고를 분석하여 직무에 맞는 자기소개서를 생성합니다.</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPage; 
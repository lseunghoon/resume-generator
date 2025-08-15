import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { supabase } from '../services/supabaseClient';
import './LandingPage.css';

const LandingPage = () => {
	const navigate = useNavigate();
	const location = useLocation();
	const [email, setEmail] = useState('');
	const [message, setMessage] = useState('');
	const [submitting, setSubmitting] = useState(false);

	// 다른 페이지에서 메뉴를 통해 이동해온 경우 해당 섹션으로 스크롤
	useEffect(() => {
		if (location.state?.scrollTo) {
			const element = document.getElementById(location.state.scrollTo);
			if (element) {
				// 페이지 로드 후 약간의 지연을 두고 스크롤 실행
				setTimeout(() => {
					element.scrollIntoView({ behavior: 'smooth' });
				}, 100);
			}
			
			// state 정보 사용 후 즉시 제거
			navigate(location.pathname, { replace: true, state: undefined });
		}
	}, [location.state, navigate]);

	const handleStart = async () => {
		try {
			// 현재 세션 확인
			const { data: { session } } = await supabase.auth.getSession();
			console.log('LandingPage - 현재 세션 상태:', !!session);
			
			if (session) {
				// 이미 로그인된 경우: 바로 job-info 페이지로 이동
				console.log('로그인된 사용자, job-info 페이지로 이동');
				navigate('/job-info');
			} else {
				// 로그인되지 않은 경우: 로그인 페이지로 이동하고, 로그인 완료 후 job-info로 이동
				console.log('로그인되지 않은 사용자, 로그인 페이지로 이동');
				
				// next 경로를 localStorage에 저장 (OAuth 콜백 후에도 접근 가능하도록)
				localStorage.setItem('auth_redirect_path', '/job-info');
				
				const loginUrl = '/login?next=/job-info';
				console.log('LandingPage - 이동할 로그인 URL:', loginUrl);
				navigate(loginUrl);
			}
		} catch (error) {
			console.error('세션 확인 중 오류 발생:', error);
			// 오류 발생 시에도 로그인 페이지로 이동
			
			// next 경로를 localStorage에 저장
			localStorage.setItem('auth_redirect_path', '/job-info');
			
			const loginUrl = '/login?next=/job-info';
			console.log('LandingPage - 오류 발생 시 이동할 로그인 URL:', loginUrl);
			navigate(loginUrl);
		}
	};

	const handleContactSubmit = (e) => {
		e.preventDefault();
		if (submitting) return;
		setSubmitting(true);
		try {
			const subject = encodeURIComponent('[써줌] 서비스 제안/문의');
			const body = encodeURIComponent(`From: ${email || 'anonymous'}\n\n${message}`);
			window.location.href = `mailto:zinozico0070@gmail.com?subject=${subject}&body=${body}`;
		} finally {
			setSubmitting(false);
		}
	};

	return (
		<div className="landing-root">
			{/* Main Content */}
			<main className="landing-main">
				{/* Hero Section */}
				<section className="hero">
					<div className="hero-card">
						<h1 className="hero-title">자소서, 쉽고 완벽하게 「써줌」 에서</h1>
						<button onClick={handleStart} className="hero-button">시작하기</button>
						<img src="/assets/example_image.png" alt="써줌 서비스 예시" className="hero-image" />
					</div>
				</section>

				{/* 서비스 소개 섹션 */}
				<section className="service-intro-section" id="service-intro">
					<div className="service-intro-content">
						<h2 className="service-intro-title">서비스 소개</h2>
						
						<div className="service-intro-grid">
							<div className="service-intro-item">
								<div className="service-intro-icon">
									<svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#0d80f2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										<path d="M2 17L12 22L22 17" stroke="#0d80f2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										<path d="M2 12L12 17L22 12" stroke="#0d80f2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								</div>
								<h3>1. 써줌이 어떤 서비스인지</h3>
								<p>AI 기반 맞춤형 자기소개서 생성 서비스입니다. 지원하고자 하는 회사와 직무에 맞춰 개인화된 자기소개서를 자동으로 작성해드립니다. 단순한 템플릿이 아닌, 실제 지원 상황에 최적화된 질문별 답변을 제공합니다.</p>
							</div>

							<div className="service-intro-item">
								<div className="service-intro-icon">
									<svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M9 12L11 14L15 10" stroke="#0d80f2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										<path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="#0d80f2" strokeWidth="2"/>
									</svg>
								</div>
								<h3>2. 왜 만들었는지</h3>
								<p>취업 준비생들이 자기소개서 작성에 어려움을 겪고, 각 회사마다 다른 요구사항에 맞춰 여러 번 작성해야 하는 번거로움을 해결하고자 했습니다. 또한 AI 기술을 활용해 개인 맞춤형 콘텐츠를 제공하여 더욱 효과적인 취업 준비를 도모합니다.</p>
							</div>

							<div className="service-intro-item">
								<div className="service-intro-icon">
									<svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="#0d80f2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								</div>
								<h3>3. 기대효과</h3>
								<p>자기소개서 작성 시간을 대폭 단축하고, 각 회사와 직무에 최적화된 맞춤형 내용을 제공받을 수 있습니다. AI의 분석을 통해 더욱 설득력 있고 체계적인 자기소개서를 작성할 수 있으며, 궁극적으로는 취업 성공률 향상과 만족스러운 직장 선택을 도울 수 있습니다.</p>
							</div>
						</div>

						{/* 사용 방법 */}
						<div style={{ display: 'flex', flexDirection: 'column', gap: 40, marginTop: 60 }}>
							{/* Step 1 */}
							<div style={{ display: 'flex', alignItems: 'flex-start', gap: 24 }}>
								<div style={{ 
									width: 40,
									height: 66.67,
									display: 'flex',
									flexDirection: 'column',
									alignItems: 'center'
								}}>
									<div style={{ 
										width: 24,
										height: 24,
										background: '#cfdbe8',
										borderRadius: '50%',
										marginBottom: 8
									}}></div>
									<div style={{ 
										width: 2,
										height: 32,
										background: '#cfdbe8'
									}}></div>
								</div>
								<div style={{ flex: 1 }}>
									<h3 style={{ 
										fontSize: '16px',
										fontWeight: 500,
										marginBottom: 8,
										color: '#0d141c'
									}}>
										지원 정보 입력
									</h3>
									<p style={{ 
										color: '#4a739c',
										lineHeight: 1.5,
										fontSize: '16px'
									}}>
										지원하고자 하는 회사명, 직무, 주요업무, 자격요건, 우대사항을 직관적인 인터페이스에 입력하세요.
									</p>
								</div>
							</div>

							{/* Step 2 */}
							<div style={{ display: 'flex', alignItems: 'flex-start', gap: 24 }}>
								<div style={{ 
									width: 40,
									height: 66.67,
									display: 'flex',
									flexDirection: 'column',
									alignItems: 'center'
								}}>
									<div style={{ 
										width: 2,
										height: 8,
										background: '#cfdbe8',
										marginBottom: 8
									}}></div>
									<div style={{ 
										width: 24,
										height: 24,
										background: '#cfdbe8',
										borderRadius: '50%',
										marginBottom: 8
									}}></div>
									<div style={{ 
										width: 2,
										height: 32,
										background: '#cfdbe8'
									}}></div>
								</div>
								<div style={{ flex: 1 }}>
									<h3 style={{ 
										fontSize: '16px',
										fontWeight: 500,
										marginBottom: 8,
										color: '#0d141c'
									}}>
										이력서 업로드
									</h3>
									<p style={{ 
										color: '#4a739c',
										lineHeight: 1.5,
										fontSize: '16px'
									}}>
										PDF 또는 DOCX 형식의 이력서를 업로드하면 AI가 자동으로 텍스트를 추출하고 분석합니다.
									</p>
								</div>
							</div>

							{/* Step 3 */}
							<div style={{ display: 'flex', alignItems: 'flex-start', gap: 24 }}>
								<div style={{ 
									width: 40,
									height: 66.67,
									display: 'flex',
									flexDirection: 'column',
									alignItems: 'center'
								}}>
									<div style={{ 
										width: 2,
										height: 8,
										background: '#cfdbe8',
										marginBottom: 8
									}}></div>
									<div style={{ 
										width: 24,
										height: 24,
										background: '#cfdbe8',
										borderRadius: '50%'
									}}></div>
								</div>
								<div style={{ flex: 1 }}>
									<h3 style={{ 
										fontSize: '16px',
										fontWeight: 500,
										marginBottom: 8,
										color: '#0d141c'
									}}>
										AI 자기소개서 생성
									</h3>
									<p style={{ 
										color: '#4a739c',
										lineHeight: 1.5,
										fontSize: '16px'
									}}>
										입력한 정보와 이력서를 바탕으로 AI가 맞춤형 자기소개서를 생성합니다. 질문별로 개별 답변을 제공합니다.
									</p>
								</div>
							</div>
						</div>
					</div>
				</section>

				{/* 자기소개서 작성하기 버튼 섹션 */}
				<section className="cta-section">
					<div className="cta-content">
						<h2 className="cta-title">지금 바로 시작해보세요</h2>
						<p className="cta-description">
							AI가 도와주는 맞춤형 자기소개서로 취업 준비를 한 단계 업그레이드하세요
						</p>
						<button onClick={handleStart} className="cta-button">
							자기소개서 작성하기
						</button>
					</div>
				</section>

				{/* Contact Section */}
				<section className="contact-section" id="feedback">
					<h2 className="contact-title">피드백</h2>
					<div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
						<div>
							<label style={{ 
								display: 'block',
								fontSize: '16px',
								fontWeight: 500,
								color: '#0d141c',
								marginBottom: 8
							}}>
								이메일
							</label>
							<input 
								type="email"
								value={email} 
								onChange={(e) => setEmail(e.target.value)} 
								placeholder="이메일을 입력하세요" 
								className="contact-input"
							/>
						</div>

						<div>
							<label style={{ 
								display: 'block',
								fontSize: '16px',
								fontWeight: 500,
								color: '#0d141c',
								marginBottom: 8
							}}>
								메시지
							</label>
							<textarea 
								value={message} 
								onChange={(e) => setMessage(e.target.value)} 
								placeholder="메시지를 입력하세요" 
								rows={6} 
								className="contact-textarea"
							/>
						</div>

						<div style={{ display: 'flex', justifyContent: 'flex-end' }}>
							<button 
								type="submit" 
								onClick={handleContactSubmit}
								disabled={submitting} 
								className="contact-submit"
							>
								{submitting ? '전송 중...' : '전송하기'}
							</button>
						</div>

					</div>
				</section>
			</main>

			{/* Footer */}
			<footer className="footer">
				<div className="footer-inner">
					<div style={{ display: 'flex', justifyContent: 'center', gap: 40, marginBottom: 20 }}>
						<button onClick={() => {
							navigate('/privacy', { replace: true });
							window.scrollTo(0, 0);
						}} className="footer-link">개인정보처리방침</button>
					</div>
				</div>
			</footer>
		</div>
	);
};

export default LandingPage;
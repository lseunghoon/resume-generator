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
						<div className="service-intro-main">
							<h2 className="service-intro-main-title">'써줌'이 완성하는 당신의 합격 자기소개서</h2>
							<div className="service-intro-description">
								<p className="service-intro-lead">
									AI 기술의 발전으로 글쓰기는 쉬워졌지만, 합격하는 자기소개서는 다릅니다.
								</p>
								<p className="service-intro-detail">
									'써줌'은 수많은 서류 합격자를 배출한 자기소개서 전문가의 노하우가 담긴,<br/>
									오직 자기소개서만을 위한 서비스입니다.<br/>
									전문가가 설계한 가이드라인이 각 문항의 의도를 정밀하게 파악하고,<br/>
									지원자의 경험과 역량을 합격에 가장 가까운 이야기로 완성합니다.
								</p>
							</div>
						</div>

												{/* 사용 방법 - 리뉴얼 (모두싸인 구조 참고) */}
						<div className="how-steps">
							{/* Step 1 */}
							<div className="how-step">
								<div className="how-step-image"><div className="image-placeholder"><span>더미 이미지</span></div></div>
								<div className="how-step-text">
									<h3 className="how-step-title">1. 채용 정보 입력</h3>
									<p className="how-step-desc">
										합격의 핵심인 '직무 적합성'을 위해<br/>
										지원하는 회사의 이름, 직무, 주요 업무, 자격 요건 등을 입력해 주세요.<br/>
										이 정보를 바탕으로 자기소개서의 방향이 설정됩니다.
									</p>
								</div>
							</div>

							{/* Step 2 */}
							<div className="how-step">
								<div className="how-step-image"><div className="image-placeholder"><span>더미 이미지</span></div></div>
								<div className="how-step-text">
									<h3 className="how-step-title">2. 기존 문서 업로드</h3>
									<p className="how-step-desc">
										나만의 경험과 역량이 담긴 문서를 업로드해 주세요.<br/>
										(이력서, 경력기술서, 포트폴리오 등)<br/>
										문서에서 채용 정보와 맞닿은 연결고리를 찾아냅니다.
									</p>
								</div>
							</div>

							{/* Step 3 */}
							<div className="how-step">
								<div className="how-step-image"><div className="image-placeholder"><span>더미 이미지</span></div></div>
								<div className="how-step-text">
									<h3 className="how-step-title">3. 문항 입력</h3>
									<p className="how-step-desc">
										작성해야 할 자기소개서 문항을 입력해 주세요.<br/>
										문항의 숨은 의도를 정확히 파악합니다.
									</p>
								</div>
							</div>

							{/* Step 4 */}
							<div className="how-step">
								<div className="how-step-image"><div className="image-placeholder"><span>더미 이미지</span></div></div>
								<div className="how-step-text">
									<h3 className="how-step-title">4. 자기소개서 작성</h3>
									<p className="how-step-desc">
										입력된 모든 정보를 종합하여, 지원하는 직무에 꼭 맞는<br/>
										자기소개서 초안이 완성됩니다.
									</p>
								</div>
							</div>

							{/* Step 5 */}
							<div className="how-step">
								<div className="how-step-image"><div className="image-placeholder"><span>더미 이미지</span></div></div>
								<div className="how-step-text">
									<h3 className="how-step-title">5. 수정 및 완성</h3>
									<p className="how-step-desc">
										'써줌'이 작성한 초안을 바탕으로 나만의 스토리를 더해<br/>
										자기소개서를 완성해 보세요.
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
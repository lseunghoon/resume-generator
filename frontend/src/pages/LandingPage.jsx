import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { supabase } from '../services/supabaseClient';
import { submitFeedback } from '../services/api';
import { scrollToElement, scrollToTop } from '../utils/scrollUtils';
import './LandingPage.css';

const LandingPage = () => {
	const navigate = useNavigate();
	const location = useLocation();
	const [email, setEmail] = useState('');
	const [message, setMessage] = useState('');
	const [submitting, setSubmitting] = useState(false);
	const [submitStatus, setSubmitStatus] = useState('idle'); // idle, loading, success, error
	const [statusMessage, setStatusMessage] = useState('');
	const [errorKey, setErrorKey] = useState(0); // 오류 애니메이션을 위한 key

	// 다른 페이지에서 메뉴를 통해 이동해온 경우 해당 섹션으로 스크롤
	useEffect(() => {
		let stateCleanupTimeout = null;
		let domRenderingTimeout = null;
		
		if (location.state?.scrollTo) {
			const sectionId = location.state.scrollTo;
			console.log(`LandingPage - scrollTo 처리: ${sectionId}`);
			
			// 페이지 렌더링 완료 후 스크롤 실행
			const handleScroll = async () => {
				try {
					// DOM 렌더링을 위한 대기 시간
					await new Promise(resolve => {
						domRenderingTimeout = setTimeout(() => {
							// 현재 여전히 랜딩페이지에 있을 때만 resolve
							if (window.location.pathname === '/') {
								resolve();
							}
						}, 300);
					});
					
					// 현재 페이지가 랜딩페이지가 아니면 스크롤하지 않음
					if (window.location.pathname !== '/') {
						console.log('LandingPage - 다른 페이지로 이동했으므로 스크롤 취소');
						return;
					}
					
					// 스크롤 유틸리티 함수 사용
					const success = await scrollToElement(sectionId, 5, 300);
					
					if (success) {
						console.log(`${sectionId} 섹션으로 스크롤 성공`);
					} else {
						console.warn(`${sectionId} 섹션으로 스크롤 실패`);
					}
				} catch (error) {
					console.error('스크롤 처리 중 오류:', error);
				} finally {
					// state 정보 사용 후 제거 (스크롤 완료 후)
					stateCleanupTimeout = setTimeout(() => {
						// 현재 여전히 랜딩페이지에 있고, scrollTo state가 있을 때만 제거
						if (window.location.pathname === '/' && location.state?.scrollTo) {
							console.log('LandingPage - scrollTo state 제거');
							navigate(location.pathname, { replace: true, state: undefined });
						}
					}, 1000);
				}
			};
			
			handleScroll();
		}
		
		// Cleanup: 컴포넌트 unmount 시 또는 의존성 변경 시 모든 timeout 정리
		return () => {
			if (stateCleanupTimeout) {
				console.log('LandingPage - scrollTo timeout 정리');
				clearTimeout(stateCleanupTimeout);
			}
			if (domRenderingTimeout) {
				console.log('LandingPage - DOM 렌더링 timeout 정리');
				clearTimeout(domRenderingTimeout);
			}
		};
	}, [location.state, navigate]);

	// 페이지 로드 시 스크롤 위치 확인 및 최상단 이동
	useEffect(() => {
		// scrollTo state가 있는 경우는 스크롤 최상단 이동하지 않음
		if (location.state?.scrollTo) {
			return;
		}
		
		// 페이지가 처음 로드될 때 스크롤을 최상단으로 이동
		const handleScrollToTop = async () => {
			try {
				// 현재 여전히 랜딩페이지에 있을 때만 스크롤 실행
				if (window.location.pathname === '/') {
					await scrollToTop(true);
					console.log('LandingPage - 최상단 스크롤 완료');
				}
			} catch (error) {
				console.error('최상단 스크롤 중 오류:', error);
			}
		};

		// 즉시 실행
		handleScrollToTop();
		
		// 페이지 렌더링 완료 후 한 번 더 시도
		const timer = setTimeout(() => {
			// 현재 여전히 랜딩페이지에 있을 때만 실행
			if (window.location.pathname === '/') {
				handleScrollToTop();
			}
		}, 200);
		
		return () => {
			clearTimeout(timer);
		};
	}, [location.pathname]); // 의존성을 pathname으로 변경하여 state 제거로 인한 재실행 방지

	const handleStart = async () => {
		try {
			// 새로 시작하기 전에 관련 데이터 모두 클리어
			console.log('LandingPage - 새로 시작하기, 모든 데이터 클리어');
			localStorage.removeItem('resultPageActiveTab');
			localStorage.removeItem('pendingSessionDelete');
			localStorage.removeItem('mockJobDataFilled');
			localStorage.removeItem('useMockApi');
			
			// 헤더 메뉴 클릭으로 인한 scrollTo state가 있다면 즉시 정리
			if (location.state?.scrollTo) {
				console.log('LandingPage - handleStart에서 scrollTo state 감지됨, 즉시 정리');
				// 현재 location.state를 null로 설정
				window.history.replaceState(null, '', window.location.pathname);
			}
			
			// 현재 세션 확인
			const { data: { session } } = await supabase.auth.getSession();
			console.log('LandingPage - 현재 세션 상태:', !!session);
			
			if (session) {
				// 이미 로그인된 경우: 바로 job-info 페이지로 이동 (state 없이 새로 시작)
				console.log('로그인된 사용자, job-info 페이지로 이동');
				navigate('/job-info', { replace: true, state: null });
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

	const handleContactSubmit = async (e) => {
		e.preventDefault();
		if (submitting) return;
		
		// 입력 검증
		if (!email.trim()) {
			setSubmitStatus('error');
			setStatusMessage('이메일을 입력해 주세요');
			setErrorKey(prev => prev + 1); // 애니메이션을 위한 key 증가
			return;
		}
		
		if (!message.trim()) {
			setSubmitStatus('error');
			setStatusMessage('메시지를 입력해 주세요');
			setErrorKey(prev => prev + 1); // 애니메이션을 위한 key 증가
			return;
		}
		
		if (message.trim().length < 5) {
			setSubmitStatus('error');
			setStatusMessage('메시지는 최소 5자 이상 입력해 주세요');
			setErrorKey(prev => prev + 1); // 애니메이션을 위한 key 증가
			return;
		}
		
		// 상태 초기화
		setSubmitStatus('loading');
		setStatusMessage('');
		setSubmitting(true);
		
		try {
			// API 호출
			const result = await submitFeedback(email.trim(), message.trim());
			
			if (result.success) {
				setSubmitStatus('success');
				setStatusMessage(result.message || '피드백이 성공적으로 전송되었습니다.');
				
				// 입력 필드 초기화
				setEmail('');
				setMessage('');
				
				// 3초 후 상태 초기화
				setTimeout(() => {
					setSubmitStatus('idle');
					setStatusMessage('');
				}, 3000);
			} else {
				setSubmitStatus('error');
				setStatusMessage(result.message || '피드백 전송에 실패했습니다.');
			}
		} catch (error) {
			console.error('피드백 제출 오류:', error);
			setSubmitStatus('error');
			setStatusMessage(error.message || '피드백 전송 중 오류가 발생했습니다.');
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
								<div className="how-step-image">
									<img src="/assets/jobinfo_example.png" alt="채용 정보 입력 예시" className="step-image" />
								</div>
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
								<div className="how-step-image">
									<img src="/assets/upload_example.png" alt="문서 업로드 예시" className="step-image" />
								</div>
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
								<div className="how-step-image">
									<img src="/assets/question_example.png" alt="문항 입력 예시" className="step-image" />
								</div>
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
								<div className="how-step-image">
									<img src="/assets/result_example.png" alt="자기소개서 완성 예시" className="step-image" />
								</div>
								<div className="how-step-text">
									<h3 className="how-step-title">4. 자기소개서 완성</h3>
									<p className="how-step-desc">
										입력된 모든 정보를 종합하여, 지원하는 직무에 꼭 맞는<br/>
										자기소개서가 작성됩니다.<br/>
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
						<h2 className="cta-title">지금 바로 시작해보세요!</h2>
						<p className="cta-description">
							써줌의 맞춤형 자기소개서로 취업 준비를 한 단계 업그레이드하세요
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
								placeholder="답변을 받을 이메일을 입력해 주세요" 
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
								placeholder="피드백 메시지를 입력해 주세요" 
								rows={6} 
								className="contact-textarea"
							/>
						</div>

						{/* 상태 메시지 표시 */}
						{submitStatus !== 'idle' && (
							<div key={`feedback-status-${submitStatus}-${errorKey}`} className={`feedback-status-message ${submitStatus}`}>
								{statusMessage}
							</div>
						)}
						
						<div style={{ display: 'flex', justifyContent: 'flex-end' }}>
							<button 
								type="submit" 
								onClick={handleContactSubmit}
								disabled={submitting} 
								className="contact-submit"
							>
								{submitting ? '전송 중...' : '보내기'}
							</button>
						</div>

					</div>
				</section>
			</main>

			{/* Footer */}
			<footer className="footer">
				<div className="footer-inner">
					<div className="footer-links">
						<button onClick={() => {
							navigate('/privacy', { replace: true });
						}} className="footer-link">개인정보처리방침</button>
						<button onClick={() => {
							// 추후 이용약관 페이지 구현 예정
							console.log('이용약관 페이지로 이동 (구현 예정)');
							// navigate('/terms', { replace: true });
							// window.scrollTo(0, 0);
						}} className="footer-link">이용약관</button>
					</div>
					
					<div className="footer-contact">
						<p className="footer-email">
							이메일 : sseojum@gmail.com
						</p>
					</div>
					
					<div className="footer-copyright">
						<p>© 2025 써줌. All rights reserved.</p>
					</div>
				</div>
			</footer>
		</div>
	);
};

export default LandingPage;
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../services/supabaseClient';
import './LandingPage.css';

const LandingPage = () => {
	const navigate = useNavigate();
	const [email, setEmail] = useState('');
	const [message, setMessage] = useState('');
	const [submitting, setSubmitting] = useState(false);

	const handleStart = async () => {
		try {
			const { data: { session } } = await supabase.auth.getSession();
			if (session) {
				navigate('/job-info');
			} else {
				navigate('/login?next=/job-info');
			}
		} catch (_) {
			navigate('/login?next=/job-info');
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
						<h1 className="hero-title">자소서, 쉽고 완벽하게 써줌에서</h1>
						<button onClick={handleStart} className="hero-button">시작하기</button>
						<img src="/assets/example_image.png" alt="써줌 서비스 예시" className="hero-image" />
					</div>
				</section>

				{/* How It Works Section */}
				<section className="how-section">
					<h2 className="how-title">자기소개서 작성 방법</h2>
					<div style={{ display: 'flex', flexDirection: 'column', gap: 40 }}>
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
									Input Your Information
								</h3>
								<p style={{ 
									color: '#4a739c',
									lineHeight: 1.5,
									fontSize: '16px'
								}}>
									Enter your work history, education, skills, and other relevant details into our intuitive interface.
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
									Customize Your Template
								</h3>
								<p style={{ 
									color: '#4a739c',
									lineHeight: 1.5,
									fontSize: '16px'
								}}>
									Select a template that matches your industry and personal style, then customize the layout, fonts, and colors.
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
									Download Your Resume
								</h3>
								<p style={{ 
									color: '#4a739c',
									lineHeight: 1.5,
									fontSize: '16px'
								}}>
									Download your polished resume in various formats, ready to be submitted to potential employers.
								</p>
							</div>
						</div>
					</div>
				</section>

				{/* Contact Section */}
				<section className="contact-section">
					<h2 className="contact-title">Contact Us</h2>
					<div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
						<div>
							<label style={{ 
								display: 'block',
								fontSize: '16px',
								fontWeight: 500,
								color: '#0d141c',
								marginBottom: 8
							}}>
								Your Email
							</label>
							<input 
								type="email"
								value={email} 
								onChange={(e) => setEmail(e.target.value)} 
								placeholder="Enter your email" 
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
								Message
							</label>
							<textarea 
								value={message} 
								onChange={(e) => setMessage(e.target.value)} 
								placeholder="Enter your message" 
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
								{submitting ? 'Sending...' : 'Submit'}
							</button>
						</div>

					</div>
				</section>
			</main>

			{/* Footer */}
			<footer className="footer">
				<div className="footer-inner">
					<div style={{ display: 'flex', justifyContent: 'center', gap: 40, marginBottom: 20 }}>
						<button onClick={() => navigate('/privacy')} className="footer-link">개인정보처리방침</button>
					</div>
				</div>
			</footer>
		</div>
	);
};

export default LandingPage;
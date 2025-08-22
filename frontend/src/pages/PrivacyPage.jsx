import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentMeta } from '../hooks/useDocumentMeta';
import Navigation from '../components/Navigation';

const PrivacyPage = () => {
	const navigate = useNavigate();

	// 페이지 진입 시 스크롤 복원 비활성화 및 최상단 이동
	useEffect(() => {
		// 브라우저의 스크롤 복원 기능 일시적으로 비활성화
		if (window.history.scrollRestoration) {
			window.history.scrollRestoration = 'manual';
		}

		// 항상 최상단으로 스크롤 이동
		const scrollToTop = () => {
			try {
				window.scrollTo(0, 0);
				document.documentElement.scrollTop = 0;
				document.body.scrollTop = 0;
			} catch (error) {
				console.error('PrivacyPage - 최상단 스크롤 중 오류:', error);
			}
		};

		// 즉시 실행
		scrollToTop();

		// DOM 렌더링 완료 후 한 번 더 시도
		const timer = setTimeout(scrollToTop, 100);

		// cleanup: 페이지 이탈 시 스크롤 복원 기능 다시 활성화
		return () => {
			clearTimeout(timer);
			if (window.history.scrollRestoration) {
				window.history.scrollRestoration = 'auto';
			}
		};
	}, []);

	const handleGoBack = () => {
		// 랜딩페이지로 돌아갈 때 scrollTo가 없어야 최상단 스크롤이 트리거됨
		// 이는 정상적인 동작이므로 그대로 유지
		navigate('/', { replace: true });
	};

	// SEO 메타데이터 설정
	useDocumentMeta({
		title: "개인정보처리방침 | 써줌",
		description: "써줌 AI 자기소개서 생성 서비스의 개인정보처리방침을 확인하세요. 개인정보 보호 정책과 사용자 데이터 처리 방식에 대한 상세 안내.",
		robots: "noindex, nofollow",
		ogTitle: "개인정보처리방침 | 써줌",
		ogDescription: "써줌 AI 자기소개서 생성 서비스의 개인정보처리방침을 확인하세요.",
		ogType: "article",
		ogUrl: "https://www.sseojum.com/privacy"
	});

	return (
		<div className="privacy-page" style={{ 
			maxWidth: 900, 
			margin: '0 auto', 
			padding: '24px',
			paddingTop: '80px', /* 헤더 높이 60px + 여백 20px */
			position: 'relative'
		}}>
			
			<Navigation 
				canGoBack={true}
				onGoBack={handleGoBack}
			/>
			
			<h1>써줌 개인정보처리방침</h1>
			<p><strong>시행일:</strong> 2025년 8월 22일</p>

			<p>
				본 개인정보처리방침은 써줌(이하 "회사")이 제공하는 AI 기반 자기소개서 작성/수정 서비스(이하 "서비스") 이용 시 개인정보의 수집, 이용, 제공, 관리 등에 관한 사항을 규정합니다.
			</p>
			<p>
				회사는 개인정보보호법 등 관련 법령을 준수하며, 이용자의 개인정보 보호 및 권익을 보호하고 개인정보와 관련한 이용자의 고충을 원활하게 처리할 수 있도록 다음과 같은 개인정보처리방침을 운영합니다.
			</p>

			<h2>1. 개인정보의 처리 목적</h2>
			<p>회사는 다음의 목적을 위하여 개인정보를 처리합니다. 처리하고 있는 개인정보는 다음의 목적 이외의 용도로는 이용되지 않으며, 이용 목적이 변경되는 경우에는 개인정보보호법 제18조에 따라 별도의 동의를 받는 등 필요한 조치를 이행할 예정입니다.</p>
			<ul>
				<li><strong>서비스 제공:</strong> AI 자기소개서 생성, 수정, 저장 및 관리</li>
				<li><strong>회원 관리:</strong> 회원 가입, 탈퇴, 서비스 이용 기록 관리</li>
				<li><strong>고객 지원:</strong> 문의사항 접수 및 응대, 피드백 처리</li>
				<li><strong>서비스 개선:</strong> 서비스 이용 통계 분석, 품질 개선</li>
				<li><strong>보안 및 안전:</strong> 부정 이용 방지, 서비스 보안 유지</li>
			</ul>

			<h2>2. 개인정보의 처리 및 보유기간</h2>
			<p>회사는 법령에 따른 개인정보 보유·이용기간 또는 정보주체로부터 개인정보를 수집 시에 동의받은 개인정보 보유·이용기간 내에서 개인정보를 처리·보유합니다.</p>
			<ul>
				<li><strong>회원 정보:</strong> 회원 탈퇴 시까지 (단, 관련 법령에 따라 일정 기간 보관이 필요한 경우 해당 기간)</li>
				<li><strong>서비스 이용 기록:</strong> 3년 (통신비밀보호법)</li>
				<li><strong>계약 또는 청약철회 등에 관한 기록:</strong> 5년 (전자상거래법)</li>
				<li><strong>대금결제 및 재화 등의 공급에 관한 기록:</strong> 5년 (전자상거래법)</li>
				<li><strong>소비자의 불만 또는 분쟁처리에 관한 기록:</strong> 3년 (전자상거래법)</li>
			</ul>

			<h2>3. 개인정보의 제3자 제공</h2>
			<p>회사는 정보주체의 개인정보를 제1조(개인정보의 처리 목적)에서 명시한 범위 내에서만 처리하며, 정보주체의 동의, 법률의 특별한 규정 등 개인정보보호법 제17조 및 제18조에 해당하는 경우에만 개인정보를 제3자에게 제공합니다.</p>
			<p>회사는 다음과 같은 경우에 개인정보를 제3자에게 제공할 수 있습니다:</p>
			<ul>
				<li>정보주체로부터 별도의 동의를 받은 경우</li>
				<li>법령에 근거하여 수사 목적으로 법령에 정해진 절차와 방법에 따라 수사기관의 요구가 있는 경우</li>
				<li>정보주체 또는 그 법정대리인이 의사표시를 할 수 없는 상태에 있거나 주소불명 등으로 사전 동의를 받을 수 없는 경우로서 명백히 정보주체 또는 제3자의 급박한 생명, 신체, 재산의 이익을 위하여 필요하다고 인정되는 경우</li>
			</ul>

			<h2>4. 개인정보처리의 위탁</h2>
			<p>회사는 원활한 개인정보 업무처리를 위하여 다음과 같이 개인정보 처리업무를 위탁하고 있습니다.</p>
			<ul>
				<li><strong>Google Cloud Platform:</strong> AI 모델 서비스(Vertex AI), OCR 서비스(Vision AI), 이메일 서비스</li>
				<li><strong>Supabase:</strong> 데이터베이스, 인증, 파일 저장소</li>
				<li><strong>Vercel:</strong> 웹 호스팅 및 배포</li>
			</ul>
			<p>위탁계약 체결 시 개인정보보호법 제26조에 따라 위탁업무 수행목적 외 개인정보 처리금지, 기술적·관리적 보호조치, 재위탁 제한, 수탁자에 대한 관리·감독, 손해배상 등 책임에 관한 사항을 계약서 등 문서에 명시하고, 수탁자가 개인정보를 안전하게 처리하는지를 감독하고 있습니다.</p>

			<h2>5. 정보주체의 권리·의무 및 행사방법</h2>
			<p>정보주체는 회사에 대해 언제든지 개인정보 열람·정정·삭제·처리정지 요구 등의 권리를 행사할 수 있습니다.</p>
			<ul>
				<li><strong>개인정보 열람요구:</strong> 개인정보보호법 제35조에 따른 개인정보의 열람</li>
				<li><strong>개인정보 정정·삭제요구:</strong> 개인정보보호법 제36조에 따른 개인정보의 정정·삭제</li>
				<li><strong>개인정보 처리정지요구:</strong> 개인정보보호법 제37조에 따른 개인정보의 처리정지</li>
			</ul>
			<p>제1항에 따른 권리 행사는 회사에 대해 서면, 전화, 전자우편, 모사전송(FAX) 등을 통하여 하실 수 있으며 회사는 이에 대해 지체없이 조치하겠습니다.</p>

			<h2>6. 처리하는 개인정보 항목</h2>
			<p>회사는 다음의 개인정보 항목을 처리하고 있습니다.</p>
			<ul>
				<li><strong>필수항목:</strong> 이메일 주소, 이름, 프로필 이미지(Google 계정에서 제공하는 경우)</li>
				<li><strong>자동수집항목:</strong> IP 주소, 쿠키, 서비스 이용 기록, 접속 로그, 기기정보</li>
				<li><strong>서비스 이용 시 생성되는 정보:</strong> 채용정보, 업로드된 문서 내용, 자기소개서 문항 및 답변, 생성된 자기소개서 내용</li>
			</ul>

			<h2>7. 개인정보의 파기</h2>
			<p>회사는 개인정보 보유기간의 경과, 처리목적 달성 등 개인정보가 불필요하게 되었을 때에는 지체없이 해당 개인정보를 파기합니다.</p>
			<ul>
				<li><strong>전자적 파일 형태:</strong> 복구 및 재생이 불가능한 방법으로 영구 삭제</li>
				<li><strong>종이 문서:</strong> 분쇄기로 분쇄하거나 소각</li>
			</ul>

			<h2>8. 개인정보의 안전성 확보 조치</h2>
			<p>회사는 개인정보보호법 제29조에 따라 다음과 같은 안전성 확보 조치를 취하고 있습니다.</p>
			<ul>
				<li><strong>개인정보의 암호화:</strong> 개인정보는 암호화하여 저장·전송</li>
				<li><strong>해킹 등에 대비한 기술적 대책:</strong> 해킹이나 컴퓨터 바이러스 등에 의한 개인정보 유출 및 훼손을 방지하기 위한 보안프로그램 설치 및 주기적인 점검·갱신</li>
				<li><strong>개인정보에 대한 접근 제한:</strong> 개인정보를 처리하는 데이터베이스시스템에 대한 접근권한의 부여, 변경, 말소를 통한 개인정보에 대한 접근통제</li>
				<li><strong>접속기록의 보관 및 위변조 방지:</strong> 개인정보처리시스템에 접속한 기록을 최소 6개월 이상 보관, 관리</li>
				<li><strong>개인정보의 안전한 전송:</strong> 개인정보를 안전하게 전송할 수 있는 보안장치 설치</li>
			</ul>

			<h2>9. 개인정보 자동 수집 장치의 설치·운영 및 거부에 관한 사항</h2>
			<p>회사는 이용자에게 개별적인 맞춤서비스를 제공하기 위해 이용정보를 저장하고 수시로 불러오는 '쿠키(cookie)'를 사용합니다.</p>
			<ul>
				<li><strong>쿠키의 사용 목적:</strong> 이용자의 접속 빈도나 방문 시간 등을 분석, 이용자의 취향과 관심분야를 파악 및 자취 추적, 각종 이벤트 참여 정도 및 방문 회수 파악 등을 통한 타겟 마케팅 및 개인 맞춤 서비스 제공</li>
				<li><strong>쿠키 설정 거부 방법:</strong> 이용자는 쿠키 설치에 대한 선택권을 가지고 있습니다. 따라서, 이용자는 웹브라우저에서 옵션을 설정함으로써 모든 쿠키를 허용하거나, 쿠키가 저장될 때마다 확인을 거치거나, 아니면 모든 쿠키의 저장을 거부할 수도 있습니다.</li>
			</ul>

			<h2>10. 개인정보 보호책임자</h2>
			<p>회사는 개인정보 처리에 관한 업무를 총괄해서 책임지고, 개인정보 처리와 관련한 정보주체의 불만처리 및 피해구제 등을 위하여 아래와 같이 개인정보 보호책임자를 지정하고 있습니다.</p>
			<ul>
				<li><strong>개인정보 보호책임자:</strong> 이승훈</li>
				<li><strong>연락처:</strong> sseojum@gmail.com</li>
			</ul>
			<p>정보주체께서는 회사의 서비스를 이용하시면서 발생한 모든 개인정보 보호 관련 문의, 불만처리, 피해구제 등에 관한 사항을 개인정보 보호책임자 및 담당부서로 문의하실 수 있습니다. 회사는 정보주체의 문의에 대해 지체없이 답변 및 처리해드릴 것입니다.</p>

			<h2>11. 개인정보 처리방침 변경</h2>
			<p>이 개인정보처리방침은 시행일로부터 적용되며, 법령 및 방침에 따른 변경내용의 추가, 삭제 및 정정이 있는 경우에는 변경사항의 시행 7일 전부터 공지사항을 통하여 고지할 것입니다.</p>

			<h2>12. 개인정보의 안전한 전송</h2>
			<p>회사는 개인정보를 안전하게 전송하기 위해 다음과 같은 보안 조치를 취하고 있습니다:</p>
			<ul>
				<li><strong>HTTPS 프로토콜:</strong> 모든 데이터 전송 시 SSL/TLS 암호화 적용</li>
				<li><strong>API 보안:</strong> 인증된 사용자만 접근 가능한 API 엔드포인트 제공</li>
				<li><strong>데이터베이스 보안:</strong> Supabase RLS(Row Level Security) 정책을 통한 사용자별 데이터 접근 제한</li>
			</ul>

			<h2>13. 연락처</h2>
			<p>개인정보 처리방침에 관한 문의사항이 있으시면 아래로 연락해 주시기 바랍니다.</p>
			<ul>
				<li><strong>이메일:</strong> sseojum@gmail.com</li>
			</ul>
		</div>
	);
};

export default PrivacyPage;



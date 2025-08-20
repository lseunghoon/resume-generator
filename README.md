# sseojum (써줌)

AI 기반 자기소개서 생성 서비스

## 프로젝트 개요

sseojum(써줌)은 AI 기술을 활용하여 사용자의 이력서와 채용정보를 바탕으로 맞춤형 자기소개서를 생성하는 웹 애플리케이션입니다.

## 기술 스택

### Backend
- **Framework**: Flask 3.0.2
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Google OAuth + Supabase Auth
- **AI**: Google Cloud Vertex AI (Gemini 2.0 Flash)
- **OCR**: Google Cloud Vision AI
- **Migration**: Supabase SQL

### Frontend
- **Framework**: React 18
- **Routing**: React Router v6
- **Authentication**: Supabase Auth + Google OAuth
- **Route Guards**: 인증 상태 기반 페이지 접근 제어
- **Styling**: CSS3
- **Build Tool**: Create React App

### External Services
- **Supabase**: Database + Authentication + Real-time
- **Google Cloud**: Vertex AI + Vision AI
- **Google OAuth**: Social Login

## 프로젝트 구조

```
sseojum/
├── backend/                 # 백엔드 API 서버
│   ├── app.py              # 메인 Flask 애플리케이션
│   ├── supabase_client.py  # Supabase 클라이언트
│   ├── supabase_models.py  # Supabase 모델
│   ├── auth_service.py     # Google OAuth 인증 서비스
│   ├── config/             # 설정 파일
│   ├── services/           # 비즈니스 로직
│   ├── utils/              # 유틸리티 함수
│   └── requirements.txt    # Python 의존성
├── frontend/               # 프론트엔드 React 앱
│   ├── src/
│   │   ├── App.js          # 메인 앱 (라우트 가드, 전용 로그인)
│   │   ├── pages/          # 페이지 컴포넌트
│   │   │   ├── LandingPage.jsx      # 랜딩 페이지
│   │   │   ├── JobInfoInputPage.jsx # 채용정보 입력 (라우트 가드)
│   │   │   ├── FileUploadPage.jsx   # 파일 업로드 (라우트 가드)
│   │   │   ├── QuestionPage.jsx     # 질문 관리 (라우트 가드)
│   │   │   ├── ResultPage.jsx       # 결과 확인 (라우트 가드)
│   │   │   └── PrivacyPage.jsx      # 개인정보처리방침
│   │   ├── components/     # 재사용 컴포넌트
│   │   │   ├── Header.jsx           # 통합 헤더 (사이드바 토글)
│   │   │   ├── Sidebar.jsx          # 자기소개서 목록
│   │   │   ├── Login.jsx            # 전용 로그인 페이지
│   │   │   ├── OAuthCallback.jsx    # OAuth 콜백 처리
│   │   │   ├── LoginButton.jsx      # 로그인 버튼
│   │   │   └── DevTools.jsx         # 개발자 도구
│   │   ├── services/       # API 통신
│   │   ├── hooks/          # React Hooks
│   │   └── utils/          # 유틸리티 함수
│   └── package.json        # Node.js 의존성
└── README.md               # 프로젝트 문서
```

## 사용자 플로우

### 1. 인증 및 보안
- **라우트 가드**: 인증되지 않은 사용자는 보호된 페이지 접근 불가
- **Google OAuth 로그인**: 전용 로그인 페이지에서 간편 로그인
- **스마트 리다이렉트**: 로그인 후 원하는 페이지로 자동 이동
- **자동 세션 관리**: 로그인 상태 유지 및 세션 만료 처리

### 2. 채용정보 입력
- 회사명, 직무, 주요업무, 자격요건, 우대사항 입력
- 실시간 유효성 검사
- 필수 필드 검증

### 3. 이력서 업로드
- PDF, DOCX 파일 업로드
- OCR을 통한 텍스트 추출
- 파일 크기 및 형식 검증

### 4. 자기소개서 생성
- AI 기반 맞춤형 자기소개서 생성
- 질문별 개별 답변 생성
- 실시간 생성 상태 표시

### 5. 결과 확인 및 수정
- 생성된 자기소개서 확인
- 수정 요청 및 버전 관리
- 최근 세션 자동 선택 
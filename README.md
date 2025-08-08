# sseojum (써줌)

AI 기반 자기소개서 생성 서비스

## 프로젝트 개요

sseojum(써줌)은 AI 기술을 활용하여 사용자의 이력서와 채용정보를 바탕으로 맞춤형 자기소개서를 생성하는 웹 애플리케이션입니다. Google OAuth를 통한 안전한 인증과 Supabase를 통한 클라우드 기반 데이터베이스를 제공합니다.

## 주요 변경사항 (v2.1)

### 🚀 새로운 기능
- **Google OAuth 인증**: Google 계정을 통한 간편하고 안전한 로그인
- **Supabase 마이그레이션**: SQLite에서 Supabase PostgreSQL로 전환
- **통합 헤더 시스템**: 로고, 사용자 프로필, 네비게이션 통합
- **모달 기반 로그인**: 페이지 전환 없이 로그인 처리
- **Row Level Security**: 사용자별 데이터 보호

### 🔄 변경된 아키텍처
- **데이터베이스**: SQLite → Supabase (PostgreSQL)
- **인증 시스템**: 이메일/비밀번호 → Google OAuth
- **UI/UX**: 개별 헤더 → 통합 헤더 + 로그인 모달
- **보안**: RLS 정책 적용으로 데이터 보안 강화

### 🛡️ 보안 강화
- **JWT 토큰**: Supabase에서 발급하는 암호화된 토큰
- **RLS 정책**: 사용자별 데이터 접근 제어
- **환경 변수**: 민감한 정보 안전한 관리
- **CORS 설정**: 허용된 도메인만 접근

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
│   │   ├── App.js          # 메인 앱 (통합 헤더, 로그인 모달)
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── components/     # 재사용 컴포넌트
│   │   │   ├── Header.jsx  # 통합 헤더
│   │   │   ├── LoginModal.jsx # 로그인 모달
│   │   │   └── OAuthCallback.jsx # OAuth 콜백 처리
│   │   ├── services/       # API 통신
│   │   └── hooks/          # React Hooks
│   └── package.json        # Node.js 의존성
└── README.md               # 프로젝트 문서
```

## 빠른 시작

### 1. 저장소 클론

```bash
git clone <repository-url>
cd sseojum
```

### 2. Supabase 설정

1. **Supabase 프로젝트 생성**:
   - [supabase.com](https://supabase.com)에서 새 프로젝트 생성
   - 프로젝트 URL과 API 키 확인

2. **데이터베이스 스키마 설정**:
   ```sql
   -- supabase_migration.sql 파일을 Supabase 대시보드의 SQL Editor에서 실행하세요
   -- 또는 다음 명령으로 실행:
   -- supabase db push
   ```

3. **Google OAuth 설정**:
   - Supabase Dashboard → Authentication → Providers
   - Google Provider 활성화 및 설정

### 3. 백엔드 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
.\venv\Scripts\Activate.ps1  # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 다음 설정을 추가하세요:
```

#### 환경 변수 설정 (.env)
```env
# Supabase 설정
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# GCP 설정
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1

# CORS 설정
CORS_ORIGINS=http://localhost:3000

# 파일 업로드 설정
MAX_FILE_SIZE=52428800  # 50MB

# 로깅 설정
LOG_LEVEL=INFO
```

### 4. 프론트엔드 설정

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
echo "REACT_APP_API_URL=http://localhost:5000" > .env

# 개발 서버 실행
npm start
```

### 5. 브라우저에서 확인

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:5000

## 사용자 플로우

### 1. 로그인
- Google 계정으로 간편 로그인
- 자동 세션 관리 및 상태 유지

### 2. 채용정보 입력
- 회사명, 직무, 주요업무, 자격요건, 우대사항 입력
- 실시간 유효성 검사

### 3. 이력서 업로드
- PDF, DOCX 파일 업로드
- OCR을 통한 텍스트 추출

### 4. 자기소개서 생성
- AI 기반 맞춤형 자기소개서 생성
- 질문별 개별 답변 생성

### 5. 결과 확인 및 수정
- 생성된 자기소개서 확인
- 수정 요청 및 버전 관리

## API 문서

### 인증 엔드포인트

- `POST /api/v1/auth/google/url` - Google OAuth URL 생성
- `POST /api/v1/auth/google/callback` - OAuth 콜백 처리
- `POST /api/v1/auth/signout` - 로그아웃
- `GET /api/v1/auth/user` - 사용자 정보 조회

### 주요 엔드포인트

- `POST /api/v1/job-info` - 채용정보 입력
- `POST /api/v1/upload` - 파일 업로드
- `POST /api/v1/generate` - 자기소개서 생성
- `POST /api/v1/revise` - 자기소개서 수정
- `GET /api/v1/user/sessions` - 사용자 세션 목록

자세한 API 문서는 [backend/README.md](backend/README.md)를 참조하세요.

## 보안 기능

### 인증 보안
- **Google OAuth**: 안전한 소셜 로그인
- **JWT 토큰**: 암호화된 토큰 기반 인증
- **세션 관리**: 자동 세션 만료 및 갱신

### 데이터 보안
- **Row Level Security (RLS)**: 사용자별 데이터 접근 제어
- **API 인증**: 모든 민감한 API에 인증 필수
- **CORS 설정**: 허용된 도메인만 접근
- **환경 변수**: 민감한 정보 환경 변수로 관리

## 개발 가이드

### 백엔드 개발
- [Backend README](backend/README.md)
- Flask 기반 REST API
- Supabase 클라이언트 연동
- Google OAuth 인증 처리

### 프론트엔드 개발
- [Frontend README](frontend/README.md)
- React 함수형 컴포넌트
- Supabase Auth 연동
- 모달 기반 UI/UX

## 배포

### Supabase 배포

```bash
# Supabase CLI 설치
npm install -g supabase

# 프로젝트 연결
supabase link --project-ref your-project-ref

# 마이그레이션 배포 (supabase_migration.sql 사용)
supabase db push
# 또는 Supabase 대시보드의 SQL Editor에서 supabase_migration.sql 실행
```

### GCP 배포

```bash
# Cloud Run 배포
gcloud run deploy sseojum-backend --source backend
gcloud run deploy sseojum-frontend --source frontend
```

### 환경 변수 설정 (배포 시)

```bash
# Supabase 설정
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# GCP 설정
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
```

## 문제 해결

### 일반적인 문제

1. **환경 변수 오류**:
   ```bash
   # .env 파일이 제대로 로드되는지 확인
   python -c "import os; print(os.getenv('SUPABASE_SERVICE_ROLE_KEY'))"
   ```

2. **CORS 오류**:
   - 백엔드 서버가 실행 중인지 확인
   - CORS_ORIGINS 설정 확인

3. **인증 오류**:
   - Supabase 프로젝트 설정 확인
   - Google OAuth 설정 확인

### 디버깅

```bash
# 백엔드 로그 확인
cd backend
python app.py

# 프론트엔드 개발자 도구
# 브라우저 F12 → Console 탭
```

## 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 라이선스

MIT License

## 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요. 
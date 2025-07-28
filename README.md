# iLoveResume

AI 기반 자기소개서 생성 서비스

## 프로젝트 개요

iLoveResume은 AI 기술을 활용하여 사용자의 이력서와 채용정보를 바탕으로 맞춤형 자기소개서를 생성하는 웹 애플리케이션입니다.

## 주요 변경사항 (v2.0)

### 🚀 새로운 기능
- **직접 입력 방식**: 채용정보를 직접 입력하여 더 정확한 자기소개서 생성
- **OCR 최적화**: 파일 업로드 시 비용 효율적인 텍스트 추출
- **향상된 데이터 구조**: 회사명, 직무, 주요업무 등 구조화된 데이터 저장

### 🔄 변경된 아키텍처
- **크롤링 제거**: 웹 크롤링 기능 완전 제거
- **사용자 직접 입력**: 채용정보를 사용자가 직접 입력하는 방식으로 전환
- **OCR 유지**: 파일 업로드 시 텍스트 추출 기능 유지

## 기술 스택

### Backend
- **Framework**: Flask 3.0.2
- **Database**: SQLite (개발) / PostgreSQL (운영)
- **ORM**: SQLAlchemy 2.0+
- **AI**: Google Cloud Vertex AI (Gemini 2.0 Flash)
- **OCR**: Google Cloud Vision AI
- **Migration**: Alembic

### Frontend
- **Framework**: React 18
- **Routing**: React Router v6
- **Styling**: CSS3
- **Build Tool**: Create React App

## 프로젝트 구조

```
iloveresume/
├── backend/                 # 백엔드 API 서버
│   ├── app.py              # 메인 Flask 애플리케이션
│   ├── models.py           # SQLAlchemy 모델
│   ├── config/             # 설정 파일
│   ├── services/           # 비즈니스 로직
│   ├── utils/              # 유틸리티 함수
│   ├── migrations/         # 데이터베이스 마이그레이션
│   └── requirements.txt    # Python 의존성
├── frontend/               # 프론트엔드 React 앱
│   ├── src/
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── components/     # 재사용 컴포넌트
│   │   ├── services/       # API 통신
│   │   └── hooks/          # React Hooks
│   └── package.json        # Node.js 의존성
└── README.md               # 프로젝트 문서
```

## 빠른 시작

### 1. 저장소 클론

```bash
git clone <repository-url>
cd iloveresume
```

### 2. 백엔드 설정

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
# .env 파일을 편집하여 GCP 설정을 추가하세요

# 데이터베이스 초기화
alembic upgrade head

# 서버 실행
python app.py
```

### 3. 프론트엔드 설정

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
echo "REACT_APP_API_URL=http://localhost:5000" > .env

# 개발 서버 실행
npm start
```

### 4. 브라우저에서 확인

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:5000

## 환경 변수 설정

### Backend (.env)

```env
# GCP 설정
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1

# 데이터베이스 설정
DATABASE_URL=sqlite:///resume_ai.db

# CORS 설정
CORS_ORIGINS=http://localhost:3000

# 파일 업로드 설정
MAX_FILE_SIZE=10485760  # 10MB

# 로깅 설정
LOG_LEVEL=INFO
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:5000
```

## 사용자 플로우

### 1. 채용정보 입력
- 회사명, 직무, 주요업무, 자격요건, 우대사항 입력
- 실시간 유효성 검사

### 2. 이력서 업로드
- PDF, DOCX 파일 업로드
- OCR을 통한 텍스트 추출

### 3. 자기소개서 생성
- AI 기반 맞춤형 자기소개서 생성
- 질문별 개별 답변 생성

### 4. 결과 확인 및 수정
- 생성된 자기소개서 확인
- 수정 요청 및 버전 관리

## API 문서

### 주요 엔드포인트

- `POST /api/v1/job-info` - 채용정보 입력
- `POST /api/v1/upload` - 파일 업로드
- `POST /api/v1/generate` - 자기소개서 생성
- `POST /api/v1/revise` - 자기소개서 수정

자세한 API 문서는 [backend/README.md](backend/README.md)를 참조하세요.

## 개발 가이드

### 백엔드 개발
- [Backend README](backend/README.md)
- Flask 기반 REST API
- SQLAlchemy ORM
- Alembic 마이그레이션

### 프론트엔드 개발
- [Frontend README](frontend/README.md)
- React 함수형 컴포넌트
- React Router v6
- CSS3 스타일링

## 배포

### Docker 배포

```bash
# Backend
cd backend
docker build -t iloveresume-backend .
docker run -p 5000:5000 iloveresume-backend

# Frontend
cd frontend
docker build -t iloveresume-frontend .
docker run -p 3000:3000 iloveresume-frontend
```

### GCP 배포

```bash
# Cloud Run 배포
gcloud run deploy iloveresume-backend --source backend
gcloud run deploy iloveresume-frontend --source frontend
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
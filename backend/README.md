# sseojum Backend

AI 기반 자기소개서 생성 서비스의 백엔드 API 서버입니다.

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
- **Database**: Supabase (PostgreSQL)
- **ORM**: Supabase 클라이언트 (SQLAlchemy 제거)
- **AI**: Google Cloud Vertex AI (Gemini 2.0 Flash)
- **OCR**: Google Cloud Vision AI
- **Migration**: Supabase SQL (Alembic 제거)

### Frontend
- **Framework**: React 18
- **Routing**: React Router v6
- **Styling**: CSS3

## 설치 및 실행

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
.\venv\Scripts\Activate.ps1  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# GCP 설정
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1

# Supabase 설정
SUPABASE_URL=your-supabase-project-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# CORS 설정
CORS_ORIGINS=http://localhost:3000

# 파일 업로드 설정
MAX_FILE_SIZE=10485760  # 10MB

# 로깅 설정
LOG_LEVEL=INFO
```

### 3. 데이터베이스 초기화

```bash
# Supabase 대시보드의 SQL Editor에서 supabase_migration.sql 실행
# 또는 Supabase CLI 사용
```

### 4. 서버 실행

```bash
# 개발 모드
python app.py

# 또는
flask run --debug
```

## API 엔드포인트

### 채용정보 입력
- `POST /api/v1/job-info` - 채용정보 직접 입력

### 파일 업로드
- `POST /api/v1/upload` - 이력서 파일 업로드 및 세션 생성

### 자기소개서 생성
- `POST /api/v1/generate` - 자기소개서 생성
- `POST /api/v1/revise` - 자기소개서 수정

### 세션 관리
- `GET /api/v1/session/<id>` - 세션 조회
- `DELETE /api/v1/session/<id>` - 세션 삭제

## 데이터베이스 스키마

### 데이터베이스 스키마

데이터베이스 스키마는 `supabase_migration.sql` 파일에 정의되어 있습니다. 
Supabase 대시보드의 SQL Editor에서 이 파일을 실행하거나 Supabase CLI를 사용하여 배포할 수 있습니다.

주요 테이블:
- **sessions**: 사용자 세션 및 채용정보 저장
- **questions**: 자기소개서 질문 및 답변 저장

모든 테이블에는 Row Level Security (RLS) 정책이 적용되어 사용자별 데이터 보호가 이루어집니다.

## 파일 처리

### 지원 형식
- **PDF**: 이력서, 자기소개서 PDF 파일
- **DOCX**: Microsoft Word 문서

### OCR 기능
- Google Cloud Vision AI를 사용한 텍스트 추출
- 이미지 전처리 및 최적화
- 비용 효율적인 처리

## 개발 가이드

### 코드 구조
```
backend/
├── app.py                 # 메인 Flask 애플리케이션
├── supabase_models.py     # Supabase 모델 (SQLAlchemy 모델 제거)
├── config/                # 설정 파일
├── services/              # 비즈니스 로직
│   ├── ai_service.py      # AI 서비스
│   ├── file_service.py    # 파일 처리 서비스
│   └── ocr_service.py     # OCR 서비스
├── utils/                 # 유틸리티 함수
└── supabase_migration.sql # Supabase 마이그레이션 스크립트
```

### 환경별 설정
- **개발**: Supabase 데이터베이스, 디버그 모드
- **운영**: PostgreSQL 데이터베이스, 프로덕션 설정

## 배포

### Docker 배포
```bash
# Docker 이미지 빌드
docker build -t sseojum-backend .

# 컨테이너 실행
docker run -p 5000:5000 sseojum-backend
```

### GCP 배포
```bash
# Cloud Run 배포
gcloud run deploy sseojum-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 라이선스

MIT License

## 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 
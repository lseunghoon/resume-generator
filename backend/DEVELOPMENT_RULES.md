# iloveresume 개발 규칙

## 프로젝트 개요
- **목적**: AI 기반 자기소개서 생성 서비스
- **기술 스택**: Flask (백엔드), React (프론트엔드), Supabase (데이터베이스 + 인증), Google Vertex AI Gemini 2.0 Flash
- **데이터베이스**: Supabase (PostgreSQL) + Row Level Security (RLS)

## 핵심 원칙

### 비용 최적화
1. **AI 모델 호출 최소화**: 1회 사용당 1회의 모델 호출만 허용 (배치 처리)
2. **OCR 최적화**: 텍스트가 충분한 경우 OCR 건너뛰기
3. **단일 이미지 OCR**: OCR 실행 시 가장 관련성 높은 단 하나의 이미지만 선별하여 처리

### 보안 및 인증
1. **Google OAuth**: 안전한 소셜 로그인 시스템
2. **JWT 토큰**: Supabase에서 발급하는 암호화된 토큰 사용
3. **Row Level Security (RLS)**: 사용자별 데이터 접근 제어
4. **환경 변수**: 민감한 정보는 환경 변수로 관리

### 데이터베이스 관리
1. **Supabase 마이그레이션**: SQL 기반 스키마 관리
2. **RLS 정책**: 모든 테이블에 RLS 정책 적용
3. **인덱스 최적화**: 성능을 위한 적절한 인덱스 설정
4. **데이터 무결성**: 외래 키 제약 조건 및 체크 제약 조건

## 새로운 아키텍처 (v2.1)

### 기존 시스템 폐지
- SQLite 데이터베이스 완전 제거
- 이메일/비밀번호 인증 시스템 제거
- 개별 페이지 헤더 시스템 제거
- 웹 크롤링 관련 모든 기능 제거

### 새로운 시스템 도입
1. **Supabase 데이터베이스**: PostgreSQL 기반 클라우드 데이터베이스
2. **Google OAuth 인증**: 안전한 소셜 로그인
3. **통합 헤더 시스템**: 로고, 사용자 프로필, 네비게이션 통합
4. **모달 기반 로그인**: 페이지 전환 없이 로그인 처리
5. **사용자별 데이터 분리**: RLS 정책으로 데이터 보호

### 주요 변경사항
- **데이터베이스**: SQLite → Supabase (PostgreSQL)
- **인증**: 이메일/비밀번호 → Google OAuth
- **UI/UX**: 개별 헤더 → 통합 헤더 + 로그인 모달
- **보안**: RLS 정책 적용으로 데이터 보안 강화
- **환경 변수**: SERVICE_ROLE_KEY 사용으로 백엔드 권한 확보

### 장점
- **확장성**: 클라우드 기반 데이터베이스로 무제한 확장
- **보안성**: Google OAuth + RLS로 강력한 보안
- **사용자 경험**: 통합된 UI/UX로 일관된 경험
- **유지보수성**: 모듈화된 구조로 쉬운 유지보수
- **비용 효율성**: Supabase 무료 티어 활용

## Error Handling
- **APIError**: 사용자 정의 API 오류 클래스
- **ValidationError**: 데이터 검증 오류
- **FileProcessingError**: 파일 처리 오류
- **AuthenticationError**: 인증 관련 오류

## API Design
- **RESTful 구조**: 표준 HTTP 메서드 사용
- **일관된 응답 형식**: JSON 기반 통일된 응답 구조
- **상태 코드 활용**: 적절한 HTTP 상태 코드 반환
- **에러 메시지**: 사용자 친화적인 오류 메시지
- **인증 필수**: 모든 민감한 API에 JWT 토큰 인증

## Environment Variables
- **SUPABASE_URL**: Supabase 프로젝트 URL
- **SUPABASE_ANON_KEY**: Supabase 익명 키 (프론트엔드용)
- **SUPABASE_SERVICE_ROLE_KEY**: Supabase 서비스 롤 키 (백엔드용)
- **PROJECT_ID**: GCP 프로젝트 ID
- **LOCATION**: Vertex AI 리전 (us-central1)
- **CORS_ORIGINS**: 허용된 프론트엔드 도메인
- **LOG_LEVEL**: 로깅 레벨 설정

## Code Quality
- **모듈화**: 기능별 서비스 분리 (AIService, OCRService, FileService, AuthService, SupabaseService)
- **설정 분리**: config 모듈로 환경 변수 관리
- **유틸리티 분리**: utils 모듈로 공통 기능 관리
- **로깅**: 구조화된 로깅 시스템
- **타입 힌트**: Python 타입 힌트 활용
- **예외 처리**: 적절한 예외 처리 및 오류 전파

## 개발 시 주의사항

### 인증 시스템
- **Google OAuth**: 프론트엔드에서 Supabase Auth 사용
- **JWT 토큰**: 백엔드에서 SERVICE_ROLE_KEY 사용
- **세션 관리**: 자동 토큰 갱신 및 세션 만료 처리
- **사용자 정보**: Google 프로필 정보 활용

### 데이터베이스 관리
- **RLS 정책**: 모든 테이블에 사용자별 접근 제어
- **마이그레이션**: Supabase SQL 기반 스키마 관리
- **트랜잭션**: 데이터 일관성을 위한 트랜잭션 처리
- **연결 관리**: Supabase 클라이언트 연결 관리

### AI 모델 사용
- **배치 처리**: 여러 질문을 한 번에 처리하여 모델 호출 최소화
- **응답 파싱**: AI 응답의 구조화된 파싱 필수
- **오류 처리**: 모델 호출 실패 시 적절한 fallback
- **비용 관리**: Gemini 2.0 Flash 모델 사용으로 비용 최적화

### 파일 처리
- **보안**: 업로드 파일 타입 및 크기 검증
- **성능**: 대용량 파일 처리 시 메모리 효율성 고려
- **정리**: 임시 파일 자동 삭제
- **OCR 최적화**: 필요시에만 OCR 실행

### UI/UX 개발
- **통합 헤더**: 모든 페이지에서 일관된 헤더 사용
- **로그인 모달**: 페이지 전환 없이 로그인 처리
- **반응형 디자인**: 모바일 및 데스크톱 최적화
- **로딩 상태**: 사용자 친화적인 로딩 인디케이터

## 데이터베이스 스키마

### Sessions 테이블
```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  user_id UUID REFERENCES auth.users(id),
  company_name TEXT,
  job_title TEXT,
  main_responsibilities TEXT,
  requirements TEXT,
  preferred_qualifications TEXT,
  jd_text TEXT,
  resume_text TEXT,
  company_info JSONB
);
```

### Questions 테이블
```sql
CREATE TABLE questions (
  id SERIAL PRIMARY KEY,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  question_number INTEGER,
  question TEXT,
  answer_history JSONB,
  current_version_index INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### RLS 정책
```sql
-- Sessions 테이블 RLS 정책
CREATE POLICY "Users can view own sessions" ON sessions
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions" ON sessions
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON sessions
FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions" ON sessions
FOR DELETE USING (auth.uid() = user_id);

-- Questions 테이블 RLS 정책
CREATE POLICY "Users can view own questions" ON questions
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM sessions 
    WHERE sessions.id = questions.session_id 
    AND sessions.user_id = auth.uid()
  )
);

CREATE POLICY "Users can insert own questions" ON questions
FOR INSERT WITH CHECK (
  EXISTS (
    SELECT 1 FROM sessions 
    WHERE sessions.id = questions.session_id 
    AND sessions.user_id = auth.uid()
  )
);

CREATE POLICY "Users can update own questions" ON questions
FOR UPDATE USING (
  EXISTS (
    SELECT 1 FROM sessions 
    WHERE sessions.id = questions.session_id 
    AND sessions.user_id = auth.uid()
  )
);

CREATE POLICY "Users can delete own questions" ON questions
FOR DELETE USING (
  EXISTS (
    SELECT 1 FROM sessions 
    WHERE sessions.id = questions.session_id 
    AND sessions.user_id = auth.uid()
  )
);
```

## 테스트 및 검증
- **Mock API**: 개발 환경에서의 API 모킹
- **단위 테스트**: 각 서비스별 독립적 테스트
- **통합 테스트**: 전체 워크플로우 테스트
- **성능 테스트**: 대용량 데이터 처리 성능 검증
- **보안 테스트**: RLS 정책 및 인증 시스템 검증

## 배포 및 운영
- **개발 환경**: 로컬 개발 + Supabase
- **테스트 환경**: GCP Cloud Run + Supabase
- **운영 환경**: GCP Cloud Run + Supabase
- **모니터링**: Supabase 대시보드 + GCP 모니터링
- **백업**: Supabase 자동 백업 활용 
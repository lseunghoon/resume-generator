-- iloveresume Supabase 마이그레이션 스크립트
-- Supabase 대시보드의 SQL Editor에서 실행하세요

-- 세션 테이블 생성
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 채용정보 필드
    company_name VARCHAR(255),
    job_title VARCHAR(255),
    main_responsibilities TEXT,
    requirements TEXT,
    preferred_qualifications TEXT,
    
    -- 기타 필드
    resume_text TEXT,
    company_info TEXT
);

-- 질문 테이블 생성
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    question_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer_history TEXT, -- JSON 형태의 문자열로 답변 리스트 저장
    current_version_index INTEGER DEFAULT 0 NOT NULL,
    
    -- 세션 내 질문 번호는 유니크해야 함
    UNIQUE(session_id, question_number)
);

-- 인덱스 생성
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);
CREATE INDEX idx_questions_session_id ON questions(session_id);
CREATE INDEX idx_questions_session_question_number ON questions(session_id, question_number);

-- RLS (Row Level Security) 활성화
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;

-- RLS 정책 생성
-- 사용자는 자신의 세션만 접근 가능
CREATE POLICY "Users can view own sessions" ON sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions" ON sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions" ON sessions
    FOR DELETE USING (auth.uid() = user_id);

-- 사용자는 자신의 세션에 속한 질문만 접근 가능
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
"""
질문 번호 필드 추가 마이그레이션
기존 질문들에 대해 세션별로 순차적인 번호를 부여합니다.
"""

import sqlite3
import os
from pathlib import Path

def migrate():
    """마이그레이션 실행"""
    # 데이터베이스 파일 경로
    db_path = Path(__file__).parent.parent / "resume_ai.db"
    
    if not db_path.exists():
        print("데이터베이스 파일을 찾을 수 없습니다.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. question_number 컬럼 추가
        print("question_number 컬럼을 추가합니다...")
        cursor.execute("ALTER TABLE questions ADD COLUMN question_number INTEGER")
        
        # 2. 기존 질문들에 대해 세션별로 순차적인 번호 부여
        print("기존 질문들에 번호를 부여합니다...")
        
        # 세션별로 질문들을 가져와서 번호 부여
        cursor.execute("""
            SELECT DISTINCT session_id FROM questions 
            ORDER BY session_id
        """)
        session_ids = [row[0] for row in cursor.fetchall()]
        
        for session_id in session_ids:
            # 해당 세션의 질문들을 생성 순서대로 가져오기
            cursor.execute("""
                SELECT id FROM questions 
                WHERE session_id = ? 
                ORDER BY id
            """, (session_id,))
            
            question_ids = [row[0] for row in cursor.fetchall()]
            
            # 순차적으로 번호 부여
            for index, question_id in enumerate(question_ids, 1):
                cursor.execute("""
                    UPDATE questions 
                    SET question_number = ? 
                    WHERE id = ?
                """, (index, question_id))
                
                print(f"세션 {session_id}: 질문 {question_id}에 번호 {index} 부여")
        
        # 3. question_number를 NOT NULL로 설정
        print("question_number를 NOT NULL로 설정합니다...")
        
        # SQLite에서는 ALTER COLUMN NOT NULL을 직접 지원하지 않으므로
        # 새로운 테이블을 만들어 데이터를 복사하는 방식 사용
        
        # 임시 테이블 생성
        cursor.execute("""
            CREATE TABLE questions_new (
                id INTEGER PRIMARY KEY,
                question VARCHAR NOT NULL,
                length INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                answer_history TEXT,
                current_version_index INTEGER NOT NULL DEFAULT 0,
                session_id VARCHAR(36) NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        
        # 데이터 복사
        cursor.execute("""
            INSERT INTO questions_new 
            SELECT id, question, length, question_number, answer_history, 
                   current_version_index, session_id 
            FROM questions
        """)
        
        # 기존 테이블 삭제
        cursor.execute("DROP TABLE questions")
        
        # 새 테이블 이름 변경
        cursor.execute("ALTER TABLE questions_new RENAME TO questions")
        
        # 인덱스 재생성 (필요한 경우)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_session_id ON questions (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_session_question_number ON questions (session_id, question_number)")
        
        conn.commit()
        print("마이그레이션이 성공적으로 완료되었습니다.")
        
    except Exception as e:
        conn.rollback()
        print(f"마이그레이션 중 오류 발생: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate() 
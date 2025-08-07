"""
Supabase 클라이언트 설정
"""

import os
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

# Supabase 설정
SUPABASE_URL = "https://orjplexhlzipkjlngoua.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # 서비스 계정 키 사용

# Supabase 클라이언트 초기화
supabase: Optional[Client] = None

def init_supabase():
    """Supabase 클라이언트 초기화"""
    global supabase
    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY 환경 변수가 설정되지 않았습니다.")
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # 연결 테스트
        supabase.table("sessions").select("id").limit(1).execute()
        print("Supabase 클라이언트 초기화 성공")
        return supabase
    except Exception as e:
        print(f"Supabase 클라이언트 초기화 실패: {str(e)}")
        raise

def get_supabase() -> Client:
    """Supabase 클라이언트 반환"""
    global supabase
    if supabase is None:
        supabase = init_supabase()
    return supabase

class SupabaseService:
    """Supabase 데이터베이스 서비스"""
    
    def __init__(self):
        self.client = get_supabase()
    
    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 세션 생성"""
        try:
            data = {
                "user_id": user_id,
                "company_name": session_data.get("company_name"),
                "job_title": session_data.get("job_title"),
                "main_responsibilities": session_data.get("main_responsibilities"),
                "requirements": session_data.get("requirements"),
                "preferred_qualifications": session_data.get("preferred_qualifications"),
                "resume_text": session_data.get("resume_text"),
                "company_info": session_data.get("company_info")
            }
            
            result = self.client.table("sessions").insert(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            raise Exception(f"세션 생성 실패: {str(e)}")
    
    def get_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """세션 조회"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.client.table("sessions").select("*").eq("id", session_id).eq("user_id", user_id).execute()
                return result.data[0] if result.data else None
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"세션 조회 실패: {str(e)}")
                else:
                    print(f"세션 조회 재시도 {attempt + 1}/{max_retries}: {str(e)}")
                    import time
                    time.sleep(1)  # 1초 대기 후 재시도
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 모든 세션 조회 (질문이 없는 세션은 자동 정리)"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 1. 사용자의 모든 세션 조회
                result = self.client.table("sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                sessions = result.data
                
                # 2. 각 세션에 대해 질문이 있는지 확인하고, 질문이 없는 세션은 삭제
                valid_sessions = []
                for session in sessions:
                    session_id = session['id']
                    
                    # 해당 세션의 질문 수 확인
                    questions_result = self.client.table("questions").select("id").eq("session_id", session_id).execute()
                    question_count = len(questions_result.data)
                    
                    if question_count > 0:
                        # 질문이 있는 세션은 유지
                        valid_sessions.append(session)
                    else:
                        # 질문이 없는 세션은 자동 삭제
                        try:
                            self.client.table("sessions").delete().eq("id", session_id).execute()
                            print(f"자동 정리: 질문이 없는 세션 삭제됨 - {session_id}")
                        except Exception as e:
                            print(f"자동 정리 실패: 세션 삭제 중 오류 - {session_id}, {str(e)}")
                
                return valid_sessions
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"사용자 세션 조회 실패: {str(e)}")
                else:
                    print(f"사용자 세션 조회 재시도 {attempt + 1}/{max_retries}: {str(e)}")
                    import time
                    time.sleep(1)  # 1초 대기 후 재시도
    
    def update_session(self, session_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """세션 업데이트"""
        try:
            result = self.client.table("sessions").update(update_data).eq("id", session_id).eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            raise Exception(f"세션 업데이트 실패: {str(e)}")
    
    def delete_session(self, session_id: str, user_id: str) -> bool:
        """세션 삭제"""
        try:
            result = self.client.table("sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            raise Exception(f"세션 삭제 실패: {str(e)}")
    
    def create_question(self, session_id: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """질문 생성"""
        try:
            data = {
                "session_id": session_id,
                "question_number": question_data.get("question_number"),
                "question": question_data.get("question"),
                "answer_history": json.dumps(question_data.get("answer_history", [])),
                "current_version_index": question_data.get("current_version_index", 0)
            }
            
            result = self.client.table("questions").insert(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            raise Exception(f"질문 생성 실패: {str(e)}")
    
    def get_session_questions(self, session_id: str) -> List[Dict[str, Any]]:
        """세션의 모든 질문 조회"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.client.table("questions").select("*").eq("session_id", session_id).order("question_number").execute()
                
                # answer_history를 파싱하여 반환
                questions = []
                for question in result.data:
                    question_copy = question.copy()
                    try:
                        if question["answer_history"]:
                            # JSON 파싱 시도
                            if isinstance(question["answer_history"], str):
                                question_copy["answer_history"] = json.loads(question["answer_history"])
                            elif isinstance(question["answer_history"], list):
                                question_copy["answer_history"] = question["answer_history"]
                            else:
                                question_copy["answer_history"] = []
                        else:
                            question_copy["answer_history"] = []
                    except (json.JSONDecodeError, TypeError):
                        # 파싱 실패 시 현재 답변을 첫 번째 히스토리로 설정
                        current_answer = question.get("answer", "")
                        question_copy["answer_history"] = [current_answer] if current_answer else []
                    questions.append(question_copy)
                
                return questions
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"세션 질문 조회 실패: {str(e)}")
                else:
                    print(f"세션 질문 조회 재시도 {attempt + 1}/{max_retries}: {str(e)}")
                    import time
                    time.sleep(1)  # 1초 대기 후 재시도
    
    def update_question(self, question_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """질문 업데이트"""
        try:
            # answer_history가 리스트인 경우 JSON으로 변환
            if "answer_history" in update_data and isinstance(update_data["answer_history"], list):
                update_data["answer_history"] = json.dumps(update_data["answer_history"])
            
            result = self.client.table("questions").update(update_data).eq("id", question_id).execute()
            
            if result.data:
                question = result.data[0].copy()
                try:
                    if question["answer_history"]:
                        # JSON 파싱 시도
                        if isinstance(question["answer_history"], str):
                            question["answer_history"] = json.loads(question["answer_history"])
                        elif isinstance(question["answer_history"], list):
                            question["answer_history"] = question["answer_history"]
                        else:
                            question["answer_history"] = []
                    else:
                        question["answer_history"] = []
                except (json.JSONDecodeError, TypeError):
                    # 파싱 실패 시 현재 답변을 첫 번째 히스토리로 설정
                    current_answer = question.get("answer", "")
                    question["answer_history"] = [current_answer] if current_answer else []
                return question
            
            return None
            
        except Exception as e:
            raise Exception(f"질문 업데이트 실패: {str(e)}")
    
    def delete_question(self, question_id: int) -> bool:
        """질문 삭제 (질문이 없는 세션이 되면 세션도 함께 삭제)"""
        try:
            # 1. 삭제할 질문의 session_id 조회
            question_result = self.client.table("questions").select("session_id").eq("id", question_id).execute()
            if not question_result.data:
                return False
            
            session_id = question_result.data[0]['session_id']
            
            # 2. 질문 삭제
            result = self.client.table("questions").delete().eq("id", question_id).execute()
            if not result.data:
                return False
            
            # 3. 해당 세션의 남은 질문 수 확인
            remaining_questions_result = self.client.table("questions").select("id").eq("session_id", session_id).execute()
            remaining_count = len(remaining_questions_result.data)
            
            # 4. 질문이 없으면 세션도 삭제
            if remaining_count == 0:
                try:
                    self.client.table("sessions").delete().eq("id", session_id).execute()
                    print(f"자동 정리: 마지막 질문 삭제로 인한 세션 삭제 - {session_id}")
                except Exception as e:
                    print(f"자동 정리 실패: 세션 삭제 중 오류 - {session_id}, {str(e)}")
            
            return True
            
        except Exception as e:
            raise Exception(f"질문 삭제 실패: {str(e)}")
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 조회"""
        try:
            result = self.client.auth.admin.list_users()
            for user in result.users:
                if user.email == email:
                    return {
                        "id": user.id,
                        "email": user.email,
                        "created_at": user.created_at
                    }
            return None
            
        except Exception as e:
            raise Exception(f"사용자 조회 실패: {str(e)}")
    
    def create_user(self, email: str, password: str) -> Dict[str, Any]:
        """새 사용자 생성"""
        try:
            result = self.client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True
            })
            
            return {
                "id": result.user.id,
                "email": result.user.email,
                "created_at": result.user.created_at
            }
            
        except Exception as e:
            raise Exception(f"사용자 생성 실패: {str(e)}") 
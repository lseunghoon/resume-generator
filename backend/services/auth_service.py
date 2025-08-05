"""
Supabase 인증 서비스
"""

import os
from supabase import create_client, Client
from typing import Optional, Dict, Any

class AuthService:
    """Supabase 인증 서비스"""
    
    def __init__(self):
        self.supabase_url = "https://orjplexhlzipkjlngoua.supabase.co"
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_key:
            raise ValueError("SUPABASE_ANON_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.client = create_client(self.supabase_url, self.supabase_key)
    
    def get_google_auth_url(self) -> str:
        """Google OAuth URL 생성"""
        try:
            # Supabase의 Google OAuth URL 반환
            return f"{self.supabase_url}/auth/v1/authorize?provider=google&redirect_to=http://localhost:3000/auth/callback"
        except Exception as e:
            raise Exception(f"Google OAuth URL 생성 오류: {str(e)}")
    
    def handle_google_callback(self, code: str) -> Dict[str, Any]:
        """Google OAuth 콜백 처리"""
        try:
            # 코드를 사용하여 세션 생성
            response = self.client.auth.exchange_code_for_session(code)
            
            if response.user and response.session:
                return {
                    "success": True,
                    "message": "Google 로그인에 성공했습니다.",
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email
                    },
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Google 로그인에 실패했습니다."
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Google 로그인 오류: {str(e)}"
            }
    
    def sign_out(self, access_token: str) -> Dict[str, Any]:
        """로그아웃"""
        try:
            # 토큰을 사용하여 로그아웃
            self.client.auth.sign_out()
            return {
                "success": True,
                "message": "로그아웃되었습니다."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"로그아웃 오류: {str(e)}"
            }
    
    def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """토큰으로 사용자 정보 조회"""
        try:
            # 토큰을 사용하여 사용자 정보 조회
            response = self.client.auth.get_user(access_token)
            
            if response.user:
                user_data = {
                    "id": response.user.id,
                    "email": response.user.email
                }
                
                # Google OAuth 사용자의 경우 프로필 사진 정보 추가
                if hasattr(response.user, 'user_metadata') and response.user.user_metadata:
                    user_metadata = response.user.user_metadata
                    if 'picture' in user_metadata:
                        user_data["picture"] = user_metadata["picture"]
                    if 'name' in user_metadata:
                        user_data["name"] = user_metadata["name"]
                
                return user_data
            return None
            
        except Exception as e:
            print(f"사용자 정보 조회 오류: {str(e)}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """토큰 갱신"""
        try:
            response = self.client.auth.refresh_session(refresh_token)
            
            if response.session:
                return {
                    "success": True,
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "토큰 갱신에 실패했습니다."
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"토큰 갱신 오류: {str(e)}"
            }
    
    def reset_password(self, email: str) -> Dict[str, Any]:
        """비밀번호 재설정 이메일 발송"""
        try:
            self.client.auth.reset_password_email(email)
            return {
                "success": True,
                "message": "비밀번호 재설정 이메일이 발송되었습니다."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"비밀번호 재설정 오류: {str(e)}"
            } 
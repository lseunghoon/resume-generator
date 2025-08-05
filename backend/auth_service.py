"""
Supabase 인증 서비스
"""

import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from supabase_client import SupabaseService

class AuthService:
    """Supabase 인증 서비스"""
    
    def __init__(self):
        self.supabase_url = "https://orjplexhlzipkjlngoua.supabase.co"
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_key:
            raise ValueError("SUPABASE_ANON_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.client = create_client(self.supabase_url, self.supabase_key)
        self.supabase_service = SupabaseService()
    
    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """회원가입"""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at
                    },
                    "message": "회원가입이 완료되었습니다."
                }
            else:
                return {
                    "success": False,
                    "message": "회원가입에 실패했습니다."
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"회원가입 오류: {str(e)}"
            }
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """로그인"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at
                    },
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at
                    },
                    "message": "로그인이 완료되었습니다."
                }
            else:
                return {
                    "success": False,
                    "message": "로그인에 실패했습니다."
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"로그인 오류: {str(e)}"
            }
    
    def sign_out(self, access_token: str) -> Dict[str, Any]:
        """로그아웃"""
        try:
            self.client.auth.sign_out()
            return {
                "success": True,
                "message": "로그아웃이 완료되었습니다."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"로그아웃 오류: {str(e)}"
            }
    
    def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """토큰으로 사용자 정보 조회"""
        try:
            # 토큰을 설정
            self.client.auth.set_session(access_token, None)
            
            # 현재 사용자 정보 가져오기
            user = self.client.auth.get_user()
            
            if user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "created_at": user.user.created_at
                }
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
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at
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
        """비밀번호 재설정"""
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
    
    def update_password(self, access_token: str, new_password: str) -> Dict[str, Any]:
        """비밀번호 변경"""
        try:
            # 토큰을 설정
            self.client.auth.set_session(access_token, None)
            
            # 비밀번호 업데이트
            response = self.client.auth.update_user({
                "password": new_password
            })
            
            if response.user:
                return {
                    "success": True,
                    "message": "비밀번호가 변경되었습니다."
                }
            else:
                return {
                    "success": False,
                    "message": "비밀번호 변경에 실패했습니다."
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"비밀번호 변경 오류: {str(e)}"
            } 
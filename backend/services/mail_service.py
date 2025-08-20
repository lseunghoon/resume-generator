"""
메일 전송 서비스
Gmail SMTP를 사용하여 피드백 메일을 전송합니다.
"""

import os
import logging
import re
from typing import Dict, Any, Optional
from flask_mail import Mail, Message
from markupsafe import escape
from utils.logger import LoggerMixin

logger = logging.getLogger(__name__)

class MailService(LoggerMixin):
    """
    Gmail SMTP를 사용한 메일 전송 서비스
    """
    
    def __init__(self, app=None):
        """
        MailService 초기화
        
        Args:
            app: Flask 애플리케이션 인스턴스
        """
        self.app = app
        self.mail = None
        self._configure_mail()
    
    def _configure_mail(self):
        """메일 설정 구성"""
        try:
            if self.app:
                # Flask-Mail 설정
                self.app.config['MAIL_SERVER'] = os.getenv('GMAIL_SMTP_SERVER', 'smtp.gmail.com')
                self.app.config['MAIL_PORT'] = int(os.getenv('GMAIL_SMTP_PORT', '587'))
                self.app.config['MAIL_USE_TLS'] = True
                self.app.config['MAIL_USE_SSL'] = False
                self.app.config['MAIL_USERNAME'] = os.getenv('GMAIL_USER', 'sseojum@gmail.com')
                self.app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD', '')
                
                # 메일 객체 생성
                self.mail = Mail(self.app)
                self.logger.info("메일 서비스 설정 완료")
                
            else:
                self.logger.warning("Flask 앱이 설정되지 않아 메일 서비스를 초기화할 수 없습니다.")
                
        except Exception as e:
            self.logger.error(f"메일 서비스 설정 실패: {e}")
            raise
    
    def send_feedback_email(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        피드백 메일 전송
        
        Args:
            feedback_data: 피드백 데이터 (email, message, user_id 등)
            
        Returns:
            전송 결과 딕셔너리
        """
        try:
            if not self.mail:
                raise Exception("메일 서비스가 초기화되지 않았습니다.")
            
            # 필수 필드 검증
            email = feedback_data.get('email')
            message = feedback_data.get('message')
            
            if not email or not message:
                raise ValueError("이메일과 메시지는 필수입니다.")
            
            # 메일 제목 및 내용 구성 (헤더 인젝션 방지)
            safe_email = re.sub(r'[\r\n]', '', email)  # \r, \n 제거
            safe_subject = f"[써줌] 피드백/문의사항 - {safe_email}"
            
            # 사용자 입력 이스케이프 처리 (XSS 방지)
            safe_message = escape(message)
            safe_email_escaped = escape(safe_email)
            safe_created_at = escape(str(feedback_data.get('created_at', 'N/A')))
            
            # HTML 형식의 메일 본문 (안전한 방식)
            html_body = f"""
            <html>
            <body>
                <h2>써줌 서비스 피드백/문의사항</h2>
                <p><strong>보낸 사람:</strong> {safe_email_escaped}</p>
                <p><strong>보낸 시간:</strong> {safe_created_at}</p>
                <hr>
                <h3>메시지 내용:</h3>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap;">
                    {safe_message}
                </div>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    이 메일은 써줌 서비스의 피드백 시스템을 통해 자동으로 전송되었습니다.
                </p>
            </body>
            </html>
            """
            
            # 텍스트 형식의 메일 본문 (HTML을 지원하지 않는 클라이언트용)
            text_body = f"""써줌 서비스 피드백/문의사항

보낸 사람: {safe_email}
보낸 시간: {feedback_data.get('created_at', 'N/A')}

메시지 내용:
{message}

---
이 메일은 써줌 서비스의 피드백 시스템을 통해 자동으로 전송되었습니다."""
            
            # 메일 메시지 생성
            msg = Message(
                subject=safe_subject,
                recipients=[os.getenv('GMAIL_USER', 'sseojum@gmail.com')],
                body=text_body,
                html=html_body,
                sender=os.getenv('GMAIL_USER', 'sseojum@gmail.com')
            )
            
            # 메일 전송
            self.mail.send(msg)
            
            self.logger.info(f"피드백 메일 전송 성공: {email}")
            
            return {
                'success': True,
                'message': '메일이 성공적으로 전송되었습니다.',
                'email': email
            }
            
        except Exception as e:
            error_msg = f"메일 전송 실패: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'success': False,
                'message': error_msg,
                'error': str(e)
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        메일 서비스 연결 테스트
        
        Returns:
            연결 테스트 결과
        """
        try:
            if not self.mail:
                return {
                    'success': False,
                    'message': '메일 서비스가 초기화되지 않았습니다.'
                }
            
            # 간단한 테스트 메일 전송
            test_msg = Message(
                subject='[써줌] 메일 서비스 연결 테스트',
                recipients=[os.getenv('GMAIL_USER', 'sseojum@gmail.com')],
                body='메일 서비스가 정상적으로 작동하고 있습니다.',
                sender=os.getenv('GMAIL_USER', 'sseojum@gmail.com')
            )
            
            self.mail.send(test_msg)
            
            return {
                'success': True,
                'message': '메일 서비스 연결 테스트 성공'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'메일 서비스 연결 테스트 실패: {str(e)}'
            }

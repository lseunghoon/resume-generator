"""
AI 서비스 - Vertex AI 기반 자기소개서 생성 및 수정 서비스
"""

import logging
from typing import List, Optional
from vertex_client import model
from utils.logger import LoggerMixin

logger = logging.getLogger(__name__)


class AIService(LoggerMixin):
    """AI 기반 자기소개서 생성 및 수정 서비스"""
    
    def __init__(self):
        """AI 서비스 초기화"""
        self.model = model
        self.logger.info("AI 서비스 초기화 완료")
    
    def _handle_response(self, response):
        """generate_content 응답 처리 헬퍼"""
        try:
            return response.text
        except Exception:
            try:
                return response.candidates[0].content.parts[0].text
            except (IndexError, AttributeError) as e:
                self.logger.error(f"응답 구문 분석 실패: {e}, 응답: {response}")
                raise ValueError("모델 응답의 형식이 예상과 다릅니다.")
    

    
    def generate_cover_letter(
        self, 
        question: str, 
        jd_text: str, 
        resume_text: str
    ) -> Optional[str]:
        """
        단일 자기소개서 문항 답변 생성
        
        Args:
            question: 자기소개서 질문
            jd_text: 채용공고 텍스트
            resume_text: 이력서 텍스트
            
        Returns:
            Optional[str]: 생성된 답변 또는 None
        """
        try:
            self.logger.info(f"단일 자기소개서 생성 시작: {question[:50]}...")
            self.logger.info(f"채용공고 텍스트 길이: {len(jd_text)}자")
            self.logger.info(f"이력서 텍스트 길이: {len(resume_text)}자")
            self.logger.info(f"채용공고 미리보기: {jd_text[:200]}...")
            
            # 이력서 텍스트가 비어있을 때 처리
            resume_section = ""
            if resume_text and resume_text.strip():
                resume_section = f"""### 정보 2: 지원자 이력서
--- 이력서 시작 ---
{resume_text}
--- 이력서 끝 ---"""
            else:
                resume_section = """### 정보 2: 지원자 이력서
이력서 정보가 제공되지 않았습니다. 채용공고 정보를 바탕으로 일반적인 경험과 역량을 중심으로 답변을 작성해주세요."""

            prompt = f"""<|system|>
당신은 대한민국 최고의 자기소개서 작성 전문가입니다. 당신의 **핵심 임무**는 **주어진 자기소개서 문항(정보 1)에 대해 심도 있게 답변**하는 것입니다. 답변을 작성할 때는 채용공고(정보 3)를 반드시 참고하고, 이력서(정보 2)가 제공된 경우 이를 활용하여 자기소개서를 생성해주세요.
|>

<|user|>
### 정보 1: 자기소개서 문항
"{question}"

{resume_section}

### 정보 3: 채용공고
--- 채용공고 시작 ---
{jd_text}
--- 채용공고 끝 ---

### 작성 지침
1. **가장 중요한 목표**: '정보 1: 자기소개서 문항'에 대한 답변을 중심으로 글을 구성하세요.
2. **채용공고 필수 활용**: 반드시 채용공고(정보 3)의 다음 요소들을 답변에 포함하세요:
   - 회사명, 직무명, 업무내용
   - 요구되는 자격요건, 우대사항
   - 회사의 비전, 문화, 성장 과정
3. **이력서 연계**: 이력서(정보 2)가 제공된 경우, 이력서의 경험과 채용공고의 요구사항을 연결하여 구체적인 사례를 제시하세요. 이력서가 없는 경우에는 일반적인 경험과 역량을 중심으로 작성하세요.
4. **사실 기반**: 채용공고에 없는 내용은 추가하지 마세요. 이력서가 없는 경우에도 허구의 경험을 만들지 마세요.
5. **회사명 주의**: 이력서의 회사명은 '과거' 경력일 뿐이므로, 현재 지원하는 회사와 혼동하지 마세요.
6. **어조 및 형식**:
   - 격식 있고 전문적인 톤을 유지하세요.
   - 제목·헤더 없이 **오직 본문만** 작성하세요.
   - 구체적인 수치와 성과를 포함하세요.
   - **언어 제한**: 오직 한국어와 영어만 사용하세요. 러시아어, 중국어, 일본어 등 다른 언어는 절대 사용하지 마세요.
   - **형식 금지**: 불릿 형태(•, -, *)를 사용하지 마세요. 연속된 문장으로 작성하세요.
   - **문구 금지**: '채용공고에서 요구하는', '채용공고의 요구사항' 등의 문구를 사용하지 마세요.

### 채용공고 분석 요구사항
답변 작성 전에 다음 사항을 반드시 확인하세요:
- 지원하는 회사와 직무가 무엇인지
- 해당 직무에서 요구하는 핵심 역량은 무엇인지
- 내 이력서의 어떤 경험이 이 직무와 연결되는지
- 회사의 비전과 내 경험이 어떻게 맞는지

위 지침을 모두 준수하여, **채용공고 정보를 충실히 반영한 구체적이고 설득력 있는 답변**을 작성하세요.
|>"""

            response = self.model.generate_content(prompt)
            answer = self._handle_response(response)
            
            self.logger.info("단일 자기소개서 생성 완료")
            return answer.strip()
            
        except Exception as e:
            self.logger.error(f"단일 자기소개서 생성 실패: {e}")
            return None
    
    def revise_cover_letter(
        self,
        question: str,
        jd_text: str,
        resume_text: str,
        original_answer: str,
        user_edit_prompt: str
    ) -> Optional[str]:
        """
        자기소개서 답변 수정
        
        Args:
            question: 원래 질문
            jd_text: 채용공고 텍스트
            resume_text: 이력서 텍스트
            original_answer: 원래 답변
            user_edit_prompt: 사용자 수정 요청
            
        Returns:
            Optional[str]: 수정된 답변 또는 None
        """
        try:
            self.logger.info(f"자기소개서 수정 시작: {user_edit_prompt[:50]}...")
            
            # 이력서 텍스트가 비어있을 때 처리
            resume_section = ""
            if resume_text and resume_text.strip():
                resume_section = f"""### 정보 2: 지원자 이력서
--- 이력서 시작 ---
{resume_text}
--- 이력서 끝 ---"""
            else:
                resume_section = """### 정보 2: 지원자 이력서
이력서 정보가 제공되지 않았습니다. 채용공고 정보를 바탕으로 일반적인 경험과 역량을 중심으로 답변을 작성해주세요."""

            prompt = f"""<|system|>
당신은 전문 자기소개서 교정자이자 채용 리뷰어입니다. 당신의 핵심 임무는 **원본 자기소개서가 '정보 1: 자기소개서 문항'의 의도를 더 잘 반영**하고, **사용자의 '수정 요청 사항'을 완벽하게 적용**하도록 수정하는 것입니다. 모든 수정은 제공된 자료(채용공고, 이력서)를 참고하여 수행해야 합니다.
|>

<|user|>
### 정보 1: 자기소개서 문항
"{question}"

{resume_section}

### 정보 3: 채용공고
--- 채용공고 시작 ---
{jd_text}
--- 채용공고 끝 ---

### 정보 4: 원본 자기소개서
--- 원본 답변 시작 ---
{original_answer}
--- 원본 답변 끝 ---

### 수정 요청 사항
"{user_edit_prompt}"

### 수정 지침
1. **최우선 과제**: 사용자의 '수정 요청 사항'과 '자기소개서 문항'의 의도를 정확히 파악하고 반영하세요.
2. **참고 자료 활용**: 채용공고(정보 3)를 반드시 참고하고, 이력서(정보 2)가 제공된 경우 이를 활용하여 수정하세요.
3. **사실성 유지**: 채용공고에 없는 내용은 절대 추가하지 마세요. 이력서가 없는 경우에도 허구의 경험을 만들지 마세요.
4. **회사명 주의**: 이력서의 과거 회사명을 현재 지원하는 회사와 혼동하여 사용하지 마세요.
5. **형식 준수**:
   - 전문적 톤을 유지하세요.
   - 제목·헤더 없이 **수정 완료된 본문만** 작성하세요.
   - **언어 제한**: 오직 한국어와 영어만 사용하세요. 러시아어, 중국어, 일본어 등 다른 언어는 절대 사용하지 마세요.
   - **형식 금지**: 불릿 형태(•, -, *)를 사용하지 마세요. 연속된 문장으로 작성하세요.
   - **문구 금지**: '채용공고에서 요구하는', '채용공고의 요구사항' 등의 문구를 사용하지 마세요.

위 지침에 따라, 원본 답변을 수정하여 **'자기소개서 문항'에 더욱 충실하고 사용자의 '수정 요청'이 완벽히 반영된** 최종 결과물을 작성하세요.
|>"""

            response = self.model.generate_content(prompt)
            revised_answer = self._handle_response(response)
            
            self.logger.info("자기소개서 수정 완료")
            return revised_answer.strip()
            
        except Exception as e:
            self.logger.error(f"자기소개서 수정 실패: {e}")
            return None
    
    def test_ai_connection(self) -> tuple[bool, str]:
        """AI 모델 연결 테스트"""
        try:
            response = self.model.generate_content("안녕하세요. 연결 테스트입니다.")
            result = self._handle_response(response)
            
            if result:
                self.logger.info("AI 모델 연결 테스트 성공")
                return True, "AI 모델이 정상적으로 작동합니다."
            else:
                return False, "AI 모델 응답이 비어있습니다."
                
        except Exception as e:
            self.logger.error(f"AI 모델 연결 테스트 실패: {e}")
            return False, f"AI 모델 연결 실패: {str(e)}" 
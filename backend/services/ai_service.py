import logging
import os
from typing import Dict, Any, Optional, Tuple

# 프로젝트 유틸리티 및 모델 임포트
from utils.logger import LoggerMixin
from vertex_client import model # << 실제 운영 시, 이 줄의 주석을 해제하세요.

# --- 개발 및 테스트를 위한 Mock(가짜) 객체 ---
# class MockResponse:
#     def __init__(self, text): self.text = text
# class MockModel:
#     def generate_content(self, prompt: str) -> MockResponse:
#         guideline_start = prompt.find("### 맞춤형 작성 가이드")
#         guideline_end = prompt.find("### 최종 결과물 지침")
#         guideline_text = prompt[guideline_start:guideline_end]
#         return MockResponse(f"--- Mock Response ---\n질문 유형에 맞는 가이드가 주입되었습니다:\n{guideline_text}\n--- (실제 AI라면 여기에 답변이 생성됩니다) ---")
# model = MockModel()
# --- Mock 객체 끝 ---

logger = logging.getLogger(__name__)

class AIService(LoggerMixin):
    """
    AI 기반 자기소개서 생성 및 수정 서비스
    (고도화된 단일 'default' 가이드라인 사용)
    """

    def __init__(self):
        self.logger.info("AI 서비스 초기화 시작...")
        self.model = model
        self.QUESTION_GUIDELINES = self._precompute_guidelines()
        self.logger.info("고도화된 'default' 가이드라인 계산 완료.")
        self.logger.info("AI 서비스 초기화 완료.")

    def _precompute_guidelines(self) -> Dict:
        """
        모든 질문 유형을 커버하는 고도화된 단일 'default' 가이드라인을 정의합니다.
        'Decomposition'과 'Self-Criticism' 기법을 적용하여 과적합을 방지하고 답변 품질을 높입니다.
        """
        guidelines = {
            # 기존 personality, career_goals 등은 모두 제거하고 default 하나만 남깁니다.
            'default': {
                'canonical_question': "",
                'guide': """
### 맞춤형 자기소개서 작성을 위한 6단계 사고 과정 (Internal Thought Process)

**[1단계: 질문의 핵심 의도 분석]**
1.  이 질문이 표면적으로 묻는 것은 무엇인가? (예: "성격의 장단점")
2.  더 깊게 파고들면, 이 질문을 통해 회사가 진짜 알고 싶어 하는 지원자의 역량이나 자질은 무엇인가? (예: "업무와 협업에 긍정적인 성격인가? 자기 객관화가 되어 있고 개선 의지가 있는가?")
3.  질문이 여러 개(예: 성장과정 및 지원동기)를 포함하고 있다면, 각각의 핵심 의도를 파악한다.

**[2단계: 전략적 경험 선별 (가장 중요)]**
1.  '정보 2: 지원자 제출 자료' 전체를 빠르게 스캔하여 질문 의도에 부합하는 모든 경험 후보군을 파악한다.
2.  **치명적 오류 방지:** 절대로 파악된 모든 경험을 나열하거나 요약하지 않는다. 이것은 가장 낮은 품질의 답변이다.
3.  후보군 중에서, 질문의 의도를 가장 강력하고 압축적으로 보여줄 수 있는 **단 1~2개의 핵심 경험(Core Experience)만을 신중하게 선택**한다.
4.  선택 기준: "왜 수많은 경험 중에 이 경험이 이 질문에 대한 가장 완벽한 증거인가?" 스스로 답할 수 있어야 한다.

**[3단계: 답변 구조 설계]**
1.  선택된 핵심 경험을 가장 효과적으로 전달할 이야기 구조를 설계한다.
    -   **경험/역량/도전/실패 관련 질문의 경우:** STAR 기법(Situation, Task, Action, Result) 또는 문제-해결-결과 구조를 적용한다.
    -   **지원동기/목표/포부 관련 질문의 경우:** 'Hook(회사/직무에 대한 관심 계기) -> 근거(나의 준비된 역량과 경험) -> 기여 방안(입사 후 구체적 기여 계획)' 구조를 설계한다.
    -   **성격/가치관 관련 질문의 경우:** '주장(나의 장점/가치관) -> 근거(핵심 경험) -> 회사 인재상/비전과의 연결' 구조를 설계한다.
2.  만약 질문이 여러 개를 포함하고 있다면, 각 질문에 대한 구조를 논리적 순서에 맞게 배열한다.

**[4단계: 초안 작성]**
-   위 1~3단계의 분석 및 설계에 따라, 선택된 핵심 경험을 설계된 구조에 맞춰 구체적이고 진정성 있는 문체로 초안을 작성한다.

**[5단계: 자기 비판 및 검토 (Self-Criticism)]**
-   작성된 초안이 아래의 '품질 저하 체크리스트'에 해당하지는 않는지 비판적으로 검토한다.
    -   **[ ] 과잉 정보 나열 오류:** 혹시 이 글이 단순히 지원자 제출 자료의 내용을 요약/나열하고 있지는 않은가?
    -   **[ ] 초점 분산 오류:** 하나의 강력한 메시지 대신 여러 경험을 늘어놓아 주장이 흐릿해지지는 않았는가?
    -   **[ ] 동문서답 오류:** 질문의 핵심 의도에 정확히 부합하는 답변인가?
    -   **[ ] 구체성 부족 오류:** "노력했습니다", "기여했습니다" 같은 추상적 표현 대신, 구체적인 행동과 수치적/정성적 결과가 드러나는가?

**[6단계: 최종 답변 생성]**
-   자기 비판 단계에서 발견된 문제점들을 모두 개선하여, 군더더기 없는 최종 결과물을 완성한다.
"""
            }
        }
        return guidelines

    def _classify_question_by_similarity(self, question: str) -> str:
        """ 모든 질문을 'default' 유형으로 분류합니다. """
        return 'default'

    def _handle_response(self, response) -> str:
        """ generate_content 응답 처리 헬퍼 """
        try:
            return response.text.strip()
        except AttributeError:
             return "응답 객체에 'text' 속성이 없습니다."
        except Exception as e:
            self.logger.error(f"응답 처리 중 예외 발생: {e}")
            return ""

    def _log_token_usage(self, response, operation_type: str, question_preview: str = "", prompt_data: dict = None):
        """
        AI 모델 응답에서 토큰 사용량을 추출하고 로깅합니다.
        
        Args:
            response: Vertex AI GenerativeModel의 응답 객체
            operation_type: 작업 유형 (예: "자기소개서 생성", "자기소개서 수정")
            question_preview: 질문 미리보기 (로깅용)
            prompt_data: 프롬프트 구성 요소별 정보 (선택적)
        """
        try:
            # Vertex AI 응답에서 토큰 사용량 정보 추출
            prompt_token_count = 0
            candidates_token_count = 0
            total_token_count = 0
            
            # 방법 1: usage_metadata 속성 확인
            usage_metadata = getattr(response, 'usage_metadata', None)
            if usage_metadata:
                prompt_token_count = getattr(usage_metadata, 'prompt_token_count', 0)
                candidates_token_count = getattr(usage_metadata, 'candidates_token_count', 0)
                total_token_count = getattr(usage_metadata, 'total_token_count', 0)
            
            # 방법 2: to_dict() 메서드로 토큰 정보 확인
            elif hasattr(response, 'to_dict'):
                try:
                    response_dict = response.to_dict()
                    if 'usage_metadata' in response_dict:
                        usage_data = response_dict['usage_metadata']
                        prompt_token_count = usage_data.get('prompt_token_count', 0)
                        candidates_token_count = usage_data.get('candidates_token_count', 0)
                        total_token_count = usage_data.get('total_token_count', 0)
                except Exception:
                    pass
            
            # 토큰 정보를 찾았다면 로그 출력
            if total_token_count > 0 or prompt_token_count > 0 or candidates_token_count > 0:
                # 입력 토큰 세부 분석 생성
                token_breakdown = self._analyze_prompt_tokens(prompt_data, prompt_token_count) if prompt_data else ""
                
                self.logger.info(f"""
╭─ AI 토큰 사용량 ({operation_type}) ─╮
│ 질문: {question_preview[:30]}{'...' if len(question_preview) > 30 else ''}
│ 입력 토큰: {prompt_token_count:,}{token_breakdown}
│ 출력 토큰: {candidates_token_count:,}
│ 총 토큰: {total_token_count:,}
╰─────────────────────────────────╯""")
                
            else:
                self.logger.warning(f"토큰 사용량 정보를 찾을 수 없습니다 ({operation_type})")
                
        except Exception as e:
            self.logger.error(f"토큰 사용량 로깅 중 오류 발생 ({operation_type}): {e}")

    def _analyze_prompt_tokens(self, prompt_data: dict, total_prompt_tokens: int) -> str:
        """
        프롬프트 구성 요소별 토큰 사용량을 대략적으로 분석합니다.
        
        Args:
            prompt_data: 프롬프트 구성 요소 정보
            total_prompt_tokens: 총 입력 토큰 수
        
        Returns:
            토큰 분석 문자열
        """
        if not prompt_data:
            return ""
        
        try:
            # 개선된 토큰 추정 (한글/영어/구조 고려)
            def estimate_tokens(text: str) -> int:
                if not text:
                    return 0
                
                # 기본적으로 3.5자 = 1토큰으로 추정 (더 정확)
                # 마크다운, 특수문자, JSON 구조 등을 고려
                base_tokens = len(text) // 3.5
                
                # 특수 구조에 대한 보정
                special_chars = text.count('###') + text.count('---') + text.count('|>')
                structure_bonus = special_chars * 2  # 구조 문자는 추가 토큰 소모
                
                return max(1, int(base_tokens + structure_bonus))
            
            breakdown = []
            estimated_total = 0
            
            # 각 구성 요소별 예상 토큰 수 계산
            components = [
                ('시스템', prompt_data.get('system_prompt', '')),
                ('질문', prompt_data.get('question', '')),
                ('파일', prompt_data.get('resume_text', '')),
                ('채용정보', prompt_data.get('jd_text', '')),
                ('가이드', prompt_data.get('guideline', '')),
                ('기존답변', prompt_data.get('original_answer', '')),
                ('수정요청', prompt_data.get('edit_request', '')),
                ('답변히스토리', prompt_data.get('answer_history_section', ''))  # 답변 히스토리 추가
            ]
            
            for name, text in components:
                tokens = estimate_tokens(text)
                if tokens > 0:
                    breakdown.append(f"{name}:{tokens}")
                    estimated_total += tokens
            
            # 실제 프롬프트에는 많은 구조적 요소들이 있음
            # - 마크다운 헤더 (### 정보 1:, ### 정보 2: 등)
            # - 구분선 (---, |>)
            # - 상세한 지침들
            # - JSON 스타일 구조
            
            # 더 현실적인 구조 오버헤드 계산
            base_structure = int(total_prompt_tokens * 0.15)  # 15%로 증가
            
            # 추가 구조 요소들 (자기소개서 수정 시 더 복잡함)
            if 'revise' in prompt_data.get('operation_type', ''):
                additional_structure = int(total_prompt_tokens * 0.05)  # 수정 시 5% 추가
                structure_overhead = base_structure + additional_structure
            else:
                structure_overhead = base_structure
                
            if structure_overhead > 0:
                breakdown.append(f"구조:{structure_overhead}")
                estimated_total += structure_overhead
            
            # 실제 토큰과 추정 토큰의 차이 표시
            difference = total_prompt_tokens - estimated_total
            if abs(difference) > 100:  # 차이가 100 토큰 이상일 때만 표시 (임계값 상향)
                if difference > 0:
                    breakdown.append(f"기타:{difference}")
                else:
                    breakdown.append(f"오차:{abs(difference)}")
            
            if breakdown:
                return f" ({', '.join(breakdown)})"
            
        except Exception as e:
            self.logger.debug(f"토큰 분석 실패: {e}")
        
        return ""

    def generate_cover_letter(
        self, 
        question: str, 
        jd_text: str, 
        resume_text: str,
        company_name: str = "",
        job_title: str = ""
    ) -> Tuple[Optional[str], str]:
        """
        단일 자기소개서 문항 답변을 생성합니다.
        (1. 질문 분류(default) -> 2. 고도화된 프롬프트 생성 -> 3. AI 호출)
        """
        try:
            self.logger.info(f"단일 자기소개서 생성 시작: {question[:50]}...")
            
            question_type = self._classify_question_by_similarity(question)
            custom_guideline = self.QUESTION_GUIDELINES[question_type]['guide']
            
            company_info = f"{company_name} 회사 정보는 현재 검색 기능이 비활성화되어 있습니다."
            
            submitted_data_section = ""
            if resume_text and resume_text.strip():
                if "--- 파일 구분선 ---" in resume_text:
                    submitted_data_section = f"""### 정보 2: 지원자 제출 자료 (이력서, 자기소개서, 포트폴리오 등)
--- 자료 시작 ---
{resume_text}
--- 자료 끝 ---

**중요**: 위 내용은 여러 파일(이력서, 포트폴리오 등)에서 추출한 정보입니다. 각 파일의 내용을 종합적으로 활용하여 답변을 작성해주세요."""
                else:
                    submitted_data_section = f"""### 정보 2: 지원자 제출 자료 (이력서, 자기소개서, 포트폴리오 등)
--- 자료 시작 ---
{resume_text}
--- 자료 끝 ---"""
            else:
                submitted_data_section = """### 정보 2: 지원자 제출 자료
자료가 제공되지 않았습니다."""

            # System Prompt 수정: 역할 부여 대신 '사고 과정' 준수를 강조
            prompt = f"""<|system|>
당신은 대한민국 최고의 자기소개서 작성 전문가입니다. 당신의 임무는 주어진 '6단계 사고 과정'을 **내부적으로, 그리고 엄격하게** 따라서, 지원자의 자료를 전략적으로 분석하고 최고의 답변을 생성하는 것입니다.
|>
<|user|>
### 정보 1: 자기소개서 문항
"{question}"
{submitted_data_section}
### 정보 3: 채용공고
--- 채용공고 시작 ---
{jd_text}
--- 채용공고 끝 ---
### 정보 4: 회사 추가 정보
--- 회사 정보 시작 ---
{company_info}
--- 회사 정보 끝 ---
### 맞춤형 작성 가이드
아래 가이드는 당신이 답변을 생성하기 위해 **머릿속으로 따라야 할 생각의 흐름**입니다. 이 가이드라인을 완벽하게 준수하여 답변의 품질을 극대화하세요.
---
{custom_guideline}
---
### 최종 결과물 지침
- **절대, 절대, 절대** '6단계 사고 과정'이나 당신의 분석 과정을 답변에 노출하지 마세요.
- 최종 결과물은 제목, 헤더, 불릿(*, -) 없이 **오직 완성된 한국어 자기소개서 본문만** 작성해주세요.
- '채용공고에서 요구하는', '제출 자료에 따르면' 같은 직접적인 문구는 사용하지 마세요.

이제, 위 모든 지침을 준수하여 **'정보 1: 자기소개서 문항'에 대한 최고의 답변**을 작성하세요.
|>"""
            
            response = self.model.generate_content(prompt)
            answer = self._handle_response(response)
            
            # 토큰 사용량 로깅 (프롬프트 구성 요소 분석 포함)
            prompt_data = {
                'system_prompt': "당신은 대한민국 최고의 자기소개서 작성 전문가입니다...",  # 시스템 프롬프트
                'question': question,
                'resume_text': resume_text,
                'jd_text': jd_text,
                'guideline': custom_guideline
            }
            self._log_token_usage(response, "자기소개서 생성", question[:50], prompt_data)
            
            self.logger.info("단일 자기소개서 생성 완료")
            return answer, company_info

        except Exception as e:
            self.logger.error(f"단일 자기소개서 생성 실패: {e}")
            return None, ""
    
    # revise_cover_letter 메소드는 기존 로직을 유지해도 좋습니다.
    # 수정 요청은 사용자의 명확한 의도가 담겨있어 과적합 문제가 덜 발생하기 때문입니다.
    def revise_cover_letter(
        self,
        question: str,
        jd_text: str,
        resume_text: str,
        original_answer: str,
        user_edit_prompt: str,
        company_info: str = "",
        company_name: str = "",
        job_title: str = "",
        answer_history: list = None
    ) -> Optional[str]:
        # (기존 코드와 동일)
        try:
            self.logger.info(f"자기소개서 수정 시작: {user_edit_prompt[:50]}...")
            
            if not company_info and company_name:
                company_info = f"{company_name} 회사 정보는 현재 검색 기능이 비활성화되어 있습니다."
            elif not company_info:
                company_info = "회사 정보가 제공되지 않았습니다."

            submitted_data_section = ""
            if resume_text and resume_text.strip():
                if "--- 파일 구분선 ---" in resume_text:
                    submitted_data_section = f"""### 정보 2: 지원자 제출 자료 (이력서, 자기소개서, 포트폴리오 등)
--- 자료 시작 ---
{resume_text}
--- 자료 끝 ---

**중요**: 위 내용은 여러 파일(이력서, 포트폴리오 등)에서 추출한 정보입니다. 각 파일의 내용을 종합적으로 활용하여 답변을 작성해주세요."""
                else:
                    submitted_data_section = f"""### 정보 2: 지원자 제출 자료 (이력서, 자기소개서, 포트폴리오 등)
--- 자료 시작 ---
{resume_text}
--- 자료 끝 ---"""
            else:
                submitted_data_section = """### 정보 2: 지원자 제출 자료
자료가 제공되지 않았습니다."""

            answer_history_section = ""
            if answer_history and len(answer_history) > 1:
                history_texts = []
                for i, version in enumerate(answer_history[:-1], 1):
                    history_texts.append(f"버전 {i}: {version}")
                
                answer_history_section = f"""### 정보 6: 이전 버전 답변 히스토리
--- 이전 버전들 시작 ---
{chr(10).join(history_texts)}
--- 이전 버전들 끝 ---

**참고**: 위 이전 버전들을 참고하여 답변의 발전 과정을 파악하고, 더 나은 방향으로 수정해주세요."""

            prompt = f"""<|system|>
당신은 전문 자기소개서 교정자이자 채용 리뷰어입니다. 당신의 핵심 임무는 **원본 자기소개서가 '정보 1: 자기소개서 문항'의 의도를 더 잘 반영**하고, **사용자의 '수정 요청 사항'을 완벽하게 적용**하도록 수정하는 것입니다. 모든 수정은 제공된 자료(채용공고, 지원자 제출 자료, 회사 정보, 이전 버전들)를 참고하여 수행해야 합니다.
|>
<|user|>
### 정보 1: 자기소개서 문항
"{question}"
{submitted_data_section}
### 정보 3: 채용공고
--- 채용공고 시작 ---
{jd_text}
--- 채용공고 끝 ---
### 정보 4: 회사 추가 정보 (AI 검색 결과)
--- 회사 정보 시작 ---
{company_info}
--- 회사 정보 끝 ---
### 정보 5: 현재 버전 자기소개서
--- 현재 답변 시작 ---
{original_answer}
--- 현재 답변 끝 ---
{answer_history_section}
### 수정 요청 사항
"{user_edit_prompt}"
### 수정 지침
1. **최우선 과제**: 사용자의 '수정 요청 사항'과 '자기소개서 문항'의 의도를 정확히 파악하고 반영하세요.
2. **참고 자료 활용**: 
   - 채용공고(정보 3)를 반드시 참고하세요.
   - 지원자 제출 자료(정보 2)가 제공된 경우 이를 활용하세요.
   - 회사 추가 정보(정보 4)를 참고하여 수정하세요.
   - 이전 버전들(정보 6)이 있다면 답변의 발전 과정을 파악하고 더 나은 방향으로 수정하세요.
3. **사실성 유지**: 제공된 자료에 없는 내용은 절대 추가하지 마세요. 허구의 경험을 만들지 마세요.
4. **형식 준수**:
   - 전문적 톤을 유지하세요.
   - 제목·헤더 없이 **수정 완료된 본문만** 작성하세요.
   - 불릿 형태(•, -, *)를 사용하지 마세요. 연속된 문장으로 작성하세요.
위 지침에 따라, 현재 답변을 수정하여 **'자기소개서 문항'에 더욱 충실하고 사용자의 '수정 요청'이 완벽히 반영된** 최종 결과물을 작성하세요.
|>"""
            response = self.model.generate_content(prompt)
            revised_answer = self._handle_response(response)
            
            # 토큰 사용량 로깅 (프롬프트 구성 요소 분석 포함)
            revision_guidelines = """1. **최우선 과제**: 사용자의 '수정 요청 사항'과 '자기소개서 문항'의 의도를 정확히 파악하고 반영하세요.
2. **참고 자료 활용**: 
   - 채용공고(정보 3)를 반드시 참고하세요.
   - 지원자 제출 자료(정보 2)가 제공된 경우 이를 활용하세요.
   - 회사 추가 정보(정보 4)를 참고하여 수정하세요.
   - 이전 버전들(정보 6)이 있다면 답변의 발전 과정을 파악하고 더 나은 방향으로 수정하세요.
3. **사실성 유지**: 제공된 자료에 없는 내용은 절대 추가하지 마세요. 허구의 경험을 만들지 마세요.
4. **형식 준수**:
   - 전문적 톤을 유지하세요.
   - 제목·헤더 없이 **수정 완료된 본문만** 작성하세요.
   - 불릿 형태(•, -, *)를 사용하지 마세요. 연속된 문장으로 작성하세요."""
            
            prompt_data = {
                'system_prompt': "당신은 전문 자기소개서 교정자이자 채용 리뷰어입니다...",
                'question': question,
                'resume_text': resume_text,
                'jd_text': jd_text,
                'original_answer': original_answer,
                'edit_request': user_edit_prompt,
                'guideline': revision_guidelines,
                'answer_history_section': answer_history_section,
                'operation_type': 'revise'  # 수정 작업임을 표시
            }
            self._log_token_usage(response, "자기소개서 수정", user_edit_prompt[:50], prompt_data)
            
            self.logger.info("자기소개서 수정 완료")
            return revised_answer
        except Exception as e:
            self.logger.error(f"자기소개서 수정 실패: {e}")
            return None
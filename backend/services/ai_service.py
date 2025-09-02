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
        """
        guidelines = {
            'default': {
                'canonical_question': "",
                'guide': """
### 🚨 가장 중요한 원칙: 사실 기반 작성 (Fact-Based Generation)
- **최우선 임무:** 당신의 가장 중요한 임무는 '정보 2: 지원자 제출 자료'에 **명시된 사실만을 기반으로** 답변을 생성하는 것입니다.
- **엄격한 금지 사항:** **절대, 절대, 절대** 제출 자료에 없는 경험, 성과, 수치(예: O% 향상, X일 단축, A/B 테스트 경험 등)를 추측하거나 만들어내지 마세요.
- **수치 데이터 처리:** 제출 자료에 구체적인 수치가 없다면, '...개선을 위해 노력했습니다', '...성과를 내는 데 기여했습니다' 와 같이 **정성적인 결과로만 서술하세요.** 없는 사실을 만드는 것보다 정성적으로 표현하는 것이 훨씬 더 중요합니다.

---

### 맞춤형 자기소개서 작성을 위한 6단계 사고 과정 (Internal Thought Process)

**[1단계: 질문의 핵심 의도 분석]**
1.  이 질문이 표면적으로 묻는 것은 무엇인가? (예: "성격의 장단점", "지원동기", "성장과정", "직무경험" 등)
2.  더 깊게 파고들면, 이 질문을 통해 회사가 진짜 알고 싶어 하는 지원자의 역량이나 자질은 무엇인가? (예: "업무와 협업에 긍정적인 성격인가? 자기 객관화가 되어 있고 개선 의지가 있는가?")
3.  질문이 여러 개(예: 성장과정 및 지원동기)를 포함하고 있다면, 각각의 핵심 의도를 파악한다.

**[2단계: 전략적 경험 선별 (가장 중요)]**
1.  '정보 2: 지원자 제출 자료' 전체를 빠르게 스캔하여 질문 의도 및 '정보 3: 채용공고'와 관련성 높은 경험 후보군을 파악한다.
2.  **치명적 오류 방지:** 절대로 파악된 모든 경험을 나열하거나 요약하지 않는다. 이것은 가장 낮은 품질의 답변이다.
3.  **선택 기준 (매우 중요):**
    -   **1순위: '정보 3: 채용공고'와의 직접적 관련성.** 선택할 경험은 지원하는 회사, 산업, 직무의 특성과 반드시 연결되어야 한다. 관련성이 없다면 아무리 인상적인 경험이라도 절대 선택해서는 안 된다. (예: '조선왕릉' 축제 지원서에 '제주 4.3 사건' 경험을 사용하는 것은 최악의 선택)
    -   **2순위: 질문 의도와의 부합성.** 관련성이 확보된 경험들 중에서, 질문의 의도를 가장 강력하고 압축적으로 보여줄 수 있는 단 1~2개의 핵심 경험을 선택한다.
4.  **자기 검증:** "왜 이 경험이 이 회사, 이 직무, 이 질문에 대한 가장 완벽한 증거인가?" 스스로 답할 수 있어야 한다.

**[3단계: 답변 구조 설계]**
1.  질문의 유형을 파악하고, 아래 **'<부록> 질문 유형별 추천 구조'**를 참조하여 가장 적합한 이야기 구조를 설계한다.
2.  단순히 패턴을 따르는 것이 아니라, **[2단계]에서 선택된 핵심 경험**이 가장 빛날 수 있도록 구조를 유연하게 적용하거나 조합한다.
    -   예시: 지원동기 질문이지만, 직무 역량을 강조하고 싶다면 '지원동기 구조'에 '경험/역량 구조'를 결합하여 경험을 구체적으로 서술할 수 있다.
3.  만약 질문이 여러 개를 포함하고 있다면, 각 질문에 대한 구조를 논리적 순서에 맞게 배열한다.

**[4단계: 초안 작성]**
-   위 1~3단계의 분석 및 설계에 따라, 선택된 핵심 경험을 설계된 구조에 맞춰 구체적이고 진정성 있는 문체로 초안을 작성한다.

**[5단계: 자기 비판 및 검토 (Self-Criticism)]**
-   작성된 초안이 아래의 '품질 저하 체크리스트'에 해당하지는 않는지 비판적으로 검토한다.
    -   **[ ] 사실 왜곡/창작 오류 (최우선 검토):** 제출 자료에 명시되지 않은 구체적인 수치나 성과를 만들어내지는 않았는가?
    -   **[ ] 과잉 정보 나열 오류:** 단순히 지원자 제출 자료의 내용을 요약/나열하고 있지는 않은가?
    -   **[ ] 초점 분산 오류:** 하나의 강력한 메시지 대신 여러 경험을 늘어놓아 주장이 흐릿해지지는 않았는가?
    -   **[ ] 동문서답 오류:** 질문의 표면적, 심층적 의도에 정확히 부합하는 답변인가?
    -   **[ ] 맥락 이탈 오류 (중요):** 작성된 내용(특히 핵심 경험)이 지원하는 회사나 직무의 성격과 완전히 동떨어져 있지는 않은가?
    -   **[ ] 구체성 부족 오류:** "노력했습니다", "기여했습니다" 같은 추상적 표현 대신, (제출 자료에 근거한) 구체적인 행동과 결과가 드러나는가?

**[6단계: 최종 답변 생성]**
-   자기 비판 단계에서 발견된 문제점들을 모두 개선하여, 군더더기 없는 최종 결과물을 완성한다.

---
### <부록> 질문 유형별 추천 구조 (Heuristics)
아래 구조들을 기본적인 틀(Framework)로 활용하되, 질문의 미묘한 뉘앙스와 지원자의 경험에 맞춰 창의적으로 변형하여 사용하라. 단순히 순서대로 나열하는 것이 아니라, 각 단계의 목적을 이해하고 유기적으로 연결된 하나의 완성된 글을 작성해야 한다.

#### 1. 성격의 장단점
- **목표:** 지원 직무에 필요한 강점을 어필하고, 단점에 대해서는 객관적인 인식과 개선 노력을 보여주어 신뢰감을 형성한다.
- **구조:**
    1.  `[장점-두괄식 주장]` 지원하는 직무와 가장 관련성이 높은 자신의 장점을 한 문장으로 명확하게 제시한다.
    2.  `[장점-경험 증명]` 해당 장점을 가장 잘 보여주는 구체적인 경험(선별된 1가지)을 STAR 기법 등을 활용하여 증명한다.
    3.  `[단점-솔직한 인정]` 자신의 단점을 솔직하게 인정하되, 직무 수행에 치명적이지 않은 것을 선택한다.
    4.  `[단점-개선 노력 및 기여]` 단점을 극복하기 위해 어떤 구체적인 노력을 하고 있는지 설명하며 마무리한다.

#### 2. 입사 후 포부
- **목표:** 회사의 비전과 직무에 대한 깊은 이해를 바탕으로, 자신의 구체적이고 현실적인 성장 계획과 기여 방안을 제시한다.
- **구조:**
    1.  `[목표 제시]` 입사 후 이루고 싶은 최종적인 비전이나 목표를 회사의 인재상 또는 사업 방향과 연결하여 제시한다.
    2.  `[단기 계획 (1~3년)]` 입사 초기, 직무에 빠르게 적응하고 성과를 내기 위한 구체적인 액션 플랜을 제시한다.
    3.  `[중장기 계획 (5~10년)]` 자신의 직무 전문성을 어떻게 심화시키고, 이를 통해 회사에 기여할 것인지에 대한 로드맵을 보여준다.
    4.  `[마무리-기여 강조]` 자신의 성장이 곧 회사의 발전으로 이어진다는 점을 강조하며 마무리한다.

#### 3. 직무와 관련된 경험 (핵심 역량)
- **목표:** 지원 직무에서 요구하는 핵심 역량을 자신이 보유하고 있음을 가장 강력한 경험으로 증명한다.
- **구조:**
    1.  `[역량-두괄식 주장]` 채용공고를 기반으로 파악한 핵심 직무 역량 중, 자신이 가장 자신 있는 역량을 명확하게 제시한다.
    2.  `[경험 서술]` 해당 역량을 발휘했던 가장 대표적인 경험을 STAR(Situation, Task, Action, Result) 기법에 따라 서술한다.
    3.  `[역량 학습 및 교훈]` 위 경험을 통해 어떤 교훈을 얻었고, 구체적으로 어떤 직무 스킬을 습득했는지 설명한다.
    4.  `[직무와의 연결]` 이 경험과 역량이 입사 후 해당 직무를 수행하는 데 어떻게 기여할 수 있을지 연결하며 마무리한다.

#### 4. 실패 또는 어려움 극복 경험
- **목표:** 실패에 좌절하지 않고, 문제를 분석하고 해결하며, 그 과정에서 배우고 성장하는 주도적인 인재임을 보여준다.
- **구조:**
    1.  `[상황 및 목표]` 도전했던 과제와 당시의 목표를 간략하게 설명하고, 실패 원인이 자신의 부족함에 있었음을 솔직하게 인정한다.
    2.  `[실패/어려움의 원인 분석]` 왜 실패했는지, 혹은 어떤 어려움에 직면했는지 객관적으로 분석하는 과정을 보여준다.
    3.  `[극복을 위한 행동]` 문제를 해결하고 상황을 개선하기 위해 어떤 구체적인 행동을 기울였는지 상세하게 서술한다.
    4.  `[결과 및 교훈]` 그 노력을 통해 얻은 결과(상황 개선 등)와 함께, 이 경험을 통해 무엇을 배웠는지 명확하게 제시한다.
    5.  `[직무 기여]` 해당 경험을 통해 얻은 교훈이 향후 직무 수행 중 어려움을 겪을 때 어떻게 긍정적으로 작용할 것인지 연결한다.

#### 5. 지원동기
- **목표:** '왜 이 회사인가?'와 '왜 이 직무인가?'에 대한 명확한 답을 자신의 경험과 가치관을 바탕으로 설득력 있게 제시한다.
- **구조:**
    1.  `[서론: 지원 의사 및 역량 제시]` 전체 글을 **"저는 [핵심 역량]을 발휘하여 [회사명] [직무명]에 기여하고자 지원하게 되었습니다."** 와 같이, 자신의 핵심 역량과 지원 의사를 명확히 밝히는 문장으로 시작한다.
    2.  `[Why the Company?: 회사 지원 이유]` 회사의 비전, 핵심가치 등 특정 측면이 자신의 가치관이나 커리어 목표와 어떻게 부합하는지 설명한다.
    3.  `[Why the Job?: 직무 지원 이유]` 해당 직무를 성공적으로 수행할 수 있다고 생각하는 이유를 자신의 핵심 역량 및 관련 경험과 연결하여 증명한다.
    4.  `[Contribution: 기여 방안 및 포부]` 입사 후 자신의 역량을 바탕으로 회사와 직무에 어떻게 기여하고 싶은지에 대한 포부로 마무리한다.

#### 6. 성장과정
- **목표:** 살아온 과정을 **시간 순서대로 나열하는 것이 아니라**, 현재의 자신을 만든 **하나의 핵심 가치관**이 어떤 계기로 형성되어, 자신의 생각과 행동에 어떻게 영향을 미쳤는지를 **일관된 서사**로 보여준다. 직무 경험 나열이 아닌, 지원자의 '사람'을 보여주는 것이 핵심이다.
- **구조:**
    1.  `[가치관/강점 제시]` 자신의 성장과정을 관통하는 **하나의 핵심 가치관**이나 직무 관련 강점을 소제목처럼 한 문장으로 제시한다. (예: "저는 위기를 기회로 바꾸는 도전정신을 통해 성장했습니다.")
    2.  `[계기가 된 경험 서술]` 해당 가치관이 형성되는 데 **결정적인 계기**가 된 사건, 인물, 경험(**단 하나만 선택**)을 구체적인 스토리로 풀어낸다. (유년 시절, 학창 시절 등 과거의 경험을 중심으로 서술)
        -   **중요:** 여러 경험을 시간 순서대로 나열하는 것은 최악의 답변이므로 절대 금지한다.
    3.  `[가치관의 심화 또는 적용]` 그 계기를 통해 얻은 깨달음이 **어떻게 다른 경험(예: 프로젝트, 대외활동, 인턴 등)으로 이어지며 발전하거나 적용되었는지** 논리적으로 연결한다. 이 단계가 이야기의 흐름을 만드는 핵심이다. (예: "부모님을 통해 배운 책임감은, 대학 시절 팀 프로젝트에서 끝까지 포기하지 않는 원동력이 되었습니다.")
    4.  `[회사/직무와의 연결]` 이렇게 형성되고 발전해 온 자신의 가치관과 강점이 회사의 인재상과 어떻게 부합하며, 직무 수행에 어떤 긍정적인 영향을 미칠 것인지 연결하며 **서사를 완성한다.**
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

    def _clean_resume_text(self, text: str) -> str:
        """
        입력 텍스트에서 AI 챗봇이 생성했을 법한 상용구(boilerplate) 문장을 제거합니다.
        """
        if not text:
            return ""

        patterns_to_remove = [
            "좋습니다. 요청하신 대로", "요청하신 대로", "자소서를 수정해 드리겠습니다.",
            "AI가 생성한 답변입니다.", "다음은 ...에 대한 답변입니다.", "생성된 자기소개서입니다.",
            "도움이 되셨기를 바랍니다.", "...에 대한 답변입니다.", "답변:", "답변 :"
        ]

        cleaned_text = text
        for pattern in patterns_to_remove:
            cleaned_text = cleaned_text.replace(pattern, "")

        return cleaned_text.strip()

    def _log_token_usage(self, response, operation_type: str, question_preview: str = "", prompt_data: dict = None):
        """ AI 모델 응답에서 토큰 사용량을 추출하고 로깅합니다. """
        try:
            prompt_token_count, candidates_token_count, total_token_count = 0, 0, 0
            
            usage_metadata = getattr(response, 'usage_metadata', None)
            if usage_metadata:
                prompt_token_count = getattr(usage_metadata, 'prompt_token_count', 0)
                candidates_token_count = getattr(usage_metadata, 'candidates_token_count', 0)
                total_token_count = getattr(usage_metadata, 'total_token_count', 0)
            
            elif hasattr(response, 'to_dict'):
                try:
                    response_dict = response.to_dict()
                    if 'usage_metadata' in response_dict:
                        usage_data = response_dict['usage_metadata']
                        prompt_token_count = usage_data.get('prompt_token_count', 0)
                        candidates_token_count = usage_data.get('candidates_token_count', 0)
                        total_token_count = usage_data.get('total_token_count', 0)
                except Exception: pass
            
            if total_token_count > 0 or prompt_token_count > 0:
                token_breakdown = self._analyze_prompt_tokens(prompt_data, prompt_token_count) if prompt_data else ""
                self.logger.info(f"╭─ AI 토큰 사용량 ({operation_type}) ─╮\n"
                                 f"│ 질문: {question_preview[:30]}{'...' if len(question_preview) > 30 else ''}\n"
                                 f"│ 입력 토큰: {prompt_token_count:,}{token_breakdown}\n"
                                 f"│ 출력 토큰: {candidates_token_count:,}\n"
                                 f"│ 총 토큰: {total_token_count:,}\n"
                                 f"╰─────────────────────────────────╯")
            else:
                self.logger.warning(f"토큰 사용량 정보를 찾을 수 없습니다 ({operation_type})")
        except Exception as e:
            self.logger.error(f"토큰 사용량 로깅 중 오류 발생 ({operation_type}): {e}")

    def _analyze_prompt_tokens(self, prompt_data: dict, total_prompt_tokens: int) -> str:
        """ 프롬프트 구성 요소별 토큰 사용량을 대략적으로 분석합니다. """
        if not prompt_data: return ""
        try:
            def estimate_tokens(text: str) -> int:
                if not text: return 0
                return max(1, int(len(text) / 2.0))

            breakdown, estimated_total = [], 0
            components = [('시스템', prompt_data.get('system_prompt', '')), ('질문', prompt_data.get('question', '')),
                          ('파일', prompt_data.get('resume_text', '')), ('채용정보', prompt_data.get('jd_text', '')),
                          ('가이드', prompt_data.get('guideline', ''))]
            
            for name, text in components:
                tokens = estimate_tokens(text)
                if tokens > 0:
                    breakdown.append(f"{name}:{tokens}")
                    estimated_total += tokens
            
            structure_overhead = int(total_prompt_tokens * 0.1)
            if structure_overhead > 0:
                breakdown.append(f"구조:{structure_overhead}")
            
            if breakdown: return f" ({', '.join(breakdown)})"
        except Exception as e:
            self.logger.debug(f"토큰 분석 실패: {e}")
        return ""

    def generate_cover_letter(
        self, question: str, jd_text: str, resume_text: str,
        company_name: str = "", job_title: str = ""
    ) -> Tuple[Optional[str], str]:
        """ 단일 자기소개서 문항 답변을 생성합니다. """
        try:
            self.logger.info(f"단일 자기소개서 생성 시작: {question[:50]}...")
            custom_guideline = self.QUESTION_GUIDELINES['default']['guide']
            company_info = f"{company_name} 회사 정보는 현재 검색 기능이 비활성화되어 있습니다."
            cleaned_resume_text = self._clean_resume_text(resume_text)

            submitted_data_section = ""
            if cleaned_resume_text and cleaned_resume_text.strip():
                submitted_data_section = f"### 정보 2: 지원자 제출 자료 (이력서 등)\n--- 자료 시작 ---\n{cleaned_resume_text}\n--- 자료 끝 ---"
            else:
                submitted_data_section = "### 정보 2: 지원자 제출 자료\n자료가 제공되지 않았습니다."

            prompt = f"""<|system|>
당신은 대한민국 최고의 자기소개서 작성 전문가입니다. 당신의 임무는 주어진 가이드라인을 **내부적으로, 그리고 엄격하게** 따라서, 지원자의 자료를 전략적으로 분석하고 최고의 답변을 생성하는 것입니다.
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
### 🚨 중요 경고: 지원 회사 정보 교차 검증 (Cross-Verification)
- **가장 중요한 임무**: 당신은 지금 **'{company_name}'** 회사, **'{job_title}'** 직무에 지원하는 자기소개서를 작성하고 있다.
- **오류 확인**: '정보 2: 지원자 제출 자료'에 '{company_name}'가 아닌 다른 회사 이름(예: 삼성디스플레이, LG전자 등)이 포함되어 있을 수 있다. 이는 지원자가 과거에 사용했던 자료이므로, **내용만 참고하되 해당 회사 이름은 절대, 절대, 절대 최종 결과물에 언급해서는 안 된다.**
- **최종 검증**: 생성할 답변에 '{company_name}' 이외의 회사 이름이 포함되어 있는지 반드시 마지막으로 확인하고 제거하라.

### 최종 결과물 지침
- **절대, 절대, 절대** '6단계 사고 과정'이나 당신의 분석 과정을 답변에 노출하지 마세요.
- **절대, 절대, 절대** 메타/설명형 문장을 쓰지 마세요. (예: "자료가 없어 일반적인 답변을 생성합니다.")
- **형식 준수:** 최종 결과물은 제목, 헤더, 불릿(*, -) 없이 **오직 완성된 한국어 자기소개서 본문만** 작성해주세요.
- **질문 반복 금지:** '정보 1: 자기소개서 문항'의 내용을 제목처럼 서두에 반복하지 말고, 바로 답변 본론으로 시작하세요.
- **채용공고 내용 인용 금지:** '정보 3: 채용공고'의 직무, 자격요건 등을 그대로 나열하거나 요약하지 마세요. 채용공고는 당신이 지원자의 경험과 역량을 어떤 방향으로 연결해야 할지 파악하기 위한 **내부 참고 자료**일 뿐입니다.
- **직접 인용 금지:** '채용공고에서 요구하는', '제출 자료에 따르면' 같은 직접적인 문구는 사용하지 마세요.
- **완성도:** 자료 유무와 관계없이 자연스럽고 완성도 높은 자기소개서를 작성하세요. 메타 정보나 상황 설명 없이 바로 본론으로 들어가세요.

이제, 위 모든 지침을 준수하여 **'정보 1: 자기소개서 문항'에 대한 최고의 답변**을 작성하세요.
|>"""
            
            response = self.model.generate_content(prompt)
            answer = self._handle_response(response)
            
            prompt_data = {'system_prompt': "...", 'question': question, 'resume_text': cleaned_resume_text,
                           'jd_text': jd_text, 'guideline': custom_guideline}
            self._log_token_usage(response, "자기소개서 생성", question[:50], prompt_data)
            
            self.logger.info("단일 자기소개서 생성 완료")
            return answer, company_info

        except Exception as e:
            self.logger.error(f"단일 자기소개서 생성 실패: {e}")
            return None, ""
    
    def revise_cover_letter(
        self, question: str, jd_text: str, resume_text: str, original_answer: str,
        user_edit_prompt: str, company_info: str = "", company_name: str = "",
        job_title: str = "", answer_history: list = None
    ) -> Optional[str]:
        try:
            self.logger.info(f"자기소개서 수정 시작: {user_edit_prompt[:50]}...")
            
            if not company_info and company_name:
                company_info = f"{company_name} 회사 정보는 현재 검색 기능이 비활성화되어 있습니다."
            elif not company_info:
                company_info = "회사 정보가 제공되지 않았습니다."
            
            cleaned_resume_text = self._clean_resume_text(resume_text)

            submitted_data_section = ""
            if cleaned_resume_text and cleaned_resume_text.strip():
                submitted_data_section = f"### 정보 2: 지원자 제출 자료\n--- 자료 시작 ---\n{cleaned_resume_text}\n--- 자료 끝 ---"
            else:
                submitted_data_section = "### 정보 2: 지원자 제출 자료\n자료가 제공되지 않았습니다."

            answer_history_section = ""
            if answer_history and len(answer_history) > 1:
                history_texts = [f"버전 {i}: {v}" for i, v in enumerate(answer_history[:-1], 1)]
                answer_history_section = f"### 정보 6: 이전 버전 답변 히스토리\n--- 이전 버전들 시작 ---\n{chr(10).join(history_texts)}\n--- 이전 버전들 끝 ---"

            prompt = f"""<|system|>
당신은 전문 자기소개서 교정자이자 채용 리뷰어입니다.
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
### 정보 5: 현재 버전 자기소개서
--- 현재 답변 시작 ---
{original_answer}
--- 현재 답변 끝 ---
{answer_history_section}
### 수정 요청 사항
"{user_edit_prompt}"

### 수정 지침
1.  **최우선 과제:** 사용자의 '수정 요청 사항'과 '자기소개서 문항'의 의도를 정확히 파악하고 반영하세요.
2.  **사실성 유지:** '정보 2: 지원자 제출 자료'에 없는 내용은 절대 추가하지 마세요. 허구의 경험을 만들지 마세요.
3.  **형식 준수:** 제목·헤더 없이 **수정 완료된 본문만** 작성하세요.
4.  **메타 문구 금지:** 메타/설명형 문장(예: "자료가 없어...")을 절대 쓰지 마세요.

위 지침에 따라, 현재 답변을 수정하여 최종 결과물을 작성하세요.
|>"""
            response = self.model.generate_content(prompt)
            revised_answer = self._handle_response(response)
            
            prompt_data = {'system_prompt': "...", 'question': question, 'resume_text': cleaned_resume_text,
                           'jd_text': jd_text, 'original_answer': original_answer, 'edit_request': user_edit_prompt,
                           'answer_history_section': answer_history_section, 'operation_type': 'revise'}
            self._log_token_usage(response, "자기소개서 수정", user_edit_prompt[:50], prompt_data)
            
            self.logger.info("자기소개서 수정 완료")
            return revised_answer
        except Exception as e:
            self.logger.error(f"자기소개서 수정 실패: {e}")
            return None
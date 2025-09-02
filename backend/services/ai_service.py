import logging
import os
import json
from typing import Dict, Any, Optional, Tuple
from scipy.spatial.distance import cosine
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

# 프로젝트 유틸리티 및 모델 임포트
from utils.logger import LoggerMixin
from vertex_client import model as generation_model 

logger = logging.getLogger(__name__)

class AIService(LoggerMixin):
    """ AI 기반 자기소개서 생성 및 수정 서비스 (지능형 분류기 및 모듈형 가이드라인 사용) """

    def __init__(self):
        self.logger.info("AI 서비스 초기화 시작...")
        self.generation_model = generation_model
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")
        
        try:
            base_dir = os.path.dirname(__file__)
            embeddings_path = os.path.join(base_dir, "canonical_embeddings.json")
            with open(embeddings_path, 'r', encoding='utf-8') as f:
                self.canonical_embeddings = json.load(f)
            self.logger.info("기준 임베딩 데이터를 성공적으로 로드했습니다.")
        except FileNotFoundError:
            self.logger.error("치명적 오류: canonical_embeddings.json 파일을 찾을 수 없습니다! generate_embeddings.py를 먼저 실행하세요.")
            self.canonical_embeddings = []

        # ================== [추가된 웜업 코드] ================== #
        # 임베딩 모델 '웜업' (Cold Start 문제 해결)
        try:
            self.logger.info("임베딩 모델 웜업을 시작합니다...")
            # 실제 API를 호출하여 모델을 미리 활성화시킵니다.
            self.embedding_model.get_embeddings(["웜업용 테스트 문장"])
            self.logger.info("임베딩 모델 웜업이 성공적으로 완료되었습니다.")
        except Exception as e:
            self.logger.error(f"임베딩 모델 웜업 중 오류가 발생했습니다: {e}")
        # ========================================================== #

        self.MAIN_GUIDE, self.APPENDICES = self._precompute_guidelines()
        self.logger.info("모듈형 가이드라인 계산 완료.")
        self.logger.info("AI 서비스 초기화 완료.")

    def _precompute_guidelines(self) -> Tuple[str, Dict[str, str]]:
        """ 가이드라인을 '핵심 가이드'와 '부록'으로 분리하여 정의합니다. """
        
        main_guide = """
### 🚨 가장 중요한 원칙: 사실 기반 작성 (Fact-Based Generation)
- **최우선 임무:** 당신의 가장 중요한 임무는 '정보 2: 지원자 제출 자료'에 **명시된 사실만을 기반으로** 답변을 생성하는 것입니다.
- **엄격한 금지 사항:** **절대, 절대, 절대** 제출 자료에 없는 경험, 성과, 수치(예: O% 향상, X일 단축, A/B 테스트 경험 등)를 추측하거나 만들어내지 마세요.
- **수치 데이터 처리:** 제출 자료에 구체적인 수치가 없다면, '...개선을 위해 노력했습니다', '...성과를 내는 데 기여했습니다' 와 같이 **정성적인 결과로만 서술하세요.** 없는 사실을 만드는 것보다 정성적으로 표현하는 것이 훨씬 더 중요합니다.

---

### 맞춤형 자기소개서 작성을 위한 6단계 사고 과정 (Internal Thought Process)
**[1단계: 질문의 핵심 의도 분석]**
1.  이 질문이 표면적으로 묻는 것은 무엇인가?
2.  더 깊게 파고들면, 이 질문을 통해 회사가 진짜 알고 싶어 하는 지원자의 역량이나 자질은 무엇인가?

**[2단계: 전략적 경험 선별 (가장 중요)]**
1.  '정보 2: 지원자 제출 자료' 전체를 스캔하여 질문 의도 및 '정보 3: 채용공고'와 관련성 높은 경험 후보군을 파악한다.
2.  **선택 기준 (매우 중요):**
    -   **1순위: '정보 3: 채용공고'와의 직접적 관련성.** 관련성이 없다면 아무리 인상적인 경험이라도 절대 선택해서는 안 된다.
    -   **2순위: 질문 의도와의 부합성.** 관련성이 확보된 경험들 중에서, 질문의 의도를 가장 강력하고 압축적으로 보여줄 수 있는 단 1~2개의 핵심 경험을 선택한다.

**[3단계: 답변 구조 설계]**
-   아래에 제공될 **'<부록>'**을 참조하여, [2단계]에서 선택된 핵심 경험이 가장 빛날 수 있도록 이야기 구조를 설계한다.

**[4단계: 초안 작성]**
-   위 분석 및 설계에 따라, 구체적이고 진정성 있는 문체로 초안을 작성한다.

**[5단계: 자기 비판 및 검토 (Self-Criticism)]**
-   작성된 초안이 아래의 '품질 저하 체크리스트'에 해당하지는 않는지 비판적으로 검토한다.
    -   **[ ] 사실 왜곡/창작 오류 (최우선 검토):** 제출 자료에 명시되지 않은 구체적인 수치나 성과를 만들어내지는 않았는가?
    -   **[ ] 맥락 이탈 오류 (중요):** 작성된 내용이 지원하는 회사나 직무의 성격과 동떨어져 있지는 않은가?
    -   **[ ] 동문서답 오류:** 질문의 핵심 의도에 정확히 부합하는 답변인가?

**[6단계: 최종 답변 생성]**
-   발견된 문제점들을 모두 개선하여, 군더더기 없는 최종 결과물을 완성한다.
"""
        
        appendices = {
            "strength_weakness": """
### <부록> 성격의 장단점 작성 가이드
- **목표:** 지원 직무에 필요한 강점을 어필하고, 단점에 대해서는 객관적인 인식과 개선 노력을 보여주어 신뢰감을 형성한다.
- **구조:**
    1.  `[장점-두괄식 주장]` 지원하는 직무와 가장 관련성이 높은 자신의 장점을 한 문장으로 명확하게 제시한다. (예: "저의 가장 큰 강점은 복잡한 문제 속에서도 핵심을 파악하는 분석력입니다.")
    2.  `[장점-경험 증명]` 해당 장점을 가장 잘 보여주는 구체적인 경험(선별된 1가지)을 STAR 기법 등을 활용하여 증명한다. 추상적인 설명이 아닌, 행동과 결과 중심으로 서술한다.
    3.  `[단점-솔직한 인정]` 자신의 단점을 솔직하게 인정하되, 직무 수행에 치명적이지 않은 것을 선택한다. (예: 지나친 꼼꼼함으로 인한 초기 속도 저하, 과도한 책임감 등)
    4.  `[단점-개선 노력 및 기여]` 단점을 극복하기 위해 어떤 구체적인 노력을 하고 있는지 설명하고, 이러한 노력이 오히려 직무에 긍정적으로 기여할 수 있음을 연결하며 마무리한다.
""",
            "aspiration": """
### <부록> 입사 후 포부 작성 가이드
- **목표:** 회사의 비전과 직무에 대한 깊은 이해를 바탕으로, 자신의 구체적이고 현실적인 성장 계획과 기여 방안을 제시한다.
- **구조:**
    1.  `[목표 제시]` 입사 후 이루고 싶은 최종적인 비전이나 목표를 회사의 인재상 또는 사업 방향과 연결하여 제시한다. (예: "데이터 분석 역량을 바탕으로 OOO 분야의 영업 전략을 고도화하는 전문가로 성장하겠습니다.")
    2.  `[단기 계획 (1~3년)]` 입사 초기, 직무에 빠르게 적응하고 성과를 내기 위한 구체적인 액션 플랜을 제시한다. (예: "입사 1년 내에 회사의 핵심 제품군과 데이터 분석 시스템을 완벽히 숙달하고...")
    3.  `[중장기 계획 (5~10년)]` 자신의 직무 전문성을 어떻게 심화시키고, 이를 통해 팀과 회사에 어떤 실질적인 기여를 할 것인지에 대한 장기적인 로드맵을 보여준다.
    4.  `[마무리-기여 강조]` 자신의 성장이 곧 회사의 발전으로 이어진다는 점을 다시 한번 강조하며, 회사와 함께 성장하고 싶다는 의지를 표현한다.
""",
            "job_experience": """
### <부록> 직무와 관련된 경험 (핵심 역량) 작성 가이드
- **목표:** 지원 직무에서 요구하는 핵심 역량을 자신이 보유하고 있음을 가장 강력한 경험으로 증명한다.
- **구조:**
    1.  `[역량-두괄식 주장]` 채용공고를 기반으로 파악한 핵심 직무 역량 중, 자신이 가장 자신 있는 역량을 명확하게 제시한다.
    2.  `[경험 서술]` 해당 역량을 발휘했던 가장 대표적인 경험을 STAR(Situation, Task, Action, Result) 기법에 따라 구체적이고 논리적으로 서술한다.
    3.  `[역량 학습 및 교훈]` 위 경험을 통해 어떤 교훈을 얻었고, 구체적으로 어떤 직무 관련 스킬이나 지식(Hard/Soft Skills)을 습득하고 발전시킬 수 있었는지 설명한다.
    4.  `[직무와의 연결]` 이 경험과 역량이 입사 후 해당 직무를 성공적으로 수행하는 데 어떻게 직접적으로 기여할 수 있을지 연결하며 마무리한다.
""",
            "failure_experience": """
### <부록> 실패 또는 어려움 극복 경험 작성 가이드
- **목표:** 실패에 좌절하지 않고, 문제를 분석하고 해결하며, 그 과정에서 배우고 성장하는 주도적인 인재임을 보여준다.
- **구조:**
    1.  `[상황 및 목표]` 도전했던 과제와 당시의 목표를 간략하게 설명한다. 실패의 원인이 자신의 통제 밖이 아닌, 자신의 부족함이나 실수에 있었음을 솔직하게 인정하는 것이 좋다.
    2.  `[실패/어려움의 원인 분석]` 왜 실패했는지, 혹은 어떤 어려움에 직면했는지 객관적으로 분석하는 과정을 보여준다.
    3.  `[극복을 위한 행동]` 문제를 해결하고 상황을 개선하기 위해 어떤 구체적인 행동과 노력을 기울였는지 상세하게 서술한다. (가장 중요한 부분)
    4.  `[결과 및 교훈]` 그 노력을 통해 얻은 결과(상황 개선, 부분적 성공 등)와 함께, 이 경험을 통해 무엇을 배웠는지(교훈) 명확하게 제시한다.
    5.  `[직무 기여]` 해당 경험을 통해 얻은 교훈이나 역량이 향후 직무 수행 중 어려움을 겪을 때 어떻게 긍정적으로 작용할 것인지 연결한다.
""",
            "motivation": """
### <부록> 지원동기 작성 가이드
- **목표:** '왜 이 회사인가?'와 '왜 이 직무인가?'에 대한 명확한 답을 자신의 경험과 가치관을 바탕으로 설득력 있게 제시한다.
- **구조:**
    1.  `[서론: 지원 의사 및 역량 제시]` 전체 글을 **"저는 [핵심 역량]을 발휘하여 [회사명] [직무명]에 기여하고자 지원하게 되었습니다."** 와 같이, 자신의 핵심 역량과 지원 의사를 명확히 밝히는 문장으로 시작한다.
    2.  `[Why the Company?: 회사 지원 이유]` 회사의 비전, 핵심가치, 기술력, 사회적 기여 등 특정 측면이 자신의 가치관이나 커리어 목표와 어떻게 부합하는지를 구체적인 근거와 함께 설명한다.
    3.  `[Why the Job?: 직무 지원 이유]` 해당 직무를 성공적으로 수행할 수 있다고 생각하는 이유를 자신의 핵심 역량 및 관련 경험과 연결하여 증명한다.
    4.  `[Contribution: 기여 방안 및 포부]` 입사 후 자신의 역량을 바탕으로 회사와 직무에 어떻게 기여하고 싶은지에 대한 포부로 마무리하며 지원의 진정성을 강조한다.
""",
            "growth_process": """
### <부록> 성장과정 작성 가이드
- **목표:** 살아온 과정을 **시간 순서대로 나열하는 것이 아니라**, 현재의 자신을 만든 **하나의 핵심 가치관**이 어떤 계기로 형성되어, 자신의 생각과 행동에 어떻게 영향을 미쳤는지를 **일관된 서사**로 보여준다. 직무 경험 나열이 아닌, 지원자의 '사람'을 보여주는 것이 핵심이다.
- **구조:**
    1.  `[가치관/강점 제시]` 자신의 성장과정을 관통하는 **하나의 핵심 가치관**이나 직무 관련 강점을 소제목처럼 한 문장으로 제시한다. (예: "저는 위기를 기회로 바꾸는 도전정신을 통해 성장했습니다.")
    2.  `[계기가 된 경험 서술]` 해당 가치관이 형성되는 데 **결정적인 계기**가 된 사건, 인물, 경험(**단 하나만 선택**)을 구체적인 스토리로 풀어낸다. (유년 시절, 학창 시절 등 과거의 경험을 중심으로 서술)
        -   **중요:** 여러 경험을 시간 순서대로 나열하는 것은 최악의 답변이므로 절대 금지한다.
    3.  `[가치관의 심화 또는 적용]` 그 계기를 통해 얻은 깨달음이 **어떻게 다른 경험(예: 프로젝트, 대외활동, 인턴 등)으로 이어지며 발전하거나 적용되었는지** 논리적으로 연결한다. 이 단계가 이야기의 흐름을 만드는 핵심이다. (예: "부모님을 통해 배운 책임감은, 대학 시절 팀 프로젝트에서 끝까지 포기하지 않는 원동력이 되었습니다.")
    4.  `[회사/직무와의 연결]` 이렇게 형성되고 발전해 온 자신의 가치관과 강점이 회사의 인재상과 어떻게 부합하며, 직무 수행에 어떤 긍정적인 영향을 미칠 것인지 연결하며 **서사를 완성한다.**
"""
        }
        return main_guide, appendices

    def _classify_question_by_similarity(self, question: str) -> str:
        """
        사용자의 질문을 '검색어'로 임베딩하여 가장 유사한 기준 '문서' 유형을 찾습니다.
        """
        if not self.canonical_embeddings:
            self.logger.warning("기준 임베딩이 로드되지 않아 'job_experience' 유형으로 처리합니다.")
            return "job_experience"

        try:
             # [수정 2] 사용자의 질문과 task_type을 TextEmbeddingInput 객체로 감싸서 전달합니다.
            inputs = [TextEmbeddingInput(text=question, task_type="RETRIEVAL_QUERY")]
            response = self.embedding_model.get_embeddings(inputs)
            question_vector = response[0].values
            
            # 모든 기준 '문서' 벡터와의 코사인 유사도를 계산합니다.
            similarities = [(1 - cosine(question_vector, item['vector']), item['key']) for item in self.canonical_embeddings]
            
            # 가장 높은 유사도를 가진 유형을 찾아 반환합니다.
            if similarities:
                best_match = max(similarities, key=lambda x: x[0])
                self.logger.info(f"질문 분류 결과: '{best_match[1]}' (유사도: {best_match[0]:.4f})")
                return best_match[1]

        except Exception as e:
            self.logger.error(f"질문 분류 중 오류 발생: {e}", exc_info=True)
        
        # 오류 발생 시 가장 보편적인 '직무 경험' 유형으로 안전하게 처리합니다.
        return "job_experience"

    def _handle_response(self, response) -> str:
        """ generate_content 응답 처리 헬퍼 """
        try:
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"응답 처리 중 예외 발생: {e}")
            return ""

    def _clean_resume_text(self, text: str) -> str:
        """ 입력 텍스트에서 AI 챗봇이 생성했을 법한 상용구(boilerplate) 문장을 제거합니다. """
        if not text: return ""
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
            # response 객체에서 usage_metadata 속성을 직접 가져옵니다.
            usage_metadata = getattr(response, 'usage_metadata', None)
            
            if usage_metadata:
                # [수정] .get() 메서드 대신, 객체의 속성에 직접 접근합니다.
                prompt_token_count = usage_metadata.prompt_token_count
                candidates_token_count = usage_metadata.candidates_token_count
                total_token_count = usage_metadata.total_token_count
                
                self.logger.info(f"╭─ AI 토큰 사용량 ({operation_type}) ─╮\n"
                                 f"│ 질문: {question_preview[:30]}...\n"
                                 f"│ 입력 토큰: {prompt_token_count:,}\n"
                                 f"│ 출력 토큰: {candidates_token_count:,}\n"
                                 f"│ 총 토큰: {total_token_count:,}\n"
                                 f"╰─────────────────────────────────╯")
            else:
                self.logger.warning(f"토큰 사용량 정보를 찾을 수 없습니다 ({operation_type})")
        except Exception as e:
            self.logger.error(f"토큰 사용량 로깅 중 오류 발생: {e}")

    def generate_cover_letter(
        self, question: str, jd_text: str, resume_text: str,
        company_name: str = "", job_title: str = ""
    ) -> Tuple[Optional[str], str]:
        """ 단일 자기소개서 문항 답변을 생성합니다. """
        try:
            self.logger.info(f"단일 자기소개서 생성 시작: {question[:50]}...")
            
            question_type = self._classify_question_by_similarity(question)
            specific_appendix = self.APPENDICES.get(question_type, self.APPENDICES['job_experience'])
            custom_guideline = f"{self.MAIN_GUIDE}\n\n{specific_appendix}"

            company_info = f"{company_name} 회사 정보는 현재 검색 기능이 비활성화되어 있습니다."
            cleaned_resume_text = self._clean_resume_text(resume_text)

            submitted_data_section = f"### 정보 2: 지원자 제출 자료\n--- 자료 시작 ---\n{cleaned_resume_text}\n--- 자료 끝 ---" if cleaned_resume_text else "### 정보 2: 지원자 제출 자료\n자료가 제공되지 않았습니다."

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
### 🚨 중요 경고: 지원 회사 정보 교차 검증
- **임무**: 지금 **'{company_name}'** 회사, **'{job_title}'** 직무에 지원하는 글을 작성하고 있다.
- **오류 확인**: 제출 자료에 다른 회사 이름이 있어도, 절대 최종 결과물에 언급해서는 안 된다.
- **최종 검증**: 생성할 답변에 '{company_name}' 이외의 회사 이름이 없는지 반드시 확인하라.

### 최종 결과물 지침
- **절대 금지**: 분석 과정 노출, 메타 설명, 질문 반복, 공고 인용, '자료에 따르면' 같은 표현.
- **형식**: 제목, 헤더, 불릿 없이 오직 완성된 한국어 본문만 작성.
- **완성도**: 자료 유무와 관계없이 바로 본론으로 시작하는 완성형 글을 작성.

이제, 위 모든 지침을 준수하여 최고의 답변을 작성하세요.
|>"""
            
            response = self.generation_model.generate_content(prompt)
            answer = self._handle_response(response)
            
            self._log_token_usage(response, "자기소개서 생성", question[:50])
            self.logger.info("단일 자기소개서 생성 완료")
            return answer, company_info

        except Exception as e:
            self.logger.error(f"단일 자기소개서 생성 실패: {e}", exc_info=True)
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
            
            cleaned_resume_text = self._clean_resume_text(resume_text)
            submitted_data_section = f"### 정보 2: 지원자 제출 자료\n--- 자료 시작 ---\n{cleaned_resume_text}\n--- 자료 끝 ---" if cleaned_resume_text else "### 정보 2: 지원자 제출 자료\n자료가 제공되지 않았습니다."

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

### 🚨 가장 중요한 원칙: 사실 기반 수정
- **최우선 임무**: '정보 2: 지원자 제출 자료'에 **명시된 사실만을 기반으로** 답변을 수정해야 합니다.
- **엄격한 금지 사항**: **절대** 제출 자료에 없는 경험, 성과, 수치를 만들어내지 마세요.

### 🚨 중요 경고: 지원 회사 정보 교차 검증
- **임무**: 지금 **'{company_name}'** 회사, **'{job_title}'** 직무의 글을 수정하고 있다.
- **오류 확인**: 제출 자료에 다른 회사 이름이 있어도, 절대 최종 결과물에 언급해서는 안 된다.

### 최종 결과물 지침
1.  **최우선 과제**: 사용자의 '수정 요청 사항'을 정확히 반영하세요.
2.  **형식**: 제목·헤더 없이 **수정 완료된 본문만** 작성하세요.
3.  **메타 문구 금지**: 메타/설명형 문장(예: "자료가 없어...")을 절대 쓰지 마세요.

위 지침에 따라, 현재 답변을 수정하여 최종 결과물을 작성하세요.
|>"""
            response = self.generation_model.generate_content(prompt)
            revised_answer = self._handle_response(response)
            
            self._log_token_usage(response, "자기소개서 수정", user_edit_prompt[:50])
            self.logger.info("자기소개서 수정 완료")
            return revised_answer
            
        except Exception as e:
            self.logger.error(f"자기소개서 수정 실패: {e}", exc_info=True)
            return None
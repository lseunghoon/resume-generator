import logging
import os
from typing import Dict, Any, Optional, Tuple

# 1. 의미 기반 유사도 측정을 위한 라이브러리 임포트
from sentence_transformers import SentenceTransformer, util

# 2. 프로젝트 유틸리티 및 모델 임포트
from utils.logger import LoggerMixin
from vertex_client import model # << 실제 운영 시, 이 줄의 주석을 해제하세요.

# --- 개발 및 테스트를 위한 Mock(가짜) 객체 ---
# 로컬에서 비용/시간 없이 테스트하려면 아래 MockModel 관련 코드의 주석을 해제하고,
# 실제 model 임포트 라인(from vertex_client...)을 주석 처리하세요.

class MockResponse:
    def __init__(self, text): self.text = text

class MockModel:
    def generate_content(self, prompt: str) -> MockResponse:
        guideline_start = prompt.find("### 맞춤형 작성 가이드")
        guideline_end = prompt.find("### 최종 결과물 지침")
        guideline_text = prompt[guideline_start:guideline_end]
        return MockResponse(f"--- Mock Response ---\n질문 유형에 맞는 가이드가 주입되었습니다:\n{guideline_text}\n--- (실제 AI라면 여기에 답변이 생성됩니다) ---")

# model = MockModel() # << 로컬 테스트 시, 이 줄의 주석을 해제하여 사용하세요.
# --- Mock 객체 끝 ---

logger = logging.getLogger(__name__)

class AIService(LoggerMixin):
    """
    AI 기반 자기소개서 생성 및 수정 서비스
    (분류 방식: 의미 기반 유사도 측정)
    """

    def __init__(self):
        """
        AI 서비스 초기화 시, 필요한 모든 모델을 로드하고 데이터 구조를 미리 계산합니다.
        이 과정은 서버 시작 시 1회만 실행되어 사용자 응답 시간에는 영향을 주지 않습니다.
        """
        self.logger.info("AI 서비스 초기화 시작...")
        
        # 자기소개서 '생성'을 위한 LLM 모델 (Vertex AI 또는 Mock)
        self.model = model

        # 임베딩 분류 기능 토글 (메모리 절약용)
        disable_embed = os.getenv("AI_DISABLE_EMBEDDING_CLASSIFIER", "false").strip().lower() in ("1", "true", "yes", "on")
        self.embedding_disabled: bool = disable_embed
        self.embedding_model = None

        if self.embedding_disabled:
            self.logger.info("AI_DISABLE_EMBEDDING_CLASSIFIER=true: 임베딩 분류를 비활성화합니다 (항상 'default' 가이드 사용).")
        else:
            # 질문 '분류'를 위한 임베딩 모델 로드
            try:
                # 경량 다국어 임베딩 모델로 교체
                self.embedding_model = SentenceTransformer('intfloat/multilingual-e5-small')
                # 메모리/속도 최적화를 위해 최대 시퀀스 길이 제한
                try:
                    self.embedding_model.max_seq_length = 128
                except Exception:
                    pass
                self.logger.info("의미 유사도 측정을 위한 임베딩 모델 로드 완료 (intfloat/multilingual-e5-small, max_seq_len=128).")
            except Exception as e:
                self.logger.error(f"임베딩 모델 로드 실패: {e}. 이 모델 없이는 질문 분류가 불가능합니다.")
                raise

        # 질문 유형별 가이드라인과 대표 질문 벡터를 미리 계산
        self.QUESTION_GUIDELINES, self.guideline_vectors = self._precompute_guidelines_and_vectors()
        
        if self.embedding_disabled:
            self.logger.info("질문 유형별 가이드라인 계산 완료 (벡터 계산 생략 - 분류 기능 비활성화).")
        else:
            self.logger.info(f"질문 유형별 가이드라인 및 벡터 계산 완료 ({len(self.guideline_vectors)}개 유형).")
        
        self.logger.info("AI 서비스 초기화 완료.")

    def _precompute_guidelines_and_vectors(self) -> Tuple[Dict, Dict]:
        """
        각 질문 유형의 가이드라인과, 분류에 사용할 대표 질문(canonical_question)을 정의하고 벡터화합니다.
        """
        guidelines = {
            'personality': {
                'canonical_question': "당신의 성격의 장단점은 무엇인가요?",
                'guide': """- **전체 구조:** 이 질문에 대한 답변은 **'장점 문단'과 '단점 문단'이라는 두 개의 분리된 문단**으로 구성하세요. 각 문단은 독립적인 두괄식 구조를 가져야 합니다.
- **장점 문단 작성법:**
    1.  **(장점 두괄식 제시):** 문단의 첫 문장에서 "저의 장점은 [장점]입니다." 와 같이 장점을 명확하게 먼저 밝히세요.
    2.  **(구체적 사례):** 그 장점을 가장 잘 보여주는 **하나의 구체적인 경험(에피소드)**을 선택하여, 상황-행동-결과를 이야기하듯 서술하세요. (여러 경험 나열 금지)
    3.  **(기여 방안):** 마지막으로, 이 장점이 지원한 회사와 직무에 어떻게 긍정적으로 기여할 수 있는지 연결하며 문단을 마무리하세요.
- **단점 문단 작성법:**
    1.  **(단점 두괄식 제시):** 문단의 첫 문장에서 "반면, [단점]이라는 단점이 있습니다." 와 같이 단점을 솔직하게 인정하세요.
    2.  **(개선 노력):** 그 단점을 인지하고 있으며, 이를 개선하고 극복하기 위해 **현재 어떤 구체적인 노력**을 하고 있는지 구체적으로 서술하세요. (예: 스터디 참여, 계획 수립 습관 등)
"""
            },
            'career_goals': {
                'canonical_question': "입사 후 포부나 미래 계획, 목표에 대해 말해주세요.",
                'guide': """- **핵심 원칙:** 모든 계획은 **채용공고(정보 3)에 언급된 회사, 직무, 그리고 회사의 핵심 서비스/제품과 구체적으로 연결**되어야 합니다. 추상적인 포부가 아닌, 실질적인 기여 방안을 보여주는 것이 중요합니다.
1.  **궁극적 목표 제시:** 입사 후 **[회사명]의 [핵심 서비스/제품명]을 어떻게 성장시키고 싶은지**, 또는 회사의 비전에 어떻게 기여하고 싶은지 당신의 최종 목표를 두괄식으로 제시하세요.
2.  **단기 계획 (초기):** 입사 초기에는 **[회사명]의 핵심 서비스와 기술 스택, 비즈니스 모델을 완벽하게 이해하기 위해** 어떤 노력을 할 것인지 서술하세요. (예: 'X 서비스의 사용자 데이터 흐름을 분석하여 주요 지표를 파악하겠습니다.')
3.  **중기 계획 (성장기):** 입사 1~3년 후에는 학습한 내용을 바탕으로, **[직무명]으로서 [핵심 서비스/제품명]의 어떤 부분을 구체적으로 개선하거나 성장**시키고 싶은지 서술하세요. (예: 'Y 기능의 사용자 이탈률을 5% 감소시키는 프로젝트를 주도하겠습니다.')
4.  **장기 계획 (전문가):** 입사 5년 후에는 **[회사명]의 [특정 사업 분야] 전문가**로 성장하여, 회사의 미래 성장을 위해 어떤 새로운 기회를 만들거나 기여하고 싶은지 장기적인 비전을 제시하세요. (예: 'Z 기술을 도입하여 새로운 수익 모델을 발굴하겠습니다.')
"""
            },
            'challenge_experience': {
                'canonical_question': "실패하거나 도전했던 어려운 경험에 대해 말해주세요.",
                'guide': """- **핵심:** 실패 그 자체가 아니라 **'실패를 통해 무엇을 배웠는가'**가 핵심입니다.
- **구조:** [상황 제시] -> [실패 또는 어려움 발생] -> [원인 분석 및 해결 노력] -> **[결과 및 배운 점]** -> [기여 다짐] 순서로 작성하세요.
- **Action:** 실패의 원인을 객관적으로 분석하고, 문제를 해결하기 위해 어떤 노력을 했는지 구체적으로 서술하세요. 남 탓을 하거나 변명하는 뉘앙스는 절대 피하세요.
- **마무리:** 이 경험을 통해 얻은 교훈이나 역량(예: 위기관리 능력)을 강조하고, 이것이 회사에 어떻게 긍정적으로 작용할지 어필하세요."""
            },
            'job_experience': {
                 'canonical_question': "직무와 관련된 경험에 대해 알려주세요.",
                 'guide': """- **핵심 구조:** 이 질문에는 **STAR 기법(Situation, Task, Action, Result)**을 사용하는 것이 가장 효과적입니다.
- **경험 선택:** 지원자의 자료에서 가장 관련성 높은 경험 1~2개를 선택하세요.
- **STAR 서술:** 각 경험을 STAR 구조에 맞춰 구체적으로 서술하세요.
    - **Situation (상황):** 어떤 프로젝트/업무 상황이었나요?
    - **Task (과제):** 주어진 구체적인 목표나 과제는 무엇이었나요?
    - **Action (행동):** 그 과제를 해결하기 위해 **직접 수행한 행동**은 무엇이었나요? (가장 중요)
    - **Result (결과):** 당신의 행동으로 인해 어떤 긍정적인 결과(정량적/정성적 성과)가 있었나요?
- **마무리:** 이 경험을 통해 얻은 역량이 지원한 직무에 어떻게 기여할 수 있는지 연결하며 마무리하세요."""
            },
            'teamwork_experience': {
                'canonical_question': "팀워크나 협업 경험에 대해 말해주세요.",
                'guide': """- **핵심:** 단순히 "협력을 잘했다"가 아니라, 공동의 목표 달성을 위해 **'내가 어떤 역할을 수행했는가'**를 보여주는 것이 중요합니다.
- **구조:** [공동의 목표 및 상황 설명] -> [나의 구체적인 역할과 기여] -> [팀 내의 어려움(선택 사항)] -> [소통/협력을 통한 해결 과정] -> [최종 성과] 순서로 작성하세요.
- **Action:** 팀 내에서 맡았던 역할(예: 리더, 중재자, 데이터 분석가)을 명시하고, 나의 어떤 행동이 팀의 목표 달성에 기여했는지 구체적으로 서술하세요."""
            },
            'core_values': {
                'canonical_question': "자신의 가치관, 성장과정, 직업 선택 기준은 무엇인가요?",
                'guide': """- **핵심:** 나의 가치관이 **'회사의 비전/인재상과 어떻게 부합하는지'**를 연결하는 것이 가장 중요합니다.
- **구조:** [나의 핵심 가치관/신념 제시] -> [그 가치관이 형성된 계기나 경험] -> **[나의 가치관과 회사의 비전/핵심가치의 연결점]** -> [입사 후 기여 다짐] 순서로 작성하세요.
- **Action:** 추상적인 가치관(예: 도전, 성장)을 제시한 후, 반드시 그것을 뒷받침하는 짧고 구체적인 경험을 덧붙여 신뢰도를 높이세요."""
            },
            'motivation': {
            'canonical_question': "회사와 직무에 지원한 동기는 무엇인가요?",
            'guide': """
- **핵심 원칙:** 당신의 임무는 지원자를 매력적으로 보이게 할 '진짜 이야기'를 만드는 것입니다. 제출된 자료와 채용공고는 그 이야기의 신뢰도를 높이기 위한 '증거'로만 사용하세요.

- **[1단계: 진정한 '연결고리(Hook)' 찾기]**
    - **(자유도 부여)** 먼저, 왜 이 지원자가 '다른 회사가 아닌 바로 이 회사'에 관심을 갖게 되었을지 가장 그럴듯한 '계기'를 찾아내세요.
    - 이 계기는 다음과 같은 것일 수 있습니다:
        - 이 회사의 서비스/제품을 사용해 본 개인적인 경험
        - 회사가 해결하려는 문제에 대한 깊은 공감
        - 회사의 기술력이나 디자인 철학에 대한 깊은 인상
        - 지원자의 가치관과 회사의 비전이 일치하는 지점

- **[2단계: '연결고리'와 자신의 강점 연결하기]**
    - 1단계에서 찾아낸 '연결고리'와, '정보 2: 지원자 제출 자료'에 있는 지원자의 핵심 역량/경험을 연결할 논리를 만드세요.
    - "나는 [1단계의 계기]를 통해 이 분야에 관심을 갖게 되었고, 이를 해결(또는 기여)하기 위해 [자료에 있는 핵심 경험]과 같은 노력을 해왔다"는 흐름을 구성하세요.
    - 여기서도 **가장 강력한 경험 딱 하나만**을 선택하여 이야기에 깊이를 더하세요.

- **[3단계: 논리적인 이야기(Narrative) 구성하기]**
    - 위에서 찾은 재료들을 바탕으로, 설득력 있는 이야기의 흐름을 설계하세요.
    - **(시작):** 왜 이 회사에 관심을 갖게 되었는지, 그 계기나 에피소드를 제시하며 흥미를 유발합니다.
    - **(전개):** 그 관심을 바탕으로, 지원자가 어떤 노력을 통해 직무 관련 역량을 키워왔는지 구체적인 경험을 들어 증명합니다.
    - **(결말):** 최종적으로, 그렇게 준비된 지원자가 이 회사, 이 직무에 입사하여 어떤 긍정적인 영향을 미칠 수 있는지 기여 방안을 제시하며 마무리합니다.

- **[4단계: 최종 답변 작성]**
    - 설계된 이야기의 흐름에 따라, 진정성 있고 전문적인 어조로 최종 답변을 작성하세요. '정보 3: 채용공고'의 내용은 직접적으로 언급하기보다, 답변의 방향성이 직무 요구사항과 일치하는지 확인하는 '가이드라인'으로만 활용하세요."""
        },
            'default': {
            'canonical_question': "",
            'guide': """
- **[1단계: 질문 핵심 파악]** 이 질문이 하나의 주제를 묻고 있는지, 여러 주제를 함께 묻고 있는지 먼저 분석하세요.
- **[2단계: 답변 계획 수립]**
    - **만약 여러 주제가 섞여 있다면 (예: 지원동기 + 입사 후 포부),** 답변할 순서를 정하고 각 주제에 맞는 소제목을 마음속으로 정하세요. (예: 1. 지원 동기, 2. 입사 후 목표)
    - **만약 하나의 주제라면,** 그 주제에 가장 설득력 있는 구조(예: 두괄식, STAR)를 설계하세요.
- **[3단계: 근거 자료 찾기]** 수립한 계획에 맞춰, 각 주장을 뒷받침할 구체적인 경험과 역량을 제출 자료에서 찾으세요.
- **[4단계: 종합 답변 작성]** 위 계획에 따라, 각 부분을 논리적으로 연결하여 하나의 완성된 답변을 작성하세요. **질문이 담고 있는 모든 요구사항을 빠짐없이 충족시키는 것이 가장 중요합니다.**
"""
        }
        }
        
        vectors = {}
        if not self.embedding_disabled and self.embedding_model is not None:
            for type_name, data in guidelines.items():
                if data['canonical_question']:
                    v = self.embedding_model.encode(data['canonical_question'], convert_to_tensor=True)
                    # 코사인 유사도 안정화를 위해 정규화
                    try:
                        util.normalize_embeddings(v)
                    except Exception:
                        pass
                    vectors[type_name] = v
            self.logger.info(f"임베딩 벡터 계산 완료 ({len(vectors)}개 유형).")
        else:
            self.logger.info("임베딩 벡터 계산 생략 (분류 기능 비활성화).")
        
        return guidelines, vectors

    def _classify_question_by_similarity(self, question: str) -> str:
        """
        사용자 질문의 의미를 분석하여 가장 유사한 질문 유형으로 분류합니다.
        (신규 로직: 최고 점수와 2등 점수의 차이가 작으면 'default'로 처리)
        """
        try:
            if self.embedding_disabled or self.embedding_model is None:
                return 'default'
            user_vector = self.embedding_model.encode(question, convert_to_tensor=True)
            try:
                util.normalize_embeddings(user_vector)
            except Exception:
                pass
            
            similarities = {}
            for type_name, vector in self.guideline_vectors.items():
                score = util.cos_sim(user_vector, vector).item()
                similarities[type_name] = score

            if not similarities: return 'default'

            # 1. 모든 점수를 내림차순으로 정렬합니다.
            scores = sorted(similarities.values(), reverse=True)

            # 2. 점수가 2개 미만이면 비교할 수 없으므로, 이전 로직을 그대로 따릅니다.
            if len(scores) < 2:
                best_type = max(similarities, key=similarities.get)
                if scores[0] > 0.60:
                    self.logger.info(f"질문 유형이 '{best_type}'으로 분류되었습니다 (유사도: {scores[0]:.2f}).")
                    return best_type
                else:
                    return 'default'

            # 3. 최고 점수와 2등 점수를 가져옵니다.
            best_score = scores[0]
            second_best_score = scores[1]
            
            # 4. (핵심 로직) 모호함을 판단할 임계값을 설정합니다. (튜닝 가능)
            AMBIGUITY_THRESHOLD = 0.15

            # 5. 최고 점수가 임계치(0.6)를 넘었는지, 그리고 1-2등 점수 차이가 충분히 큰지 확인합니다.
            if best_score > 0.55 and (best_score - second_best_score) > AMBIGUITY_THRESHOLD:
                # 점수 차이가 충분히 커서 명확할 경우에만 해당 유형으로 분류
                best_type = max(similarities, key=similarities.get)
                self.logger.info(f"질문이 명확하여 '{best_type}'으로 분류되었습니다 (유사도: {best_score:.2f}, 2등과 차이: {(best_score - second_best_score):.2f}).")
                return best_type
            else:
                # 점수 차이가 임계치보다 작으면, 복합 질문으로 간주하고 'default'로 분류
                # 1등, 2등이 무엇인지 확인하기 위해 상위 2개 유형과 점수를 로그에 포함
                sorted_items = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
                first_place_type, first_place_score = sorted_items[0]
                second_place_type, second_place_score = sorted_items[1]
                
                self.logger.info(f"질문이 모호하여 'default'로 분류되었습니다. 1등: '{first_place_type}' ({first_place_score:.2f}), 2등: '{second_place_type}' ({second_place_score:.2f}), 차이: {(first_place_score - second_place_score):.2f}")
                return 'default'

        except Exception as e:
            self.logger.error(f"유사도 기반 질문 분류 실패: {e}")
            return 'default'

    def _handle_response(self, response) -> str:
        """generate_content 응답 처리 헬퍼"""
        try:
            return response.text.strip()
        except AttributeError:
             return "응답 객체에 'text' 속성이 없습니다."
        except Exception as e:
            self.logger.error(f"응답 처리 중 예외 발생: {e}")
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
        (1. 질문 분류 -> 2. 맞춤형 프롬프트 생성 -> 3. AI 호출)
        """
        try:
            self.logger.info(f"단일 자기소개서 생성 시작: {question[:50]}...")
            
            question_type = self._classify_question_by_similarity(question)
            custom_guideline = self.QUESTION_GUIDELINES[question_type]['guide']
            
            company_info = f"{company_name} 회사 정보는 현재 검색 기능이 비활성화되어 있습니다."
            
            submitted_data_section = ""
            if resume_text and resume_text.strip():
                # 여러 파일이 구분선으로 나뉘어 있는지 확인
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

            prompt = f"""<|system|>
당신은 대한민국 최고의 자기소개서 작성 전문가입니다. 당신의 임무는 주어진 '맞춤형 작성 가이드'에 따라, 지원자의 자료를 분석하여 최고의 답변을 생성하는 것입니다.
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
아래 가이드는 당신이 답변을 생성하기 위해 **머릿속으로 따라야 할 생각의 흐름**입니다. 이 가이드라인을 완벽하게 준수하여 답변의 품질을 높이세요.
---
{custom_guideline}
---
### 최종 결과물 지침
- **절대, 절대, 절대** '맞춤형 작성 가이드'나 당신의 분석 과정을 답변에 노출하지 마세요.
- 최종 결과물은 제목, 헤더, 불릿(*, -) 없이 **오직 완성된 한국어 자기소개서 본문만** 작성해주세요.
- '채용공고에서 요구하는', '제출 자료에 따르면' 같은 직접적인 문구는 사용하지 마세요.

이제, 위 모든 지침을 준수하여 **'정보 1: 자기소개서 문항'에 대한 최고의 답변**을 작성하세요.
|>"""
            
            response = self.model.generate_content(prompt)
            answer = self._handle_response(response)
            
            self.logger.info("단일 자기소개서 생성 완료")
            return answer, company_info

        except Exception as e:
            self.logger.error(f"단일 자기소개서 생성 실패: {e}")
            return None, ""
    
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
        """
        자기소개서 답변을 수정합니다.
        모든 이전 버전의 답변과 업로드된 파일들을 참고하여 수정합니다.
        """
        try:
            self.logger.info(f"자기소개서 수정 시작: {user_edit_prompt[:50]}...")
            
            if not company_info and company_name:
                company_info = f"{company_name} 회사 정보는 현재 검색 기능이 비활성화되어 있습니다."
            elif not company_info:
                company_info = "회사 정보가 제공되지 않았습니다."

            submitted_data_section = ""
            if resume_text and resume_text.strip():
                # 여러 파일이 구분선으로 나뉘어 있는지 확인
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

            # 이전 버전들의 답변 히스토리 섹션 구성
            answer_history_section = ""
            if answer_history and len(answer_history) > 1:
                history_texts = []
                for i, version in enumerate(answer_history[:-1], 1):  # 현재 버전 제외
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
            self.logger.info("자기소개서 수정 완료")
            return revised_answer
        except Exception as e:
            self.logger.error(f"자기소개서 수정 실패: {e}")
            return None
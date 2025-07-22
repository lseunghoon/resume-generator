import logging
from vertex_client import model  # vertex_client.py에서 초기화된 모델 사용

logger = logging.getLogger(__name__)

def _handle_response(response):
    """generate_content 응답 처리 헬퍼"""
    try:
        return response.text
    except Exception:
        try:
            return response.candidates[0].content.parts[0].text
        except (IndexError, AttributeError) as e:
            logger.error(f"응답 구문 분석 실패: {e}, 응답: {response}")
            raise ValueError("모델 응답의 형식이 예상과 다릅니다.")

def generate_cover_letter(question, jd_text, resume_text, length):
    """질문·JD·이력서 기반으로 자기소개서 답변 생성"""
    try:
        prompt = f"""<|system|>
당신은 대한민국 최고의 자기소개서 작성 전문가입니다. 당신의 **핵심 임무**는 **주어진 자기소개서 문항(정보 1)에 대해 심도 있게 답변**하는 것입니다. 답변을 작성할 때는 지원자의 이력서(정보 2)와 채용공고(정보 3)를 근거로 활용하여, 지원자의 경험과 역량이 문항의 주제 및 지원 직무와 어떻게 연결되는지를 논리적으로 보여주어야 합니다.
|>

<|user|>
### 정보 1: 자기소개서 문항
"{question}"

### 정보 2: 지원자 이력서
--- 이력서 시작 ---
{resume_text}
--- 이력서 끝 ---

### 정보 3: 채용공고
--- 채용공고 시작 ---
{jd_text}
--- 채용공고 끝 ---

### 작성 지침
1. **가장 중요한 목표**: '정보 1: 자기소개서 문항'에 대한 답변을 중심으로 글을 구성하세요.
2. **경험 연결**: 답변을 뒷받침하기 위해 이력서(정보 2)의 경험과 채용공고(정보 3)의 직무를 연결하되, 단순히 경력을 나열해서는 안 됩니다.
3. **사실 기반**: 이력서·채용공고에 없는 경험이나 역량은 추가하지 마세요.
4. **회사명 주의**: 이력서의 회사명은 '과거' 경력일 뿐이므로, 현재 지원하는 회사와 혼동하지 마세요.
5. **어조 및 형식**:
   - 격식 있고 전문적인 톤을 유지하세요.
   - 제목·헤더 없이 **오직 본문만**, 한국어 기준 **{length}자 내외**로 작성하세요.

위 지침을 모두 준수하여, **'정보 1: 자기소개서 문항'에 대한 답변을 지원자의 경험과 연결하여 설득력 있게 작성**하세요.
|>

<|assistant|>
"""
        response = model.generate_content(prompt)
        return _handle_response(response)
    except Exception as e:
        logger.error(f"자기소개서 생성 실패: {e}")
        return f"답변 생성 중 오류가 발생했습니다: {e}"

def revise_cover_letter(question, jd_text, resume_text, original_answer, user_edit_prompt):
    """기존 답변을 주어진 요청에 맞춰 수정"""
    try:
        prompt = f"""<|system|>
당신은 전문 자기소개서 교정자이자 채용 리뷰어입니다. 당신의 핵심 임무는 **원본 자기소개서가 '정보 1: 자기소개서 문항'의 의도를 더 잘 반영**하고, **사용자의 '수정 요청 사항'을 완벽하게 적용**하도록 수정하는 것입니다. 모든 수정은 제공된 자료(이력서, 채용공고)에 근거해야 합니다.
|>

<|user|>
### 정보 1: 자기소개서 문항
"{question}"

### 정보 2: 지원자 이력서
--- 이력서 시작 ---
{resume_text}
--- 이력서 끝 ---

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
2. **논리 강화**: 원본의 핵심 메시지를 유지하되, 문항의 답변과 직결되도록 논리 구조를 재구성하거나 표현을 다듬으세요.
3. **사실성 유지**: 이력서·채용공고에 없는 내용은 절대 추가하지 마세요.
4. **회사명 주의**: 이력서의 과거 회사명을 현재 지원하는 회사와 혼동하여 사용하지 마세요.
5. **형식 준수**:
   - 전문적 톤을 유지하세요.
   - 제목·헤더 없이 **수정 완료된 본문만** 작성하세요.

위 지침에 따라, 원본 답변을 수정하여 **'자기소개서 문항'에 더욱 충실하고 사용자의 '수정 요청'이 완벽히 반영된** 최종 결과물을 작성하세요.
|>

<|assistant|>
"""
        response = model.generate_content(prompt)
        return _handle_response(response)
    except Exception as e:
        logger.error(f"자기소개서 수정 실패: {e}")
        return f"답변 수정 중 오류가 발생했습니다: {e}"
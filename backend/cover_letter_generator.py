import logging
from vertex_client import model # vertex_client.py에서 초기화된 모델 사용

logger = logging.getLogger(__name__)

# generate_content 응답을 처리하는 헬퍼 함수
def _handle_response(response):
    try:
        # Vertex AI의 응답은 response.text로 직접 접근
        return response.text
    except Exception:
        # 때로는 response.candidates[0].content.parts[0].text 형태로 올 수 있음
        try:
            return response.candidates[0].content.parts[0].text
        except (IndexError, AttributeError) as e:
            logger.error(f"응답 구문 분석 실패: {e}, 응답: {response}")
            raise ValueError("모델 응답의 형식이 예상과 다릅니다.")

def generate_cover_letter(question, jd_text, resume_text, length):
    """질문, JD, 이력서 기반으로 자기소개서 답변 생성"""
    try:
        prompt = f"""
        당신은 대한민국 최고의 자기소개서 작성 전문가입니다. 아래 정보를 바탕으로, [지원 회사]에 합격할 수 있는 자기소개서를 작성해주세요.

        ### 정보 1: 자기소개서 문항
        - "{question}"

        ### 정보 2: 지원자의 이력서 (과거 경력)
        ---이력서 시작---
        {resume_text[:2000]}
        ---이력서 끝---

        ### 정보 3: [지원 회사]의 채용 공고 (JD)
        ---채용공고 시작---
        {jd_text[:2000]}
        ---채용공고 끝---

        ### 작성 지침 및 규칙 (매우 중요!)
        1.  **[지원 회사] 식별**: [지원 회사]는 '정보 3: 채용 공고'에 명시된 회사입니다.
        2.  **목표**: '정보 2: 지원자의 이력서'에 나타난 지원자의 과거 경험과 역량을 '정보 3: [지원 회사]의 채용 공고'의 직무와 논리적으로 연결하여, 지원자가 [지원 회사]에 왜 적합한 인재인지 설득력 있게 어필해야 합니다.
        3.  **가장 중요한 규칙 (회사명 혼동 방지)**:
            -   자기소개서는 오직 [지원 회사]에 지원하는 내용이어야 합니다.
            -   '정보 2: 지원자의 이력서'에 언급된 회사(예: 뤼이드, 아토머스 등)는 지원자의 **과거 경력일 뿐**입니다.
            -   **절대로 과거 경력의 회사 이름을 마치 현재 지원하는 회사인 것처럼 작성해서는 안 됩니다.** (예: "네이버에 지원하면서 '뤼이드의 비전에 공감하여...'" 와 같이 작성하면 안 됨)
            -   이력서에 없는 경험이나 역량을 지어내서는 안 됩니다.
        4.  **출력 형식**:
            -   **제목이나 헤더(예: `## 지원 동기`)를 절대 포함하지 마세요.** 오직 자기소개서 본문만 작성해주세요.
            -   답변은 반드시 한국어 기준 **{length}자 내외**로 작성해야 합니다.
            -   격식 있고 전문적인 톤을 유지해야 합니다.

        위 규칙을 반드시 준수하여 답변을 생성해주세요.
        """
        response = model.generate_content(prompt)
        return _handle_response(response)
    except Exception as e:
        logger.error(f"자기소개서 생성 실패: {str(e)}")
        return f"답변 생성 중 오류가 발생했습니다: {e}"

def revise_cover_letter(question, jd_text, resume_text, original_answer, prompt):
    """기존 답변을 주어진 프롬프트에 따라 수정 (전체 문맥 사용)"""
    try:
        revise_prompt = f"""
        당신은 자기소개서 교정 전문가입니다. 아래 정보를 바탕으로 **원본 답변**을 **수정 요청**에 맞게 다시 작성해주세요.

        ### 정보 1: 자기소개서 문항
        - "{question}"

        ### 정보 2: 지원자의 이력서 (참고용)
        ---이력서 시작---
        {resume_text[:2000]}
        ---이력서 끝---

        ### 정보 3: 채용 공고 (참고용)
        ---채용공고 시작---
        {jd_text[:2000]}
        ---채용공고 끝---

        ### 정보 4: 수정할 원본 답변
        ---원본 답변 시작---
        {original_answer}
        ---원본 답변 끝---

        ### 정보 5: 구체적인 수정 요청 사항
        - "{prompt}"

        ### 수정 지침 및 규칙
        1.  **수정 요청 반영**: 사용자의 **수정 요청 사항**을 최우선으로 반영하여 답변을 자연스럽게 다시 작성해주세요.
        2.  **사실 기반 작성**:
            -   **수정 과정에서도 이력서에 없는 내용을 추가하거나, 지원자가 채용공고의 회사에서 근무한 것처럼 사실을 왜곡해서는 안 됩니다.**
            -   모든 내용은 이력서와 채용공고에 명시된 사실만을 바탕으로 해야 합니다.
        3.  **출력 형식**: **제목이나 헤더를 포함하지 말고**, 수정된 최종 답변만 간결하고 완결된 형태로 작성해주세요.
        4.  **핵심 내용 유지**: 원래 답변의 핵심적인 강점과 메시지는 유지하면서 문맥을 다듬어주세요.
        """
        response = model.generate_content(revise_prompt)
        return _handle_response(response)
    except Exception as e:
        logger.error(f"자기소개서 수정 실패: {str(e)}")
        return f"답변 수정 중 오류가 발생했습니다: {e}"
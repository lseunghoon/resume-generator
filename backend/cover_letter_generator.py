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

def generate_cover_letters_batch(questions, jd_text, resume_text, lengths):
    """여러 질문을 한 번의 모델 호출로 처리하여 배치 답변 생성"""
    try:
        # 질문들을 포맷팅
        questions_text = ""
        for i, (question, length) in enumerate(zip(questions, lengths), 1):
            questions_text += f"문항 {i}: {question} (목표 글자수: {length}자)\n"
        
        prompt = f"""<|system|>
당신은 대한민국 최고의 자기소개서 작성 전문가입니다. 주어진 여러 자기소개서 문항들에 대해 각각 답변을 작성해야 합니다.

중요한 규칙:
1. 각 문항에 대해 개별적으로 답변을 작성하세요
2. 답변은 제목이나 헤더 없이 본문만 작성하세요
3. 각 답변은 지정된 글자수 내외로 작성하세요
4. 이력서와 채용공고를 근거로 답변을 작성하세요
|>

<|user|>
### 질문 목록
{questions_text}

### 지원자 이력서
{resume_text}

### 채용공고
{jd_text}

### 답변 작성 요청
위 질문들에 대해 각각 답변을 작성해주세요. 반드시 다음 형식으로 작성하세요:

문항 1: [첫 번째 질문에 대한 답변]

문항 2: [두 번째 질문에 대한 답변]

문항 3: [세 번째 질문에 대한 답변]

각 답변은 제목 없이 본문만 작성하고, 지정된 글자수 내외로 작성하세요.
|>

<|assistant|>
"""
        response = model.generate_content(prompt)
        full_response = _handle_response(response)
        
        # 응답을 개별 답변으로 분리
        answers = _parse_batch_response(full_response, len(questions))
        
        return answers
    except Exception as e:
        logger.error(f"배치 자기소개서 생성 실패: {e}")
        # 에러 발생 시 각 질문에 대해 에러 메시지 반환
        return [f"답변 생성 중 오류가 발생했습니다: {e}"] * len(questions)

def _parse_batch_response(response_text, expected_count):
    """배치 응답을 개별 답변으로 분리"""
    try:
        # "문항 1:", "문항 2:" 등으로 구분된 답변들을 분리
        answers = []
        lines = response_text.split('\n')
        current_answer = []
        in_answer = False
        current_question_num = 0
        
        for line in lines:
            line = line.strip()
            
            # 새로운 문항 시작 확인
            if line.startswith('문항') and ':' in line:
                # 이전 답변 저장
                if current_answer and in_answer:
                    answers.append('\n'.join(current_answer).strip())
                
                # 새로운 문항 시작
                current_answer = []
                in_answer = False
                
                # 문항 번호 추출
                try:
                    question_num = int(line.split(':')[0].replace('문항', '').strip())
                    current_question_num = question_num
                    
                    # 답변 부분이 시작되는지 확인
                    if ':' in line and len(line.split(':', 1)) > 1:
                        answer_part = line.split(':', 1)[1].strip()
                        if answer_part:
                            current_answer.append(answer_part)
                            in_answer = True
                except:
                    pass
                    
            elif in_answer and line:
                # 답변 내용 추가
                current_answer.append(line)
        
        # 마지막 답변 추가
        if current_answer and in_answer:
            answers.append('\n'.join(current_answer).strip())
        
        # 답변 개수가 맞지 않으면 더 정교한 분할 시도
        if len(answers) != expected_count:
            logger.warning(f"예상 답변 수: {expected_count}, 실제 분리된 답변 수: {len(answers)}")
            
            # 전체 텍스트에서 "문항" 키워드로 분할 시도
            import re
            question_sections = re.split(r'문항\s*\d+\s*:', response_text)
            
            if len(question_sections) > 1:
                # 첫 번째 섹션은 제거 (질문 목록)
                answers = []
                for section in question_sections[1:]:
                    if section.strip():
                        # 불필요한 공백 제거
                        clean_answer = re.sub(r'\n+', '\n', section.strip())
                        answers.append(clean_answer)
            else:
                # 문장 단위로 균등 분할
                sentences = response_text.replace('\n', ' ').split('.')
                total_sentences = len(sentences)
                sentences_per_answer = max(1, total_sentences // expected_count)
                
                answers = []
                for i in range(expected_count):
                    start_idx = i * sentences_per_answer
                    end_idx = start_idx + sentences_per_answer if i < expected_count - 1 else total_sentences
                    answer_text = '. '.join(sentences[start_idx:end_idx]).strip()
                    if answer_text:
                        answers.append(answer_text)
                    else:
                        answers.append("답변을 생성할 수 없습니다.")
        
        # 최종 검증
        if len(answers) != expected_count:
            logger.error(f"최종 답변 수 불일치: 예상 {expected_count}, 실제 {len(answers)}")
            # 부족한 경우 기본 메시지로 채움
            while len(answers) < expected_count:
                answers.append("답변을 생성할 수 없습니다.")
            # 초과한 경우 잘라냄
            answers = answers[:expected_count]
        
        return answers
        
    except Exception as e:
        logger.error(f"배치 응답 파싱 실패: {e}")
        # 파싱 실패 시 전체 텍스트를 균등 분할
        return [response_text] * expected_count

def generate_cover_letter(question, jd_text, resume_text, length):
    """질문·JD·이력서 기반으로 자기소개서 답변 생성 (단일 질문용)"""
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
        return f"수정 중 오류가 발생했습니다: {e}"
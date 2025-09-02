import json
import os
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

vertexai.init(project="gen-lang-client-0050370482") # 여기에 실제 프로젝트 ID를 입력하세요.

print("Step 1: 명확하게 구분된 기준 질문 정의")
canonical_questions = [
    {"key": "strength_weakness", "question": "성격의 장점, 단점, 강점, 약점"},
    {"key": "aspiration", "question": "입사 후 포부, 미래 계획, 커리어 목표"},
    {"key": "job_experience", "question": "직무 수행 경험, 프로젝트, 업무 역량"},
    {"key": "failure_experience", "question": "실패, 어려움, 역경, 문제 해결, 극복"},
    {"key": "motivation", "question": "지원 동기, 회사에 지원하는 이유, 관심을 가지게 된 계기"},
    {"key": "growth_process", "question": "성장 과정, 가치관, 인생관, 영향을 준 인물"}
]

print("Step 2: Vertex AI 임베딩 모델 로드 (text-embedding-005)")
model = TextEmbeddingModel.from_pretrained("text-embedding-005")

print("Step 3: 각 기준 질문에 대한 임베딩 벡터 생성 (문서 모드)")
embeddings_data = []
for item in canonical_questions:
    try:
        # '검색 대상 문서' 모드로 임베딩을 생성합니다.
        # TextEmbeddingInput 객체를 사용하여 텍스트와 task_type을 함께 전달합니다.
        inputs = [TextEmbeddingInput(text=item["question"], task_type="RETRIEVAL_DOCUMENT")]
        response = model.get_embeddings(inputs)
        vector = response[0].values
        
        embeddings_data.append({"key": item["key"], "question": item["question"], "vector": vector})
        print(f" -> 성공: '{item['key']}' 유형의 임베딩 생성 완료.")
    except Exception as e:
        print(f" -> 실패: '{item['key']}' 유형 처리 중 오류 발생: {e}")
        exit()

output_filename = "canonical_embeddings.json"
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(embeddings_data, f, ensure_ascii=False, indent=2)

print(f"\n성공! '{output_filename}' 파일을 backend/services/ 폴더로 이동해주세요.")
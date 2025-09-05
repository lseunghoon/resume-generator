import json
import os
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
import numpy as np # 벡터 평균 계산을 위해 NumPy 라이브러리를 임포트합니다.

# --------------------------------------------------------------------------
# Vertex AI 초기화
# --------------------------------------------------------------------------
# gcloud auth application-default login 명령어로 인증이 필요할 수 있습니다.
try:
    vertexai.init(project="gen-lang-client-0050370482") # 실제 프로젝트 ID를 입력하세요.
except Exception as e:
    print(f"Vertex AI 초기화 중 오류 발생: {e}")
    print("gcloud CLI 인증을 확인하세요. (gcloud auth application-default login)")
    exit()

# --------------------------------------------------------------------------
# Step 1: 카테고리별 기준 질문 정의 (다중 문장 방식)
# --------------------------------------------------------------------------
# 각 카테고리의 의미적 '영역'을 정의하기 위해 여러 개의 대표 질문을 리스트로 정의합니다.
# 이렇게 하면 분류기의 안정성과 정확도가 크게 향상됩니다.
print("Step 1: 명확하게 구분된 기준 질문 정의 (다중 문장 방식)")
canonical_questions = [
    {
        "key": "strength_weakness", 
        "questions": [
            "당신의 성격의 장점과 단점은 무엇이라고 생각하나요?",
            "자신의 강점과 약점에 대해 설명해주세요.",
            "지원자님의 강점 한 가지와 보완점에 대해 말씀해주세요.",
            "본인의 가장 큰 장점은 무엇이며, 직무 수행에 어떻게 기여할 수 있나요?"
        ]
    },
    {
        "key": "aspiration", 
        "questions": [
            "우리 회사에 입사한 후의 포부나 이루고 싶은 목표에 대해 말씀해주세요.",
            "입사 후 5년, 10년 뒤의 커리어 계획은 무엇인가요?",
            "회사 생활을 통해 어떻게 성장하고 기여하고 싶으신가요?",
            "우리 회사에서 최종적으로 이루고 싶은 꿈은 무엇입니까?"
        ]
    },
    {
        "key": "job_experience", 
        "questions": [
            "지원하신 직무와 관련하여 가장 의미 있었던 경험은 무엇인가요?",
            "프로젝트를 수행하면서 본인의 역량을 발휘했던 사례를 소개해주세요.",
            "직무 수행 경험 중 가장 성공적이었던 것은 무엇입니까?",
            "가장 기억에 남는 직무 관련 경험에 대해 구체적으로 설명해주세요."
        ]
    },
    {
        "key": "failure_experience", 
        "questions": [
            "지금까지 겪었던 가장 큰 어려움이나 실패는 무엇이며, 어떻게 극복했나요?",
            "도전적인 목표를 세우고 실행했지만 실패했던 경험이 있나요?",
            "팀원과의 갈등이나 문제를 해결했던 경험에 대해 말씀해주세요.",
            "예상치 못한 문제에 부딪혔을 때 어떻게 해결했는지 구체적인 사례를 들어주세요."
        ]
    },
    {
        "key": "motivation", 
        "questions": [
            "우리 회사와 지원하신 직무에 관심을 가지게 된 계기는 무엇인가요?",
            "왜 다른 회사가 아닌 우리 회사에 지원하셨나요?",
            "지원 동기를 구체적인 경험과 연결하여 설명해주세요.",
            "수많은 기업 중에서 특별히 우리 회사에 지원한 이유가 궁금합니다."
        ]
    },
    {
        "key": "growth_process", 
        "questions": [
            "자신의 성장 과정에 대해 설명하고, 가치관에 가장 큰 영향을 미친 경험이 있다면 알려주세요.",
            "본인의 인생관이나 좌우명은 무엇이며, 그렇게 생각하게 된 계기가 있나요?",
            "살아오면서 가장 중요하게 생각하는 가치는 무엇입니까?",
            "자신이 어떤 사람인지 성장 과정을 바탕으로 설명해주세요."
        ]
    }
]

# --------------------------------------------------------------------------
# Step 2: Vertex AI 임베딩 모델 로드
# --------------------------------------------------------------------------
print("\nStep 2: Vertex AI 임베딩 모델 로드 (text-multilingual-embedding-002)")
try:
    model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")
except Exception as e:
    print(f"임베딩 모델 로딩 실패: {e}")
    exit()

# --------------------------------------------------------------------------
# Step 3: 각 카테고리의 '중심 벡터(Centroid)' 생성
# --------------------------------------------------------------------------
print("\nStep 3: 각 카테고리에 대한 임베딩 벡터 생성 및 평균(중심점) 계산")
embeddings_data = []
for item in canonical_questions:
    key = item['key']
    questions = item['questions']
    
    try:
        # 각 카테고리에 속한 모든 질문들의 벡터를 저장할 리스트
        vectors = []
        
        # '검색 대상 문서' 모드로 각 질문의 임베딩을 생성합니다.
        # 한 번에 여러 문장을 API에 보내는 것이 더 효율적입니다.
        inputs = [TextEmbeddingInput(text=q, task_type="RETRIEVAL_DOCUMENT") for q in questions]
        response = model.get_embeddings(inputs)
        
        for emb in response:
            vectors.append(emb.values)
        
        # [핵심 로직]
        # NumPy를 사용하여 해당 카테고리의 모든 벡터들의 평균 벡터(중심점)를 계산합니다.
        # 이 중심 벡터가 해당 카테고리를 대표하는 가장 안정적인 값이 됩니다.
        centroid_vector = np.array(vectors).mean(axis=0).tolist()
        
        # 대표 질문은 JSON 파일에서 사람이 읽기 쉽도록 리스트의 첫 번째 질문으로 저장합니다.
        representative_question = questions[0]
        embeddings_data.append({
            "key": key,
            "question": representative_question, 
            "vector": centroid_vector
        })
        
        print(f" -> 성공: '{key}' 유형의 중심 벡터 생성 완료. ({len(questions)}개 문장 사용)")
        
    except Exception as e:
        print(f" -> 실패: '{key}' 유형 처리 중 오류 발생: {e}")
        exit()

# --------------------------------------------------------------------------
# Step 4: 결과 파일 저장
# --------------------------------------------------------------------------
output_filename = "canonical_embeddings.json"
try:
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(embeddings_data, f, ensure_ascii=False, indent=2)
    print(f"\n성공! '{output_filename}' 파일을 backend/services/ 폴더로 이동해주세요.")
except Exception as e:
    print(f"\n파일 저장 실패: {e}")
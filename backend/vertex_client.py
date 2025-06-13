import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

# .env 파일에서 환경 변수 로드
load_dotenv()

# Vertex AI 초기화
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")

# 환경 변수가 설정되지 않았을 경우를 대비한 검증
if not PROJECT_ID or not LOCATION:
    raise ValueError("환경 변수 파일(.env)에 PROJECT_ID와 LOCATION을 반드시 설정해야 합니다.")

vertexai.init(project=PROJECT_ID, location=LOCATION)

# 애플리케이션 전체에서 공유될 Gemini 모델 인스턴스
model = GenerativeModel("gemini-2.0-flash-001") 
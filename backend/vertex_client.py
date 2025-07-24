"""
Vertex AI 클라이언트 설정 (리팩토링 버전)
"""

import vertexai
from vertexai.generative_models import GenerativeModel
from config.settings import get_vertex_ai_config

# Vertex AI 설정 가져오기
config = get_vertex_ai_config()

# Vertex AI 초기화
vertexai.init(project=config['project_id'], location=config['location'])

# 애플리케이션 전체에서 공유될 Gemini 모델 인스턴스
model = GenerativeModel(config['model_name']) 
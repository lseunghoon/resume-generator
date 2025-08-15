# sseojum/backend/Dockerfile
# Python 3.11 슬림 버전을 기반으로 합니다.
FROM python:3.11-slim

# Python 실행 환경 최적화
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 작업 디렉토리 설정
WORKDIR /app

# ML/이미지 라이브러리 실행에 필요한 시스템 라이브러리를 미리 설치합니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    curl \
    libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Python 라이브러리를 설치합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드를 복사합니다.
COPY . .

# Gunicorn 프로덕션 서버를 실행합니다.
# Fly.io가 동적으로 주는 $PORT를 사용하고, 없으면 8080을 사용합니다.
# 워커/스레드/타임아웃 설정을 통해 안정성을 높입니다.
CMD ["bash", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 1 --timeout 120 app:app"]
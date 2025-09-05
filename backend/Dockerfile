# sseojum/backend/Dockerfile (Multi-stage Build 적용 버전)

# --- 스테이지 1: 빌더 (Builder) ---
# 라이브러리 설치에 필요한 모든 도구를 포함하는 무거운 환경
FROM python:3.11-slim as builder

# Python 실행 환경 최적화
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 빌드에 필요한 시스템 라이브러리 설치
# build-essential 같은 무거운 도구들은 이 스테이지에만 존재하게 됩니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 가상환경 생성 및 활성화 경로 설정
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# requirements.txt를 먼저 복사하여 pip install 캐시를 활용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- 스테이지 2: 최종 이미지 (Final Image) ---
# 실제 애플리케이션 실행에 필요한 최소한의 환경
FROM python:3.11-slim

# Python 실행 환경 최적화
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 실행에 필요한 최소한의 시스템 라이브러리만 설치
# build-essential 같은 무거운 패키지는 여기에 포함되지 않습니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# [핵심] 빌더 스테이지에서 설치된 가상환경(라이브러리)만 복사해옵니다.
COPY --from=builder /opt/venv /opt/venv

# 가상환경 경로를 PATH에 추가
ENV PATH="/opt/venv/bin:$PATH"

# 소스 코드를 복사합니다. (.dockerignore 덕분에 .venv 등은 제외됩니다)
COPY . .

# Gunicorn 프로덕션 서버를 실행합니다.
CMD ["bash", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 1 --timeout 120 app:app"]
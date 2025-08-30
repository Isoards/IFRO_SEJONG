FROM python:3.11-slim

# 한글 지원을 위한 로케일 설정
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV LC_CTYPE=ko_KR.UTF-8

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    locales \
    && rm -rf /var/lib/apt/lists/*

# 한글 로케일 생성
RUN locale-gen ko_KR.UTF-8

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 엔트리포인트 스크립트 실행 권한 부여
RUN chmod +x docker-entrypoint.sh

# 필요한 디렉토리 생성
RUN mkdir -p /app/data /app/vector_store /app/logs /app/models

# 포트 노출
EXPOSE 8008

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV MODEL_TYPE=ollama
ENV MODEL_NAME=qwen2:1.5b
ENV EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
ENV OLLAMA_HOST=http://ollama:11434

# 엔트리포인트 스크립트 실행
ENTRYPOINT ["./docker-entrypoint.sh"]

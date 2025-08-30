#!/bin/bash

echo "🚀 Docker Compose 설정 테스트 시작..."

# 1. 기존 컨테이너 정리
echo "📦 기존 컨테이너 정리 중..."
docker-compose down -v

# 2. 이미지 빌드
echo "🔨 이미지 빌드 중..."
docker-compose build

# 3. 서비스 시작
echo "▶️  서비스 시작 중..."
docker-compose up -d

# 4. 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
echo "⏳ Ollama 모델 다운로드 대기 중... (최대 20분)"
for i in {1..40}; do
    echo "진행률: $((i * 2.5))% ($i/40)"
    docker-compose ps
    echo "---"
    sleep 30
done

# 5. Ollama 서비스 로그 확인
echo "📋 Ollama 서비스 로그 확인 중..."
docker-compose logs ollama

# 6. 모델 설치 확인
echo "🤖 모델 설치 확인 중..."
docker exec ollama ollama list

# 7. Healthcheck 상태 확인
echo "🏥 Healthcheck 상태 확인 중..."
docker-compose ps

echo "✅ 테스트 완료!"
echo ""
echo "다음 명령어로 로그를 확인할 수 있습니다:"
echo "  docker-compose logs -f ollama"
echo "  docker-compose logs -f chatbot"

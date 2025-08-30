#!/bin/bash

# 스크립트에 실행 권한 부여
chmod +x /ollama-entrypoint.sh

# 오류 발생 시 스크립트 중단
set -e

echo "=== Ollama 서비스 시작 ==="
ollama serve &

# Ollama 서비스가 완전히 시작될 때까지 대기
echo "Ollama 서비스가 준비될 때까지 대기 중..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if ollama list >/dev/null 2>&1; then
        echo "Ollama 서비스가 준비되었습니다!"
        break
    fi
    echo "시도 $((attempt + 1))/$max_attempts - Ollama 서비스 대기 중..."
    sleep 10
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "오류: Ollama 서비스가 시작되지 않았습니다!"
    exit 1
fi

# 현재 모델 목록 확인
echo "=== 현재 모델 목록 확인 ==="
ollama list

# 필요한 모델이 없으면 다운로드
if ! ollama list | grep -q "qwen2:1.5b"; then
    echo "=== qwen2:1.5b 모델 다운로드 시작 ==="
    ollama pull qwen2:1.5b
    ollama pull sqlcoder:7b
    
    # 다운로드 완료 확인
    echo "모델 다운로드 완료 확인 중..."
    if ollama list | grep -q "qwen2:1.5b"; then
        echo "✅ qwen2:1.5b 모델 다운로드 완료!"
    else
        echo "❌ 오류: 모델 다운로드가 실패했습니다!"
        exit 1
    fi
else
    echo "✅ qwen2:1.5b 모델이 이미 존재합니다!"
fi

# 모델이 실제로 사용 가능한지 테스트
echo "=== 모델 사용 가능성 테스트 ==="
test_response=$(ollama run qwen2:1.5b "Hello" 2>/dev/null | head -1)
if [ -n "$test_response" ]; then
    echo "✅ 모델 테스트 성공: $test_response"
else
    echo "❌ 오류: 모델 테스트 실패!"
    exit 1
fi

# 최종 모델 목록 출력
echo "=== 최종 모델 목록 ==="
ollama list

echo "=== Ollama 설정 완료! 챗봇 서버 시작 준비됨 ==="

# 메인 프로세스 대기
wait

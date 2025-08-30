#!/bin/bash

# 한글 지원 설정
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8
export LC_CTYPE=ko_KR.UTF-8

# 스크립트 실행 권한 부여
chmod +x /ollama-entrypoint.sh
chmod +x /ollama-healthcheck.sh

# 오류 발생 시 스크립트 중단
set -e

echo "=== Ollama 서비스 시작 ==="
ollama serve &

# Ollama 서비스가 완전히 작동할 때까지 대기
echo "Ollama 서비스가 준비될 때까지 대기 중..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if ollama list >/dev/null 2>&1; then
        echo "Ollama 서비스가 준비되었습니다!"
        break
    fi
    echo "시도 $((attempt + 1))/$max_attempts - Ollama 서비스 대기 중..."
    sleep 15
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "경고: Ollama 서비스 시간 초과, 계속 진행합니다..."
fi

# 현재 모델 목록 확인
echo "=== 현재 모델 목록 확인 ==="
ollama list

# 필요한 모델들을 다운로드
echo "=== 필요한 모델들 확인 및 다운로드 ==="

# qwen2:1.5b 모델 확인 및 다운로드
if ! ollama list | grep -q "qwen2:1.5b"; then
    echo "=== qwen2:1.5b 모델 다운로드 시작 ==="
    ollama pull qwen2:1.5b
    
    # 다운로드 완료 확인
    echo "qwen2:1.5b 모델 다운로드 완료 확인 중..."
    if ollama list | grep -q "qwen2:1.5b"; then
        echo "✅ qwen2:1.5b 모델 다운로드 완료!"
    else
        echo "❌ 오류: qwen2:1.5b 모델 다운로드가 실패했습니다!"
        exit 1
    fi
else
    echo "✅ qwen2:1.5b 모델이 이미 존재합니다"
fi

# sqlcoder:7b 모델 확인 및 다운로드 (SQL 질의용)
if ! ollama list | grep -q "sqlcoder:7b"; then
    echo "=== sqlcoder:7b 모델 다운로드 시작 ==="
    ollama pull sqlcoder:7b
    
    # 다운로드 완료 확인
    echo "sqlcoder:7b 모델 다운로드 완료 확인 중..."
    if ollama list | grep -q "sqlcoder:7b"; then
        echo "✅ sqlcoder:7b 모델 다운로드 완료!"
    else
        echo "❌ 오류: sqlcoder:7b 모델 다운로드가 실패했습니다!"
        exit 1
    fi
else
    echo "✅ sqlcoder:7b 모델이 이미 존재합니다"
fi

# 모델의 제대로 사용 가능한지 테스트 (선택사항)
echo "=== 모델 사용 가능성 테스트 ==="
if ollama list | grep -q "qwen2:1.5b"; then
    test_response=$(ollama run qwen2:1.5b "Hello" 2>/dev/null | head -1)
    if [ -n "$test_response" ]; then
        echo "✅ 모델 테스트 성공: $test_response"
    else
        echo "⚠️ 경고: 모델 테스트 실패, 계속 진행합니다..."
    fi
else
    echo "⚠️ 경고: qwen2:1.5b 모델이 없습니다, 계속 진행합니다..."
fi

# 최종 모델 목록 출력
echo "=== 최종 모델 목록 ==="
ollama list

echo "=== Ollama 설정 완료! 챗봇 서버 시작 준비됨 ==="

# 모델 준비 완료 신호 파일 생성
echo "ready" > /tmp/ollama_ready

# 메인 프로세스 대기
wait

#!/bin/bash

# Ollama 서비스가 완전히 준비되었는지 확인하는 healthcheck 스크립트

# 1. Ollama 서비스가 실행 중인지 확인
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "Ollama 서비스가 실행되지 않았습니다."
    exit 1
fi

# 2. Ollama API가 응답하는지 확인 (ollama list 명령어로 확인)
if ! ollama list > /dev/null 2>&1; then
    echo "Ollama API가 응답하지 않습니다."
    exit 1
fi

# 3. 필요한 모델들이 설치되어 있는지 확인
if ! ollama list | grep -q "qwen2:1.5b"; then
    echo "qwen2:1.5b 모델이 설치되지 않았습니다."
    exit 1
fi

# 4. 모델이 실제로 사용 가능한지 간단한 테스트
if ! ollama run qwen2:1.5b "test" > /dev/null 2>&1; then
    echo "qwen2:1.5b 모델이 사용할 수 없습니다."
    exit 1
fi

# 5. 준비 완료 신호 파일 확인
if [ ! -f "/tmp/ollama_ready" ]; then
    echo "Ollama 모델 다운로드가 아직 완료되지 않았습니다."
    exit 1
fi

echo "Ollama 서비스가 정상적으로 작동합니다."
exit 0

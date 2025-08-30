#!/bin/bash
set -e

echo "🚀 IFRO 챗봇 서버 시작 중..."

# 환경 변수 설정
export PYTHONPATH=/app
export MODEL_TYPE=${MODEL_TYPE:-ollama}
export MODEL_NAME=${MODEL_NAME:-mistral:latest}
export EMBEDDING_MODEL=${EMBEDDING_MODEL:-jhgan/ko-sroberta-multitask}

# 로그 디렉토리 생성
mkdir -p /app/logs

echo "📋 환경 설정:"
echo "  - MODEL_TYPE: $MODEL_TYPE"
echo "  - MODEL_NAME: $MODEL_NAME"
echo "  - EMBEDDING_MODEL: $EMBEDDING_MODEL"
echo "  - PYTHONPATH: $PYTHONPATH"

# 1단계: 의존성 확인
echo "🔍 1단계: 의존성 확인 중..."
python -c "
import sys
required_packages = ['sentence_transformers', 'torch', 'transformers', 'numpy', 'sklearn']
missing_packages = []

for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
        print(f'✅ {package}')
    except ImportError:
        print(f'❌ {package} (설치 필요)')
        missing_packages.append(package)

if missing_packages:
    print(f'❌ 누락된 패키지: {missing_packages}')
    sys.exit(1)
else:
    print('✅ 모든 의존성이 설치되어 있습니다.')
"

if [ $? -ne 0 ]; then
    echo "❌ 의존성 확인 실패. 컨테이너를 종료합니다."
    exit 1
fi

# 2단계: SBERT 모델 자동 다운로드
echo "🤖 2단계: SBERT 모델 자동 다운로드 중..."
python setup_sbert.py

if [ $? -ne 0 ]; then
    echo "❌ SBERT 모델 다운로드 실패. 컨테이너를 종료합니다."
    exit 1
fi

echo "✅ SBERT 모델 다운로드 완료 (한국어 특화 모델 우선 사용)"

# 3단계: 의도 분류기 초기화
echo "🎯 3단계: 의도 분류기 초기화 중..."
python -c "
import sys
sys.path.append('/app')

try:
    from core.intent_classifier import create_intent_classifier
    classifier = create_intent_classifier('traffic')
    print('✅ 의도 분류기 초기화 완료')
except Exception as e:
    print(f'❌ 의도 분류기 초기화 실패: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 의도 분류기 초기화 실패. 컨테이너를 종료합니다."
    exit 1
fi

# 4단계: Ollama 서버 대기
echo "⏳ 4단계: Ollama 서버 대기 중..."
python -c "
import sys
import os
import time
import requests

def check_ollama_server():
    try:
        ollama_host = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
        response = requests.get(f'{ollama_host}/api/tags', timeout=5)
        return response.status_code == 200
    except:
        return False

def wait_for_ollama_server(max_wait=60):
    print('Ollama 서버 시작 대기 중...')
    for i in range(max_wait):
        if check_ollama_server():
            print('✅ Ollama 서버가 준비되었습니다.')
            return True
        time.sleep(1)
        if i % 10 == 0:
            print(f'Ollama 서버 대기 중... ({i}/{max_wait}초)')
    
    print('❌ Ollama 서버가 시작되지 않았습니다.')
    return False

if not wait_for_ollama_server():
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Ollama 서버 연결 실패. 컨테이너를 종료합니다."
    exit 1
fi

# 5단계: Ollama 모델 다운로드
echo "📥 5단계: Ollama 모델 다운로드 중..."
python -c "
import sys
import os
import requests
import time

def download_ollama_model(model_name):
    try:
        print(f'모델 다운로드 시작: {model_name}')
        ollama_host = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
        
        # 모델이 이미 설치되어 있는지 확인
        try:
            response = requests.get(f'{ollama_host}/api/tags', timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                for model in models:
                    if model.get('name') == model_name:
                        print(f'✅ 모델 {model_name}이 이미 설치되어 있습니다.')
                        return True
        except Exception as e:
            print(f'⚠️ 모델 목록 확인 실패: {e}')
        
        # 모델 다운로드
        print(f'모델 {model_name} 다운로드 중...')
        download_data = {'name': model_name}
        
        response = requests.post(
            f'{ollama_host}/api/pull',
            json=download_data,
            timeout=600,
            stream=True
        )
        
        if response.status_code == 200:
            print(f'✅ 모델 {model_name} 다운로드 완료!')
            return True
        else:
            print(f'❌ 모델 다운로드 실패: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ 모델 다운로드 중 오류: {e}')
        return False

model_name = os.getenv('MODEL_NAME', 'mistral:latest')
if not download_ollama_model(model_name):
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Ollama 모델 다운로드 실패. 컨테이너를 종료합니다."
    exit 1
fi

# 6단계: 서버 시작
echo "🚀 6단계: 챗봇 서버 시작 중..."
echo "============================================================"
echo "🎉 모든 초기화가 완료되었습니다!"
echo "챗봇 서버가 시작됩니다..."
echo "============================================================"

# 서버 실행
exec python run_server.py

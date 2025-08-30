#!/usr/bin/env python3
"""
PDF QA 시스템 서버 실행 스크립트

이 스크립트는 Dual Pipeline이 통합된 PDF QA 시스템을 서버 모드로 실행합니다.
"""

import sys
import os
import logging
import subprocess
import time
import requests
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from api.endpoints import app, initialize_system

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_ollama_server():
    """Ollama 서버가 실행 중인지 확인"""
    try:
        # Docker 네트워크에서는 서비스 이름으로 접근
        ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def wait_for_ollama_server(max_wait=60):
    """Ollama 서버가 시작될 때까지 대기"""
    logger.info("Ollama 서버 시작 대기 중...")
    for i in range(max_wait):
        if check_ollama_server():
            logger.info("Ollama 서버가 준비되었습니다.")
            return True
        time.sleep(1)
        if i % 10 == 0:
            logger.info(f"Ollama 서버 대기 중... ({i}/{max_wait}초)")
    
    logger.error("Ollama 서버가 시작되지 않았습니다.")
    return False

def download_ollama_model(model_name):
    """Ollama 모델 다운로드 (API 사용)"""
    try:
        logger.info(f"모델 다운로드 시작: {model_name}")
        
        # Ollama API 엔드포인트
        ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        
        # 모델이 이미 설치되어 있는지 확인
        try:
            response = requests.get(f"{ollama_host}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    if model.get("name") == model_name:
                        logger.info(f"모델 {model_name}이 이미 설치되어 있습니다.")
                        return True
        except Exception as e:
            logger.warning(f"모델 목록 확인 실패: {e}")
        
        # 모델 다운로드
        logger.info(f"모델 {model_name} 다운로드 중...")
        download_data = {"name": model_name}
        
        response = requests.post(
            f"{ollama_host}/api/pull",
            json=download_data,
            timeout=600,  # 10분 타임아웃
            stream=True
        )
        
        if response.status_code == 200:
            logger.info(f"모델 {model_name} 다운로드 완료!")
            return True
        else:
            logger.error(f"모델 다운로드 실패: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"모델 다운로드 시간 초과: {model_name}")
        return False
    except Exception as e:
        logger.error(f"모델 다운로드 중 오류: {e}")
        return False

def main():
    """서버 실행 메인 함수 (최적화 버전)"""
    
    print("=" * 60)
    print("IFRO 챗봇 시스템 서버 시작")
    print("최적화된 버전 - 빠른 응답!")
    print("=" * 60)
    print()
    print("기능:")
    print("- SBERT 라우팅: 질문을 적절한 파이프라인으로 분기")
    print("- 규칙 기반 SQL 추출: LLM 없이 빠른 SQL 생성")
    print("- 인메모리 캐싱: 반복 질문 즉시 응답")
    print()
    print("API 문서: http://localhost:8008/docs")
    print("서버 주소: http://localhost:8008")
    print()
    print("=" * 60)
    
    # 환경 변수에서 설정 가져오기
    model_type = os.getenv("MODEL_TYPE", "ollama")
    model_name = os.getenv("MODEL_NAME", "qwen2:1.5b")
    embedding_model = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")
    
    # Ollama 모델 자동 다운로드
    if model_type == "ollama":
        logger.info("Ollama 모델 자동 다운로드 시작...")
        
        # Ollama 서버 대기
        if not wait_for_ollama_server():
            logger.error("Ollama 서버를 찾을 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            sys.exit(1)
        
        # 모델 다운로드
        if not download_ollama_model(model_name):
            logger.error(f"모델 {model_name} 다운로드에 실패했습니다.")
            sys.exit(1)
        
        logger.info("모델 다운로드 완료!")
    
    try:
        logger.info("시스템 초기화 및 자동 PDF 업로드 시작...")
        
        # 시스템 초기화 (PDF 자동 업로드 포함)
        initialize_system()
        
        logger.info("API 서버를 시작합니다...")
        
        # FastAPI 서버 실행
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8008)
        
    except KeyboardInterrupt:
        logger.info("서버가 중단되었습니다.")
    except Exception as e:
        logger.error(f"서버 실행 중 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

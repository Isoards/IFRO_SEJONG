#!/usr/bin/env python3
"""
PDF QA 시스템 설치 스크립트
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 이상이 필요합니다.")
        return False
    logger.info(f"Python 버전 확인: {sys.version}")
    return True

def install_requirements():
    """의존성 설치"""
    try:
        logger.info("의존성 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✅ 의존성 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 의존성 설치 실패: {e}")
        return False

def setup_directories():
    """필요한 디렉토리 생성"""
    directories = [
        "data",
        "logs",
        "vector_store",
        "models"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"디렉토리 생성: {directory}")

def main():
    """메인 설치 함수"""
    logger.info("=" * 50)
    logger.info("PDF QA 시스템 설치 시작")
    logger.info("=" * 50)
    
    # 1. Python 버전 확인
    if not check_python_version():
        sys.exit(1)
    
    # 2. 디렉토리 설정
    setup_directories()
    
    # 3. 의존성 설치
    if not install_requirements():
        sys.exit(1)
    
    logger.info("=" * 50)
    logger.info("✅ 설치 완료!")
    logger.info("=" * 50)
    logger.info("시스템 시작: python main.py")
    logger.info("웹 서버 시작: python run_server.py")

if __name__ == "__main__":
    main()

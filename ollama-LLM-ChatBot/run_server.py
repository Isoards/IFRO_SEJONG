#!/usr/bin/env python3
"""
IFRO_SEJONG AI 챗봇 시스템 서버

이 스크립트는 Dual Pipeline이 통합된 AI 챗봇 시스템을 
FastAPI 서버 모드로 실행합니다.
"""

import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from api.endpoints import app, initialize_system

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ChatbotServer:
    """챗봇 서버 관리 클래스"""
    
    def __init__(self):
        self.model_type = os.getenv("MODEL_TYPE", "local")
        self.model_name = os.getenv("MODEL_NAME", "monologg/koelectra-small-v3-discriminator")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")
        
    def check_local_model_available(self) -> bool:
        """로컬 모델이 사용 가능한지 확인"""
        try:
            from transformers import AutoTokenizer, AutoModel
            AutoTokenizer.from_pretrained(self.model_name)
            AutoModel.from_pretrained(self.model_name)
            return True
        except Exception as e:
            logger.warning(f"로컬 모델 확인 실패: {e}")
            return False
    
    def wait_for_local_model(self, max_wait: int = 60) -> bool:
        """로컬 모델이 준비될 때까지 대기"""
        logger.info("로컬 모델 준비 대기 중...")
        for i in range(max_wait):
            if self.check_local_model_available():
                logger.info("로컬 모델이 준비되었습니다.")
                return True
            time.sleep(1)
            if i % 10 == 0:
                logger.info(f"로컬 모델 대기 중... ({i}/{max_wait}초)")
        
        logger.error("로컬 모델이 준비되지 않았습니다.")
        return False
    
    def print_startup_banner(self):
        """시작 배너 출력"""
        print("=" * 60)
        print("🚀 IFRO_SEJONG AI 챗봇 시스템 서버 시작")
        print("🤖 최적화된 버전 - 빠른 응답!")
        print("=" * 60)
        print()
        print("✨ 주요 기능:")
        print("   • SBERT 라우팅: 질문을 적절한 파이프라인으로 분기")
        print("   • 규칙 기반 SQL 추출: LLM 없이 빠른 SQL 생성")
        print("   • 인메모리 캐싱: 반복 질문 즉시 응답")
        print("   • 하이브리드 검색: 키워드 + 의미 기반 검색")
        print()
        print("🌐 서비스 정보:")
        print("   • API 문서: http://localhost:8008/docs")
        print("   • 서버 주소: http://localhost:8008")
        print("   • 헬스체크: http://localhost:8008/health")
        print()
        print("=" * 60)
    
    def initialize_system(self) -> bool:
        """시스템 초기화"""
        try:
            logger.info("시스템 초기화 및 자동 PDF 업로드 시작...")
            
            # 시스템 초기화 (PDF 자동 업로드 포함)
            initialize_system()
            
            logger.info("✅ 시스템 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"시스템 초기화 실패: {e}")
            return False
    
    def start_server(self):
        """FastAPI 서버 시작"""
        try:
            logger.info("API 서버를 시작합니다...")
            
            # uvicorn 서버 실행
            import uvicorn
            uvicorn.run(
                app, 
                host="0.0.0.0", 
                port=8008,
                log_level="info",
                access_log=True
            )
            
        except KeyboardInterrupt:
            logger.info("서버가 중단되었습니다.")
        except Exception as e:
            logger.error(f"서버 실행 중 오류: {e}")
            sys.exit(1)
    
    def run(self):
        """메인 실행 로직"""
        # 시작 배너 출력
        self.print_startup_banner()
        
        # 로컬 모델 준비 확인
        if self.model_type == "local":
            logger.info("로컬 모델 준비 확인 중...")
            
            if not self.wait_for_local_model():
                logger.error("로컬 모델을 찾을 수 없습니다. 모델이 다운로드되었는지 확인해주세요.")
                sys.exit(1)
            
            logger.info("✅ 로컬 모델 준비 완료!")
        
        # 시스템 초기화
        if not self.initialize_system():
            logger.error("시스템 초기화에 실패했습니다.")
            sys.exit(1)
        
        # 서버 시작
        self.start_server()


def main():
    """메인 함수"""
    # 로그 디렉토리 생성
    Path("logs").mkdir(exist_ok=True)
    
    # 서버 인스턴스 생성 및 실행
    server = ChatbotServer()
    server.run()


if __name__ == "__main__":
    main()

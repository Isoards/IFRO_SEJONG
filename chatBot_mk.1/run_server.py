#!/usr/bin/env python3
"""
PDF QA 시스템 서버 실행 스크립트

이 스크립트는 Dual Pipeline이 통합된 PDF QA 시스템을 서버 모드로 실행합니다.
"""

import sys
import os
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from main import PDFQASystem

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

def main():
    """서버 실행 메인 함수"""
    
    print("=" * 60)
    print("PDF QA 시스템 서버 시작")
    print("Dual Pipeline 기능이 통합되었습니다!")
    print("=" * 60)
    print()
    print("기능:")
    print("- 문서 검색 파이프라인: PDF 내용 기반 질문 답변")
    print("- SQL 질의 파이프라인: 데이터베이스 스키마 기반 SQL 생성")
    print("- 하이브리드 파이프라인: 두 파이프라인 결과 통합")
    print()
    print("API 문서: http://localhost:8008/docs")
    print("서버 주소: http://localhost:8008")
    print()
    print("=" * 60)
    
    # 환경 변수에서 설정 가져오기
    model_type = os.getenv("MODEL_TYPE", "ollama")
    model_name = os.getenv("MODEL_NAME", "mistral:latest")
    embedding_model = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")
    
    # 시스템 초기화
    system = PDFQASystem(
        model_type=model_type,
        model_name=model_name,
        embedding_model=embedding_model
    )
    
    try:
        # 컴포넌트 초기화
        logger.info("시스템 초기화 중...")
        if not system.initialize_components():
            logger.error("시스템 초기화 실패")
            sys.exit(1)
        
        logger.info("시스템 초기화 완료!")
        logger.info("API 서버를 시작합니다...")
        
        # 서버 실행
        from api.endpoints import run_server
        run_server(host="0.0.0.0", port=8008, debug=False)
        
    except KeyboardInterrupt:
        logger.info("서버가 중단되었습니다.")
    except Exception as e:
        logger.error(f"서버 실행 중 오류: {e}")
        sys.exit(1)
    finally:
        system.cleanup()

if __name__ == "__main__":
    main()

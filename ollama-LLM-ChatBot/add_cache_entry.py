#!/usr/bin/env python3
"""
캐시에 특정 질문-답변 쌍을 추가하는 스크립트
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.fast_cache import get_question_cache
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_cache_entry():
    """캐시에 질문-답변 쌍 추가"""
    
    # 질문-답변 캐시 가져오기
    question_cache = get_question_cache()
    
    # 추가할 질문과 답변
    question = "챗봇에게 평일 18시에 가장 막히는곳이 어디인가요?"
    answer = "소담동 새샘교차로입니다."
    
    # 캐시에 저장
    question_cache.put(
        query=question,
        data={
            "answer": answer,
            "type": "cached_response",
            "confidence": 1.0,
            "source": "manual_cache_entry"
        },
        context="traffic_congestion",
        ttl=86400  # 24시간 TTL
    )
    
    logger.info(f"캐시에 질문-답변 쌍 추가 완료:")
    logger.info(f"질문: {question}")
    logger.info(f"답변: {answer}")
    
    # 캐시 통계 출력
    stats = question_cache.get_stats()
    logger.info(f"캐시 통계: {stats}")
    
    # 저장된 데이터 확인
    cached_data = question_cache.get(question, "traffic_congestion")
    if cached_data:
        logger.info(f"캐시 저장 확인 성공: {cached_data}")
    else:
        logger.error("캐시 저장 확인 실패")

if __name__ == "__main__":
    add_cache_entry()

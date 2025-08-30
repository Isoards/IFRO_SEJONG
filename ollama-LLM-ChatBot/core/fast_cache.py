"""
빠른 메모리 캐시 시스템

속도 최적화를 위한 간단한 인메모리 캐시 구현
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheItem:
    """캐시 아이템"""
    data: Any
    timestamp: float
    access_count: int = 0
    ttl: float = 3600  # 1시간 기본 TTL

class FastCache:
    """
    빠른 메모리 캐시
    
    특징:
    - 단순한 딕셔너리 기반 캐시
    - TTL(Time To Live) 지원
    - LRU 기반 자동 정리
    - 해시 기반 키 생성
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        """
        FastCache 초기화
        
        Args:
            max_size: 최대 캐시 크기
            default_ttl: 기본 TTL (초)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheItem] = {}
        self.hits = 0
        self.misses = 0
        
        logger.info(f"FastCache 초기화: max_size={max_size}, ttl={default_ttl}초")
    
    def _generate_key(self, query: str, context: str = "") -> str:
        """
        쿼리와 컨텍스트를 기반으로 캐시 키 생성
        
        Args:
            query: 사용자 쿼리
            context: 추가 컨텍스트
            
        Returns:
            해시된 캐시 키
        """
        combined = f"{query}|{context}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def get(self, query: str, context: str = "") -> Optional[Any]:
        """
        캐시에서 데이터 조회
        
        Args:
            query: 사용자 쿼리
            context: 추가 컨텍스트
            
        Returns:
            캐시된 데이터 또는 None
        """
        key = self._generate_key(query, context)
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        item = self.cache[key]
        current_time = time.time()
        
        # TTL 확인
        if current_time - item.timestamp > item.ttl:
            del self.cache[key]
            self.misses += 1
            logger.debug(f"캐시 만료: {key[:8]}...")
            return None
        
        # 히트 처리
        item.access_count += 1
        self.hits += 1
        logger.debug(f"캐시 히트: {key[:8]}...")
        return item.data
    
    def put(self, query: str, data: Any, context: str = "", ttl: Optional[float] = None) -> None:
        """
        캐시에 데이터 저장
        
        Args:
            query: 사용자 쿼리
            data: 저장할 데이터
            context: 추가 컨텍스트
            ttl: TTL (초, None이면 기본값 사용)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        key = self._generate_key(query, context)
        
        # 캐시 크기 제한 확인
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        # 캐시 저장
        self.cache[key] = CacheItem(
            data=data,
            timestamp=time.time(),
            ttl=ttl
        )
        
        logger.debug(f"캐시 저장: {key[:8]}...")
    
    def _evict_oldest(self) -> None:
        """
        가장 오래된 캐시 항목 제거 (LRU)
        """
        if not self.cache:
            return
        
        # 가장 적게 접근된 항목 찾기
        oldest_key = min(self.cache.keys(), 
                        key=lambda k: (self.cache[k].access_count, self.cache[k].timestamp))
        
        del self.cache[oldest_key]
        logger.debug(f"캐시 제거 (LRU): {oldest_key[:8]}...")
    
    def clear(self) -> None:
        """캐시 전체 삭제"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("캐시 전체 삭제")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 반환
        
        Returns:
            캐시 통계 딕셔너리
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    def cleanup_expired(self) -> int:
        """
        만료된 캐시 항목들 정리
        
        Returns:
            정리된 항목 수
        """
        current_time = time.time()
        expired_keys = []
        
        for key, item in self.cache.items():
            if current_time - item.timestamp > item.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"만료된 캐시 {len(expired_keys)}개 정리")
        
        return len(expired_keys)

# 전역 캐시 인스턴스들
question_cache = FastCache(max_size=500, default_ttl=1800)  # 질문-답변 캐시 (30분)
sql_cache = FastCache(max_size=200, default_ttl=3600)       # SQL 쿼리 캐시 (1시간)
vector_cache = FastCache(max_size=1000, default_ttl=7200)   # 벡터 검색 캐시 (2시간)

def get_question_cache() -> FastCache:
    """질문-답변 캐시 반환"""
    return question_cache

def get_sql_cache() -> FastCache:
    """SQL 쿼리 캐시 반환"""
    return sql_cache

def get_vector_cache() -> FastCache:
    """벡터 검색 캐시 반환"""
    return vector_cache

def clear_all_caches() -> None:
    """모든 캐시 삭제"""
    question_cache.clear()
    sql_cache.clear()
    vector_cache.clear()
    logger.info("모든 캐시 삭제 완료")

def get_all_cache_stats() -> Dict[str, Dict[str, Any]]:
    """모든 캐시 통계 반환"""
    return {
        "question_cache": question_cache.get_stats(),
        "sql_cache": sql_cache.get_stats(),
        "vector_cache": vector_cache.get_stats()
    }

if __name__ == "__main__":
    # 테스트 코드
    cache = FastCache(max_size=3, default_ttl=2)
    
    # 캐시 저장
    cache.put("안녕하세요", "안녕하세요! 무엇을 도와드릴까요?")
    cache.put("날씨", "오늘 날씨는 맑습니다.")
    
    # 캐시 조회
    print(cache.get("안녕하세요"))  # 히트
    print(cache.get("없는질문"))    # 미스
    
    # 통계 출력
    print(cache.get_stats())
    
    # TTL 테스트
    time.sleep(3)
    print(cache.get("안녕하세요"))  # TTL 만료로 미스
    
    print("FastCache 테스트 완료")

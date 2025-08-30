"""
쿼리 라우터 - SBERT 기반 라우팅

SBERT는 라우팅용으로만 사용하여 질문을 적절한 처리 파이프라인으로 분기
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    logging.warning("sentence-transformers 라이브러리를 찾을 수 없습니다.")

logger = logging.getLogger(__name__)

class QueryRoute(Enum):
    """쿼리 라우팅 경로"""
    PDF_SEARCH = "pdf_search"      # PDF 문서 검색
    SQL_QUERY = "sql_query"        # SQL 데이터베이스 쿼리
    GREETING = "greeting"          # 인사말
    UNKNOWN = "unknown"            # 알 수 없음

@dataclass
class RouteResult:
    """라우팅 결과"""
    route: QueryRoute
    confidence: float
    reasoning: str
    metadata: Optional[Dict] = None

class QueryRouter:
    """
    쿼리 라우터 - SBERT 기반 빠른 라우팅
    
    기능:
    1. 질문을 적절한 처리 파이프라인으로 라우팅
    2. PDF 검색 vs SQL 쿼리 구분
    3. 빠른 의사결정을 위한 임베딩 기반 유사도 계산
    """
    
    def __init__(self, embedding_model: str = "jhgan/ko-sroberta-multitask"):
        """쿼리 라우터 초기화"""
        
        self.embedding_model = None
        if SBERT_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(embedding_model)
                logger.info(f"✅ 라우팅용 SBERT 모델 로드: {embedding_model}")
            except Exception as e:
                logger.warning(f"SBERT 모델 로드 실패: {e}")
                self.embedding_model = None
        
        # 라우팅을 위한 참조 질문들
        self.reference_questions = {
            QueryRoute.SQL_QUERY: [
                "교차로가 몇 개인가요?",
                "교통량이 많은 곳은?", 
                "사고가 가장 많은 지역은?",
                "통행량 데이터를 보여주세요",
                "강남구 교차로 개수",
                "평균 교통량은?",
                "총 교통사고 건수",
                "상위 10개 지역",
                "최대 교통량",
                "구별 통계",
                "월별 데이터",
                "시간대별 분석"
            ],
            QueryRoute.PDF_SEARCH: [
                "IFRO 시스템이란?",
                "교통 관리 방법",
                "시스템 사용법",
                "기능 설명",
                "설치 방법",
                "운영 절차", 
                "문서에서 찾아주세요",
                "매뉴얼 내용",
                "가이드라인",
                "정책 내용",
                "어떻게 작동하나요?",
                "원리가 무엇인가요?"
            ],
            QueryRoute.GREETING: [
                "안녕하세요",
                "반갑습니다", 
                "안녕",
                "하이",
                "좋은 아침입니다",
                "도움이 필요해요",
                "처음 사용해요",
                "질문이 있어요"
            ]
        }
        
        # 참조 질문들의 임베딩 미리 계산
        self.reference_embeddings = {}
        if self.embedding_model:
            self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        """참조 질문들의 임베딩 미리 계산"""
        try:
            for route, questions in self.reference_questions.items():
                embeddings = self.embedding_model.encode(questions)
                self.reference_embeddings[route] = embeddings
                logger.debug(f"임베딩 계산 완료: {route.value} ({len(questions)}개)")
            
            logger.info("✅ 참조 질문 임베딩 사전 계산 완료")
        except Exception as e:
            logger.error(f"임베딩 사전 계산 실패: {e}")
    
    def route_query(self, question: str) -> RouteResult:
        """
        질문을 적절한 파이프라인으로 라우팅
        
        Args:
            question: 사용자 질문
            
        Returns:
            라우팅 결과
        """
        if not self.embedding_model or not self.reference_embeddings:
            # SBERT를 사용할 수 없는 경우 규칙 기반 폴백
            return self._rule_based_routing(question)
        
        try:
            # 질문 임베딩 생성
            query_embedding = self.embedding_model.encode([question])[0]
            
            # 각 라우트와의 유사도 계산
            route_scores = {}
            
            for route, ref_embeddings in self.reference_embeddings.items():
                # 코사인 유사도 계산
                similarities = np.dot(ref_embeddings, query_embedding) / (
                    np.linalg.norm(ref_embeddings, axis=1) * np.linalg.norm(query_embedding)
                )
                
                # 최대 유사도 사용
                max_similarity = float(np.max(similarities))
                route_scores[route] = max_similarity
                
                logger.debug(f"라우트 {route.value}: 최대 유사도 {max_similarity:.3f}")
            
            # 최고 점수 라우트 선택
            best_route = max(route_scores, key=route_scores.get)
            best_score = route_scores[best_route]
            
            # 신뢰도 임계값 검사
            if best_score < 0.3:
                return RouteResult(
                    route=QueryRoute.UNKNOWN,
                    confidence=best_score,
                    reasoning=f"모든 라우트의 유사도가 낮음 (최대: {best_score:.3f})"
                )
            
            # SQL vs PDF 구분 로직
            sql_score = route_scores.get(QueryRoute.SQL_QUERY, 0.0)
            pdf_score = route_scores.get(QueryRoute.PDF_SEARCH, 0.0)
            greeting_score = route_scores.get(QueryRoute.GREETING, 0.0)
            
            # 인사말이 가장 높은 경우
            if greeting_score > 0.5 and greeting_score > max(sql_score, pdf_score):
                return RouteResult(
                    route=QueryRoute.GREETING,
                    confidence=greeting_score,
                    reasoning=f"인사말로 분류 (유사도: {greeting_score:.3f})",
                    metadata={"scores": route_scores}
                )
            
            # SQL과 PDF 중 선택
            if sql_score > pdf_score and sql_score > 0.4:
                return RouteResult(
                    route=QueryRoute.SQL_QUERY,
                    confidence=sql_score,
                    reasoning=f"SQL 쿼리로 분류 (SQL: {sql_score:.3f} vs PDF: {pdf_score:.3f})",
                    metadata={"scores": route_scores}
                )
            elif pdf_score > 0.4:
                return RouteResult(
                    route=QueryRoute.PDF_SEARCH,
                    confidence=pdf_score,
                    reasoning=f"PDF 검색으로 분류 (PDF: {pdf_score:.3f} vs SQL: {sql_score:.3f})",
                    metadata={"scores": route_scores}
                )
            else:
                # 둘 다 낮은 경우 기본값 (PDF 검색)
                return RouteResult(
                    route=QueryRoute.PDF_SEARCH,
                    confidence=max(sql_score, pdf_score),
                    reasoning=f"기본 라우트 (PDF 검색) 선택",
                    metadata={"scores": route_scores}
                )
                
        except Exception as e:
            logger.error(f"SBERT 라우팅 실패: {e}")
            return self._rule_based_routing(question)
    
    def _rule_based_routing(self, question: str) -> RouteResult:
        """
        규칙 기반 라우팅 (SBERT 폴백)
        
        Args:
            question: 사용자 질문
            
        Returns:
            라우팅 결과
        """
        question_lower = question.lower()
        
        # 인사말 패턴
        greeting_patterns = ['안녕', '반갑', '하이', '처음', '도움']
        if any(pattern in question_lower for pattern in greeting_patterns):
            return RouteResult(
                route=QueryRoute.GREETING,
                confidence=0.8,
                reasoning="규칙 기반: 인사말 패턴 매칭"
            )
        
        # SQL 쿼리 패턴 (숫자, 통계, 집계 키워드)
        sql_patterns = [
            '몇', '개수', '건수', '총', '평균', '최대', '최소', '상위', '하위',
            '교통량', '통행량', '사고', '구별', '지역별', '시간별', '통계',
            '분석', '데이터', '수치', '비율', '순위'
        ]
        
        sql_score = sum(1 for pattern in sql_patterns if pattern in question_lower)
        
        # PDF 검색 패턴 (설명, 방법, 개념 키워드)  
        pdf_patterns = [
            '무엇', '어떻게', '왜', '방법', '설명', '기능', '시스템', '매뉴얼',
            '가이드', '정책', '절차', '사용법', '원리', '개념', '정의'
        ]
        
        pdf_score = sum(1 for pattern in pdf_patterns if pattern in question_lower)
        
        # 점수 기반 라우팅
        if sql_score > pdf_score and sql_score > 0:
            confidence = min(0.7 + sql_score * 0.1, 1.0)
            return RouteResult(
                route=QueryRoute.SQL_QUERY,
                confidence=confidence,
                reasoning=f"규칙 기반: SQL 패턴 매칭 (점수: {sql_score})"
            )
        elif pdf_score > 0:
            confidence = min(0.7 + pdf_score * 0.1, 1.0)
            return RouteResult(
                route=QueryRoute.PDF_SEARCH,
                confidence=confidence,
                reasoning=f"규칙 기반: PDF 패턴 매칭 (점수: {pdf_score})"
            )
        else:
            # 기본값은 PDF 검색
            return RouteResult(
                route=QueryRoute.PDF_SEARCH,
                confidence=0.5,
                reasoning="규칙 기반: 기본 라우트 (PDF 검색)"
            )
    
    def add_reference_question(self, route: QueryRoute, question: str):
        """참조 질문 추가"""
        if route not in self.reference_questions:
            self.reference_questions[route] = []
        
        self.reference_questions[route].append(question)
        
        # 임베딩 다시 계산
        if self.embedding_model:
            self._precompute_embeddings()
        
        logger.info(f"참조 질문 추가: {route.value} - {question}")
    
    def get_route_statistics(self) -> Dict[str, int]:
        """라우트별 참조 질문 통계"""
        return {
            route.value: len(questions) 
            for route, questions in self.reference_questions.items()
        }

if __name__ == "__main__":
    # 테스트 코드
    router = QueryRouter()
    
    test_questions = [
        "안녕하세요",
        "강남구 교차로가 몇 개인가요?",
        "IFRO 시스템이 무엇인가요?",
        "평균 교통량은 얼마인가요?",
        "시스템 사용 방법을 알려주세요",
        "교통사고가 가장 많은 지역은?"
    ]
    
    for question in test_questions:
        result = router.route_query(question)
        print(f"\n질문: {question}")
        print(f"라우트: {result.route.value}")
        print(f"신뢰도: {result.confidence:.3f}")
        print(f"이유: {result.reasoning}")

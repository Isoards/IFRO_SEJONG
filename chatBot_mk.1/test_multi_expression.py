"""
다중 표현 인덱싱 기능 테스트 스크립트

이 스크립트는 다중 표현 인덱싱 기능이 제대로 작동하는지 테스트합니다.
"""

import sys
import os
import logging
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.keyword_enhancer import KeywordEnhancer
from core.question_analyzer import QuestionAnalyzer
from core.vector_store import HybridVectorStore

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiExpressionTester:
    """다중 표현 인덱싱 테스터"""
    
    def __init__(self):
        """테스터 초기화"""
        self.keyword_enhancer = KeywordEnhancer(domain="traffic")
        self.question_analyzer = QuestionAnalyzer()
        self.vector_store = HybridVectorStore()
        
        logger.info("다중 표현 인덱싱 테스터 초기화 완료")
    
    def test_expression_extraction(self):
        """표현 추출 테스트"""
        logger.info("=== 표현 추출 테스트 ===")
        
        test_queries = [
            "교통사고가 언제 발생했나요?",
            "교차로에서 신호등이 어떻게 작동하나요?",
            "교통량 통계를 조회해주세요",
            "사고 발생 건수를 알려주세요",
            "트래픽 데이터를 분석해주세요"
        ]
        
        for query in test_queries:
            logger.info(f"\n질문: {query}")
            
            # 교통 컨텍스트에서 표현 추출
            traffic_expressions = self.keyword_enhancer.get_multi_expressions(query, "traffic")
            logger.info(f"교통 표현: {traffic_expressions}")
            
            # 데이터베이스 컨텍스트에서 표현 추출
            db_expressions = self.keyword_enhancer.get_multi_expressions(query, "database")
            logger.info(f"DB 표현: {db_expressions}")
            
            # 최적 표현 선택
            optimal_traffic = self.keyword_enhancer.get_optimal_expressions(query, "traffic", top_k=3)
            logger.info(f"최적 교통 표현: {optimal_traffic}")
    
    def test_question_analysis_with_expressions(self):
        """표현을 고려한 질문 분석 테스트"""
        logger.info("\n=== 표현을 고려한 질문 분석 테스트 ===")
        
        test_questions = [
            "교통사고 통계를 보여주세요",
            "어제 발생한 사고는 몇 건인가요?",
            "교차로별 교통량을 조회해주세요"
        ]
        
        for question in test_questions:
            logger.info(f"\n질문: {question}")
            
            # 다중 표현을 고려한 분석
            analyzed = self.question_analyzer.analyze_question_with_expressions(
                question, expression_enhancer=self.keyword_enhancer
            )
            
            logger.info(f"분석된 키워드: {analyzed.keywords}")
            logger.info(f"의도: {analyzed.intent}")
            logger.info(f"컨텍스트: {analyzed.metadata.get('context', 'N/A') if analyzed.metadata else 'N/A'}")
            logger.info(f"사용된 표현: {analyzed.metadata.get('expressions', []) if analyzed.metadata else []}")
    
    def test_query_enhancement(self):
        """쿼리 향상 테스트"""
        logger.info("\n=== 쿼리 향상 테스트 ===")
        
        test_queries = [
            "교통사고",
            "교차로 신호등",
            "교통량 분석"
        ]
        
        for query in test_queries:
            logger.info(f"\n원본 쿼리: {query}")
            
            # 교통 컨텍스트에서 쿼리 향상
            enhanced_traffic = self.keyword_enhancer.enhance_query_with_expressions(query, "traffic")
            logger.info(f"향상된 교통 쿼리: {enhanced_traffic}")
            
            # 데이터베이스 컨텍스트에서 쿼리 향상
            enhanced_db = self.keyword_enhancer.enhance_query_with_expressions(query, "database")
            logger.info(f"향상된 DB 쿼리: {enhanced_db}")
    
    def test_expression_suggestions(self):
        """표현 제안 테스트"""
        logger.info("\n=== 표현 제안 테스트 ===")
        
        test_questions = [
            "교통사고 정보를 알려주세요",
            "교통량 데이터를 보여주세요"
        ]
        
        for question in test_questions:
            logger.info(f"\n질문: {question}")
            
            # 교통 컨텍스트에서 제안
            traffic_suggestions = self.question_analyzer.get_expression_suggestions(
                question, self.keyword_enhancer, "traffic"
            )
            logger.info(f"교통 제안: {traffic_suggestions}")
            
            # 데이터베이스 컨텍스트에서 제안
            db_suggestions = self.question_analyzer.get_expression_suggestions(
                question, self.keyword_enhancer, "database"
            )
            logger.info(f"DB 제안: {db_suggestions}")
    
    def test_custom_expression_management(self):
        """사용자 정의 표현 관리 테스트"""
        logger.info("\n=== 사용자 정의 표현 관리 테스트 ===")
        
        # 새로운 표현 체인 추가
        self.keyword_enhancer.add_custom_expression_chain(
            "교통안전",
            ["안전", "교통안전", "안전관리", "교통안전관리"],
            context="traffic",
            weight=1.5
        )
        
        # 추가된 표현 테스트
        query = "교통안전에 대해 알려주세요"
        expressions = self.keyword_enhancer.get_multi_expressions(query, "traffic")
        logger.info(f"사용자 정의 표현 테스트 - 질문: {query}")
        logger.info(f"추출된 표현: {expressions}")
    
    def test_expression_statistics(self):
        """표현 통계 테스트"""
        logger.info("\n=== 표현 통계 테스트 ===")
        
        # 일부 표현 사용 피드백 추가
        test_feedback = [
            ("교통사고 정보를 알려주세요", ["교통사고", "사고"], True),
            ("교차로 신호등 작동방식을 설명해주세요", ["교차로", "신호등"], True),
            ("교통량 데이터를 보여주세요", ["교통량", "트래픽"], False)
        ]
        
        for query, expressions, success in test_feedback:
            self.keyword_enhancer.update_expression_feedback(query, expressions, success)
        
        # 통계 조회
        stats = self.keyword_enhancer.get_expression_statistics()
        logger.info(f"표현 통계: {stats}")
    
    def test_context_specific_expressions(self):
        """컨텍스트별 표현 테스트"""
        logger.info("\n=== 컨텍스트별 표현 테스트 ===")
        
        contexts = ["traffic", "database", "general"]
        
        for context in contexts:
            expressions = self.keyword_enhancer.get_context_specific_expressions(context)
            logger.info(f"{context} 컨텍스트 표현: {list(expressions.keys())}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("다중 표현 인덱싱 기능 테스트 시작")
        
        try:
            self.test_expression_extraction()
            self.test_question_analysis_with_expressions()
            self.test_query_enhancement()
            self.test_expression_suggestions()
            self.test_custom_expression_management()
            self.test_expression_statistics()
            self.test_context_specific_expressions()
            
            logger.info("\n=== 모든 테스트 완료 ===")
            
        except Exception as e:
            logger.error(f"테스트 실행 중 오류 발생: {e}")
            raise

def main():
    """메인 함수"""
    tester = MultiExpressionTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()

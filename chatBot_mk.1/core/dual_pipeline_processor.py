"""
Dual Pipeline 처리 모듈

이 모듈은 질문을 분석하여 SQL 질의와 문서 검색을 분리 처리하는
Dual Pipeline을 구현합니다.
"""

import time
import logging
import re
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from .question_analyzer import QuestionAnalyzer, AnalyzedQuestion, QuestionType
from .answer_generator import AnswerGenerator, Answer, ModelType, GenerationConfig
from .sql_generator import SQLGenerator, DatabaseSchema, SQLQuery
from .vector_store import HybridVectorStore
from .pdf_processor import TextChunk

logger = logging.getLogger(__name__)

class PipelineType(Enum):
    """파이프라인 타입"""
    DOCUMENT_SEARCH = "document_search"  # 문서 검색
    SQL_QUERY = "sql_query"              # SQL 질의
    HYBRID = "hybrid"                    # 하이브리드 (둘 다)

@dataclass
class PipelineResult:
    """파이프라인 처리 결과"""
    pipeline_type: PipelineType
    answer: Optional[Answer] = None
    sql_query: Optional[SQLQuery] = None
    relevant_chunks: List[TextChunk] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0
    metadata: Optional[Dict] = None

@dataclass
class DualPipelineResult:
    """Dual Pipeline 최종 결과"""
    question: str
    analyzed_question: AnalyzedQuestion
    final_answer: str
    confidence_score: float
    total_processing_time: float
    document_result: Optional[PipelineResult] = None
    sql_result: Optional[PipelineResult] = None
    metadata: Optional[Dict] = None

class DualPipelineProcessor:
    """
    Dual Pipeline 처리 클래스
    
    주요 기능:
    1. 질문 분석을 통한 파이프라인 분기
    2. 문서 검색 파이프라인 처리
    3. SQL 질의 파이프라인 처리
    4. 결과 통합 및 최종 답변 생성
    """
    
    def __init__(self,
                 question_analyzer: QuestionAnalyzer,
                 answer_generator: AnswerGenerator,
                 sql_generator: SQLGenerator,
                 vector_store: HybridVectorStore,
                 database_schema: Optional[DatabaseSchema] = None,
                 expression_enhancer=None):
        """
        DualPipelineProcessor 초기화
        
        Args:
            question_analyzer: 질문 분석기
            answer_generator: 답변 생성기
            sql_generator: SQL 생성기
            vector_store: 벡터 저장소
            database_schema: 데이터베이스 스키마
            expression_enhancer: 표현 향상기 (KeywordEnhancer)
        """
        self.question_analyzer = question_analyzer
        self.answer_generator = answer_generator
        self.sql_generator = sql_generator
        self.vector_store = vector_store
        self.database_schema = database_schema
        self.expression_enhancer = expression_enhancer
        
        # Few-shot 예시 (SQL 생성용)
        self.few_shot_examples = [
            {
                "question": "사용자 테이블에서 모든 사용자 정보를 조회해주세요",
                "sql": "SELECT * FROM users"
            },
            {
                "question": "2023년에 가입한 사용자 수를 알려주세요",
                "sql": "SELECT COUNT(*) FROM users WHERE YEAR(created_at) = 2023"
            },
            {
                "question": "가장 최근에 가입한 사용자 10명을 조회해주세요",
                "sql": "SELECT * FROM users ORDER BY created_at DESC LIMIT 10"
            }
        ]
        
        logger.info("Dual Pipeline Processor 초기화 완료 (다중 표현 지원)")
    
    def process_question(self, question: str, 
                        conversation_history: Optional[List] = None,
                        use_context: bool = True) -> DualPipelineResult:
        """
        질문 처리 (기본 메서드)
        
        Args:
            question: 사용자 질문
            conversation_history: 대화 히스토리
            use_context: 컨텍스트 사용 여부
            
        Returns:
            처리 결과
        """
        return self.process_question_with_expressions(question, conversation_history, use_context)
    
    def process_question_with_expressions(self, question: str, 
                                        conversation_history: Optional[List] = None,
                                        use_context: bool = True) -> DualPipelineResult:
        """
        다중 표현을 고려한 질문 처리 (오류 처리 개선)
        
        Args:
            question: 사용자 질문
            conversation_history: 대화 히스토리
            use_context: 컨텍스트 사용 여부
            
        Returns:
            처리 결과
        """
        try:
            start_time = time.time()
            
            # 1. 다중 표현을 고려한 질문 분석
            analyzed_question = self.question_analyzer.analyze_question_with_expressions(
                question, conversation_history, self.expression_enhancer
            )
            
            # 2. 컨텍스트 결정
            context = analyzed_question.metadata.get("context", "general") if analyzed_question.metadata else "general"
            
            # 3. 파이프라인 분기 결정
            pipeline_type = self._determine_pipeline_type_with_expressions(analyzed_question, context)
            
            # 4. 파이프라인별 처리
            document_result = None
            sql_result = None
            
            try:
                if pipeline_type in [PipelineType.DOCUMENT_SEARCH, PipelineType.HYBRID]:
                    document_result = self._process_document_search_with_expressions(
                        analyzed_question, context
                    )
            except Exception as doc_error:
                logger.error(f"문서 검색 처리 중 오류: {doc_error}")
                document_result = None
            
            try:
                if pipeline_type in [PipelineType.SQL_QUERY, PipelineType.HYBRID]:
                    sql_result = self._process_sql_query_with_expressions(
                        analyzed_question, context
                    )
            except Exception as sql_error:
                logger.error(f"SQL 쿼리 처리 중 오류: {sql_error}")
                sql_result = None
            
            # 5. 결과 통합
            final_answer = self._combine_results_with_expressions(
                document_result, sql_result, analyzed_question, context
            )
            
            # 6. 피드백 업데이트 (오류가 있어도 계속 진행)
            try:
                self._update_expression_feedback(question, analyzed_question, context)
            except Exception as feedback_error:
                logger.warning(f"피드백 업데이트 중 오류: {feedback_error}")
            
            total_time = time.time() - start_time
            
            return DualPipelineResult(
                question=question,
                analyzed_question=analyzed_question,
                final_answer=final_answer,
                confidence_score=self._calculate_confidence_with_expressions(
                    document_result, sql_result, analyzed_question
                ),
                total_processing_time=total_time,
                document_result=document_result,
                sql_result=sql_result,
                metadata={
                    "pipeline_type": pipeline_type.value,
                    "context": context,
                    "expressions_used": analyzed_question.metadata.get("expressions", []) if analyzed_question.metadata else []
                }
            )
        
        except Exception as e:
            logger.error(f"Dual Pipeline 처리 중 오류: {e}")
            # 오류 발생 시 기본 응답 반환
            return DualPipelineResult(
                question=question,
                analyzed_question=AnalyzedQuestion(
                    original_question=question,
                    processed_question=question,
                    question_type=QuestionType.FACTUAL,
                    keywords=[],
                    entities=[],
                    intent="error",
                    context_keywords=[],
                    requires_sql=False,
                    sql_intent=None
                ),
                final_answer="죄송합니다. 질문을 처리하는 중 오류가 발생했습니다. 일반 파이프라인으로 다시 시도해주세요.",
                confidence_score=0.0,
                total_processing_time=0.0,
                document_result=None,
                sql_result=None,
                metadata={
                    "pipeline_type": "error",
                    "context": "general",
                    "expressions_used": [],
                    "error": str(e)
                }
            )
    
    def _determine_pipeline_type(self, analyzed_question: AnalyzedQuestion) -> PipelineType:
        """
        파이프라인 타입 결정 (개선된 버전)
        
        Args:
            analyzed_question: 분석된 질문
            
        Returns:
            파이프라인 타입
        """
        question_lower = analyzed_question.original_question.lower()
        
        # 1. 장소 이동 요청 패턴 확인 (문서 검색만 필요)
        location_movement_patterns = [
            r'[으]?로\s*이동', r'[으]?로\s*가', r'[으]?로\s*보여', r'[으]?로\s*전환',
            r'[으]?로\s*바꿔', r'[으]?로\s*변경', r'[으]?로\s*이동해', r'[으]?로\s*가줘',
            r'[으]?로\s*보여줘', r'[으]?로\s*전환해', r'[으]?로\s*바꿔줘',
            r'이동\s*[해줘]?', r'가\s*[줘]?', r'보여\s*[줘]?', r'전환\s*[해줘]?',
            r'바꿔\s*[줘]?', r'변경\s*[해줘]?'
        ]
        
        is_location_movement = any(re.search(pattern, question_lower) for pattern in location_movement_patterns)
        
        # 2. 정량적 질문 패턴 확인 (SQL 필요)
        quantitative_patterns = [
            r'얼마나', r'몇\s*개', r'몇\s*명', r'몇\s*대', r'몇\s*건', r'몇\s*회',
            r'통행량\s*[이]?\s*얼마', r'교통량\s*[이]?\s*얼마', r'사고\s*[가]?\s*몇\s*건',
            r'평균\s*[이]?\s*얼마', r'최대\s*[가]?\s*얼마', r'최소\s*[가]?\s*얼마',
            r'합계\s*[가]?\s*얼마', r'총\s*[이]?\s*얼마', r'갯수\s*[가]?\s*얼마',
            r'count', r'sum', r'avg', r'max', r'min', r'total',
            r'통계', r'집계', r'분석', r'데이터\s*분석'
        ]
        
        is_quantitative = any(re.search(pattern, question_lower) for pattern in quantitative_patterns)
        
        # 3. 파이프라인 타입 결정
        if is_location_movement:
            # 장소 이동 요청은 문서 검색만 필요
            return PipelineType.DOCUMENT_SEARCH
        elif is_quantitative and self.database_schema:
            # 정량적 질문은 SQL 필요
            return PipelineType.SQL_QUERY
        elif analyzed_question.requires_sql and self.database_schema:
            # SQL이 필요한 경우
            if analyzed_question.question_type in [QuestionType.CONCEPTUAL, QuestionType.ANALYTICAL]:
                return PipelineType.HYBRID
            else:
                return PipelineType.SQL_QUERY
        else:
            # 문서 검색만 필요한 경우
            return PipelineType.DOCUMENT_SEARCH
    
    def _process_document_pipeline(self, analyzed_question: AnalyzedQuestion) -> PipelineResult:
        """
        문서 검색 파이프라인 처리
        
        Args:
            analyzed_question: 분석된 질문
            
        Returns:
            문서 검색 결과
        """
        start_time = time.time()
        
        try:
            # 1. 벡터 검색
            relevant_chunks = self.vector_store.search(
                query=analyzed_question.processed_question,
                top_k=5,
                filter_metadata=None
            )
            
            if not relevant_chunks:
                logger.warning("관련 문서 청크를 찾을 수 없음")
                return PipelineResult(
                    pipeline_type=PipelineType.DOCUMENT_SEARCH,
                    confidence_score=0.0,
                    processing_time=time.time() - start_time
                )
            
            # 2. 답변 생성
            answer = self.answer_generator.generate_answer(
                question=analyzed_question.original_question,
                context_chunks=relevant_chunks,
                analyzed_question=analyzed_question
            )
            
            processing_time = time.time() - start_time
            
            return PipelineResult(
                pipeline_type=PipelineType.DOCUMENT_SEARCH,
                answer=answer,
                relevant_chunks=relevant_chunks,
                confidence_score=answer.confidence_score,
                processing_time=processing_time,
                metadata={
                    "chunks_found": len(relevant_chunks),
                    "model_used": answer.model_name
                }
            )
            
        except Exception as e:
            logger.error(f"문서 검색 파이프라인 처리 실패: {e}")
            return PipelineResult(
                pipeline_type=PipelineType.DOCUMENT_SEARCH,
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def _process_sql_pipeline(self, analyzed_question: AnalyzedQuestion) -> PipelineResult:
        """
        SQL 질의 파이프라인 처리
        
        Args:
            analyzed_question: 분석된 질문
            
        Returns:
            SQL 질의 결과
        """
        start_time = time.time()
        
        try:
            # 1. SQL 생성
            sql_query = self.sql_generator.generate_sql(
                question=analyzed_question.original_question,
                schema=self.database_schema,
                few_shot_examples=self.few_shot_examples
            )
            
            # 2. SQL 실행 (실제 DB 연결이 없는 경우 시뮬레이션)
            # TODO: 실제 데이터베이스 연결 및 쿼리 실행 구현
            sql_result_text = f"생성된 SQL: {sql_query.query}\n\n"
            sql_result_text += f"쿼리 타입: {sql_query.query_type}\n"
            sql_result_text += f"검증 결과: {'성공' if sql_query.validation_passed else '실패'}"
            
            if sql_query.error_message:
                sql_result_text += f"\n오류: {sql_query.error_message}"
            
            # 3. 답변 생성 (SQL 결과를 바탕으로)
            answer = Answer(
                content=sql_result_text,
                confidence_score=sql_query.confidence_score,
                used_chunks=[],  # SQL은 문서 청크를 사용하지 않음
                generation_time=sql_query.execution_time,
                model_name=sql_query.model_name,
                metadata={
                    "sql_query": sql_query.query,
                    "query_type": sql_query.query_type,
                    "validation_passed": sql_query.validation_passed
                }
            )
            
            processing_time = time.time() - start_time
            
            return PipelineResult(
                pipeline_type=PipelineType.SQL_QUERY,
                answer=answer,
                sql_query=sql_query,
                confidence_score=sql_query.confidence_score,
                processing_time=processing_time,
                metadata={
                    "sql_generated": True,
                    "validation_passed": sql_query.validation_passed
                }
            )
            
        except Exception as e:
            logger.error(f"SQL 질의 파이프라인 처리 실패: {e}")
            return PipelineResult(
                pipeline_type=PipelineType.SQL_QUERY,
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    def _integrate_results(self,
                          analyzed_question: AnalyzedQuestion,
                          document_result: Optional[PipelineResult],
                          sql_result: Optional[PipelineResult]) -> Tuple[str, float]:
        """
        결과 통합
        
        Args:
            analyzed_question: 분석된 질문
            document_result: 문서 검색 결과
            sql_result: SQL 질의 결과
            
        Returns:
            (최종 답변, 신뢰도 점수)
        """
        # 단일 파이프라인 결과인 경우
        if document_result and not sql_result:
            return document_result.answer.content, document_result.confidence_score
        elif sql_result and not document_result:
            return sql_result.answer.content, sql_result.confidence_score
        
        # 하이브리드 결과인 경우
        if document_result and sql_result:
            # 문서 검색 결과를 기본으로 하고 SQL 결과를 보완
            base_answer = document_result.answer.content
            sql_info = f"\n\n[데이터베이스 정보]\n{sql_result.answer.content}"
            
            final_answer = base_answer + sql_info
            
            # 신뢰도는 문서 검색 결과를 우선으로 하되 SQL 결과도 고려
            confidence = (document_result.confidence_score * 0.7 + 
                         sql_result.confidence_score * 0.3)
            
            return final_answer, confidence
        
        # 결과가 없는 경우
        return "죄송합니다. 질문에 대한 답변을 찾을 수 없습니다.", 0.0
    
    def _determine_pipeline_type_with_expressions(self, analyzed_question: AnalyzedQuestion, 
                                                context: str) -> PipelineType:
        """표현을 고려한 파이프라인 타입 결정 (개선된 버전)"""
        question_lower = analyzed_question.original_question.lower()
        
        # 1. 장소 이동 요청 패턴 확인 (문서 검색만 필요)
        location_movement_patterns = [
            r'[으]?로\s*이동', r'[으]?로\s*가', r'[으]?로\s*보여', r'[으]?로\s*전환',
            r'[으]?로\s*바꿔', r'[으]?로\s*변경', r'[으]?로\s*이동해', r'[으]?로\s*가줘',
            r'[으]?로\s*보여줘', r'[으]?로\s*전환해', r'[으]?로\s*바꿔줘',
            r'이동\s*[해줘]?', r'가\s*[줘]?', r'보여\s*[줘]?', r'전환\s*[해줘]?',
            r'바꿔\s*[줘]?', r'변경\s*[해줘]?'
        ]
        
        is_location_movement = any(re.search(pattern, question_lower) for pattern in location_movement_patterns)
        
        # 2. 정량적 질문 패턴 확인 (SQL 필요)
        quantitative_patterns = [
            r'얼마나', r'몇\s*개', r'몇\s*명', r'몇\s*대', r'몇\s*건', r'몇\s*회',
            r'통행량\s*[이]?\s*얼마', r'교통량\s*[이]?\s*얼마', r'사고\s*[가]?\s*몇\s*건',
            r'평균\s*[이]?\s*얼마', r'최대\s*[가]?\s*얼마', r'최소\s*[가]?\s*얼마',
            r'합계\s*[가]?\s*얼마', r'총\s*[이]?\s*얼마', r'갯수\s*[가]?\s*얼마',
            r'count', r'sum', r'avg', r'max', r'min', r'total',
            r'통계', r'집계', r'분석', r'데이터\s*분석'
        ]
        
        is_quantitative = any(re.search(pattern, question_lower) for pattern in quantitative_patterns)
        
        # 3. 표현 기반 파이프라인 조정
        if is_location_movement:
            # 장소 이동 요청은 문서 검색만 필요
            return PipelineType.DOCUMENT_SEARCH
        elif is_quantitative and self.database_schema:
            # 정량적 질문은 SQL 필요
            return PipelineType.SQL_QUERY
        elif context == "database" and analyzed_question.requires_sql:
            return PipelineType.SQL_QUERY
        elif context == "traffic" and "사고" in question_lower:
            return PipelineType.HYBRID  # 교통사고는 문서와 데이터 모두 필요
        elif context == "general" and len(analyzed_question.metadata.get("expressions", [])) > 2:
            return PipelineType.HYBRID  # 다양한 표현이 있으면 하이브리드
        else:
            # 기본 파이프라인 결정
            return self._determine_pipeline_type(analyzed_question)
    
    def _process_document_search_with_expressions(self, analyzed_question: AnalyzedQuestion, 
                                                context: str) -> PipelineResult:
        """표현을 고려한 문서 검색 처리"""
        start_time = time.time()
        
        # 표현을 활용한 쿼리 향상
        enhanced_query = analyzed_question.processed_question
        if self.expression_enhancer:
            enhanced_query = self.expression_enhancer.enhance_query_with_expressions(
                analyzed_question.processed_question, context
            )
        
        # 표현을 고려한 검색
        relevant_chunks = self.vector_store.search_with_expressions(
            enhanced_query, self.expression_enhancer, context, top_k=5
        )
        
        # 답변 생성
        answer = self.answer_generator.generate_answer_from_chunks(
            analyzed_question.processed_question,
            [chunk for chunk, _ in relevant_chunks],
            model_type=ModelType.OLLAMA
        )
        
        processing_time = time.time() - start_time
        
        return PipelineResult(
            pipeline_type=PipelineType.DOCUMENT_SEARCH,
            answer=answer,
            relevant_chunks=[chunk for chunk, _ in relevant_chunks],
            confidence_score=self._calculate_document_confidence(relevant_chunks),
            processing_time=processing_time,
            metadata={
                "enhanced_query": enhanced_query,
                "context": context,
                "expressions_used": analyzed_question.metadata.get("expressions", []) if analyzed_question.metadata else []
            }
        )
    
    def _calculate_document_confidence(self, relevant_chunks: List[Tuple[TextChunk, float]]) -> float:
        """문서 검색 결과의 신뢰도 계산"""
        if not relevant_chunks:
            return 0.0
        
        # 상위 3개 청크의 평균 유사도 점수 사용
        top_scores = [score for _, score in relevant_chunks[:3]]
        avg_score = sum(top_scores) / len(top_scores)
        
        # 점수를 0.0-1.0 범위로 정규화
        confidence = min(avg_score, 1.0)
        
        # 청크 수에 따른 보정
        if len(relevant_chunks) >= 3:
            confidence *= 1.1  # 충분한 컨텍스트가 있으면 신뢰도 증가
        elif len(relevant_chunks) == 1:
            confidence *= 0.8  # 단일 청크만 있으면 신뢰도 감소
        
        return min(confidence, 1.0)
    
    def _process_sql_query_with_expressions(self, analyzed_question: AnalyzedQuestion, 
                                          context: str) -> PipelineResult:
        """표현을 고려한 SQL 쿼리 처리"""
        start_time = time.time()
        
        # 표현을 활용한 SQL 생성
        enhanced_question = analyzed_question.processed_question
        if self.expression_enhancer:
            # 데이터베이스 관련 표현으로 쿼리 향상
            db_expressions = self.expression_enhancer.get_multi_expressions(
                analyzed_question.processed_question, "database"
            )
            if db_expressions:
                enhanced_question += f" ({', '.join(db_expressions[:3])})"
        
        # SQL 생성
        sql_query = self.sql_generator.generate_sql(
            enhanced_question,
            self.database_schema,
            few_shot_examples=self.few_shot_examples
        )
        
        # SQL 실행 및 결과 처리
        if sql_query.is_valid:
            try:
                result = self.sql_generator.execute_sql(sql_query)
                answer = self.answer_generator.generate_answer_from_sql_result(
                    analyzed_question.processed_question,
                    result,
                    model_type=ModelType.OLLAMA
                )
            except Exception as e:
                logger.error(f"SQL 실행 오류: {e}")
                answer = Answer(
                    content=f"데이터베이스 조회 중 오류가 발생했습니다: {str(e)}",
                    confidence=0.3
                )
        else:
            answer = Answer(
                content="적절한 SQL 쿼리를 생성할 수 없습니다.",
                confidence=0.2
            )
        
        processing_time = time.time() - start_time
        
        return PipelineResult(
            pipeline_type=PipelineType.SQL_QUERY,
            answer=answer,
            sql_query=sql_query,
            confidence_score=sql_query.confidence if sql_query.is_valid else 0.2,
            processing_time=processing_time,
            metadata={
                "enhanced_question": enhanced_question,
                "context": context,
                "db_expressions_used": self.expression_enhancer.get_multi_expressions(
                    analyzed_question.processed_question, "database"
                ) if self.expression_enhancer else []
            }
        )
    
    def _combine_results_with_expressions(self, document_result: Optional[PipelineResult],
                                        sql_result: Optional[PipelineResult],
                                        analyzed_question: AnalyzedQuestion,
                                        context: str) -> str:
        """표현을 고려한 결과 통합 (오류 처리 개선)"""
        try:
            if document_result and sql_result:
                # 하이브리드 결과 통합
                doc_answer = document_result.answer.content if document_result.answer else "문서 정보를 찾을 수 없습니다."
                sql_answer = sql_result.answer.content if sql_result.answer else "데이터베이스 정보를 찾을 수 없습니다."
                
                # 컨텍스트별 통합 전략
                if context == "traffic":
                    combined = f"{sql_answer}\n\n추가 정보: {doc_answer}"
                elif context == "database":
                    combined = f"{sql_answer}\n\n관련 문서: {doc_answer}"
                else:
                    combined = f"{sql_answer}\n\n{doc_answer}"
                
                return combined
            
            elif document_result and document_result.answer:
                return document_result.answer.content
            elif sql_result and sql_result.answer:
                return sql_result.answer.content
            elif document_result:
                return "문서를 검색했지만 적절한 답변을 생성할 수 없습니다."
            elif sql_result:
                return "SQL 쿼리는 생성되었지만 실행 결과를 가져올 수 없습니다."
            else:
                return "죄송합니다. 적절한 답변을 찾을 수 없습니다."
        
        except Exception as e:
            logger.error(f"결과 통합 중 오류 발생: {e}")
            return "죄송합니다. 답변을 생성하는 중 오류가 발생했습니다."
    
    def _calculate_confidence(self, document_result: Optional[PipelineResult],
                            sql_result: Optional[PipelineResult]) -> float:
        """기본 신뢰도 계산"""
        if document_result and sql_result:
            # 하이브리드 결과: 두 결과의 가중 평균
            doc_confidence = document_result.confidence_score
            sql_confidence = sql_result.confidence_score
            return (doc_confidence * 0.6 + sql_confidence * 0.4)
        elif document_result:
            return document_result.confidence_score
        elif sql_result:
            return sql_result.confidence_score
        else:
            return 0.0
    
    def _calculate_confidence_with_expressions(self, document_result: Optional[PipelineResult],
                                             sql_result: Optional[PipelineResult],
                                             analyzed_question: AnalyzedQuestion) -> float:
        """표현을 고려한 신뢰도 계산"""
        base_confidence = self._calculate_confidence(document_result, sql_result)
        
        # 표현 기반 신뢰도 보정
        if analyzed_question.metadata and "expressions" in analyzed_question.metadata:
            expression_count = len(analyzed_question.metadata["expressions"])
            expression_boost = min(expression_count * 0.05, 0.2)  # 최대 20% 보정
            base_confidence += expression_boost
        
        return min(base_confidence, 1.0)
    
    def _update_expression_feedback(self, question: str, analyzed_question: AnalyzedQuestion, context: str):
        """표현 사용 피드백 업데이트"""
        if self.expression_enhancer and analyzed_question.metadata:
            expressions_used = analyzed_question.metadata.get("expressions", [])
            if expressions_used:
                # 임시로 성공으로 처리 (실제로는 사용자 피드백 필요)
                self.expression_enhancer.update_expression_feedback(
                    question, expressions_used, success=True
                )
    
    def update_database_schema(self, schema: DatabaseSchema):
        """데이터베이스 스키마 업데이트"""
        self.database_schema = schema
        logger.info(f"데이터베이스 스키마 업데이트: {schema.table_name}")
    
    def add_few_shot_example(self, question: str, sql: str):
        """Few-shot 예시 추가"""
        self.few_shot_examples.append({"question": question, "sql": sql})
        logger.info(f"Few-shot 예시 추가: {question}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """파이프라인 통계 반환"""
        return {
            "sql_generator_stats": self.sql_generator.get_cache_stats(),
            "few_shot_examples_count": len(self.few_shot_examples),
            "database_schema_available": self.database_schema is not None
        }

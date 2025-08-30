"""
질문 분석 및 컨텍스트 관리 모듈

이 모듈은 사용자의 자연어 질문을 분석하고, 이전 대화 내용을 고려하여
적절한 컨텍스트를 유지하는 기능을 제공합니다.
"""

import re
import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import logging
logger = logging.getLogger(__name__)

# 키워드 향상 모듈 import
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.keyword_enhancer import KeywordEnhancer

# 핵심요소 추출 및 컨텍스트 연속성 관리 모듈 import
from .core_element_extractor import CoreElementExtractor, ExtractedElements
from .context_continuity_manager import ContextContinuityManager, ConversationContext, ContinuityResult
from .intent_classifier import IntentResult, IntentType, IntentClassifier

class QuestionType(Enum):
    """질문 유형 분류"""
    GREETING = "greeting"            # 인사말 (안녕, 반갑, 하이 등)
    FACTUAL = "factual"              # 사실 질문 (무엇, 언제, 어디서)
    CONCEPTUAL = "conceptual"        # 개념 질문 (어떻게, 왜)
    COMPARATIVE = "comparative"      # 비교 질문 (차이점, 유사점)
    PROCEDURAL = "procedural"        # 절차 질문 (방법, 단계)
    ANALYTICAL = "analytical"        # 분석 질문 (분석, 평가)
    FOLLOW_UP = "follow_up"         # 후속 질문 (이전 답변 관련)
    CLARIFICATION = "clarification"  # 명확화 질문 (구체적 설명 요구)
    DATABASE_QUERY = "database_query"  # 데이터베이스 질의 (SQL 생성 필요)
    QUANTITATIVE = "quantitative"    # 정량적 질문 (얼마나, 몇 개, 통행량 등)
    LOCATION_MOVEMENT = "location_movement"  # 장소 이동 요청 (조치원으로 이동 등)

@dataclass
class ConversationItem:
    """대화 항목 데이터 클래스"""
    question: str
    answer: str
    timestamp: datetime
    question_type: QuestionType
    relevant_chunks: List[str]  # 답변에 사용된 청크 ID들
    confidence_score: float = 0.0
    metadata: Optional[Dict] = None

@dataclass 
class AnalyzedQuestion:
    """분석된 질문 데이터 클래스"""
    original_question: str
    processed_question: str
    question_type: QuestionType
    keywords: List[str]
    entities: List[str]
    intent: str
    context_keywords: List[str]  # 이전 대화에서 가져온 키워드
    requires_sql: bool = False  # SQL 생성 필요 여부
    sql_intent: Optional[str] = None  # SQL 의도 (SELECT, INSERT, UPDATE, DELETE)
    embedding: Optional[np.ndarray] = None
    metadata: Optional[Dict] = None
    # 새로운 필드들
    core_elements: Optional[ExtractedElements] = None  # 추출된 핵심요소
    enhanced_question: Optional[str] = None  # 향상된 질문
    continuity_result: Optional[ContinuityResult] = None  # 연속성 분석 결과

class QuestionAnalyzer:
    """
    질문 분석 및 컨텍스트 관리 클래스
    
    주요 기능:
    1. 질문 유형 분류
    2. 키워드 및 개체명 추출
    3. 이전 대화 컨텍스트 관리
    4. 질문 의도 분석
    5. 후속 질문 처리
    """
    
    def __init__(self, embedding_model: str = "jhgan/ko-sroberta-multitask", domain: str = "general"):
        """
        QuestionAnalyzer 초기화
        
        Args:
            embedding_model: 임베딩 모델 이름
            domain: 도메인 (general, technical, business, academic 등)
        """
        # 임베딩 모델 로드
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"질문 분석용 임베딩 모델 로드: {embedding_model}")
        except Exception as e:
            logger.warning(f"한국어 모델 로드 실패, 기본 모델 사용: {e}")
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # TF-IDF 벡터라이저 (키워드 추출용)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            stop_words=None
        )
        
        # 키워드 향상 모듈 초기화
        self.keyword_enhancer = KeywordEnhancer(domain=domain)
        
        # 핵심요소 추출기 초기화
        self.core_element_extractor = CoreElementExtractor()
        
        # 컨텍스트 연속성 관리자 초기화
        self.context_manager = ContextContinuityManager()
        
        # 의도 분류기 초기화 (시스템 시작 시 미리 초기화)
        self.intent_classifier = None
        try:
            if IntentClassifier is not None:
                self.intent_classifier = IntentClassifier()
                logger.info("✓ 의도 분류기 초기화 완료")
        except Exception as e:
            logger.warning(f"의도 분류기 초기화 실패: {e}")
            self.intent_classifier = None
        
        # 대화 기록 저장
        self.conversation_history: List[ConversationItem] = []
        
        # 현재 대화 컨텍스트
        self.current_context = ConversationContext()
        
        # 질문 유형 분류를 위한 패턴 (개선된 버전)
        self.question_patterns = {
            QuestionType.FACTUAL: [
                r'무엇', r'뭐', r'언제', r'어디', r'누구', r'몇', r'얼마',
                r'어떤', r'어느', r'몇 개', r'몇 명'
            ],
            QuestionType.CONCEPTUAL: [
                r'어떻게', r'왜', r'이유', r'원인', r'목적', r'의미',
                r'정의', r'개념', r'원리'
            ],
            QuestionType.COMPARATIVE: [
                r'차이', r'비교', r'다른점', r'같은점', r'유사', r'반대',
                r'vs', r'대비', r'구별'
            ],
            QuestionType.PROCEDURAL: [
                r'방법', r'단계', r'과정', r'절차', r'순서', r'어떻게 하',
                r'진행', r'실행'
            ],
            QuestionType.ANALYTICAL: [
                r'분석', r'평가', r'장단점', r'문제점', r'해결', r'개선',
                r'영향', r'결과', r'효과'
            ],
            QuestionType.FOLLOW_UP: [
                r'그럼', r'그러면', r'그것', r'이것', r'저것', r'앞서',
                r'위에서', r'이전', r'방금', r'더', r'추가로'
            ],
            QuestionType.CLARIFICATION: [
                r'구체적으로', r'자세히', r'정확히', r'명확히', r'구체적',
                r'상세히', r'더 자세히', r'보다 구체적'
            ],
            QuestionType.QUANTITATIVE: [
                # 정량적 질문 패턴 (우선순위 높음)
                r'통행량\s*[이]?\s*얼마', r'교통량\s*[이]?\s*얼마', r'사고\s*[가]?\s*몇\s*건',
                r'평균\s*[이]?\s*얼마', r'최대\s*[가]?\s*얼마', r'최소\s*[가]?\s*얼마',
                r'합계\s*[가]?\s*얼마', r'총\s*[이]?\s*얼마', r'갯수\s*[가]?\s*얼마',
                r'얼마나\s*많', r'몇\s*개', r'몇\s*명', r'몇\s*대', r'몇\s*건', r'몇\s*회',
                r'count', r'sum', r'avg', r'max', r'min', r'total',
                r'통계', r'집계', r'분석', r'데이터\s*분석'
            ],
            QuestionType.LOCATION_MOVEMENT: [
                # 장소 이동 요청 패턴
                r'[으]?로\s*이동', r'[으]?로\s*가', r'[으]?로\s*보여', r'[으]?로\s*전환',
                r'[으]?로\s*바꿔', r'[으]?로\s*변경', r'[으]?로\s*이동해', r'[으]?로\s*가줘',
                r'[으]?로\s*보여줘', r'[으]?로\s*전환해', r'[으]?로\s*바꿔줘',
                r'이동\s*[해줘]?', r'가\s*[줘]?', r'보여\s*[줘]?', r'전환\s*[해줘]?',
                r'바꿔\s*[줘]?', r'변경\s*[해줘]?'
            ],
            QuestionType.DATABASE_QUERY: [
                # 데이터베이스 관련 키워드
                r'데이터', r'테이블', r'레코드', r'행', r'컬럼', r'필드', r'DB', r'데이터베이스',
                # 조회 관련 키워드
                r'조회', r'검색', r'찾기', r'가져오기', r'추출', r'보기', r'확인', r'출력',
                r'리스트', r'목록', r'데이터 목록', r'정보 조회',
                # 통계 관련 키워드
                r'통계', r'집계', r'분석', r'개수', r'합계', r'평균', r'최대', r'최소', r'총계', r'갯수',
                r'count', r'sum', r'avg', r'max', r'min', r'total',
                # 필터링/정렬 관련
                r'정렬', r'필터', r'조건', r'where', r'order by', r'group by',
                r'순서', r'기준', r'기간', r'날짜', r'시간', r'기준',
                # SQL 키워드
                r'select', r'insert', r'update', r'delete', r'from', r'join',
                r'where', r'group by', r'order by', r'limit', r'offset',
                # 교통 관련 데이터 키워드
                r'교통량', r'교차로', r'사고', r'인시던트', r'교통사고', r'교통 흐름',
                r'평균속도', r'총 교통량', r'혼잡도', r'교통상황',
                # 특정 패턴
                r'얼마나', r'어떤', r'어디서', r'언제', r'누가',
                r'가장 많이', r'가장 적게', r'평균적으로', r'대부분'
            ]
        }
        
        # 한국어 불용어 (간단한 버전)
        self.stopwords = {
            '은', '는', '이', '가', '을', '를', '의', '에', '에서', '로', '으로',
            '와', '과', '도', '만', '까지', '부터', '께서', '한테', '에게',
            '그', '저', '이', '그것', '저것', '이것', '것', '수', '때'
        }
        
        logger.info(f"QuestionAnalyzer 초기화 완료 (도메인: {domain})")
    
    def analyze_question(self, question: str, 
                        use_conversation_context: bool = True) -> AnalyzedQuestion:
        """
        질문을 종합적으로 분석 (개선된 버전 - 컨텍스트 연속성 고려)
        
        Args:
            question: 사용자 질문
            use_conversation_context: 이전 대화 컨텍스트 사용 여부
            
        Returns:
            분석된 질문 객체
        """
        # 1. 질문 전처리
        processed_question = self._preprocess_question(question)
        
        # 2. 핵심요소 추출
        core_elements = self.core_element_extractor.extract_core_elements(question)
        
        # 3. 컨텍스트 연속성 분석
        continuity_result = None
        enhanced_question = question
        
        if use_conversation_context and self.conversation_history:
            # 이전 질문의 핵심요소 추출
            previous_question = self.conversation_history[-1].question
            previous_elements = self.core_element_extractor.extract_core_elements(previous_question)
            
            # 연속성 분석
            continuity_result = self.context_manager.check_context_continuity(
                question, self.current_context, core_elements, previous_elements
            )
            
            # 컨텍스트 병합 (필요시)
            if continuity_result.should_merge:
                enhanced_question = continuity_result.enhanced_question or question
                core_elements = self.context_manager.merge_context(
                    core_elements, previous_elements, continuity_result
                )
                
                # 컨텍스트 업데이트
                self.current_context = self.context_manager.update_conversation_context(
                    self.current_context, core_elements, continuity_result
                )
        
        # 4. 질문 유형 분류 (향상된 질문 사용)
        question_type = self._classify_question_type(enhanced_question)
        
        # 5. 키워드 추출 (핵심요소 기반)
        keywords = self._extract_keywords_with_core_elements(enhanced_question, core_elements)
        
        # 6. 개체명 추출
        entities = self._extract_entities(enhanced_question)
        
        # 7. 질문 의도 분석 (의도 분류기 사용)
        intent_result = None
        if self.intent_classifier is not None:
            try:
                # 의도 분류 수행 (이미 초기화된 분류기 사용)
                intent_result = self.intent_classifier.classify_intent(enhanced_question)
                intent = intent_result.intent.value
                
                # 메타데이터에 의도 분류 정보 추가
                intent_metadata = {
                    "intent_confidence": intent_result.confidence,
                    "intent_classifier_used": intent_result.classifier_used,
                    "intent_processing_time": intent_result.processing_time
                }
            except Exception as e:
                logger.warning(f"의도 분류기 사용 실패, 기본 의도 분석 사용: {e}")
                intent = self._analyze_intent(enhanced_question, question_type)
                intent_result = None
                intent_metadata = {}
        else:
            # 의도 분류기가 없는 경우 기본 의도 분석 사용
            intent = self._analyze_intent(enhanced_question, question_type)
            intent_metadata = {}
        
        # 8. 컨텍스트 키워드 추출
        context_keywords = []
        if use_conversation_context and self.conversation_history:
            context_keywords = self._extract_context_keywords(enhanced_question)
        
        # 9. SQL 필요 여부 및 의도 분석 (의도 분류 결과 활용)
        if intent_result is not None:
            requires_sql, sql_intent = self._analyze_sql_requirements_with_intent(enhanced_question, question_type, intent_result)
        else:
            requires_sql, sql_intent = self._analyze_sql_requirements(enhanced_question, question_type)
        
        # 10. 임베딩 생성
        embedding = self.embedding_model.encode(enhanced_question)
        
        # 메타데이터에 의도 분류 정보 추가
        metadata = {
            "analysis_timestamp": datetime.now().isoformat(),
            "has_context": len(context_keywords) > 0,
            "continuity_type": continuity_result.continuity_type.value if continuity_result else "none",
            "overlap_score": continuity_result.overlap_score if continuity_result else 0.0
        }
        metadata.update(intent_metadata)
        
        analyzed_question = AnalyzedQuestion(
            original_question=question,
            processed_question=enhanced_question,
            question_type=question_type,
            keywords=keywords,
            entities=entities,
            intent=intent,
            context_keywords=context_keywords,
            requires_sql=requires_sql,
            sql_intent=sql_intent,
            embedding=embedding,
            core_elements=core_elements,
            enhanced_question=enhanced_question,
            continuity_result=continuity_result,
            metadata=metadata
        )
        
        logger.info(f"질문 분석 완료: {question_type.value}, 키워드: {len(keywords)}개, 연속성: {continuity_result.continuity_type.value if continuity_result else 'none'}")
        return analyzed_question
    
    def analyze_question_with_expressions(self, question: str, 
                                        conversation_history: Optional[List[ConversationItem]] = None,
                                        expression_enhancer=None) -> AnalyzedQuestion:
        """
        다중 표현을 고려한 질문 분석
        
        Args:
            question: 분석할 질문
            conversation_history: 대화 히스토리
            expression_enhancer: 표현 향상기 (KeywordEnhancer)
            
        Returns:
            분석된 질문 정보
        """
        # 기본 질문 분석
        analyzed = self.analyze_question(question, conversation_history)
        
        # 다중 표현 분석 추가
        if expression_enhancer:
            analyzed = self._enhance_analysis_with_expressions(analyzed, expression_enhancer)
        
        return analyzed
    
    def _is_greeting(self, question: str) -> bool:
        """
        인사말인지 확인
        
        Args:
            question: 확인할 질문
            
        Returns:
            인사말 여부
        """
        # 인사말 패턴들
        greeting_patterns = [
            r'안녕',
            r'반갑',
            r'하이',
            r'hi',
            r'hello',
            r'좋은\s*(아침|점심|저녁|하루)',
            r'만나서\s*반가워',
            r'반가워',
            r'인사',
            r'오랜만',
            r'오래간만',
            r'잘\s*지내',
            r'어떻게\s*지내',
            r'안녕하세요',
            r'안녕하십니까',
            r'반갑습니다',
            r'반가워요',
            r'하이하이',
            r'헬로',
            r'헬로우'
        ]
        
        question_lower = question.lower().strip()
        
        # 패턴 매칭
        for pattern in greeting_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return True
        
        # 단순한 인사말 확인 (2단어 이하)
        words = question_lower.split()
        if len(words) <= 2:
            simple_greetings = ['안녕', '하이', 'hi', 'hello', '반가워', '반갑다']
            if any(word in simple_greetings for word in words):
                return True
        
        return False
    
    def _enhance_analysis_with_expressions(self, analyzed: AnalyzedQuestion, 
                                         expression_enhancer) -> AnalyzedQuestion:
        """표현을 활용한 분석 강화"""
        # 컨텍스트 결정
        context = self._determine_context(analyzed.original_question)
        
        # 관련 표현들 추출
        expressions = expression_enhancer.get_multi_expressions(
            analyzed.original_question, context
        )
        
        # 최적 표현 선택
        optimal_expressions = expression_enhancer.get_optimal_expressions(
            analyzed.original_question, context, top_k=3
        )
        
        # 키워드 확장
        enhanced_keywords = analyzed.keywords.copy()
        for expr, score in optimal_expressions:
            if expr not in enhanced_keywords:
                enhanced_keywords.append(expr)
        
        # 의도 분석 강화
        enhanced_intent = self._analyze_intent_with_expressions(
            analyzed.original_question, expressions, context
        )
        
        # 메타데이터에 표현 정보 추가
        expression_metadata = {
            "context": context,
            "expressions": expressions,
            "optimal_expressions": optimal_expressions,
            "expression_count": len(expressions)
        }
        
        if analyzed.metadata is None:
            analyzed.metadata = {}
        analyzed.metadata.update(expression_metadata)
        
        # 분석 결과 업데이트
        analyzed.keywords = enhanced_keywords
        analyzed.intent = enhanced_intent
        
        return analyzed
    
    def _determine_context(self, question: str) -> str:
        """질문의 컨텍스트 결정"""
        question_lower = question.lower()
        
        # 교통 관련 키워드
        traffic_keywords = ["교통", "사고", "교차로", "신호등", "교통량", "정체", "교통사고"]
        if any(keyword in question_lower for keyword in traffic_keywords):
            return "traffic"
        
        # 데이터베이스 관련 키워드
        db_keywords = ["조회", "통계", "데이터", "테이블", "SELECT", "COUNT", "WHERE"]
        if any(keyword in question_lower for keyword in db_keywords):
            return "database"
        
        return "general"
    
    def _analyze_intent_with_expressions(self, question: str, 
                                       expressions: List[str], 
                                       context: str) -> str:
        """표현을 고려한 의도 분석"""
        question_lower = question.lower()
        
        # 기본 의도 분석
        base_intent = self._analyze_basic_intent(question)
        
        # 표현 기반 의도 보정
        if context == "traffic":
            if any(expr in question_lower for expr in ["사고", "충돌", "발생"]):
                return "traffic_accident_inquiry"
            elif any(expr in question_lower for expr in ["교통량", "트래픽", "정체"]):
                return "traffic_volume_inquiry"
            elif any(expr in question_lower for expr in ["교차로", "신호등", "신호"]):
                return "traffic_signal_inquiry"
        
        elif context == "database":
            if any(expr in question_lower for expr in ["조회", "검색", "찾기"]):
                return "data_retrieval"
            elif any(expr in question_lower for expr in ["통계", "집계", "평균"]):
                return "data_analysis"
            elif any(expr in question_lower for expr in ["기간", "날짜", "시간"]):
                return "temporal_analysis"
        
        return base_intent
    
    def _analyze_basic_intent(self, question: str) -> str:
        """기본 의도 분석"""
        question_lower = question.lower()
        
        # 질문 유형별 의도 분류
        if any(word in question_lower for word in ["무엇", "뭐", "어떤"]):
            return "what_inquiry"
        elif any(word in question_lower for word in ["언제", "몇시", "날짜"]):
            return "when_inquiry"
        elif any(word in question_lower for word in ["어디", "장소", "위치"]):
            return "where_inquiry"
        elif any(word in question_lower for word in ["누가", "누구", "사람"]):
            return "who_inquiry"
        elif any(word in question_lower for word in ["왜", "이유", "원인"]):
            return "why_inquiry"
        elif any(word in question_lower for word in ["어떻게", "방법", "과정"]):
            return "how_inquiry"
        else:
            return "general_inquiry"
    
    def get_expression_suggestions(self, question: str, 
                                 expression_enhancer=None,
                                 context: str = "general") -> List[str]:
        """
        질문에 대한 표현 제안
        
        Args:
            question: 원본 질문
            expression_enhancer: 표현 향상기
            context: 컨텍스트
            
        Returns:
            제안 표현 리스트
        """
        if not expression_enhancer:
            return []
        
        # 관련 표현들 가져오기
        expressions = expression_enhancer.get_multi_expressions(question, context)
        
        # 질문 개선 제안 생성
        suggestions = []
        for expr in expressions[:5]:  # 상위 5개만 사용
            if expr.lower() not in question.lower():
                # 질문에 표현을 추가한 제안 생성
                suggestion = f"{question} ({expr} 관련)"
                suggestions.append(suggestion)
        
        return suggestions
    
    def update_expression_feedback(self, question: str, 
                                 expressions_used: List[str],
                                 success: bool,
                                 expression_enhancer=None):
        """
        표현 사용 피드백 업데이트
        
        Args:
            question: 원본 질문
            expressions_used: 사용된 표현들
            success: 성공 여부
            expression_enhancer: 표현 향상기
        """
        if expression_enhancer:
            expression_enhancer.update_expression_feedback(
                question, expressions_used, success
            )
    
    def _preprocess_question(self, question: str) -> str:
        """
        질문 전처리
        
        Args:
            question: 원본 질문
            
        Returns:
            전처리된 질문
        """
        # 공백 정리
        question = re.sub(r'\s+', ' ', question.strip())
        
        # 불필요한 문자 제거
        question = re.sub(r'[^\w\s가-힣?!.]', ' ', question)
        
        # 연속된 공백 제거
        question = re.sub(r'\s+', ' ', question)
        
        return question.strip()
    
    def _classify_question_type(self, question: str) -> QuestionType:
        """
        질문 유형 분류 (개선된 버전)
        
        Args:
            question: 전처리된 질문
            
        Returns:
            질문 유형
        """
        # 먼저 인사말인지 확인
        if self._is_greeting(question):
            return QuestionType.GREETING
        
        question_lower = question.lower()
        
        # 우선순위가 높은 유형들을 먼저 확인
        priority_types = [
            QuestionType.LOCATION_MOVEMENT,  # 장소 이동 요청 (최우선)
            QuestionType.QUANTITATIVE,       # 정량적 질문 (우선)
            QuestionType.DATABASE_QUERY      # 데이터베이스 질의
        ]
        
        for q_type in priority_types:
            if q_type in self.question_patterns:
                patterns = self.question_patterns[q_type]
                for pattern in patterns:
                    if re.search(pattern, question_lower):
                        return q_type
        
        # 나머지 유형들에 대해 점수 계산
        type_scores = {}
        
        for q_type, patterns in self.question_patterns.items():
            if q_type not in priority_types:  # 이미 확인한 우선순위 유형 제외
                score = 0
                for pattern in patterns:
                    if re.search(pattern, question_lower):
                        score += 1
                type_scores[q_type] = score
        
        # 가장 높은 점수의 유형 반환
        if type_scores and max(type_scores.values()) > 0:
            return max(type_scores, key=type_scores.get)
        
        # 기본값: FACTUAL
        return QuestionType.FACTUAL
    
    def _extract_keywords(self, question: str) -> List[str]:
        """
        질문에서 키워드 추출 (기본 버전)
        
        Args:
            question: 전처리된 질문
            
        Returns:
            키워드 리스트
        """
        # 1. 기본 토큰화 및 불용어 제거
        tokens = question.split()
        basic_keywords = []
        
        for token in tokens:
            # 불용어 제거
            if token not in self.stopwords and len(token) > 1:
                # 특수문자 제거
                clean_token = re.sub(r'[^\w가-힣]', '', token)
                if clean_token and len(clean_token) > 1:
                    basic_keywords.append(clean_token)
        
        # 2. 키워드 향상 (동의어, 약어 확장 등)
        enhanced_keywords = self.keyword_enhancer.enhance_keywords(basic_keywords)
        
        # 3. 도메인 특화 키워드 추가
        domain_keywords = self.keyword_enhancer.extract_domain_specific_keywords(question)
        enhanced_keywords.extend(domain_keywords)
        
        # 4. 중복 제거 및 정렬
        unique_keywords = list(set(enhanced_keywords))
        unique_keywords.sort(key=len, reverse=True)  # 긴 키워드 우선
        
        # 5. 키워드 가중치 계산 및 상위 키워드 선택
        keyword_weights = []
        for keyword in unique_keywords:
            weight = self.keyword_enhancer.calculate_keyword_weight(keyword, question)
            keyword_weights.append((keyword, weight))
        
        # 가중치로 정렬하고 상위 15개 선택
        keyword_weights.sort(key=lambda x: x[1], reverse=True)
        top_keywords = [kw for kw, _ in keyword_weights[:15]]
        
        return top_keywords
    
    def _extract_keywords_with_core_elements(self, question: str, core_elements: ExtractedElements) -> List[str]:
        """
        핵심요소를 고려한 키워드 추출 (개선된 버전)
        
        Args:
            question: 전처리된 질문
            core_elements: 추출된 핵심요소
            
        Returns:
            키워드 리스트
        """
        # 1. 기본 키워드 추출
        basic_keywords = self._extract_keywords(question)
        
        # 2. 핵심요소에서 키워드 추가
        core_keywords = []
        
        # 주제 키워드 (높은 우선순위)
        if core_elements.topic:
            core_keywords.append(core_elements.topic.text)
        
        # 개체 키워드 (중간 우선순위)
        for entity in core_elements.entities:
            if entity.text not in core_keywords:
                core_keywords.append(entity.text)
        
        # 속성 키워드 (중간 우선순위)
        for attr in core_elements.attributes:
            if attr.text not in core_keywords:
                core_keywords.append(attr.text)
        
        # 관계 키워드 (낮은 우선순위)
        for relation in core_elements.relations:
            if relation.text not in core_keywords:
                core_keywords.append(relation.text)
        
        # 시간 키워드 (낮은 우선순위)
        for temporal in core_elements.temporal:
            if temporal.text not in core_keywords:
                core_keywords.append(temporal.text)
        
        # 위치 키워드 (중간 우선순위)
        for location in core_elements.locations:
            if location.text not in core_keywords:
                core_keywords.append(location.text)
        
        # 3. 키워드 통합 및 우선순위 적용
        all_keywords = []
        
        # 핵심요소 키워드를 먼저 추가 (높은 우선순위)
        all_keywords.extend(core_keywords)
        
        # 기본 키워드 추가 (중복 제거)
        for keyword in basic_keywords:
            if keyword not in all_keywords:
                all_keywords.append(keyword)
        
        # 4. 키워드 향상
        enhanced_keywords = self.keyword_enhancer.enhance_keywords(all_keywords)
        
        # 5. 도메인 특화 키워드 추가
        domain_keywords = self.keyword_enhancer.extract_domain_specific_keywords(question)
        enhanced_keywords.extend(domain_keywords)
        
        # 6. 중복 제거 및 정렬
        unique_keywords = list(set(enhanced_keywords))
        unique_keywords.sort(key=len, reverse=True)  # 긴 키워드 우선
        
        # 7. 키워드 가중치 계산 및 상위 키워드 선택
        keyword_weights = []
        for keyword in unique_keywords:
            weight = self.keyword_enhancer.calculate_keyword_weight(keyword, question)
            # 핵심요소 키워드에 가중치 부여
            if keyword in core_keywords:
                weight *= 1.5
            keyword_weights.append((keyword, weight))
        
        # 가중치로 정렬하고 상위 20개 선택 (핵심요소 고려로 더 많은 키워드)
        keyword_weights.sort(key=lambda x: x[1], reverse=True)
        top_keywords = [kw for kw, _ in keyword_weights[:20]]
        
        return top_keywords
    
    def _extract_entities(self, question: str) -> List[str]:
        """
        간단한 개체명 추출 (규칙 기반)
        
        Args:
            question: 전처리된 질문
            
        Returns:
            개체명 리스트
        """
        entities = []
        
        # 숫자 패턴
        numbers = re.findall(r'\d+(?:\.\d+)?', question)
        entities.extend([f"NUMBER_{num}" for num in numbers])
        
        # 날짜 패턴 (간단한 형태만)
        dates = re.findall(r'\d{4}년|\d+월|\d+일', question)
        entities.extend([f"DATE_{date}" for date in dates])
        
        # 단위 패턴
        units = re.findall(r'\d+(?:개|명|번|회|년|월|일|시간|분|초)', question)
        entities.extend([f"UNIT_{unit}" for unit in units])
        
        return entities
    
    def _analyze_intent(self, question: str, question_type: QuestionType) -> str:
        """
        질문 의도 분석
        
        Args:
            question: 전처리된 질문
            question_type: 질문 유형
            
        Returns:
            질문 의도
        """
        intent_keywords = {
            "정보_요청": ["알려주", "알고 싶", "궁금", "설명", "무엇", "뭐"],
            "비교_요청": ["차이", "비교", "다른", "같은", "유사"],
            "방법_문의": ["어떻게", "방법", "어떤 식", "어떤 방식"],
            "확인_요청": ["맞는지", "정확한지", "확인", "검증"],
            "추가_정보": ["더", "추가", "상세", "자세히", "구체적"],
            "명확화": ["정확히", "명확히", "확실히", "분명히"]
        }
        
        question_lower = question.lower()
        intent_scores = {}
        
        for intent, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            intent_scores[intent] = score
        
        # 가장 높은 점수의 의도 반환
        if max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        
        # 질문 유형에 따른 기본 의도
        default_intents = {
            QuestionType.FACTUAL: "정보_요청",
            QuestionType.CONCEPTUAL: "정보_요청", 
            QuestionType.COMPARATIVE: "비교_요청",
            QuestionType.PROCEDURAL: "방법_문의",
            QuestionType.ANALYTICAL: "정보_요청",
            QuestionType.FOLLOW_UP: "추가_정보",
            QuestionType.CLARIFICATION: "명확화"
        }
        
        return default_intents.get(question_type, "정보_요청")
    
    def _extract_context_keywords(self, question: str) -> List[str]:
        """
        이전 대화에서 관련 키워드 추출
        
        Args:
            question: 현재 질문
            
        Returns:
            컨텍스트 키워드 리스트
        """
        if not self.conversation_history:
            return []
        
        context_keywords = []
        
        # 최근 3개 대화에서 키워드 추출
        recent_conversations = self.conversation_history[-3:]
        
        for conv_item in recent_conversations:
            # 이전 질문과 답변에서 키워드 추출
            prev_text = conv_item.question + " " + conv_item.answer
            prev_keywords = self._extract_keywords(prev_text)
            
            # 현재 질문과의 유사도 계산
            current_keywords = set(self._extract_keywords(question))
            prev_keywords_set = set(prev_keywords)
            
            # 공통 키워드가 있으면 관련성이 높음
            common_keywords = current_keywords & prev_keywords_set
            if common_keywords:
                context_keywords.extend(prev_keywords)
        
        # 중복 제거 및 빈도 기반 정렬
        from collections import Counter
        keyword_counts = Counter(context_keywords)
        
        # 상위 5개 키워드만 반환
        return [keyword for keyword, _ in keyword_counts.most_common(5)]
    
    def add_conversation_item(self, question: str, answer: str, 
                            relevant_chunks: List[str],
                            confidence_score: float = 0.0) -> None:
        """
        대화 항목을 기록에 추가 (개선된 버전 - 컨텍스트 관리 포함)
        
        Args:
            question: 질문
            answer: 답변
            relevant_chunks: 답변에 사용된 청크 ID들
            confidence_score: 답변 신뢰도
        """
        # 질문 분석 (컨텍스트 연속성 고려)
        analyzed_q = self.analyze_question(question, use_conversation_context=True)
        
        # 컨텍스트 정보 추가
        context_info = {}
        if analyzed_q.continuity_result:
            context_info.update({
                "continuity_type": analyzed_q.continuity_result.continuity_type.value,
                "overlap_score": analyzed_q.continuity_result.overlap_score,
                "should_merge": analyzed_q.continuity_result.should_merge,
                "missing_elements_count": len(analyzed_q.continuity_result.missing_elements)
            })
        
        if analyzed_q.core_elements:
            context_info.update({
                "topic": analyzed_q.core_elements.topic.text if analyzed_q.core_elements.topic else None,
                "entities_count": len(analyzed_q.core_elements.entities),
                "attributes_count": len(analyzed_q.core_elements.attributes)
            })
        
        conv_item = ConversationItem(
            question=question,
            answer=answer,
            timestamp=datetime.now(),
            question_type=analyzed_q.question_type,
            relevant_chunks=relevant_chunks,
            confidence_score=confidence_score,
            metadata={
                "keywords": analyzed_q.keywords,
                "intent": analyzed_q.intent,
                "enhanced_question": analyzed_q.enhanced_question,
                "context_info": context_info,
                "conversation_depth": self.current_context.depth
            }
        )
        
        self.conversation_history.append(conv_item)
        
        # 메모리 관리: 최대 50개 대화만 유지
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
        
        logger.info(f"대화 항목 추가: {analyzed_q.question_type.value}, 연속성: {analyzed_q.continuity_result.continuity_type.value if analyzed_q.continuity_result else 'none'}")
    
    def get_conversation_context(self, max_items: int = 3) -> List[Dict]:
        """
        최근 대화 컨텍스트 반환
        
        Args:
            max_items: 최대 반환할 대화 항목 수
            
        Returns:
            대화 컨텍스트 리스트
        """
        recent_conversations = self.conversation_history[-max_items:]
        
        context = []
        for conv_item in recent_conversations:
            context.append({
                "question": conv_item.question,
                "answer": conv_item.answer,
                "question_type": conv_item.question_type.value,
                "timestamp": conv_item.timestamp.isoformat(),
                "confidence": conv_item.confidence_score
            })
        
        return context
    
    def find_similar_previous_questions(self, current_question: str, 
                                      threshold: float = 0.7,
                                      top_k: int = 3) -> List[Tuple[ConversationItem, float]]:
        """
        유사한 이전 질문 찾기
        
        Args:
            current_question: 현재 질문
            threshold: 유사도 임계값
            top_k: 반환할 최대 결과 수
            
        Returns:
            (대화항목, 유사도) 튜플 리스트
        """
        if not self.conversation_history:
            return []
        
        # 현재 질문 임베딩
        current_embedding = self.embedding_model.encode([current_question])
        
        # 이전 질문들과 유사도 계산
        similarities = []
        
        for conv_item in self.conversation_history:
            # 이전 질문 임베딩
            prev_embedding = self.embedding_model.encode([conv_item.question])
            
            # 코사인 유사도 계산
            similarity = cosine_similarity(current_embedding, prev_embedding)[0][0]
            
            if similarity >= threshold:
                similarities.append((conv_item, similarity))
        
        # 유사도 순으로 정렬하여 상위 k개 반환
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def save_conversation_history(self, file_path: str) -> None:
        """
        대화 기록을 파일로 저장
        
        Args:
            file_path: 저장할 파일 경로
        """
        conversation_data = []
        
        for conv_item in self.conversation_history:
            item_dict = asdict(conv_item)
            item_dict['timestamp'] = conv_item.timestamp.isoformat()
            item_dict['question_type'] = conv_item.question_type.value
            conversation_data.append(item_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"대화 기록 저장 완료: {file_path}")
    
    def load_conversation_history(self, file_path: str) -> None:
        """
        파일에서 대화 기록 로드
        
        Args:
            file_path: 로드할 파일 경로
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            self.conversation_history = []
            
            for item_dict in conversation_data:
                conv_item = ConversationItem(
                    question=item_dict['question'],
                    answer=item_dict['answer'],
                    timestamp=datetime.fromisoformat(item_dict['timestamp']),
                    question_type=QuestionType(item_dict['question_type']),
                    relevant_chunks=item_dict['relevant_chunks'],
                    confidence_score=item_dict.get('confidence_score', 0.0),
                    metadata=item_dict.get('metadata', {})
                )
                self.conversation_history.append(conv_item)
            
            logger.info(f"대화 기록 로드 완료: {len(self.conversation_history)}개 항목")
            
        except Exception as e:
            logger.error(f"대화 기록 로드 실패: {e}")
    
    def _analyze_sql_requirements_with_intent(self, question: str, question_type: QuestionType, intent_result: IntentResult) -> Tuple[bool, Optional[str]]:
        """
        의도 분류 결과를 활용한 SQL 필요 여부 분석 (개선된 버전)
        
        Args:
            question: 처리된 질문
            question_type: 질문 유형
            intent_result: 의도 분류 결과
            
        Returns:
            (SQL 필요 여부, SQL 의도)
        """
        requires_sql = False
        sql_intent = None
        
        # 1. 의도 기반 SQL 필요 여부 판단
        sql_required_intents = [
            IntentType.DB_QUERY,
            IntentType.DATA_ANALYSIS,
            IntentType.STATISTICAL_QUERY,
            IntentType.RANKING_INQUIRY
        ]
        
        if intent_result.intent in sql_required_intents:
            requires_sql = True
            sql_intent = 'SELECT'
        
        # 2. 질문 유형 기반 보완 판단
        if question_type in [QuestionType.QUANTITATIVE, QuestionType.DATABASE_QUERY]:
            requires_sql = True
            sql_intent = 'SELECT'
        
        # 3. 특수 케이스: 장소 이동 요청은 SQL 불필요
        if intent_result.intent == IntentType.LOCATION_MOVEMENT or question_type == QuestionType.LOCATION_MOVEMENT:
            requires_sql = False
            sql_intent = None
        
        # 4. 신뢰도 기반 조정
        if intent_result.confidence < 0.6:
            # 신뢰도가 낮은 경우 기존 로직으로 보완
            fallback_requires_sql, fallback_sql_intent = self._analyze_sql_requirements(question, question_type)
            if not requires_sql and fallback_requires_sql:
                requires_sql = fallback_requires_sql
                sql_intent = fallback_sql_intent
        
        return requires_sql, sql_intent
    
    def _analyze_sql_requirements(self, question: str, question_type: QuestionType) -> Tuple[bool, Optional[str]]:
        """
        SQL 필요 여부 및 의도 분석 (보완용 - 기존 로직)
        
        Args:
            question: 처리된 질문
            question_type: 질문 유형
            
        Returns:
            (SQL 필요 여부, SQL 의도)
        """
        requires_sql = False
        sql_intent = None
        question_lower = question.lower()
        
        # 1. 정량적 질문 패턴 (통행량, 개수, 수치 등)
        quantitative_patterns = [
            r'얼마나', r'몇\s*개', r'몇\s*명', r'몇\s*대', r'몇\s*건', r'몇\s*회',
            r'통행량\s*[이]?\s*얼마', r'교통량\s*[이]?\s*얼마', r'사고\s*[가]?\s*몇\s*건',
            r'평균\s*[이]?\s*얼마', r'최대\s*[가]?\s*얼마', r'최소\s*[가]?\s*얼마',
            r'합계\s*[가]?\s*얼마', r'총\s*[이]?\s*얼마', r'갯수\s*[가]?\s*얼마',
            r'count', r'sum', r'avg', r'max', r'min', r'total',
            r'통계', r'집계', r'분석', r'데이터\s*분석'
        ]
        
        # 2. 장소 이동 요청 패턴
        location_movement_patterns = [
            r'[으]?로\s*이동', r'[으]?로\s*가', r'[으]?로\s*보여', r'[으]?로\s*전환',
            r'[으]?로\s*바꿔', r'[으]?로\s*변경', r'[으]?로\s*이동해', r'[으]?로\s*가줘',
            r'[으]?로\s*보여줘', r'[으]?로\s*전환해', r'[으]?로\s*바꿔줘',
            r'이동\s*[해줘]?', r'가\s*[줘]?', r'보여\s*[줘]?', r'전환\s*[해줘]?',
            r'바꿔\s*[줘]?', r'변경\s*[해줘]?'
        ]
        
        # 3. 질문 유형별 SQL 필요 여부 판단
        if question_type == QuestionType.LOCATION_MOVEMENT:
            # 장소 이동 요청은 SQL 불필요
            requires_sql = False
            sql_intent = None
        elif question_type == QuestionType.QUANTITATIVE:
            # 정량적 질문은 SQL 필요
            requires_sql = True
            sql_intent = 'SELECT'
        elif question_type == QuestionType.DATABASE_QUERY:
            requires_sql = True
            
            # SQL 의도 분석 (더 정확한 패턴 매칭)
            select_keywords = ['조회', '검색', '찾기', '가져오기', '추출', '개수', '합계', '평균', '최대', '최소', 
                             '보기', '확인', '출력', '리스트', '목록', '얼마나', '몇 개', '어떤', '어디서', '언제']
            insert_keywords = ['추가', '삽입', '등록', '생성', '입력', '저장']
            update_keywords = ['수정', '변경', '업데이트', '갱신', '편집']
            delete_keywords = ['삭제', '제거', '지우기', '제거']
            
            if any(word in question_lower for word in select_keywords):
                sql_intent = 'SELECT'
            elif any(word in question_lower for word in insert_keywords):
                sql_intent = 'INSERT'
            elif any(word in question_lower for word in update_keywords):
                sql_intent = 'UPDATE'
            elif any(word in question_lower for word in delete_keywords):
                sql_intent = 'DELETE'
            else:
                sql_intent = 'SELECT'  # 기본값
        
        # 4. 일반 질문이지만 정량적 질문인 경우 SQL 필요
        else:
            # 정량적 질문 패턴 확인
            quantitative_match = any(re.search(pattern, question_lower) for pattern in quantitative_patterns)
            
            # 장소 이동 요청 패턴 확인 (SQL 불필요)
            location_movement_match = any(re.search(pattern, question_lower) for pattern in location_movement_patterns)
            
            # 데이터베이스 관련 키워드
            db_keywords = ['데이터', '테이블', '레코드', '행', '컬럼', '필드', 'db', '데이터베이스']
            
            # 교통 관련 데이터 키워드
            traffic_keywords = ['교통량', '교차로', '사고', '인시던트', '교통사고', '교통 흐름', 
                              '평균속도', '총 교통량', '혼잡도', '교통상황']
            
            # 통계 관련 키워드
            stats_keywords = ['통계', '개수', '합계', '평균', '최대', '최소', '총계', '갯수', 'count', 'sum', 'avg', 'max', 'min']
            
            # 특정 질문 패턴
            sql_patterns = ['얼마나', '몇 개', '어떤', '어디서', '언제', '누가', '가장 많이', '가장 적게', '평균적으로', '대부분']
            
            # 장소 이동 요청이 아닌 경우에만 SQL 필요 여부 판단
            if not location_movement_match:
                # 정량적 질문이거나 SQL이 필요한 키워드가 2개 이상 포함된 경우
                matching_keywords = 0
                for keywords in [db_keywords, traffic_keywords, stats_keywords, sql_patterns]:
                    if any(word in question_lower for word in keywords):
                        matching_keywords += 1
                
                if quantitative_match or matching_keywords >= 2:
                    requires_sql = True
                    sql_intent = 'SELECT'
        
        return requires_sql, sql_intent
    
    def get_intent_classification_stats(self) -> Dict[str, Any]:
        """
        의도 분류 통계 반환
        
        Returns:
            의도 분류 통계 정보
        """
        return self.intent_classifier.get_classification_stats()
    
    def add_intent_training_example(self, question: str, intent: IntentType):
        """
        의도 분류기 학습 예시 추가
        
        Args:
            question: 학습할 질문
            intent: 정답 의도
        """
        self.intent_classifier.add_training_example(question, intent)
    
    def retrain_intent_classifier(self):
        """의도 분류기 재학습"""
        self.intent_classifier.retrain_classifiers()
    
    def save_intent_classifier(self, file_path: str):
        """의도 분류기 저장"""
        self.intent_classifier.save_classifier(file_path)
    
    def load_intent_classifier(self, file_path: str):
        """의도 분류기 로드"""
        self.intent_classifier.load_classifier(file_path)
    
    def get_current_context(self) -> ConversationContext:
        """
        현재 대화 컨텍스트 반환
        
        Returns:
            현재 대화 컨텍스트
        """
        return self.current_context
    
    def reset_context(self) -> None:
        """
        대화 컨텍스트 초기화
        """
        self.current_context = ConversationContext()
        logger.info("대화 컨텍스트 초기화 완료")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        현재 컨텍스트 요약 정보 반환
        
        Returns:
            컨텍스트 요약 정보
        """
        return {
            "topic": self.current_context.topic,
            "entities": self.current_context.entities,
            "attributes": self.current_context.attributes,
            "relations": self.current_context.relations,
            "temporal": self.current_context.temporal,
            "locations": self.current_context.locations,
            "depth": self.current_context.depth,
            "conversation_count": len(self.conversation_history)
        }
    
    def analyze_conversation_flow(self) -> Dict[str, Any]:
        """
        대화 흐름 분석
        
        Returns:
            대화 흐름 분석 결과
        """
        if len(self.conversation_history) < 2:
            return {"message": "분석할 대화가 충분하지 않습니다."}
        
        flow_analysis = {
            "total_conversations": len(self.conversation_history),
            "context_changes": 0,
            "continuity_scores": [],
            "topic_transitions": [],
            "average_depth": 0
        }
        
        continuity_scores = []
        topic_transitions = []
        
        for i in range(1, len(self.conversation_history)):
            prev_item = self.conversation_history[i-1]
            curr_item = self.conversation_history[i]
            
            # 연속성 점수 추출
            if "context_info" in curr_item.metadata:
                context_info = curr_item.metadata["context_info"]
                if "overlap_score" in context_info:
                    continuity_scores.append(context_info["overlap_score"])
                
                # 주제 전환 확인
                if "continuity_type" in context_info:
                    if context_info["continuity_type"] == "none":
                        flow_analysis["context_changes"] += 1
        
        if continuity_scores:
            flow_analysis["continuity_scores"] = continuity_scores
            flow_analysis["average_continuity"] = sum(continuity_scores) / len(continuity_scores)
        
        # 평균 대화 깊이 계산
        depths = [item.metadata.get("conversation_depth", 0) for item in self.conversation_history]
        flow_analysis["average_depth"] = sum(depths) / len(depths) if depths else 0
        
        return flow_analysis

    def classify_sql_vs_pdf(self, question: str, embedding: np.ndarray) -> Dict[str, Any]:
        """
        SQL 답변 vs PDF 답변 이진 분류
        
        Args:
            question: 사용자 질문
            embedding: SBERT 임베딩 벡터
            
        Returns:
            분류 결과 딕셔너리
        """
        # 1. 명확한 SQL 지시어 확인
        sql_indicators = [
            "통계", "집계", "개수", "합계", "평균", "최대", "최소", "총계",
            "count", "sum", "avg", "max", "min", "total",
            "얼마나", "몇 개", "몇 명", "몇 건", "몇 회", "몇 대",
            "통행량", "교통량", "사고 건수", "발생 건수",
            "데이터 분석", "데이터 조회", "테이블 조회",
            "기간별", "월별", "연도별", "지역별"
        ]
        
        # 2. 명확한 PDF 지시어 확인
        pdf_indicators = [
            "설명", "방법", "과정", "원인", "결과", "개념", "정의", "의미",
            "어떻게", "왜", "무엇", "무슨", "어떤", "어디서", "언제",
            "안전 운전", "교통 규칙", "신호등", "교차로", "도로",
            "사고 예방", "안전 수칙", "주의사항", "가이드라인"
        ]
        
        # 3. 지시어 기반 점수 계산
        question_lower = question.lower()
        sql_score = sum(1 for indicator in sql_indicators if indicator in question_lower)
        pdf_score = sum(1 for indicator in pdf_indicators if indicator in question_lower)
        
        # 4. SBERT 임베딩 기반 유사도 계산
        sql_examples = [
            "통계를 보여주세요",
            "개수를 세어주세요", 
            "평균을 계산해주세요",
            "2023년 데이터를 조회해주세요",
            "지역별 통계를 알려주세요"
        ]
        
        pdf_examples = [
            "설명해주세요",
            "방법을 알려주세요", 
            "개념을 설명해주세요",
            "원인을 분석해주세요",
            "안전 운전 방법을 알려주세요"
        ]
        
        # SQL 예시들과의 유사도 계산
        sql_embeddings = self.embedding_model.encode(sql_examples)
        sql_similarities = cosine_similarity([embedding], sql_embeddings)[0]
        max_sql_similarity = np.max(sql_similarities)
        
        # PDF 예시들과의 유사도 계산
        pdf_embeddings = self.embedding_model.encode(pdf_examples)
        pdf_similarities = cosine_similarity([embedding], pdf_embeddings)[0]
        max_pdf_similarity = np.max(pdf_similarities)
        
        # 5. 종합 점수 계산
        total_sql_score = sql_score * 0.3 + max_sql_similarity * 0.7
        total_pdf_score = pdf_score * 0.3 + max_pdf_similarity * 0.7
        
        # 6. 분류 결정
        threshold = 0.6
        classification = "UNKNOWN"
        confidence = 0.0
        
        if total_sql_score > threshold and total_sql_score > total_pdf_score:
            classification = "SQL"
            confidence = total_sql_score
        elif total_pdf_score > threshold and total_pdf_score > total_sql_score:
            classification = "PDF"
            confidence = total_pdf_score
        elif total_sql_score > 0.4 and total_pdf_score > 0.4:
            classification = "HYBRID"
            confidence = (total_sql_score + total_pdf_score) / 2
        else:
            classification = "PDF"  # 기본값
            confidence = max(total_sql_score, total_pdf_score)
        
        return {
            "classification": classification,
            "confidence": confidence,
            "sql_score": total_sql_score,
            "pdf_score": total_pdf_score,
            "sql_similarity": max_sql_similarity,
            "pdf_similarity": max_pdf_similarity,
            "sql_indicators_found": [ind for ind in sql_indicators if ind in question_lower],
            "pdf_indicators_found": [ind for ind in pdf_indicators if ind in question_lower]
        }

# 유틸리티 함수들
def calculate_question_complexity(analyzed_question: AnalyzedQuestion) -> float:
    """
    질문 복잡도 계산
    
    Args:
        analyzed_question: 분석된 질문
        
    Returns:
        복잡도 점수 (0.0 ~ 1.0)
    """
    complexity_score = 0.0
    
    # 키워드 수에 따른 복잡도
    keyword_complexity = min(len(analyzed_question.keywords) / 10.0, 0.3)
    complexity_score += keyword_complexity
    
    # 질문 유형에 따른 복잡도
    type_complexity = {
        QuestionType.FACTUAL: 0.1,
        QuestionType.CONCEPTUAL: 0.3,
        QuestionType.COMPARATIVE: 0.4,
        QuestionType.PROCEDURAL: 0.3,
        QuestionType.ANALYTICAL: 0.5,
        QuestionType.FOLLOW_UP: 0.2,
        QuestionType.CLARIFICATION: 0.2
    }
    complexity_score += type_complexity.get(analyzed_question.question_type, 0.3)
    
    # 컨텍스트 의존성
    if analyzed_question.context_keywords:
        complexity_score += 0.2
    
    return min(complexity_score, 1.0)

if __name__ == "__main__":
    # 테스트 코드
    analyzer = QuestionAnalyzer()
    
    test_questions = [
        "이 문서에서 주요 개념이 무엇인가요?",
        "앞서 말한 방법과 다른 접근법은 어떤 것들이 있나요?",
        "A와 B의 차이점을 구체적으로 설명해주세요.",
        "이 과정을 단계별로 어떻게 진행하나요?"
    ]
    
    for question in test_questions:
        analyzed = analyzer.analyze_question(question)
        print(f"질문: {question}")
        print(f"유형: {analyzed.question_type.value}")
        print(f"의도: {analyzed.intent}")
        print(f"키워드: {analyzed.keywords}")
        print("---")
    
    print("QuestionAnalyzer 모듈이 정상적으로 로드되었습니다.")

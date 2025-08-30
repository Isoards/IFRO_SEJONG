"""
질문 분석 모듈 (최적화 버전)

빠른 질문 분석을 위한 간소화된 분석기
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class QuestionType(Enum):
    """질문 유형 분류 (단순화)"""
    GREETING = "greeting"            # 인사말
    FACTUAL = "factual"              # 사실 질문
    CONCEPTUAL = "conceptual"        # 개념 질문
    DATABASE_QUERY = "database_query"  # 데이터베이스 질의
    QUANTITATIVE = "quantitative"    # 정량적 질문
    UNKNOWN = "unknown"              # 알 수 없음

@dataclass
class ConversationItem:
    """대화 항목 데이터 클래스"""
    question: str
    answer: str
    timestamp: datetime
    question_type: QuestionType
    relevant_chunks: List[str]
    confidence_score: float = 0.0
    metadata: Optional[Dict] = None

@dataclass 
class AnalyzedQuestion:
    """분석된 질문 데이터 클래스 (단순화)"""
    original_question: str
    processed_question: str
    question_type: QuestionType
    keywords: List[str]
    entities: List[str]
    intent: str
    context_keywords: List[str]
    requires_sql: bool = False
    sql_intent: Optional[str] = None
    embedding: Optional[np.ndarray] = None
    metadata: Optional[Dict] = None
    enhanced_question: Optional[str] = None

class QuestionAnalyzer:
    """질문 분석기 (최적화)"""
    
    def __init__(self, embedding_model: str = "jhgan/ko-sroberta-multitask"):
        """QuestionAnalyzer 초기화"""
        # 임베딩 모델 로드
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"질문 분석용 임베딩 모델 로드: {embedding_model}")
        except Exception as e:
            logger.error(f"임베딩 모델 로드 실패: {e}")
            self.embedding_model = None
        
        # 대화 히스토리 (단순화)
        self.conversation_history: List[ConversationItem] = []
        
        # 질문 유형 패턴 (단순화)
        self.question_patterns = {
            QuestionType.GREETING: [
                r'안녕', r'반갑', r'하이', r'처음', r'도움'
            ],
            QuestionType.FACTUAL: [
                r'무엇', r'언제', r'어디서', r'누가', r'어떤'
            ],
            QuestionType.CONCEPTUAL: [
                r'어떻게', r'왜', r'원리', r'개념', r'정의'
            ],
            QuestionType.DATABASE_QUERY: [
                r'몇', r'개수', r'건수', r'총', r'평균', r'최대', r'최소',
                r'교통량', r'통행량', r'사고', r'구별', r'지역별', r'통계'
            ],
            QuestionType.QUANTITATIVE: [
                r'얼마나', r'비율', r'순위', r'분석', r'데이터'
            ]
        }
        
        # 키워드 추출 패턴
        self.keyword_patterns = [
            r'\b\w+구\b',  # 지역명
            r'\b\w+교차로\b',  # 교차로명
            r'\b교통량\b', r'\b통행량\b',  # 교통 관련
            r'\b사고\b', r'\b접촉사고\b',  # 사고 관련
            r'\b신호\b', r'\b신호등\b',  # 신호 관련
            r'\bIFRO\b', r'\b시스템\b'  # 시스템 관련
        ]
        
        logger.info("질문 분석기 초기화 완료")
    
    def analyze_question(self, question: str, use_conversation_context: bool = True) -> AnalyzedQuestion:
        """질문 분석 (최적화)"""
        import time
        total_start_time = time.time()
        
        # 1. 기본 전처리
        preprocess_start = time.time()
        processed_question = self._preprocess_question(question)
        preprocess_time = time.time() - preprocess_start
        
        # 2. 질문 유형 분류
        classify_start = time.time()
        question_type = self._classify_question_type(processed_question)
        classify_time = time.time() - classify_start
        
        # 3. 키워드 추출
        keyword_start = time.time()
        keywords = self._extract_keywords(processed_question)
        keyword_time = time.time() - keyword_start
        
        # 4. 개체명 추출
        entity_start = time.time()
        entities = self._extract_entities(processed_question)
        entity_time = time.time() - entity_start
        
        # 5. 의도 분석
        intent_start = time.time()
        intent = self._analyze_intent(processed_question, question_type)
        intent_time = time.time() - intent_start
        
        # 6. 컨텍스트 키워드 (단순화)
        context_start = time.time()
        context_keywords = []
        if use_conversation_context and self.conversation_history:
            context_keywords = self._extract_context_keywords()
        context_time = time.time() - context_start
        
        # 7. SQL 요구사항 확인
        sql_start = time.time()
        requires_sql, sql_intent = self._check_sql_requirement(question_type, keywords)
        sql_time = time.time() - sql_start
        
        # 8. 임베딩 생성 (가장 오래 걸릴 수 있는 부분)
        embedding_start = time.time()
        embedding = None
        if self.embedding_model:
            try:
                embedding = self.embedding_model.encode([processed_question])[0]
            except Exception as e:
                logger.warning(f"임베딩 생성 실패: {e}")
        embedding_time = time.time() - embedding_start
        
        # 9. 향상된 질문 생성 (단순화)
        enhance_start = time.time()
        enhanced_question = self._enhance_question(processed_question, context_keywords)
        enhance_time = time.time() - enhance_start
        
        # 10. 메타데이터 생성
        metadata_start = time.time()
        total_time = time.time() - total_start_time
        metadata = {
            "processing_time": total_time,
            "question_length": len(question),
            "keywords_count": len(keywords),
            "entities_count": len(entities),
            "timing_breakdown": {
                "preprocess": preprocess_time,
                "classify": classify_time,
                "keyword_extract": keyword_time,
                "entity_extract": entity_time,
                "intent_analysis": intent_time,
                "context_keywords": context_time,
                "sql_check": sql_time,
                "embedding": embedding_time,
                "enhance": enhance_time
            }
        }
        metadata_time = time.time() - metadata_start
        
        analyzed_question = AnalyzedQuestion(
            original_question=question,
            processed_question=processed_question,
            question_type=question_type,
            keywords=keywords,
            entities=entities,
            intent=intent,
            context_keywords=context_keywords,
            requires_sql=requires_sql,
            sql_intent=sql_intent,
            embedding=embedding,
            enhanced_question=enhanced_question,
            metadata=metadata
        )
        
        print(f"  🔍 분석 세부: 전처리({preprocess_time:.3f}s) | 분류({classify_time:.3f}s) | 키워드({keyword_time:.3f}s) | 임베딩({embedding_time:.3f}s) | 기타({(entity_time+intent_time+context_time+sql_time+enhance_time+metadata_time):.3f}s)")
        
        logger.info(f"질문 분석 완료: {question_type.value}, 키워드: {len(keywords)}개")
        return analyzed_question
    
    def _preprocess_question(self, question: str) -> str:
        """질문 전처리"""
        # 기본 정규화
        processed = question.strip()
        processed = re.sub(r'\s+', ' ', processed)  # 연속 공백 제거
        processed = re.sub(r'[^\w\s가-힣]', '', processed)  # 특수문자 제거 (한글 제외)
        return processed
    
    def _classify_question_type(self, question: str) -> QuestionType:
        """질문 유형 분류"""
        question_lower = question.lower()
        
        # 패턴 매칭으로 유형 결정
        for question_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    return question_type
        
        return QuestionType.UNKNOWN
    
    def _extract_keywords(self, question: str) -> List[str]:
        """키워드 추출"""
        keywords = []
        
        # 패턴 기반 키워드 추출
        for pattern in self.keyword_patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            keywords.extend(matches)
        
        # 중복 제거 및 정렬
        keywords = list(set(keywords))
        keywords.sort()
        
        return keywords
    
    def _extract_entities(self, question: str) -> List[str]:
        """개체명 추출 (단순화)"""
        entities = []
        
        # 지역명 추출
        location_pattern = r'\b\w+구\b'
        locations = re.findall(location_pattern, question)
        entities.extend(locations)
        
        # 교차로명 추출
        intersection_pattern = r'\b\w+교차로\b'
        intersections = re.findall(intersection_pattern, question)
        entities.extend(intersections)
        
        return list(set(entities))
    
    def _analyze_intent(self, question: str, question_type: QuestionType) -> str:
        """의도 분석 (단순화)"""
        if question_type == QuestionType.GREETING:
            return "인사"
        elif question_type == QuestionType.DATABASE_QUERY:
            return "데이터_조회"
        elif question_type == QuestionType.CONCEPTUAL:
            return "개념_설명"
        elif question_type == QuestionType.FACTUAL:
            return "사실_조회"
        else:
            return "일반_질문"
    
    def _extract_context_keywords(self) -> List[str]:
        """컨텍스트 키워드 추출 (단순화)"""
        if not self.conversation_history:
            return []
        
        # 최근 3개 대화에서 키워드 추출
        recent_keywords = []
        for item in self.conversation_history[-3:]:
            recent_keywords.extend(item.question.split()[:5])  # 상위 5개 단어만
        
        return list(set(recent_keywords))
    
    def _check_sql_requirement(self, question_type: QuestionType, keywords: List[str]) -> tuple[bool, Optional[str]]:
        """SQL 요구사항 확인"""
        if question_type == QuestionType.DATABASE_QUERY:
            return True, "SELECT"
        
        # 키워드 기반 확인
        sql_keywords = ['교통량', '통행량', '사고', '구별', '통계', '개수', '건수']
        if any(keyword in keywords for keyword in sql_keywords):
            return True, "SELECT"
        
        return False, None
    
    def _enhance_question(self, question: str, context_keywords: List[str]) -> str:
        """질문 향상 (단순화)"""
        if not context_keywords:
            return question
        
        # 컨텍스트 키워드가 질문에 없으면 추가
        enhanced = question
        for keyword in context_keywords[:2]:  # 최대 2개만 추가
            if keyword not in question:
                enhanced += f" {keyword}"
        
        return enhanced
    

    
    def get_conversation_summary(self) -> Dict:
        """대화 요약 반환"""
        return {
            "total_conversations": len(self.conversation_history),
            "recent_questions": [item.question for item in self.conversation_history[-3:]],
            "question_types": [item.question_type.value for item in self.conversation_history[-5:]]
        }
    
    def clear_conversation_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history.clear()
        logger.info("대화 히스토리 초기화 완료")
    
    def get_conversation_context(self, max_items: int = 3) -> List[Dict]:
        """대화 컨텍스트 반환"""
        if not self.conversation_history:
            return []
        
        # 최근 대화 항목들을 딕셔너리 형태로 변환
        context = []
        for item in self.conversation_history[-max_items:]:
            context.append({
                "question": item.question,
                "answer": item.answer,
                "timestamp": item.timestamp.isoformat(),
                "question_type": item.question_type.value,
                "confidence_score": item.confidence_score
            })
        
        return context
    
    def add_conversation_item(self, question: str, answer: str, used_chunks: List[str], confidence_score: float):
        """대화 항목 추가 (단순화된 버전)"""
        item = ConversationItem(
            question=question,
            answer=answer,
            timestamp=datetime.now(),
            question_type=QuestionType.UNKNOWN,  # 기본값
            relevant_chunks=used_chunks,
            confidence_score=confidence_score
        )
        self.conversation_history.append(item)
        
        # 히스토리 크기 제한 (최근 10개만 유지)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

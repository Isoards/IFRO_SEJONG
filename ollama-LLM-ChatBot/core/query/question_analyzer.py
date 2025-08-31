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
        """개체명 추출 (개선된 버전)"""
        entities = []
        
        # 세종시 동/읍/면 패턴
        sejong_patterns = [
            r'([가-힣]+동)',  # 동 패턴
            r'([가-힣]+읍)',  # 읍 패턴
            r'([가-힣]+면)',  # 면 패턴
            r'세종특별자치시([가-힣]+)',  # 세종특별자치시 패턴
        ]
        
        for pattern in sejong_patterns:
            matches = re.findall(pattern, question)
            entities.extend(matches)
        
        # 교차로명 패턴 (세종특별자치시 형식)
        intersection_patterns = [
            r'세종특별자치시[가-힣]+\(\d+\)',  # 세종특별자치시조치원읍(1) 형식
            r'세종특별자치시[가-힣]+',  # 세종특별자치시조치원읍 형식
        ]
        
        for pattern in intersection_patterns:
            matches = re.findall(pattern, question)
            entities.extend(matches)
        
        # 기존 패턴들
        existing_patterns = [
            r'\b\w+구\b',  # 지역명
            r'\b\w+교차로\b',  # 교차로명
            r'\b\w+역\b',  # 역명
        ]
        
        for pattern in existing_patterns:
            matches = re.findall(pattern, question)
            entities.extend(matches)
        
        # 교차로명 정규화
        normalized_entities = []
        for entity in entities:
            if "세종특별자치시" in entity:
                normalized = self._normalize_intersection_name(entity)
                normalized_entities.append(normalized)
            else:
                normalized_entities.append(entity)
        
        return list(set(normalized_entities))  # 중복 제거
    
    def _normalize_intersection_name(self, intersection_name: str) -> str:
        """교차로명 정규화 (세종시 형식 -> 지역명)"""
        # 교차로 매핑 테이블
        intersection_mapping = {
            # 조치원읍 교차로들
            "세종특별자치시조치원읍": "조치원읍",
            "세종특별자치시조치원읍(1)": "조치원읍",
            "세종특별자치시조치원읍(2)": "조치원읍",
            "세종특별자치시조치원읍(3)": "조치원읍",
            "세종특별자치시조치원읍(4)": "조치원읍",
            "세종특별자치시조치원읍(5)": "조치원읍",
            "세종특별자치시조치원읍(6)": "조치원읍",
            "세종특별자치시조치원읍(7)": "조치원읍",
            "세종특별자치시조치원읍(8)": "조치원읍",
            "세종특별자치시조치원읍(9)": "조치원읍",
            "세종특별자치시조치원읍(10)": "조치원읍",
            
            # 연기면 교차로들
            "세종특별자치시연기면": "연기면",
            "세종특별자치시연기면(1)": "연기면",
            "세종특별자치시연기면(2)": "연기면",
            "세종특별자치시연기면(3)": "연기면",
            "세종특별자치시연기면(4)": "연기면",
            "세종특별자치시연기면(5)": "연기면",
            
            # 연동면 교차로들
            "세종특별자치시연동면": "연동면",
            "세종특별자치시연동면(1)": "연동면",
            "세종특별자치시연동면(2)": "연동면",
            "세종특별자치시연동면(3)": "연동면",
            "세종특별자치시연동면(4)": "연동면",
            "세종특별자치시연동면(5)": "연동면",
            "세종특별자치시연동면(6)": "연동면",
            "세종특별자치시연동면(7)": "연동면",
            "세종특별자치시연동면(8)": "연동면",
            "세종특별자치시연동면(9)": "연동면",
            "세종특별자치시연동면(10)": "연동면",
            
            # 부강면 교차로들
            "세종특별자치시부강면": "부강면",
            "세종특별자치시부강면(1)": "부강면",
            "세종특별자치시부강면(2)": "부강면",
            "세종특별자치시부강면(3)": "부강면",
            "세종특별자치시부강면(4)": "부강면",
            "세종특별자치시부강면(5)": "부강면",
            "세종특별자치시부강면(6)": "부강면",
            "세종특별자치시부강면(7)": "부강면",
            "세종특별자치시부강면(8)": "부강면",
            "세종특별자치시부강면(9)": "부강면",
            "세종특별자치시부강면(10)": "부강면",
            
            # 금남면 교차로들
            "세종특별자치시금남면": "금남면",
            "세종특별자치시금남면(1)": "금남면",
            "세종특별자치시금남면(2)": "금남면",
            "세종특별자치시금남면(3)": "금남면",
            "세종특별자치시금남면(4)": "금남면",
            "세종특별자치시금남면(5)": "금남면",
            "세종특별자치시금남면(6)": "금남면",
            "세종특별자치시금남면(7)": "금남면",
            "세종특별자치시금남면(8)": "금남면",
            "세종특별자치시금남면(9)": "금남면",
            "세종특별자치시금남면(10)": "금남면",
            
            # 장군면 교차로들
            "세종특별자치시장군면": "장군면",
            "세종특별자치시장군면(1)": "장군면",
            "세종특별자치시장군면(2)": "장군면",
            "세종특별자치시장군면(3)": "장군면",
            "세종특별자치시장군면(4)": "장군면",
            "세종특별자치시장군면(5)": "장군면",
            "세종특별자치시장군면(6)": "장군면",
            "세종특별자치시장군면(7)": "장군면",
            "세종특별자치시장군면(8)": "장군면",
            "세종특별자치시장군면(9)": "장군면",
            "세종특별자치시장군면(10)": "장군면",
            
            # 연서면 교차로들
            "세종특별자치시연서면": "연서면",
            "세종특별자치시연서면(1)": "연서면",
            "세종특별자치시연서면(2)": "연서면",
            "세종특별자치시연서면(3)": "연서면",
            "세종특별자치시연서면(4)": "연서면",
            "세종특별자치시연서면(5)": "연서면",
            "세종특별자치시연서면(6)": "연서면",
            "세종특별자치시연서면(7)": "연서면",
            "세종특별자치시연서면(8)": "연서면",
            "세종특별자치시연서면(9)": "연서면",
            "세종특별자치시연서면(10)": "연서면",
            
            # 전의면 교차로들
            "세종특별자치시전의면": "전의면",
            "세종특별자치시전의면(1)": "전의면",
            "세종특별자치시전의면(2)": "전의면",
            "세종특별자치시전의면(3)": "전의면",
            "세종특별자치시전의면(4)": "전의면",
            "세종특별자치시전의면(5)": "전의면",
            "세종특별자치시전의면(6)": "전의면",
            "세종특별자치시전의면(7)": "전의면",
            "세종특별자치시전의면(8)": "전의면",
            "세종특별자치시전의면(9)": "전의면",
            "세종특별자치시전의면(10)": "전의면",
            
            # 전동면 교차로들
            "세종특별자치시전동면": "전동면",
            "세종특별자치시전동면(1)": "전동면",
            "세종특별자치시전동면(2)": "전동면",
            "세종특별자치시전동면(3)": "전동면",
            "세종특별자치시전동면(4)": "전동면",
            "세종특별자치시전동면(5)": "전동면",
            "세종특별자치시전동면(6)": "전동면",
            "세종특별자치시전동면(7)": "전동면",
            "세종특별자치시전동면(8)": "전동면",
            "세종특별자치시전동면(9)": "전동면",
            "세종특별자치시전동면(10)": "전동면",
            
            # 소정면 교차로들
            "세종특별자치시소정면": "소정면",
            "세종특별자치시소정면(1)": "소정면",
            "세종특별자치시소정면(2)": "소정면",
            "세종특별자치시소정면(3)": "소정면",
            "세종특별자치시소정면(4)": "소정면",
            "세종특별자치시소정면(5)": "소정면",
            "세종특별자치시소정면(6)": "소정면",
            "세종특별자치시소정면(7)": "소정면",
            "세종특별자치시소정면(8)": "소정면",
            "세종특별자치시소정면(9)": "소정면",
            "세종특별자치시소정면(10)": "소정면",
            
            # 동 지역 교차로들
            "세종특별자치시한솔동": "한솔동",
            "세종특별자치시새롬동": "새롬동",
            "세종특별자치시도담동": "도담동",
            "세종특별자치시아름동": "아름동",
            "세종특별자치시종촌동": "종촌동",
            "세종특별자치시고운동": "고운동",
            "세종특별자치시소담동": "소담동",
            "세종특별자치시보람동": "보람동",
            "세종특별자치시대평동": "대평동",
            "세종특별자치시다정동": "다정동",
            "세종특별자치시어진동": "어진동",
            "세종특별자치시반곡동": "반곡동",
            "세종특별자치시가람동": "가람동",
            "세종특별자치시한별동": "한별동",
            "세종특별자치시새아름동": "새아름동"
        }
        
        return intersection_mapping.get(intersection_name, intersection_name)
    
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

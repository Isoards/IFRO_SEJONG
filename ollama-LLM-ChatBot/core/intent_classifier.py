"""
고도화된 의도 분류기 (SBERT + FastText 하이브리드)

이 모듈은 질문의 의도를 정확하게 분류하기 위해 다층 구조를 사용합니다:
1. FastText: 빠른 1차 필터링 (80% 케이스)
2. SBERT: 정확한 2차 분류 (15% 케이스)  
3. LLM: 복잡한 3차 판단 (5% 케이스)
"""

import re
import json
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

import fasttext
import os

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """의도 유형 분류"""
    # 데이터 관련 의도
    DB_QUERY = "db_query"              # 데이터베이스 질의
    DATA_ANALYSIS = "data_analysis"    # 데이터 분석
    STATISTICAL_QUERY = "statistical_query"  # 통계 질의
    
    # 정보 관련 의도
    FACTUAL_INQUIRY = "factual_inquiry"      # 사실 질문
    CONCEPTUAL_INQUIRY = "conceptual_inquiry"  # 개념 질문
    PROCEDURAL_INQUIRY = "procedural_inquiry"  # 절차 질문
    
    # 비교 관련 의도
    COMPARISON_INQUIRY = "comparison_inquiry"  # 비교 질문
    RANKING_INQUIRY = "ranking_inquiry"        # 순위 질문
    
    # 기타 의도
    GREETING = "greeting"              # 인사말
    CLARIFICATION = "clarification"    # 명확화 요청
    FOLLOW_UP = "follow_up"           # 후속 질문
    LOCATION_MOVEMENT = "location_movement"  # 장소 이동 요청

@dataclass
class IntentResult:
    """의도 분류 결과"""
    intent: IntentType
    confidence: float
    classifier_used: str  # "fasttext", "sbert", "llm"
    processing_time: float
    metadata: Optional[Dict] = None

class IntentClassifier:
    """
    하이브리드 의도 분류기
    
    특징:
    - 3단계 분류: FastText → SBERT → LLM
    - 교통 도메인 특화 학습 데이터
    - 실시간 응답 최적화
    - 점진적 학습 지원
    """
    
    def __init__(self, 
                 sbert_model: str = "jhgan/ko-sroberta-multitask",
                 fasttext_model_path: Optional[str] = None,
                 training_data_path: Optional[str] = None):
        """
        IntentClassifier 초기화
        
        Args:
            sbert_model: SBERT 모델 이름 (HuggingFace 모델 ID)
            fasttext_model_path: FastText 모델 경로 (없으면 새로 학습)
            training_data_path: 학습 데이터 경로
        """
        logger.info("IntentClassifier 초기화 시작...")
        
        # SBERT 모델 로드 (자동 다운로드)
        try:
            logger.info(f"SBERT 모델 다운로드 중: {sbert_model}")
            self.sbert_model = SentenceTransformer(sbert_model)
            logger.info(f"✅ SBERT 모델 로드 완료: {sbert_model}")
        except Exception as e:
            logger.error(f"❌ SBERT 모델 로드 실패: {e}")
            logger.info("대안 모델로 시도합니다: 'sentence-transformers/all-MiniLM-L6-v2'")
            try:
                self.sbert_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                logger.info("✅ 대안 SBERT 모델 로드 완료")
            except Exception as e2:
                logger.error(f"❌ 대안 모델도 로드 실패: {e2}")
                raise RuntimeError("SBERT 모델을 로드할 수 없습니다. 인터넷 연결을 확인하거나 모델을 수동으로 다운로드하세요.")
        
        # FastText 분류기 초기화
        self.fasttext_classifier = None
        self.fasttext_model_path = fasttext_model_path
        
        # SBERT 분류기 초기화
        self.sbert_classifier = None
        self.sbert_embeddings = {}
        self.sbert_intent_embeddings = {}
        
        # LLM 분류기 (필요시 사용)
        self.llm_classifier = None
        
        # 학습 데이터
        logger.info("학습 데이터 로드 중...")
        self.training_data = self._load_training_data(training_data_path)
        
        # 분류기 초기화
        logger.info("분류기 초기화 중...")
        self._initialize_classifiers()
        
        # 성능 통계
        self.classification_stats = {
            "fasttext_usage": 0,
            "sbert_usage": 0,
            "llm_usage": 0,
            "total_queries": 0
        }
        
        logger.info("✅ IntentClassifier 초기화 완료")
    
    def _load_training_data(self, training_data_path: Optional[str]) -> Dict[str, List[str]]:
        """교통 도메인 특화 학습 데이터 로드"""
        
        # 기본 교통 도메인 학습 데이터
        training_data = {
            IntentType.DB_QUERY.value: [
                "교통량이 가장 많은 구간은 어디인가요?",
                "어제 사고가 몇 건 발생했나요?",
                "평균 통행 시간이 가장 긴 교차로는?",
                "이번 주 교통사고 통계를 보여주세요",
                "특정 구간의 교통량 데이터를 조회하고 싶어요",
                "교차로별 사고 발생 건수를 알려주세요",
                "시간대별 교통량 분포를 확인해주세요",
                "주말과 평일의 교통량 차이는?",
                "가장 혼잡한 시간대는 언제인가요?",
                "교통사고가 가장 많이 발생한 지역은?",
                "평균 속도가 가장 낮은 구간은?",
                "교통량 증가율이 가장 높은 구간은?",
                "사고 발생률이 가장 높은 시간대는?",
                "교통 정체가 가장 심한 구간은?",
                "신호등 대기 시간이 가장 긴 교차로는?"
            ],
            
            IntentType.DATA_ANALYSIS.value: [
                "교통량 데이터를 분석해주세요",
                "사고 발생 패턴을 분석하고 싶어요",
                "교통 흐름을 분석해보세요",
                "통계적 분석 결과를 보여주세요",
                "데이터 분석을 통해 인사이트를 얻고 싶어요",
                "교통량과 사고 발생의 상관관계를 분석해주세요",
                "시간대별 교통 패턴을 분석해보세요",
                "지역별 교통 특성을 분석해주세요",
                "교통 데이터의 트렌드를 분석해보세요",
                "교통량 예측 모델을 만들어주세요"
            ],
            
            IntentType.STATISTICAL_QUERY.value: [
                "교통량 평균값은 얼마인가요?",
                "사고 발생 건수의 합계를 알려주세요",
                "최대 교통량은 얼마인가요?",
                "최소 통행 시간은 얼마인가요?",
                "교통량의 표준편차는?",
                "사고 발생률의 백분율은?",
                "교통량 증가율을 계산해주세요",
                "평균 대기 시간은?",
                "교통량의 중앙값은?",
                "사고 건수의 분산은?"
            ],
            
            IntentType.FACTUAL_INQUIRY.value: [
                "교통량이란 무엇인가요?",
                "교통사고의 정의는?",
                "신호등의 작동 원리는?",
                "교차로의 종류는?",
                "교통 정체의 원인은?",
                "교통량 측정 방법은?",
                "사고 발생 원인은?",
                "교통 신호의 의미는?",
                "교통 규칙은?",
                "교통 안전 기준은?"
            ],
            
            IntentType.CONCEPTUAL_INQUIRY.value: [
                "교통량과 통행량의 차이는?",
                "교통사고와 교통인시던트의 차이는?",
                "신호등과 신호기의 차이는?",
                "교차로와 사거리의 차이는?",
                "교통 정체와 교통 혼잡의 차이는?",
                "교통량과 교통 밀도의 차이는?",
                "교통사고와 교통사고의 차이는?",
                "교통 신호와 교통 표지의 차이는?",
                "교통 규칙과 교통 법규의 차이는?",
                "교통 안전과 교통 보안의 차이는?"
            ],
            
            IntentType.PROCEDURAL_INQUIRY.value: [
                "교통량을 확인하는 방법은?",
                "사고 데이터를 조회하는 방법은?",
                "교통 통계를 보는 방법은?",
                "교차로 정보를 찾는 방법은?",
                "교통 상황을 확인하는 방법은?",
                "사고 발생 현황을 파악하는 방법은?",
                "교통량 데이터를 다운로드하는 방법은?",
                "교통 분석 결과를 확인하는 방법은?",
                "교통 정보를 업데이트하는 방법은?",
                "교통 데이터를 백업하는 방법은?"
            ],
            
            IntentType.COMPARISON_INQUIRY.value: [
                "A구간과 B구간의 교통량을 비교해주세요",
                "평일과 주말의 교통량 차이는?",
                "아침과 저녁의 교통 상황을 비교해보세요",
                "이번 달과 지난 달의 사고 발생률을 비교해주세요",
                "다른 지역과의 교통량을 비교해보세요",
                "다른 시간대와의 교통 상황을 비교해주세요",
                "다른 교차로와의 사고 발생률을 비교해보세요",
                "다른 도로와의 교통량을 비교해주세요",
                "다른 기간과의 교통 데이터를 비교해보세요",
                "다른 조건과의 교통 상황을 비교해주세요"
            ],
            
            IntentType.RANKING_INQUIRY.value: [
                "교통량이 가장 많은 구간 순위를 알려주세요",
                "사고 발생이 가장 많은 지역 순위는?",
                "가장 혼잡한 시간대 순위를 보여주세요",
                "교통량이 가장 적은 구간 순위는?",
                "가장 안전한 교차로 순위를 알려주세요",
                "평균 속도가 가장 높은 구간 순위는?",
                "대기 시간이 가장 긴 교차로 순위를 보여주세요",
                "교통량 증가율이 가장 높은 구간 순위는?",
                "사고 발생률이 가장 낮은 지역 순위를 알려주세요",
                "가장 효율적인 교통 흐름을 가진 구간 순위는?"
            ],
            
            IntentType.GREETING.value: [
                "안녕하세요",
                "안녕",
                "반갑습니다",
                "하이",
                "hi",
                "hello",
                "좋은 아침입니다",
                "좋은 하루 되세요",
                "만나서 반가워요",
                "오랜만입니다"
            ],
            
            IntentType.CLARIFICATION.value: [
                "좀 더 구체적으로 설명해주세요",
                "정확히 무엇을 의미하나요?",
                "명확하게 알려주세요",
                "더 자세히 설명해주세요",
                "구체적인 예시를 들어주세요",
                "정확한 수치를 알려주세요",
                "명확한 기준을 제시해주세요",
                "더 상세한 정보를 제공해주세요",
                "정확한 정의를 알려주세요",
                "명확한 범위를 설정해주세요"
            ],
            
            IntentType.FOLLOW_UP.value: [
                "그럼 다른 방법은?",
                "추가로 알려주세요",
                "더 자세한 정보가 필요해요",
                "이어서 설명해주세요",
                "그 다음은?",
                "추가 질문이 있어요",
                "더 구체적으로 말씀해주세요",
                "다른 관점에서도 설명해주세요",
                "관련된 다른 정보도 알려주세요",
                "이어서 다른 내용도 설명해주세요"
            ],
            
            IntentType.LOCATION_MOVEMENT.value: [
                "조치원으로 이동해주세요",
                "다른 지역으로 가주세요",
                "서울로 이동하고 싶어요",
                "부산으로 가주세요",
                "대구로 이동해주세요",
                "인천으로 가주세요",
                "광주로 이동하고 싶어요",
                "대전으로 가주세요",
                "울산으로 이동해주세요",
                "세종으로 가주세요"
            ]
        }
        
        # 외부 학습 데이터가 있으면 로드
        if training_data_path and os.path.exists(training_data_path):
            try:
                with open(training_data_path, 'r', encoding='utf-8') as f:
                    external_data = json.load(f)
                
                # 외부 데이터와 기본 데이터 병합
                for intent, examples in external_data.items():
                    if intent in training_data:
                        training_data[intent].extend(examples)
                    else:
                        training_data[intent] = examples
                
                logger.info(f"외부 학습 데이터 로드: {training_data_path}")
            except Exception as e:
                logger.warning(f"외부 학습 데이터 로드 실패: {e}")
        
        return training_data
    
    def _initialize_classifiers(self):
        """분류기들 초기화"""
        
        # 1. FastText 분류기 초기화
        self._initialize_fasttext_classifier()
        
        # 2. SBERT 분류기 초기화
        self._initialize_sbert_classifier()
        
        # 3. LLM 분류기 초기화 (필요시)
        # self._initialize_llm_classifier()
    
    def _initialize_fasttext_classifier(self):
        """FastText 분류기 초기화"""
        try:
            if self.fasttext_model_path and os.path.exists(self.fasttext_model_path):
                # 기존 모델 로드
                self.fasttext_classifier = fasttext.load_model(self.fasttext_model_path)
                logger.info(f"FastText 모델 로드: {self.fasttext_model_path}")
            else:
                # 새로 학습
                self._train_fasttext_classifier()
        except Exception as e:
            logger.warning(f"FastText 분류기 초기화 실패: {e}")
            self.fasttext_classifier = None
    
    def _train_fasttext_classifier(self):
        """FastText 분류기 학습"""
        try:
            # 학습 데이터 준비
            training_file = "fasttext_training_data.txt"
            
            with open(training_file, 'w', encoding='utf-8') as f:
                for intent, examples in self.training_data.items():
                    for example in examples:
                        # FastText 형식: __label__intent text
                        f.write(f"__label__{intent} {example}\n")
            
            # FastText 모델 학습
            self.fasttext_classifier = fasttext.train_supervised(
                input=training_file,
                lr=0.5,
                epoch=25,
                wordNgrams=2,
                minCount=1,
                loss='ova'
            )
            
            # 모델 저장
            if self.fasttext_model_path:
                self.fasttext_classifier.save_model(self.fasttext_model_path)
            
            # 임시 파일 삭제
            os.remove(training_file)
            
            logger.info("FastText 분류기 학습 완료")
            
        except Exception as e:
            logger.error(f"FastText 분류기 학습 실패: {e}")
            self.fasttext_classifier = None
    
    def _initialize_sbert_classifier(self):
        """SBERT 분류기 초기화"""
        try:
            # 각 의도별 대표 문장들의 임베딩 생성
            for intent, examples in self.training_data.items():
                # 각 의도별로 대표 문장 선택 (처음 5개)
                representative_examples = examples[:5]
                
                # 임베딩 생성
                embeddings = self.sbert_model.encode(representative_examples)
                
                # 평균 임베딩을 해당 의도의 대표 임베딩으로 저장
                self.sbert_intent_embeddings[intent] = np.mean(embeddings, axis=0)
            
            logger.info("SBERT 분류기 초기화 완료")
            
        except Exception as e:
            logger.error(f"SBERT 분류기 초기화 실패: {e}")
    
    def classify_intent(self, question: str) -> IntentResult:
        """
        질문의 의도를 분류 (3단계 하이브리드 방식)
        
        Args:
            question: 분류할 질문
            
        Returns:
            의도 분류 결과
        """
        import time
        start_time = time.time()
        
        self.classification_stats["total_queries"] += 1
        
        # 1단계: FastText 분류 (빠른 필터링)
        if self.fasttext_classifier:
            fasttext_result = self._classify_with_fasttext(question)
            if fasttext_result.confidence > 0.8:
                self.classification_stats["fasttext_usage"] += 1
                processing_time = time.time() - start_time
                return IntentResult(
                    intent=fasttext_result.intent,
                    confidence=fasttext_result.confidence,
                    classifier_used="fasttext",
                    processing_time=processing_time,
                    metadata={"stage": "fasttext_only"}
                )
        
        # 2단계: SBERT 분류 (정확한 분류)
        if self.sbert_intent_embeddings:
            sbert_result = self._classify_with_sbert(question)
            if sbert_result.confidence > 0.7:
                self.classification_stats["sbert_usage"] += 1
                processing_time = time.time() - start_time
                return IntentResult(
                    intent=sbert_result.intent,
                    confidence=sbert_result.confidence,
                    classifier_used="sbert",
                    processing_time=processing_time,
                    metadata={"stage": "sbert_only"}
                )
        
        # 3단계: LLM 분류 (복잡한 케이스)
        # 현재는 SBERT 결과를 반환하되, 신뢰도가 낮음을 표시
        if self.sbert_intent_embeddings:
            sbert_result = self._classify_with_sbert(question)
            self.classification_stats["llm_usage"] += 1
            processing_time = time.time() - start_time
            return IntentResult(
                intent=sbert_result.intent,
                confidence=sbert_result.confidence,
                classifier_used="llm_fallback",
                processing_time=processing_time,
                metadata={"stage": "llm_fallback"}
            )
        
        # 기본값: FACTUAL_INQUIRY
        processing_time = time.time() - start_time
        return IntentResult(
            intent=IntentType.FACTUAL_INQUIRY,
            confidence=0.5,
            classifier_used="default",
            processing_time=processing_time,
            metadata={"stage": "default_fallback"}
        )
    
    def _classify_with_fasttext(self, question: str) -> IntentResult:
        """FastText를 사용한 의도 분류"""
        try:
            # FastText 예측
            prediction = self.fasttext_classifier.predict(question, k=1)
            
            intent_label = prediction[0][0].replace("__label__", "")
            confidence = prediction[1][0]
            
            # IntentType으로 변환
            try:
                intent = IntentType(intent_label)
            except ValueError:
                intent = IntentType.FACTUAL_INQUIRY
            
            return IntentResult(
                intent=intent,
                confidence=confidence,
                classifier_used="fasttext",
                processing_time=0.0,
                metadata={"fasttext_label": intent_label}
            )
            
        except Exception as e:
            logger.error(f"FastText 분류 실패: {e}")
            return IntentResult(
                intent=IntentType.FACTUAL_INQUIRY,
                confidence=0.0,
                classifier_used="fasttext_error",
                processing_time=0.0
            )
    
    def _classify_with_sbert(self, question: str) -> IntentResult:
        """SBERT를 사용한 의도 분류"""
        try:
            # 질문 임베딩 생성
            question_embedding = self.sbert_model.encode([question])[0]
            
            # 각 의도와의 유사도 계산
            similarities = {}
            for intent, intent_embedding in self.sbert_intent_embeddings.items():
                similarity = cosine_similarity(
                    [question_embedding], 
                    [intent_embedding]
                )[0][0]
                similarities[intent] = similarity
            
            # 가장 유사한 의도 선택
            best_intent = max(similarities, key=similarities.get)
            confidence = similarities[best_intent]
            
            # IntentType으로 변환
            try:
                intent = IntentType(best_intent)
            except ValueError:
                intent = IntentType.FACTUAL_INQUIRY
            
            return IntentResult(
                intent=intent,
                confidence=confidence,
                classifier_used="sbert",
                processing_time=0.0,
                metadata={"similarities": similarities}
            )
            
        except Exception as e:
            logger.error(f"SBERT 분류 실패: {e}")
            return IntentResult(
                intent=IntentType.FACTUAL_INQUIRY,
                confidence=0.0,
                classifier_used="sbert_error",
                processing_time=0.0
            )
    
    def add_training_example(self, question: str, intent: IntentType):
        """새로운 학습 예시 추가"""
        try:
            intent_str = intent.value
            if intent_str not in self.training_data:
                self.training_data[intent_str] = []
            
            self.training_data[intent_str].append(question)
            
            # SBERT 임베딩 업데이트
            if self.sbert_intent_embeddings:
                self._update_sbert_embeddings(intent_str, question)
            
            logger.info(f"학습 예시 추가: {intent.value} - {question}")
            
        except Exception as e:
            logger.error(f"학습 예시 추가 실패: {e}")
    
    def _update_sbert_embeddings(self, intent_str: str, new_example: str):
        """SBERT 임베딩 업데이트"""
        try:
            # 새로운 예시의 임베딩 생성
            new_embedding = self.sbert_model.encode([new_example])[0]
            
            # 기존 임베딩과 새로운 임베딩의 평균 계산
            if intent_str in self.sbert_intent_embeddings:
                old_embedding = self.sbert_intent_embeddings[intent_str]
                # 가중 평균 (기존: 0.9, 새로운: 0.1)
                updated_embedding = 0.9 * old_embedding + 0.1 * new_embedding
                self.sbert_intent_embeddings[intent_str] = updated_embedding
            
        except Exception as e:
            logger.error(f"SBERT 임베딩 업데이트 실패: {e}")
    
    def retrain_classifiers(self):
        """분류기 재학습"""
        try:
            # FastText 재학습
            if self.fasttext_classifier:
                self._train_fasttext_classifier()
            
            # SBERT 재초기화
            self._initialize_sbert_classifier()
            
            logger.info("분류기 재학습 완료")
            
        except Exception as e:
            logger.error(f"분류기 재학습 실패: {e}")
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """분류 통계 반환"""
        total = self.classification_stats["total_queries"]
        if total == 0:
            return self.classification_stats
        
        stats = self.classification_stats.copy()
        stats.update({
            "fasttext_usage_rate": stats["fasttext_usage"] / total,
            "sbert_usage_rate": stats["sbert_usage"] / total,
            "llm_usage_rate": stats["llm_usage"] / total
        })
        
        return stats
    
    def save_classifier(self, file_path: str):
        """분류기 저장"""
        try:
            classifier_data = {
                "training_data": self.training_data,
                "sbert_intent_embeddings": self.sbert_intent_embeddings,
                "classification_stats": self.classification_stats
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(classifier_data, f)
            
            logger.info(f"분류기 저장 완료: {file_path}")
            
        except Exception as e:
            logger.error(f"분류기 저장 실패: {e}")
    
    def load_classifier(self, file_path: str):
        """분류기 로드"""
        try:
            with open(file_path, 'rb') as f:
                classifier_data = pickle.load(f)
            
            self.training_data = classifier_data["training_data"]
            self.sbert_intent_embeddings = classifier_data["sbert_intent_embeddings"]
            self.classification_stats = classifier_data["classification_stats"]
            
            # 분류기 재초기화
            self._initialize_classifiers()
            
            logger.info(f"분류기 로드 완료: {file_path}")
            
        except Exception as e:
            logger.error(f"분류기 로드 실패: {e}")

# 유틸리티 함수들
def create_intent_classifier(domain: str = "traffic") -> IntentClassifier:
    """
    도메인별 의도 분류기 생성
    
    Args:
        domain: 도메인 ("traffic", "general" 등)
        
    Returns:
        IntentClassifier 인스턴스
    """
    if domain == "traffic":
        return IntentClassifier(
            sbert_model="jhgan/ko-sroberta-multitask",
            training_data_path=None  # 기본 교통 도메인 데이터 사용
        )
    else:
        return IntentClassifier(
            sbert_model="jhgan/ko-sroberta-multitask"
        )

def evaluate_intent_classifier(classifier: IntentClassifier, 
                             test_questions: List[Tuple[str, IntentType]]) -> Dict[str, Any]:
    """
    의도 분류기 성능 평가
    
    Args:
        classifier: 평가할 분류기
        test_questions: (질문, 정답 의도) 튜플 리스트
        
    Returns:
        평가 결과
    """
    predictions = []
    true_labels = []
    
    for question, true_intent in test_questions:
        result = classifier.classify_intent(question)
        predictions.append(result.intent.value)
        true_labels.append(true_intent.value)
    
    # 정확도 계산
    accuracy = accuracy_score(true_labels, predictions)
    
    # 분류 리포트
    report = classification_report(true_labels, predictions, output_dict=True)
    
    return {
        "accuracy": accuracy,
        "classification_report": report,
        "total_samples": len(test_questions)
    }

if __name__ == "__main__":
    # 테스트 코드
    classifier = create_intent_classifier("traffic")
    
    test_questions = [
        "교통량이 가장 많은 구간은 어디인가요?",
        "교통량을 확인하는 방법은?",
        "안녕하세요",
        "조치원으로 이동해주세요",
        "교통량과 통행량의 차이는?"
    ]
    
    for question in test_questions:
        result = classifier.classify_intent(question)
        print(f"질문: {question}")
        print(f"의도: {result.intent.value}")
        print(f"신뢰도: {result.confidence:.3f}")
        print(f"사용된 분류기: {result.classifier_used}")
        print("---")
    
    # 통계 출력
    stats = classifier.get_classification_stats()
    print("분류 통계:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    print("IntentClassifier 모듈이 정상적으로 로드되었습니다.")

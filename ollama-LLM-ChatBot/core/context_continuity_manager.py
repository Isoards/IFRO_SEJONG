"""
컨텍스트 연속성 관리 모듈

이 모듈은 대화의 연속성을 관리하고, 이전 컨텍스트를 현재 질문에
자동으로 병합하는 기능을 제공합니다.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .core_element_extractor import ExtractedElements, CoreElement, ElementType

logger = logging.getLogger(__name__)

class ContinuityType(Enum):
    """연속성 유형"""
    STRONG = "strong"           # 강한 연속성 (핵심요소 70% 이상 유지)
    MODERATE = "moderate"       # 중간 연속성 (핵심요소 30-70% 유지)
    WEAK = "weak"              # 약한 연속성 (핵심요소 30% 미만 유지)
    NONE = "none"              # 연속성 없음

@dataclass
class ContinuityResult:
    """연속성 분석 결과"""
    continuity_type: ContinuityType
    overlap_score: float
    should_merge: bool
    missing_elements: List[CoreElement]
    enhanced_question: Optional[str] = None
    confidence: float = 0.0

@dataclass
class ConversationContext:
    """대화 컨텍스트"""
    topic: Optional[str] = None
    entities: List[str] = None
    attributes: List[str] = None
    relations: List[str] = None
    temporal: List[str] = None
    locations: List[str] = None
    intent: str = ""
    depth: int = 0  # 대화 깊이
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = []
        if self.attributes is None:
            self.attributes = []
        if self.relations is None:
            self.relations = []
        if self.temporal is None:
            self.temporal = []
        if self.locations is None:
            self.locations = []

class ContextContinuityManager:
    """
    대화 컨텍스트의 연속성을 관리하는 클래스
    """
    
    def __init__(self):
        """ContextContinuityManager 초기화"""
        # 연속성 판단 임계값
        self.strong_threshold = 0.7
        self.moderate_threshold = 0.3
        
        # 후속 질문 패턴
        self.follow_up_patterns = [
            r'그럼\s*',
            r'그러면\s*',
            r'그것\s*',
            r'이것\s*',
            r'저것\s*',
            r'앞서\s*',
            r'위에서\s*',
            r'이전\s*',
            r'방금\s*',
            r'더\s*',
            r'추가로\s*',
            r'또한\s*',
            r'그리고\s*',
            r'또\s*',
            r'다른\s*',
            r'비슷한\s*',
            r'같은\s*',
            r'유사한\s*',
            r'반대로\s*',
            r'반면\s*',
            r'하지만\s*',
            r'그런데\s*',
            r'그런\s*',
            r'이런\s*',
            r'저런\s*',
            r'어떤\s*',
            r'어떻게\s*',
            r'왜\s*',
            r'언제\s*',
            r'어디서\s*',
            r'누가\s*',
            r'무엇\s*',
            r'뭐\s*',
            r'몇\s*',
            r'얼마\s*',
            r'어느\s*',
            r'어떤\s*식\s*',
            r'어떤\s*방식\s*',
            r'어떤\s*방법\s*',
            r'어떤\s*과정\s*',
            r'어떤\s*단계\s*',
            r'어떤\s*절차\s*',
            r'어떤\s*순서\s*',
            r'어떤\s*기간\s*',
            r'어떤\s*시점\s*',
            r'어떤\s*장소\s*',
            r'어떤\s*지역\s*',
            r'어떤\s*기관\s*',
            r'어떤\s*차량\s*',
            r'어떤\s*통계\s*',
            r'어떤\s*비율\s*',
            r'어떤\s*수량\s*',
            r'어떤\s*성능\s*',
            r'어떤\s*효율\s*',
            r'어떤\s*속도\s*',
            r'어떤\s*정확도\s*',
            r'어떤\s*신뢰도\s*',
            r'어떤\s*영향\s*',
            r'어떤\s*효과\s*',
            r'어떤\s*결과\s*',
            r'어떤\s*원인\s*',
            r'어떤\s*이유\s*',
            r'어떤\s*차이\s*',
            r'어떤\s*비교\s*',
            r'어떤\s*유사\s*',
            r'어떤\s*반대\s*',
            r'어떤\s*같은\s*',
            r'어떤\s*다른\s*',
            r'어떤\s*순서\s*',
            r'어떤\s*단계\s*',
            r'어떤\s*과정\s*',
            r'어떤\s*절차\s*',
            r'어떤\s*방법\s*',
            r'어떤\s*방식\s*',
            r'어떤\s*기간\s*',
            r'어떤\s*시점\s*',
            r'어떤\s*장소\s*',
            r'어떤\s*지역\s*',
            r'어떤\s*기관\s*',
            r'어떤\s*차량\s*',
            r'어떤\s*통계\s*',
            r'어떤\s*비율\s*',
            r'어떤\s*수량\s*',
            r'어떤\s*성능\s*',
            r'어떤\s*효율\s*',
            r'어떤\s*속도\s*',
            r'어떤\s*정확도\s*',
            r'어떤\s*신뢰도\s*',
            r'어떤\s*영향\s*',
            r'어떤\s*효과\s*',
            r'어떤\s*결과\s*',
            r'어떤\s*원인\s*',
            r'어떤\s*이유\s*',
            r'어떤\s*차이\s*',
            r'어떤\s*비교\s*',
            r'어떤\s*유사\s*',
            r'어떤\s*반대\s*',
            r'어떤\s*같은\s*',
            r'어떤\s*다른\s*'
        ]
        
        logger.info("ContextContinuityManager 초기화 완료")
    
    def check_context_continuity(self, 
                               current_question: str, 
                               previous_context: ConversationContext,
                               current_elements: ExtractedElements,
                               previous_elements: ExtractedElements) -> ContinuityResult:
        """
        현재 질문이 이전 컨텍스트와 연속되는지 확인
        
        Args:
            current_question: 현재 질문
            previous_context: 이전 대화 컨텍스트
            current_elements: 현재 질문의 핵심요소
            previous_elements: 이전 질문의 핵심요소
            
        Returns:
            연속성 분석 결과
        """
        # 1. 후속 질문 패턴 확인
        is_follow_up = self._is_follow_up_question(current_question)
        
        # 2. 핵심요소 중복도 계산
        overlap_score = self._calculate_element_overlap(current_elements, previous_elements)
        
        # 3. 연속성 유형 판단
        continuity_type = self._determine_continuity_type(overlap_score, is_follow_up)
        
        # 4. 누락된 핵심요소 찾기
        missing_elements = self._find_missing_elements(current_elements, previous_elements)
        
        # 5. 병합 필요 여부 판단
        should_merge = self._should_merge_context(continuity_type, missing_elements)
        
        # 6. 향상된 질문 생성 (필요시)
        enhanced_question = None
        if should_merge:
            enhanced_question = self._create_enhanced_question(
                current_question, missing_elements, previous_context
            )
        
        # 7. 신뢰도 계산
        confidence = self._calculate_continuity_confidence(
            overlap_score, is_follow_up, len(missing_elements)
        )
        
        return ContinuityResult(
            continuity_type=continuity_type,
            overlap_score=overlap_score,
            should_merge=should_merge,
            missing_elements=missing_elements,
            enhanced_question=enhanced_question,
            confidence=confidence
        )
    
    def _is_follow_up_question(self, question: str) -> bool:
        """후속 질문인지 확인"""
        question_lower = question.lower()
        
        for pattern in self.follow_up_patterns:
            if re.search(pattern, question_lower):
                return True
        
        return False
    
    def _calculate_element_overlap(self, current: ExtractedElements, 
                                 previous: ExtractedElements) -> float:
        """핵심요소 중복도 계산"""
        current_texts = set(current.get_element_texts())
        previous_texts = set(previous.get_element_texts())
        
        if not previous_texts:
            return 0.0
        
        intersection = len(current_texts.intersection(previous_texts))
        return intersection / len(previous_texts)
    
    def _determine_continuity_type(self, overlap_score: float, is_follow_up: bool) -> ContinuityType:
        """연속성 유형 판단"""
        if is_follow_up:
            if overlap_score >= self.strong_threshold:
                return ContinuityType.STRONG
            elif overlap_score >= self.moderate_threshold:
                return ContinuityType.MODERATE
            else:
                return ContinuityType.WEAK
        else:
            if overlap_score >= self.strong_threshold:
                return ContinuityType.STRONG
            elif overlap_score >= self.moderate_threshold:
                return ContinuityType.MODERATE
            else:
                return ContinuityType.NONE
    
    def _find_missing_elements(self, current: ExtractedElements, 
                             previous: ExtractedElements) -> List[CoreElement]:
        """누락된 핵심요소 찾기"""
        current_texts = set(current.get_element_texts())
        missing_elements = []
        
        for element in previous.get_all_elements():
            if element.text not in current_texts:
                missing_elements.append(element)
        
        return missing_elements
    
    def _should_merge_context(self, continuity_type: ContinuityType, 
                            missing_elements: List[CoreElement]) -> bool:
        """컨텍스트 병합 필요 여부 판단"""
        if continuity_type == ContinuityType.STRONG:
            return len(missing_elements) > 0
        elif continuity_type == ContinuityType.MODERATE:
            return len(missing_elements) >= 1
        elif continuity_type == ContinuityType.WEAK:
            return len(missing_elements) >= 2
        else:
            return False
    
    def _create_enhanced_question(self, original_question: str, 
                                missing_elements: List[CoreElement],
                                previous_context: ConversationContext) -> str:
        """향상된 질문 생성"""
        enhanced_question = original_question
        
        # 주제가 누락된 경우 추가
        topic_elements = [elem for elem in missing_elements if elem.element_type == ElementType.TOPIC]
        if topic_elements and previous_context.topic:
            if not any(topic in enhanced_question for topic in [previous_context.topic, "교통사고", "교통량", "신호등"]):
                enhanced_question = f"{previous_context.topic}에 대해 {enhanced_question}"
        
        # 개체가 누락된 경우 추가
        entity_elements = [elem for elem in missing_elements if elem.element_type == ElementType.ENTITY]
        for entity in entity_elements[:2]:  # 최대 2개까지만 추가
            if entity.text not in enhanced_question:
                enhanced_question = f"{entity.text}의 {enhanced_question}"
        
        # 위치가 누락된 경우 추가
        location_elements = [elem for elem in missing_elements if elem.element_type == ElementType.LOCATION]
        for location in location_elements[:1]:  # 최대 1개까지만 추가
            if location.text not in enhanced_question:
                enhanced_question = f"{location.text}에서 {enhanced_question}"
        
        # 시간이 누락된 경우 추가
        temporal_elements = [elem for elem in missing_elements if elem.element_type == ElementType.TEMPORAL]
        for temporal in temporal_elements[:1]:  # 최대 1개까지만 추가
            if temporal.text not in enhanced_question:
                enhanced_question = f"{temporal.text} {enhanced_question}"
        
        return enhanced_question
    
    def _calculate_continuity_confidence(self, overlap_score: float, 
                                       is_follow_up: bool, 
                                       missing_count: int) -> float:
        """연속성 신뢰도 계산"""
        base_confidence = overlap_score
        
        # 후속 질문 보너스
        if is_follow_up:
            base_confidence += 0.2
        
        # 누락 요소 페널티
        missing_penalty = min(missing_count * 0.1, 0.3)
        base_confidence -= missing_penalty
        
        return max(0.0, min(1.0, base_confidence))
    
    def merge_context(self, current_elements: ExtractedElements, 
                     previous_elements: ExtractedElements,
                     continuity_result: ContinuityResult) -> ExtractedElements:
        """
        현재 질문과 이전 컨텍스트를 병합
        
        Args:
            current_elements: 현재 질문의 핵심요소
            previous_elements: 이전 질문의 핵심요소
            continuity_result: 연속성 분석 결과
            
        Returns:
            병합된 핵심요소
        """
        merged = ExtractedElements()
        
        # 주제 병합 (현재 주제가 없으면 이전 주제 사용)
        merged.topic = current_elements.topic or previous_elements.topic
        
        # 개체 병합 (중복 제거)
        current_entity_texts = {elem.text for elem in current_elements.entities}
        for elem in previous_elements.entities:
            if elem.text not in current_entity_texts:
                merged.entities.append(elem)
        merged.entities.extend(current_elements.entities)
        
        # 속성 병합
        current_attr_texts = {elem.text for elem in current_elements.attributes}
        for elem in previous_elements.attributes:
            if elem.text not in current_attr_texts:
                merged.attributes.append(elem)
        merged.attributes.extend(current_elements.attributes)
        
        # 관계 병합
        current_rel_texts = {elem.text for elem in current_elements.relations}
        for elem in previous_elements.relations:
            if elem.text not in current_rel_texts:
                merged.relations.append(elem)
        merged.relations.extend(current_elements.relations)
        
        # 시간 병합
        current_temp_texts = {elem.text for elem in current_elements.temporal}
        for elem in previous_elements.temporal:
            if elem.text not in current_temp_texts:
                merged.temporal.append(elem)
        merged.temporal.extend(current_elements.temporal)
        
        # 위치 병합
        current_loc_texts = {elem.text for elem in current_elements.locations}
        for elem in previous_elements.locations:
            if elem.text not in current_loc_texts:
                merged.locations.append(elem)
        merged.locations.extend(current_elements.locations)
        
        return merged
    
    def update_conversation_context(self, context: ConversationContext,
                                  elements: ExtractedElements,
                                  continuity_result: ContinuityResult) -> ConversationContext:
        """
        대화 컨텍스트 업데이트
        
        Args:
            context: 현재 컨텍스트
            elements: 새로운 핵심요소
            continuity_result: 연속성 분석 결과
            
        Returns:
            업데이트된 컨텍스트
        """
        updated_context = ConversationContext()
        
        # 주제 업데이트
        if elements.topic:
            updated_context.topic = elements.topic.text
        else:
            updated_context.topic = context.topic
        
        # 개체 업데이트 (최근 5개만 유지)
        updated_context.entities = context.entities[-4:] + [elem.text for elem in elements.entities]
        updated_context.entities = updated_context.entities[-5:]
        
        # 속성 업데이트
        updated_context.attributes = context.attributes[-4:] + [elem.text for elem in elements.attributes]
        updated_context.attributes = updated_context.attributes[-5:]
        
        # 관계 업데이트
        updated_context.relations = context.relations[-4:] + [elem.text for elem in elements.relations]
        updated_context.relations = updated_context.relations[-5:]
        
        # 시간 업데이트
        updated_context.temporal = context.temporal[-4:] + [elem.text for elem in elements.temporal]
        updated_context.temporal = updated_context.temporal[-5:]
        
        # 위치 업데이트
        updated_context.locations = context.locations[-4:] + [elem.text for elem in elements.locations]
        updated_context.locations = updated_context.locations[-5:]
        
        # 대화 깊이 업데이트
        if continuity_result.continuity_type in [ContinuityType.STRONG, ContinuityType.MODERATE]:
            updated_context.depth = context.depth + 1
        else:
            updated_context.depth = 1
        
        return updated_context

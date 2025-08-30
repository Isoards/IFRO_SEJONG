"""
핵심요소 추출 모듈

이 모듈은 질문에서 핵심요소(주제, 개체, 속성, 관계, 시간)를 추출하여
대화의 연속성을 파악하는 기능을 제공합니다.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ElementType(Enum):
    """핵심요소 유형"""
    TOPIC = "topic"           # 주제 (교통사고, 교통량, 신호등 등)
    ENTITY = "entity"         # 개체 (강남역, 2023년, 승용차 등)
    ATTRIBUTE = "attribute"   # 속성 (발생률, 평균, 최대값 등)
    RELATION = "relation"     # 관계 (비교, 원인, 결과 등)
    TEMPORAL = "temporal"     # 시간 (기간, 날짜, 시점 등)
    LOCATION = "location"     # 위치 (지역, 장소, 구역 등)

@dataclass
class CoreElement:
    """핵심요소 데이터 클래스"""
    text: str
    element_type: ElementType
    confidence: float
    position: Tuple[int, int]  # (시작, 끝) 위치
    metadata: Optional[Dict] = None

@dataclass
class ExtractedElements:
    """추출된 핵심요소들"""
    topic: Optional[CoreElement] = None
    entities: List[CoreElement] = None
    attributes: List[CoreElement] = None
    relations: List[CoreElement] = None
    temporal: List[CoreElement] = None
    locations: List[CoreElement] = None
    
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
    
    def get_all_elements(self) -> List[CoreElement]:
        """모든 핵심요소 반환"""
        elements = []
        if self.topic:
            elements.append(self.topic)
        elements.extend(self.entities)
        elements.extend(self.attributes)
        elements.extend(self.relations)
        elements.extend(self.temporal)
        elements.extend(self.locations)
        return elements
    
    def get_element_texts(self) -> List[str]:
        """모든 핵심요소의 텍스트 반환"""
        return [elem.text for elem in self.get_all_elements()]

class CoreElementExtractor:
    """
    질문에서 핵심요소를 추출하는 클래스
    """
    
    def __init__(self):
        """CoreElementExtractor 초기화"""
        # 주제 패턴 (교통 관련)
        self.topic_patterns = {
            "교통사고": [r'교통\s*사고', r'사고', r'충돌', r'추돌', r'교통\s*사망'],
            "교통량": [r'교통\s*량', r'트래픽', r'정체', r'혼잡', r'교통\s*흐름'],
            "신호등": [r'신호\s*등', r'신호', r'교차로', r'신호\s*체계'],
            "교통정책": [r'교통\s*정책', r'교통\s*규제', r'교통\s*법규'],
            "대중교통": [r'대중\s*교통', r'버스', r'지하철', r'전철', r'택시'],
            "도로": [r'도로', r'고속도로', r'국도', r'지방도', r'도시\s*도로']
        }
        
        # 개체 패턴
        self.entity_patterns = {
            "지역": [r'[가-힣]+(시|군|구|동|읍|면)', r'[가-힣]+역', r'[가-힣]+로', r'[가-힣]+길'],
            "시간": [r'\d{4}년', r'\d+월', r'\d+일', r'\d+시', r'\d+분'],
            "차량": [r'승용차', r'버스', r'트럭', r'오토바이', r'자전거', r'보행자'],
            "기관": [r'경찰서', r'소방서', r'병원', r'학교', r'기업', r'정부']
        }
        
        # 속성 패턴
        self.attribute_patterns = {
            "수량": [r'\d+(?:\.\d+)?(?:개|명|건|대|대|회|번)'],
            "비율": [r'\d+(?:\.\d+)?%', r'\d+(?:\.\d+)?퍼센트'],
            "통계": [r'평균', r'최대', r'최소', r'합계', r'총계', r'증감'],
            "성능": [r'효율', r'성능', r'속도', r'정확도', r'신뢰도']
        }
        
        # 관계 패턴
        self.relation_patterns = {
            "비교": [r'비교', r'차이', r'다른', r'같은', r'유사', r'반대'],
            "원인": [r'원인', r'이유', r'때문', r'로\s*인해', r'때문에'],
            "결과": [r'결과', r'영향', r'효과', r'발생', r'증가', r'감소'],
            "순서": [r'순서', r'단계', r'과정', r'절차', r'방법']
        }
        
        # 시간 패턴
        self.temporal_patterns = {
            "기간": [r'\d+(?:년|월|일|시간|분|초)\s*(?:동안|간|후|전)'],
            "시점": [r'오늘', r'어제', r'내일', r'이번\s*주', r'다음\s*주'],
            "빈도": [r'매일', r'매주', r'매월', r'정기적', r'주기적']
        }
        
        # 위치 패턴
        self.location_patterns = {
            "지역": [r'[가-힣]+(시|군|구|동|읍|면)', r'[가-힣]+지역', r'[가-힣]+구역'],
            "교차로": [r'[가-힣]+교차로', r'[가-힣]+사거리', r'[가-힣]+삼거리'],
            "도로": [r'[가-힣]+로', r'[가-힣]+길', r'[가-힣]+대로']
        }
        
        logger.info("CoreElementExtractor 초기화 완료")
    
    def extract_core_elements(self, question: str) -> ExtractedElements:
        """
        질문에서 핵심요소 추출
        
        Args:
            question: 분석할 질문
            
        Returns:
            추출된 핵심요소들
        """
        question_lower = question.lower()
        extracted = ExtractedElements()
        
        # 1. 주제 추출
        extracted.topic = self._extract_topic(question_lower)
        
        # 2. 개체 추출
        extracted.entities = self._extract_entities(question_lower)
        
        # 3. 속성 추출
        extracted.attributes = self._extract_attributes(question_lower)
        
        # 4. 관계 추출
        extracted.relations = self._extract_relations(question_lower)
        
        # 5. 시간 추출
        extracted.temporal = self._extract_temporal(question_lower)
        
        # 6. 위치 추출
        extracted.locations = self._extract_locations(question_lower)
        
        logger.debug(f"핵심요소 추출 완료: 주제={extracted.topic}, 개체={len(extracted.entities)}개")
        return extracted
    
    def _extract_topic(self, question: str) -> Optional[CoreElement]:
        """주제 추출"""
        for topic_name, patterns in self.topic_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, question)
                if match:
                    return CoreElement(
                        text=topic_name,
                        element_type=ElementType.TOPIC,
                        confidence=0.9,
                        position=(match.start(), match.end()),
                        metadata={"original_text": match.group()}
                    )
        return None
    
    def _extract_entities(self, question: str) -> List[CoreElement]:
        """개체 추출"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, question)
                for match in matches:
                    entities.append(CoreElement(
                        text=match.group(),
                        element_type=ElementType.ENTITY,
                        confidence=0.8,
                        position=(match.start(), match.end()),
                        metadata={"entity_type": entity_type}
                    ))
        
        return entities
    
    def _extract_attributes(self, question: str) -> List[CoreElement]:
        """속성 추출"""
        attributes = []
        
        for attr_type, patterns in self.attribute_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, question)
                for match in matches:
                    attributes.append(CoreElement(
                        text=match.group(),
                        element_type=ElementType.ATTRIBUTE,
                        confidence=0.8,
                        position=(match.start(), match.end()),
                        metadata={"attribute_type": attr_type}
                    ))
        
        return attributes
    
    def _extract_relations(self, question: str) -> List[CoreElement]:
        """관계 추출"""
        relations = []
        
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, question)
                for match in matches:
                    relations.append(CoreElement(
                        text=match.group(),
                        element_type=ElementType.RELATION,
                        confidence=0.7,
                        position=(match.start(), match.end()),
                        metadata={"relation_type": relation_type}
                    ))
        
        return relations
    
    def _extract_temporal(self, question: str) -> List[CoreElement]:
        """시간 추출"""
        temporal = []
        
        for temporal_type, patterns in self.temporal_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, question)
                for match in matches:
                    temporal.append(CoreElement(
                        text=match.group(),
                        element_type=ElementType.TEMPORAL,
                        confidence=0.8,
                        position=(match.start(), match.end()),
                        metadata={"temporal_type": temporal_type}
                    ))
        
        return temporal
    
    def _extract_locations(self, question: str) -> List[CoreElement]:
        """위치 추출"""
        locations = []
        
        for location_type, patterns in self.location_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, question)
                for match in matches:
                    locations.append(CoreElement(
                        text=match.group(),
                        element_type=ElementType.LOCATION,
                        confidence=0.8,
                        position=(match.start(), match.end()),
                        metadata={"location_type": location_type}
                    ))
        
        return locations
    
    def calculate_element_overlap(self, elements1: ExtractedElements, 
                                elements2: ExtractedElements) -> float:
        """
        두 핵심요소 집합 간의 중복도 계산
        
        Args:
            elements1: 첫 번째 핵심요소 집합
            elements2: 두 번째 핵심요소 집합
            
        Returns:
            중복도 점수 (0.0 ~ 1.0)
        """
        texts1 = set(elements1.get_element_texts())
        texts2 = set(elements2.get_element_texts())
        
        if not texts1 or not texts2:
            return 0.0
        
        intersection = len(texts1.intersection(texts2))
        union = len(texts1.union(texts2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_missing_elements(self, current: ExtractedElements, 
                           previous: ExtractedElements) -> List[CoreElement]:
        """
        현재 질문에서 누락된 핵심요소 찾기
        
        Args:
            current: 현재 질문의 핵심요소
            previous: 이전 질문의 핵심요소
            
        Returns:
            누락된 핵심요소 리스트
        """
        current_texts = set(current.get_element_texts())
        previous_texts = set(previous.get_element_texts())
        
        missing_texts = previous_texts - current_texts
        missing_elements = []
        
        for element in previous.get_all_elements():
            if element.text in missing_texts:
                missing_elements.append(element)
        
        return missing_elements

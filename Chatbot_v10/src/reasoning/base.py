"""
v5.2 Reasoning Engine Base
심볼릭 추론 엔진의 기반 클래스 및 데이터 구조

핵심 원리:
- 모든 추론은 수식 기반 (deterministic)
- LLM 의존성 최소화
- confidence/sign 전파 규칙 고정
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class ReasoningResultType(Enum):
    """추론 결과 유형"""
    PATH = "path"              # 경로 기반 추론
    MECHANISM = "mechanism"    # 메커니즘 전파
    SCENARIO = "scenario"      # 시나리오 시뮬레이션
    COMBINED = "combined"      # 복합 추론


@dataclass
class ReasoningPath:
    """추론 경로"""
    nodes: List[str]           # entity_id 리스트
    edges: List[Tuple[str, str, float, int]]  # (from, to, conf, sign)
    path_confidence: float     # 경로 전체 confidence
    path_sign: int             # 최종 sign: +1 or -1
    length: int
    
    @property
    def is_valid(self) -> bool:
        return self.path_confidence > 0 and len(self.nodes) >= 2


@dataclass
class ReasoningResult:
    """추론 결과"""
    result_type: ReasoningResultType
    success: bool
    confidence: float          # 0.0 ~ 1.0
    sign: Optional[int]        # +1, -1, or None
    paths: List[ReasoningPath] = field(default_factory=list)
    explanation: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # v5.2: 추론 과정 추적
    trace: List[str] = field(default_factory=list)


@dataclass
class PropagationEffect:
    """영향도 전파 결과"""
    entity_id: str
    entity_name: str
    effect_value: float        # 영향도 크기 (magnitude)
    effect_sign: int           # +1 (증가) or -1 (감소)
    confidence: float          # 이 영향도에 대한 확신도
    path_length: int           # 영향도 경로 길이
    contributing_paths: List[ReasoningPath] = field(default_factory=list)


class BaseReasoner(ABC):
    """
    추론 엔진 베이스 클래스
    
    v5.2 핵심 원칙:
    - 모든 계산은 수식으로 고정
    - depth 제한으로 복잡도 관리
    - sign × confidence 전파
    """
    
    # v5.2 기준값
    MAX_DEPTH = 3
    LENGTH_PENALTY_BASE = 0.92
    CONFLICT_PENALTY = 0.5
    MIN_CONFIDENCE_THRESHOLD = 0.1
    
    def __init__(self, graph: Any = None):
        self.graph = graph
        self._trace: List[str] = []
    
    @abstractmethod
    async def reason(self, *args, **kwargs) -> ReasoningResult:
        """추론 실행 - 서브클래스에서 구현"""
        pass
    
    def _add_trace(self, message: str):
        """추론 과정 추적"""
        self._trace.append(message)
    
    def _clear_trace(self):
        """추적 초기화"""
        self._trace = []
    
    def _calculate_path_confidence(
        self,
        edge_confidences: List[float],
        path_length: int
    ) -> float:
        """
        v5.2 경로 confidence 계산
        
        공식: path_conf = Π(ci) * 0.92^(k-1)
        """
        if not edge_confidences:
            return 0.0
        
        # 곱셈 전파
        product = 1.0
        for c in edge_confidences:
            product *= c
        
        # 길이 패널티
        penalty = self.LENGTH_PENALTY_BASE ** max(0, path_length - 1)
        
        return product * penalty
    
    def _propagate_sign(self, signs: List[int]) -> int:
        """
        v5.2 sign 전파
        
        공식: sign = s1 * s2 * ... * sk
        """
        result = 1
        for s in signs:
            result *= s
        return result
    
    def _apply_conflict_penalty(
        self,
        confidence: float,
        has_conflict: bool
    ) -> float:
        """
        v5.2 충돌 패널티 적용
        
        공식: if conflicting → conf *= 0.5
        """
        if has_conflict:
            return confidence * self.CONFLICT_PENALTY
        return confidence

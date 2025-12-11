"""
v5.2 Scenario Simulator
영향도 전파 엔진

핵심 기능:
- 초기 신호 → 전체 그래프 전파
- V(N) += V(E) * sign(E→N) * conf(E→N)
- 충돌 조정: weaker_effect *= 0.6
"""
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict

from src.reasoning.base import (
    BaseReasoner, ReasoningResult, PropagationEffect,
    ReasoningResultType
)
from src.domain.relations import OntologyGraph, Relation
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScenarioInput:
    """시나리오 입력"""
    root_entity_id: str
    initial_magnitude: float  # 변화 크기 (양수)
    initial_sign: int         # +1 (증가) or -1 (감소)
    context_conditions: List[str] = field(default_factory=list)


@dataclass 
class ScenarioOutput:
    """시나리오 출력"""
    effects: Dict[str, PropagationEffect]  # entity_id → effect
    total_entities_affected: int
    max_propagation_depth: int
    has_oscillation: bool = False
    oscillation_entities: List[str] = field(default_factory=list)


class ScenarioSimulator(BaseReasoner):
    """
    v5.2 Scenario Simulator
    
    영향도 전파 규칙:
    - V(N) += V(E) * sign(E→N) * conf(E→N)
    - 충돌 시: weaker_effect *= 0.6, final_sign = stronger sign
    """
    
    CONFLICT_DAMPING = 0.6     # 충돌 시 약한 효과 감쇠
    MIN_EFFECT_THRESHOLD = 0.05  # 최소 영향도 임계값
    
    def __init__(self, graph: OntologyGraph):
        super().__init__(graph)
    
    async def reason(
        self,
        scenario_input: ScenarioInput
    ) -> ReasoningResult:
        """
        시나리오 시뮬레이션 실행
        """
        self._clear_trace()
        self._add_trace(f"ScenarioSimulator: root={scenario_input.root_entity_id}, mag={scenario_input.initial_magnitude}")
        
        if not self.graph:
            return ReasoningResult(
                result_type=ReasoningResultType.SCENARIO,
                success=False,
                confidence=0.0,
                sign=None,
                explanation="Graph not provided"
            )
        
        # 시뮬레이션 실행
        output = self._simulate(scenario_input)
        
        if not output.effects:
            return ReasoningResult(
                result_type=ReasoningResultType.SCENARIO,
                success=False,
                confidence=0.0,
                sign=None,
                explanation="No effects propagated",
                trace=self._trace.copy()
            )
        
        # 평균 confidence 계산
        avg_confidence = sum(e.confidence for e in output.effects.values()) / len(output.effects)
        
        return ReasoningResult(
            result_type=ReasoningResultType.SCENARIO,
            success=True,
            confidence=avg_confidence,
            sign=scenario_input.initial_sign,
            explanation=f"Affected {output.total_entities_affected} entities, max depth {output.max_propagation_depth}",
            trace=self._trace.copy(),
            details={
                "effects": {
                    eid: {
                        "name": e.entity_name,
                        "value": e.effect_value,
                        "sign": e.effect_sign,
                        "confidence": e.confidence
                    }
                    for eid, e in output.effects.items()
                },
                "has_oscillation": output.has_oscillation,
                "oscillation_entities": output.oscillation_entities
            }
        )
    
    def _simulate(self, scenario_input: ScenarioInput) -> ScenarioOutput:
        """
        BFS 기반 영향도 전파 시뮬레이션
        """
        root_id = scenario_input.root_entity_id
        
        # 영향도 저장: entity_id → (value, sign, confidence, depth)
        effects: Dict[str, List[Tuple[float, int, float, int]]] = defaultdict(list)
        
        # 초기 신호
        root_entity = self.graph.get_entity(root_id)
        if not root_entity:
            return ScenarioOutput(effects={}, total_entities_affected=0, max_propagation_depth=0)
        
        effects[root_id].append((
            scenario_input.initial_magnitude,
            scenario_input.initial_sign,
            1.0,  # 초기 confidence
            0     # depth
        ))
        
        # BFS 전파
        visited_edges: Set[Tuple[str, str]] = set()
        queue = [(root_id, scenario_input.initial_magnitude, scenario_input.initial_sign, 1.0, 0)]
        max_depth = 0
        
        while queue:
            current_id, current_value, current_sign, current_conf, depth = queue.pop(0)
            
            if depth >= self.MAX_DEPTH:
                continue
            
            max_depth = max(max_depth, depth)
            
            # 이웃으로 전파
            for relation in self.graph.relations:
                if relation.source_entity_id != current_id:
                    continue
                
                edge_key = (current_id, relation.target_entity_id)
                if edge_key in visited_edges:
                    continue
                visited_edges.add(edge_key)
                
                target_id = relation.target_entity_id
                
                # v5.2 전파 공식
                rel_sign = self._extract_sign(relation)
                rel_conf = relation.validation_score if relation.validation_score > 0 else 0.5
                
                # V(N) += V(E) * sign(E→N) * conf(E→N)
                propagated_sign = current_sign * rel_sign
                propagated_value = abs(current_value) * rel_conf
                propagated_conf = current_conf * rel_conf
                
                if propagated_value >= self.MIN_EFFECT_THRESHOLD:
                    effects[target_id].append((
                        propagated_value,
                        propagated_sign,
                        propagated_conf,
                        depth + 1
                    ))
                    
                    queue.append((
                        target_id,
                        propagated_value,
                        propagated_sign,
                        propagated_conf,
                        depth + 1
                    ))
        
        # 최종 효과 통합
        final_effects = self._consolidate_effects(effects)
        
        # 진동 감지
        oscillation_entities = [
            eid for eid, effect_list in effects.items()
            if len(effect_list) > 1 and self._has_sign_conflict(effect_list)
        ]
        
        self._add_trace(f"Propagation complete: {len(final_effects)} entities, max_depth={max_depth}")
        
        return ScenarioOutput(
            effects=final_effects,
            total_entities_affected=len(final_effects),
            max_propagation_depth=max_depth,
            has_oscillation=len(oscillation_entities) > 0,
            oscillation_entities=oscillation_entities
        )
    
    def _extract_sign(self, relation: Relation) -> int:
        """관계에서 sign 추출"""
        sign = getattr(relation, 'sign', None)
        if sign is not None:
            return sign
        
        direction = getattr(relation, 'direction', None)
        if direction in {'inverse', '-', 'negative'}:
            return -1
        
        return 1
    
    def _has_sign_conflict(
        self,
        effect_list: List[Tuple[float, int, float, int]]
    ) -> bool:
        """sign 충돌 여부"""
        signs = set(e[1] for e in effect_list)
        return len(signs) > 1
    
    def _consolidate_effects(
        self,
        effects: Dict[str, List[Tuple[float, int, float, int]]]
    ) -> Dict[str, PropagationEffect]:
        """
        v5.2 충돌 조정 및 최종 효과 계산
        
        충돌 시:
        - weaker_effect *= 0.6
        - final_sign = sign with larger magnitude
        """
        final_effects = {}
        
        for entity_id, effect_list in effects.items():
            if not effect_list:
                continue
            
            entity = self.graph.get_entity(entity_id)
            entity_name = entity.canonical_name if entity else entity_id
            
            # 동일 sign 효과 합산
            positive_sum = sum(e[0] for e in effect_list if e[1] > 0)
            negative_sum = sum(e[0] for e in effect_list if e[1] < 0)
            
            # 충돌 처리
            if positive_sum > 0 and negative_sum > 0:
                # 충돌 발생
                if positive_sum >= negative_sum:
                    final_sign = 1
                    final_value = positive_sum - (negative_sum * self.CONFLICT_DAMPING)
                else:
                    final_sign = -1
                    final_value = negative_sum - (positive_sum * self.CONFLICT_DAMPING)
                
                self._add_trace(f"Conflict at {entity_name}: +{positive_sum:.2f} vs -{negative_sum:.2f}")
            else:
                final_sign = 1 if positive_sum > 0 else -1
                final_value = max(positive_sum, negative_sum)
            
            # 평균 confidence / 최소 depth
            avg_conf = sum(e[2] for e in effect_list) / len(effect_list)
            min_depth = min(e[3] for e in effect_list)
            
            final_effects[entity_id] = PropagationEffect(
                entity_id=entity_id,
                entity_name=entity_name,
                effect_value=final_value,
                effect_sign=final_sign,
                confidence=avg_conf,
                path_length=min_depth
            )
        
        return final_effects
    
    async def simulate_what_if(
        self,
        entity_name: str,
        change_direction: str  # "increase" or "decrease"
    ) -> Dict[str, Any]:
        """
        "만약 X가 증가/감소하면?" 시뮬레이션
        
        Args:
            entity_name: 엔티티 이름
            change_direction: "increase" or "decrease"
        """
        entity = self.graph.get_entity_by_name(entity_name)
        if not entity:
            return {"error": f"Entity not found: {entity_name}"}
        
        scenario = ScenarioInput(
            root_entity_id=entity.id,
            initial_magnitude=1.0,
            initial_sign=1 if change_direction == "increase" else -1
        )
        
        result = await self.reason(scenario)
        
        if not result.success:
            return {"error": result.explanation}
        
        # 영향도 기준 정렬
        effects = result.details.get("effects", {})
        sorted_effects = sorted(
            effects.items(),
            key=lambda x: x[1]["value"] * x[1]["confidence"],
            reverse=True
        )
        
        return {
            "query": f"What if {entity_name} {change_direction}s?",
            "effects": [
                {
                    "entity": e[1]["name"],
                    "direction": "increases" if e[1]["sign"] > 0 else "decreases",
                    "magnitude": e[1]["value"],
                    "confidence": e[1]["confidence"]
                }
                for e in sorted_effects[:10]
            ],
            "total_affected": result.details.get("total_entities_affected", 0)
        }

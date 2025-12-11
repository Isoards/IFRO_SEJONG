"""
v5.2 Mechanism Reasoner
메커니즘 기반 추론 엔진

핵심 기능:
- sign × confidence 전파
- 조건 충돌 보정
- 인과 메커니즘 분석
"""
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

from src.reasoning.base import (
    BaseReasoner, ReasoningResult, ReasoningPath,
    ReasoningResultType
)
from src.domain.relations import OntologyGraph, Relation
from config.constants import RelationType
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MechanismChain:
    """메커니즘 체인"""
    source_entity_id: str
    target_entity_id: str
    intermediate_entities: List[str]
    chain_sign: int           # 최종 sign
    chain_confidence: float   # 체인 전체 confidence
    has_condition_conflict: bool = False
    conditions: List[str] = field(default_factory=list)


class MechanismReasoner(BaseReasoner):
    """
    v5.2 Mechanism Reasoner
    
    전파 규칙:
    - sign = s1 * s2
    - conf = c1 * c2
    - conflicting_conditions → conf *= 0.5
    """
    
    def __init__(self, graph: OntologyGraph):
        super().__init__(graph)
    
    async def reason(
        self,
        source_entity_id: str,
        target_entity_id: str,
        context_conditions: Optional[List[str]] = None
    ) -> ReasoningResult:
        """
        메커니즘 기반 추론
        
        A가 변하면 B는 어떻게 변하는가?
        
        Args:
            source_entity_id: 원인 엔티티
            target_entity_id: 결과 엔티티
            context_conditions: 현재 조건 목록
        """
        self._clear_trace()
        self._add_trace(f"MechanismReasoner: {source_entity_id} → {target_entity_id}")
        
        if not self.graph:
            return ReasoningResult(
                result_type=ReasoningResultType.MECHANISM,
                success=False,
                confidence=0.0,
                sign=None,
                explanation="Graph not provided"
            )
        
        # 모든 메커니즘 체인 탐색
        chains = self._find_mechanism_chains(
            source_entity_id,
            target_entity_id,
            context_conditions or []
        )
        
        if not chains:
            self._add_trace("No mechanism chains found")
            return ReasoningResult(
                result_type=ReasoningResultType.MECHANISM,
                success=False,
                confidence=0.0,
                sign=None,
                explanation="No causal mechanism found",
                trace=self._trace.copy()
            )
        
        # 체인 결과 통합
        combined_sign, combined_conf = self._combine_chains(chains)
        
        # ReasoningPath로 변환
        paths = []
        for chain in chains:
            all_nodes = [chain.source_entity_id] + chain.intermediate_entities + [chain.target_entity_id]
            paths.append(ReasoningPath(
                nodes=all_nodes,
                edges=[],  # 상세 edge는 chain에서 추출
                path_confidence=chain.chain_confidence,
                path_sign=chain.chain_sign,
                length=len(all_nodes)
            ))
        
        self._add_trace(f"Combined: sign={combined_sign}, conf={combined_conf:.3f}")
        
        return ReasoningResult(
            result_type=ReasoningResultType.MECHANISM,
            success=True,
            confidence=combined_conf,
            sign=combined_sign,
            paths=paths,
            explanation=f"Found {len(chains)} mechanism chains",
            trace=self._trace.copy(),
            details={
                "chain_count": len(chains),
                "has_conflicts": any(c.has_condition_conflict for c in chains)
            }
        )
    
    def _find_mechanism_chains(
        self,
        source_id: str,
        target_id: str,
        context_conditions: List[str]
    ) -> List[MechanismChain]:
        """메커니즘 체인 탐색"""
        chains = []
        
        # DFS로 모든 인과 경로 탐색
        stack = [(source_id, [], 1.0, 1, [])]  # (current, path, conf, sign, conditions)
        
        while stack:
            current, path, acc_conf, acc_sign, acc_conditions = stack.pop()
            
            if current == target_id and path:
                # 조건 충돌 검사
                has_conflict = self._check_condition_conflict(
                    acc_conditions,
                    context_conditions
                )
                
                final_conf = acc_conf
                if has_conflict:
                    final_conf *= self.CONFLICT_PENALTY
                
                chains.append(MechanismChain(
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    intermediate_entities=path[:-1] if path else [],
                    chain_sign=acc_sign,
                    chain_confidence=final_conf,
                    has_condition_conflict=has_conflict,
                    conditions=acc_conditions
                ))
                continue
            
            if len(path) >= self.MAX_DEPTH:
                continue
            
            # 다음 관계 탐색
            for relation in self.graph.relations:
                if relation.source_entity_id != current:
                    continue
                
                next_id = relation.target_entity_id
                
                # 이미 방문한 노드 스킵
                if next_id in path or next_id == source_id:
                    continue
                
                # v5.2: sign × confidence 전파
                rel_sign = self._extract_sign(relation)
                rel_conf = relation.validation_score if relation.validation_score > 0 else 0.5
                
                new_sign = acc_sign * rel_sign
                new_conf = acc_conf * rel_conf
                
                # 조건 수집
                rel_conditions = getattr(relation, 'conditions', []) or []
                
                if new_conf >= self.MIN_CONFIDENCE_THRESHOLD:
                    stack.append((
                        next_id,
                        path + [next_id],
                        new_conf,
                        new_sign,
                        acc_conditions + rel_conditions
                    ))
        
        return chains
    
    def _extract_sign(self, relation: Relation) -> int:
        """관계에서 sign 추출"""
        # sign 필드가 있으면 사용
        sign = getattr(relation, 'sign', None)
        if sign is not None:
            return sign
        
        # relation_type에서 추정
        if relation.relation_type in {RelationType.INVERSE}:
            return -1
        
        # direction에서 추정
        direction = getattr(relation, 'direction', None)
        if direction in {'inverse', '-', 'negative'}:
            return -1
        
        return 1  # 기본값
    
    def _check_condition_conflict(
        self,
        chain_conditions: List[str],
        context_conditions: List[str]
    ) -> bool:
        """조건 충돌 검사"""
        if not chain_conditions or not context_conditions:
            return False
        
        # 간단한 충돌 검사: 동일 조건이 반대 상태면 충돌
        # TODO: 더 정교한 조건 로직 필요 시 확장
        chain_set = set(c.lower() for c in chain_conditions)
        context_set = set(c.lower() for c in context_conditions)
        
        # 예: "recession=true"와 "recession=false" 충돌
        for c in chain_set:
            negated = f"not_{c}" if not c.startswith("not_") else c[4:]
            if negated in context_set:
                return True
        
        return False
    
    def _combine_chains(
        self,
        chains: List[MechanismChain]
    ) -> Tuple[int, float]:
        """
        여러 체인 결과 통합
        
        v5.2 규칙:
        - sign이 다르면 더 높은 confidence 체인의 sign 선택
        - confidence는 최대값 사용 (OR 조합)
        """
        if not chains:
            return 0, 0.0
        
        # confidence 기준 정렬
        sorted_chains = sorted(chains, key=lambda c: c.chain_confidence, reverse=True)
        
        # 최고 confidence 체인 기준
        best = sorted_chains[0]
        
        # 다른 sign의 체인이 있는지 확인
        positive_chains = [c for c in chains if c.chain_sign > 0]
        negative_chains = [c for c in chains if c.chain_sign < 0]
        
        if positive_chains and negative_chains:
            # 충돌하는 경우: 더 높은 confidence 체인 선택
            pos_max = max(c.chain_confidence for c in positive_chains)
            neg_max = max(c.chain_confidence for c in negative_chains)
            
            if pos_max >= neg_max:
                final_sign = 1
                final_conf = pos_max
            else:
                final_sign = -1
                final_conf = neg_max
            
            # 충돌 패널티 적용
            final_conf *= 0.8
            
            self._add_trace(f"Sign conflict: pos={pos_max:.2f}, neg={neg_max:.2f}")
        else:
            final_sign = best.chain_sign
            final_conf = best.chain_confidence
        
        return final_sign, final_conf
    
    async def analyze_impact(
        self,
        entity_id: str,
        change_sign: int = 1
    ) -> Dict[str, Tuple[int, float]]:
        """
        엔티티 변화가 다른 엔티티에 미치는 영향 분석
        
        Returns:
            {entity_id: (sign, confidence)}
        """
        impacts = {}
        
        for entity in self.graph.entities:
            if entity.id == entity_id:
                continue
            
            result = await self.reason(entity_id, entity.id)
            if result.success and result.confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                final_sign = change_sign * (result.sign or 1)
                impacts[entity.id] = (final_sign, result.confidence)
        
        return impacts

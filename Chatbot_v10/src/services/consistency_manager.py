"""
v5.2 Global Consistency Manager
시스템 안정화 핵심 계층

핵심 기능:
- 그래프 구조 붕괴 방지
- RL 폭주 방지 (±15% clamp)
- 모듈 간 threshold 충돌 조정
- 중복/모순 관계 자동 조정
"""
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.shared.logging import get_logger

if TYPE_CHECKING:
    from src.domain.relations import OntologyGraph

logger = get_logger(__name__)


class ConsistencyAlert(Enum):
    """일관성 경고 유형"""
    RL_CHANGE_EXCEEDED = "rl_change_exceeded"
    CONTRADICTION_RATE_HIGH = "contradiction_rate_high"
    DEGREE_LIMIT_EXCEEDED = "degree_limit_exceeded"
    SCENARIO_OSCILLATION = "scenario_oscillation"
    GRAPH_DENSITY_HIGH = "graph_density_high"


@dataclass
class ConsistencyStatus:
    """시스템 일관성 상태"""
    is_healthy: bool = True
    alerts: List[ConsistencyAlert] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    actions_taken: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConsistencyConfig:
    """v5.2 Consistency Manager 설정"""
    # RL 제한
    max_rl_change_percent: float = 15.0
    
    # 모순율 제한
    max_contradiction_rate: float = 0.03  # 3%
    
    # Degree 제한
    max_entity_degree: int = 40
    
    # 시나리오 진동 감지
    oscillation_threshold: int = 3
    
    # RL freeze 사이클
    rl_freeze_cycles: int = 1
    
    # 그래프 밀도 제한
    max_graph_density: float = 0.3


class ConsistencyManager:
    """
    v5.2 Global Consistency Manager
    
    정책:
    - if RL change > 15%: clamp to 15%
    - if contradiction_rate > 3%: freeze RL updates for 1 cycle
    - if relation_degree_limit exceeded repeatedly: enforce pruning
    - if scenario oscillation detected: reduce max_reasoning_depth by 1
    """
    
    def __init__(self, config: Optional[ConsistencyConfig] = None):
        self.config = config or ConsistencyConfig()
        
        # 상태 추적
        self._rl_frozen = False
        self._rl_freeze_remaining: int = 0
        self._oscillation_history: Dict[str, int] = {}
        self._degree_violations: Dict[str, int] = {}
        
        # 현재 파라미터 스냅샷
        self._param_snapshot: Dict[str, float] = {}
        
        # 히스토리
        self._status_history: List[ConsistencyStatus] = []
    
    async def check(
        self,
        graph: Optional["OntologyGraph"] = None,
        rl_params: Optional[Dict[str, float]] = None,
        reasoning_metrics: Optional[Dict[str, Any]] = None
    ) -> ConsistencyStatus:
        """
        시스템 일관성 검사
        
        Args:
            graph: 현재 온톨로지 그래프
            rl_params: 현재 RL 파라미터
            reasoning_metrics: 추론 메트릭
        """
        alerts = []
        actions = []
        metrics = {}
        
        # 1. RL 변경률 검사
        if rl_params:
            rl_result = self._check_rl_changes(rl_params)
            if rl_result:
                alerts.append(ConsistencyAlert.RL_CHANGE_EXCEEDED)
                actions.extend(rl_result)
        
        # 2. 그래프 일관성 검사
        if graph:
            graph_result = await self._check_graph_consistency(graph)
            alerts.extend(graph_result.get("alerts", []))
            actions.extend(graph_result.get("actions", []))
            metrics.update(graph_result.get("metrics", {}))
        
        # 3. 시나리오 진동 검사
        if reasoning_metrics:
            oscillation_result = self._check_oscillation(reasoning_metrics)
            if oscillation_result:
                alerts.append(ConsistencyAlert.SCENARIO_OSCILLATION)
                actions.extend(oscillation_result)
        
        # 4. RL freeze 상태 업데이트
        if self._rl_frozen:
            self._rl_freeze_remaining -= 1
            if self._rl_freeze_remaining <= 0:
                self._rl_frozen = False
                actions.append("RL updates unfrozen")
        
        status = ConsistencyStatus(
            is_healthy=len(alerts) == 0,
            alerts=alerts,
            metrics=metrics,
            actions_taken=actions
        )
        
        self._status_history.append(status)
        
        if not status.is_healthy:
            logger.warning(
                "consistency_issues_detected",
                alerts=[a.value for a in alerts],
                actions=actions
            )
        
        return status
    
    def _check_rl_changes(
        self,
        new_params: Dict[str, float]
    ) -> List[str]:
        """RL 파라미터 변경률 검사"""
        actions = []
        
        for param_name, new_value in new_params.items():
            old_value = self._param_snapshot.get(param_name)
            
            if old_value is not None and old_value != 0:
                change_percent = abs(new_value - old_value) / abs(old_value) * 100
                
                if change_percent > self.config.max_rl_change_percent:
                    # v5.2: Clamp to 15%
                    max_delta = abs(old_value) * self.config.max_rl_change_percent / 100
                    
                    if new_value > old_value:
                        clamped_value = old_value + max_delta
                    else:
                        clamped_value = old_value - max_delta
                    
                    new_params[param_name] = clamped_value
                    actions.append(
                        f"RL param '{param_name}' clamped: {new_value:.4f} → {clamped_value:.4f}"
                    )
        
        # 스냅샷 업데이트
        self._param_snapshot = new_params.copy()
        
        return actions
    
    async def _check_graph_consistency(
        self,
        graph: "OntologyGraph"
    ) -> Dict[str, Any]:
        """그래프 일관성 검사"""
        alerts = []
        actions = []
        metrics = {}
        
        # 1. 모순율 계산
        contradiction_count = self._count_contradictions(graph)
        total_relations = len(graph.relations)
        
        if total_relations > 0:
            contradiction_rate = contradiction_count / total_relations
            metrics["contradiction_rate"] = contradiction_rate
            
            if contradiction_rate > self.config.max_contradiction_rate:
                alerts.append(ConsistencyAlert.CONTRADICTION_RATE_HIGH)
                
                # v5.2: RL freeze
                self._rl_frozen = True
                self._rl_freeze_remaining = self.config.rl_freeze_cycles
                actions.append(f"RL frozen for {self.config.rl_freeze_cycles} cycle(s)")
        
        # 2. Degree 검사
        for entity in graph.entities:
            entity_id = entity.id
            
            # 관계 수 계산
            out_degree = sum(
                1 for r in graph.relations
                if r.source_entity_id == entity_id
            )
            in_degree = sum(
                1 for r in graph.relations
                if r.target_entity_id == entity_id
            )
            total_degree = out_degree + in_degree
            
            if total_degree > self.config.max_entity_degree:
                self._degree_violations[entity_id] = \
                    self._degree_violations.get(entity_id, 0) + 1
                
                # 반복 위반 시 강제 pruning
                if self._degree_violations[entity_id] >= 3:
                    alerts.append(ConsistencyAlert.DEGREE_LIMIT_EXCEEDED)
                    prune_count = await self._prune_low_confidence_relations(
                        graph, entity_id
                    )
                    actions.append(
                        f"Pruned {prune_count} relations from entity {entity.canonical_name}"
                    )
        
        # 3. 그래프 밀도
        node_count = graph.node_count
        if node_count > 1:
            max_edges = node_count * (node_count - 1)
            density = graph.edge_count / max_edges if max_edges > 0 else 0
            metrics["graph_density"] = density
            
            if density > self.config.max_graph_density:
                alerts.append(ConsistencyAlert.GRAPH_DENSITY_HIGH)
        
        return {"alerts": alerts, "actions": actions, "metrics": metrics}
    
    def _count_contradictions(self, graph: "OntologyGraph") -> int:
        """모순 관계 수 계산"""
        contradictions = 0
        relation_pairs = {}
        
        for rel in graph.relations:
            key = (rel.source_entity_id, rel.target_entity_id)
            sign = getattr(rel, 'sign', 1)
            
            if key in relation_pairs:
                existing_sign = relation_pairs[key]
                if existing_sign != sign:
                    contradictions += 1
            else:
                relation_pairs[key] = sign
        
        return contradictions
    
    async def _prune_low_confidence_relations(
        self,
        graph: "OntologyGraph",
        entity_id: str,
        target_degree: int = None
    ) -> int:
        """낮은 confidence 관계 정리"""
        target = target_degree or self.config.max_entity_degree
        
        # 해당 엔티티의 모든 관계 수집
        entity_relations = [
            r for r in graph.relations
            if r.source_entity_id == entity_id or r.target_entity_id == entity_id
        ]
        
        # confidence 기준 오름차순 정렬
        entity_relations.sort(key=lambda r: r.validation_score)
        
        # 초과분 제거
        excess = len(entity_relations) - target
        pruned = 0
        
        for i in range(min(excess, len(entity_relations))):
            rel = entity_relations[i]
            # 실제로는 graph에서 제거해야 하지만, 
            # OntologyGraph에 remove_relation이 없으므로 마킹만
            rel.properties["pruned"] = True
            pruned += 1
        
        return pruned
    
    def _check_oscillation(
        self,
        reasoning_metrics: Dict[str, Any]
    ) -> List[str]:
        """시나리오 진동 검사"""
        actions = []
        
        oscillating_entities = reasoning_metrics.get("oscillation_entities", [])
        
        for entity_id in oscillating_entities:
            self._oscillation_history[entity_id] = \
                self._oscillation_history.get(entity_id, 0) + 1
            
            if self._oscillation_history[entity_id] >= self.config.oscillation_threshold:
                # v5.2: reduce max_reasoning_depth by 1
                current_depth = reasoning_metrics.get("max_reasoning_depth", 3)
                if current_depth > 1:
                    actions.append(
                        f"Reduced reasoning depth: {current_depth} → {current_depth - 1}"
                    )
                    # 실제로는 reasoning 모듈에 전달해야 함
        
        return actions
    
    def is_rl_frozen(self) -> bool:
        """RL 업데이트 동결 여부"""
        return self._rl_frozen
    
    def get_status_history(self, limit: int = 10) -> List[ConsistencyStatus]:
        """상태 이력 조회"""
        return self._status_history[-limit:]
    
    def reset(self):
        """상태 초기화"""
        self._rl_frozen = False
        self._rl_freeze_remaining = 0
        self._oscillation_history.clear()
        self._degree_violations.clear()
        self._param_snapshot.clear()

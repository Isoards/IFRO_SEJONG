"""
Relation Validator - v4.2 Validation Pyramid
계획서 3.2: Validator 역할 (Rule → Small Model → LLM + RL)

v4.2 핵심:
- L0: Self-loop 방지, 동일/반대 방향 모순 체크
- L1: Small model coarse check
- L2: LLM 의미 검증
- 헤어볼 방지: Transitive Reduction 후보 판단, Degree Limit
"""
from typing import Any, List, Optional, Dict, Tuple, TYPE_CHECKING

from config.constants import RelationType, FeasibilityLevel, ValidationLayer, RelationTypeMode
from src.validators.base import BaseValidator, ValidationResult, LayerResult, LayerDecision
from src.domain.relations import Relation, OntologyGraph
from src.shared.logging import get_logger

if TYPE_CHECKING:
    from src.services.llm_service import LLMService
    from src.storage.policy_store import PolicyStore
    from src.storage.graph_store import GraphStore

logger = get_logger(__name__)


class RelationValidator(BaseValidator):
    """
    Relation 검증기 - v4.2 Validation Pyramid
    
    L0 (Rule Filter):
    - Self-loop 방지 (A→A)
    - 동일 방향 중복 체크
    - 반대 방향 모순 체크
    - Degree Limit 초과 체크
    
    L1 (Small Model):
    - "이 관계 조합이 말이 되는지" coarse check
    
    L2 (LLM + RL):
    - 의미적 타당성 검증
    - Transitive Reduction 후보 판단
    
    헤어볼 방지:
    - Transitive Reduction 후보로 판단되는 관계는 기본 reject 후보
    - "A→B, B→C가 이미 있을 때, A→C 직접 추가는 기본 reject"
    """
    
    # 유효한 관계 조합 정의
    VALID_RELATION_PAIRS = {
        ("concept", "concept"): {RelationType.IS_A, RelationType.PART_OF, RelationType.EQUIVALENT},
        ("event", "event"): {RelationType.PRECEDES, RelationType.CAUSES},
        ("entity", "entity"): {RelationType.INFLUENCES, RelationType.PROPORTIONAL, RelationType.INVERSE},
    }
    
    # 모순 관계 쌍
    OPPOSITE_RELATIONS = {
        RelationType.PROPORTIONAL: RelationType.INVERSE,
        RelationType.INVERSE: RelationType.PROPORTIONAL,
    }
    
    def __init__(
        self,
        llm_service: Optional["LLMService"] = None,
        policy_store: Optional["PolicyStore"] = None,
        graph_store: Optional["GraphStore"] = None
    ):
        super().__init__(
            llm_service=llm_service,
            policy_store=policy_store,
            validator_name="RelationValidator"
        )
        
        # v4.2: Graph Store 참조 (degree 체크용)
        self.graph_store = graph_store
        
        # 검증용 그래프 컨텍스트 (validate 호출 시 설정)
        self._current_graph: Optional[OntologyGraph] = None
    
    async def validate(self, item: Any) -> ValidationResult:
        """
        v4.2 Validation Pyramid 검증
        
        item은 (Relation, OntologyGraph) 튜플이어야 함
        """
        if isinstance(item, tuple) and len(item) == 2:
            relation, graph = item
            self._current_graph = graph
            return await super().validate(relation)
        
        return ValidationResult(
            is_valid=False,
            score=0.0,
            reasons=["Invalid input: expected (Relation, OntologyGraph) tuple"],
            layer=ValidationLayer.RULE,
            rejected_early=True
        )
    
    async def validate_relation(
        self,
        relation: Relation,
        graph: OntologyGraph,
        use_llm: bool = True
    ) -> ValidationResult:
        """
        Relation 검증 (레거시 호환)
        """
        self._current_graph = graph
        if use_llm:
            return await super().validate(relation)
        else:
            # Rule만 사용
            rule_result = await self.rule_check(relation)
            return ValidationResult(
                is_valid=rule_result.decision != LayerDecision.REJECT,
                score=rule_result.score,
                reasons=rule_result.reasons,
                details=rule_result.details,
                layer=ValidationLayer.RULE,
                rejected_early=rule_result.decision == LayerDecision.REJECT
            )
    
    # ========== L0: Rule Check ==========
    
    async def rule_check(self, item: Any) -> LayerResult:
        """
        L0: Rule-based 빠른 필터링
        
        검증 항목:
        - Self-loop 방지
        - 엔티티 존재 확인
        - 중복 관계 체크
        - 모순 관계 체크
        - Degree Limit 체크
        - Transitive Reduction 후보 판단
        """
        relation = item
        graph = self._current_graph
        
        if not graph:
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=["Graph context not provided"],
                details={"error": "no_graph_context"}
            )
        
        score = 1.0
        reasons: List[str] = []
        details: Dict[str, Any] = {}
        
        # 1. Self-loop 방지 (A→A)
        if relation.source_entity_id == relation.target_entity_id:
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=["Self-loop 관계 (A→A)"],
                details={"rule": "self_loop"}
            )
        
        # 2. 엔티티 존재 확인
        source = graph.get_entity(relation.source_entity_id)
        target = graph.get_entity(relation.target_entity_id)
        
        if not source:
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=[f"Source 엔티티 없음: {relation.source_entity_id}"],
                details={"rule": "missing_source"}
            )
        
        if not target:
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=[f"Target 엔티티 없음: {relation.target_entity_id}"],
                details={"rule": "missing_target"}
            )
        
        # 3. 라벨 존재 여부
        if not relation.label or len(relation.label.strip()) < 2:
            score -= 0.2
            reasons.append("관계 라벨 누락 또는 너무 짧음")
        
        # 4. 중복 관계 체크
        if self._is_duplicate(relation, graph):
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=["중복 관계"],
                details={"rule": "duplicate"}
            )
        
        # 5. 모순 관계 체크 (반대 방향)
        contradictions = self._find_contradictions(relation, graph)
        if contradictions:
            return LayerResult(
                score=0.0,
                decision=LayerDecision.REJECT,
                reasons=[f"모순 관계 감지: {contradictions}"],
                details={"rule": "contradiction", "contradictions": contradictions}
            )
        
        # 6. 순환 관계 감지 (계층 관계에만 적용)
        if relation.relation_type in {RelationType.IS_A, RelationType.PART_OF}:
            if self._would_create_cycle(relation, graph):
                score -= 0.4
                reasons.append("순환 관계 발생 (계층 관계)")
        
        # 7. v4.2: Degree Limit 체크
        out_degree = self._get_out_degree(relation.source_entity_id, graph)
        in_degree = self._get_in_degree(relation.target_entity_id, graph)
        
        if out_degree >= self.settings.max_entity_out_degree:
            score -= 0.3
            reasons.append(f"Source out_degree 초과: {out_degree} >= {self.settings.max_entity_out_degree}")
            details["needs_admin_review"] = True
        
        if in_degree >= self.settings.max_entity_in_degree:
            score -= 0.3
            reasons.append(f"Target in_degree 초과: {in_degree} >= {self.settings.max_entity_in_degree}")
            details["needs_admin_review"] = True
        
        # 8. v4.2: Transitive Reduction 후보 판단
        # "A→B, B→C가 이미 있을 때, A→C 직접 추가는 reject 후보"
        is_transitive = self._is_transitive_relation(relation, graph)
        if is_transitive:
            score -= 0.3
            reasons.append("Transitive Reduction 대상 (간접 경로 존재)")
            details["transitive_redundant"] = True
            details["suggested_type"] = RelationTypeMode.INDIRECT.value
        
        # 9. 근거 Fragment 존재 여부
        if not relation.source_fragment_ids:
            score -= 0.1
            reasons.append("근거 Fragment 없음")
        
        # 결정
        score = max(0.0, score)
        details["relation_type"] = relation.relation_type.value
        details["source_name"] = source.canonical_name
        details["target_name"] = target.canonical_name
        
        if score < self.settings.rule_reject_threshold:
            return LayerResult(
                score=score,
                decision=LayerDecision.REJECT,
                reasons=reasons,
                details=details
            )
        
        return LayerResult(
            score=score,
            decision=LayerDecision.PASS,
            reasons=reasons,
            details=details
        )
    
    # ========== L1: Small Model Check ==========
    
    async def _call_small_model(self, item: Any) -> LayerResult:
        """
        L1: Small Model 검증
        
        "이 관계 조합이 말이 되는지" coarse check
        """
        relation = item
        graph = self._current_graph
        
        # Small Model endpoint가 없으면 pass-through
        if not self.settings.small_model_endpoint:
            return LayerResult(
                score=0.7,
                decision=LayerDecision.PASS,
                reasons=[],
                details={"small_model": "pass_through"}
            )
        
        # TODO: Small Model API 호출 구현
        # 현재는 휴리스틱으로 대체
        score = 0.7
        reasons = []
        
        # 휴리스틱: 엔티티 타입 조합 체크
        if graph:
            source = graph.get_entity(relation.source_entity_id)
            target = graph.get_entity(relation.target_entity_id)
            
            if source and target:
                type_pair = (source.entity_type, target.entity_type)
                valid_relations = self.VALID_RELATION_PAIRS.get(type_pair)
                
                if valid_relations and relation.relation_type not in valid_relations:
                    score -= 0.2
                    reasons.append(f"엔티티 타입 조합에 부적합한 관계: {type_pair}")
        
        if score < self.settings.small_model_reject_threshold:
            return LayerResult(
                score=score,
                decision=LayerDecision.REJECT,
                reasons=reasons,
                details={"small_model": "heuristic_reject"}
            )
        
        return LayerResult(
            score=score,
            decision=LayerDecision.PASS,
            reasons=reasons,
            details={"small_model": "heuristic_pass"}
        )
    
    # ========== L2: LLM Check ==========
    
    def _build_llm_prompt(self, item: Any) -> str:
        """L2: LLM 검증 프롬프트 생성"""
        relation = item
        graph = self._current_graph
        
        source = graph.get_entity(relation.source_entity_id) if graph else None
        target = graph.get_entity(relation.target_entity_id) if graph else None
        
        source_name = source.canonical_name if source else "Unknown"
        target_name = target.canonical_name if target else "Unknown"
        
        return f"""다음 온톨로지 관계의 의미적 타당성을 평가하세요.

관계 정보:
- Source: {source_name}
- Target: {target_name}
- 관계 유형: {relation.relation_type.value}
- 관계 라벨: {relation.label}
- 방향: {relation.direction or '없음'}
- 크기: {relation.magnitude or '없음'}

평가 기준:
1. Source와 Target 사이의 관계가 의미적으로 타당한가?
2. 관계 유형이 적절한가?
3. 이 관계가 실제 세계에서 성립하는가?
4. 관계 라벨이 관계 유형과 일치하는가?

JSON 형식으로 응답하세요:
{{
    "score": 0.0-1.0,
    "is_valid": true/false,
    "semantic_validity": "high/medium/low",
    "issues": ["발견된 문제점 목록"],
    "reasoning": "평가 근거"
}}
"""
    
    def _history_score(self, item: Any) -> float:
        """관계 유형별 히스토리 점수"""
        relation = item
        
        similar_feedbacks = [
            f for f in self._feedback_history
            if f.get("relation_type") == relation.relation_type.value
        ]
        
        if not similar_feedbacks:
            return 0.5
        
        approved = sum(1 for f in similar_feedbacks if f.get("approved", False))
        return approved / len(similar_feedbacks)
    
    # ========== Hairball Prevention Helpers ==========
    
    def _is_duplicate(
        self,
        relation: Relation,
        graph: OntologyGraph
    ) -> bool:
        """중복 관계 체크"""
        for existing in graph.relations:
            if (existing.source_entity_id == relation.source_entity_id and
                existing.target_entity_id == relation.target_entity_id and
                existing.relation_type == relation.relation_type and
                existing.id != relation.id):  # 자기 자신 제외
                return True
        return False
    
    def _find_contradictions(
        self,
        relation: Relation,
        graph: OntologyGraph
    ) -> List[str]:
        """모순 관계 감지"""
        contradictions = []
        
        if relation.relation_type in self.OPPOSITE_RELATIONS:
            opposite = self.OPPOSITE_RELATIONS[relation.relation_type]
            
            for existing in graph.relations:
                # 같은 방향 모순
                if (existing.source_entity_id == relation.source_entity_id and
                    existing.target_entity_id == relation.target_entity_id and
                    existing.relation_type == opposite):
                    contradictions.append(
                        f"동일 방향 모순: {relation.relation_type.value} vs {opposite.value}"
                    )
                
                # 반대 방향 모순 (A→B와 B→A가 같은 관계일 때)
                if (existing.source_entity_id == relation.target_entity_id and
                    existing.target_entity_id == relation.source_entity_id and
                    existing.relation_type == relation.relation_type):
                    # 대칭 관계가 아닌 경우에만 모순
                    if relation.relation_type not in {RelationType.EQUIVALENT}:
                        contradictions.append(
                            f"반대 방향 동일 관계: {relation.relation_type.value}"
                        )
        
        return contradictions
    
    def _would_create_cycle(
        self,
        relation: Relation,
        graph: OntologyGraph
    ) -> bool:
        """순환 관계 발생 여부 체크"""
        path = graph.find_path(relation.target_entity_id, relation.source_entity_id)
        return path is not None
    
    def _get_out_degree(self, entity_id: str, graph: OntologyGraph) -> int:
        """엔티티의 출력 차수 계산"""
        return sum(1 for r in graph.relations if r.source_entity_id == entity_id)
    
    def _get_in_degree(self, entity_id: str, graph: OntologyGraph) -> int:
        """엔티티의 입력 차수 계산"""
        return sum(1 for r in graph.relations if r.target_entity_id == entity_id)
    
    def _is_transitive_relation(
        self,
        relation: Relation,
        graph: OntologyGraph
    ) -> bool:
        """
        v4.2 Transitive Reduction 후보 판단
        
        "A→B, B→C가 이미 있을 때, A→C 직접 추가는 redundant"
        returns True if:
          A→?→...→C 경로가 이미 존재 (직접 경로 제외)
        """
        source_id = relation.source_entity_id
        target_id = relation.target_entity_id
        
        # 간접 경로 존재 확인 (길이 2 이상)
        # BFS로 source에서 target까지 가는 경로 탐색
        visited = {source_id}
        queue = [(source_id, 0)]  # (entity_id, depth)
        
        while queue:
            current_id, depth = queue.pop(0)
            
            for existing in graph.relations:
                if existing.source_entity_id == current_id:
                    next_id = existing.target_entity_id
                    
                    # target에 도달했고, 간접 경로 (depth >= 1)
                    if next_id == target_id and depth >= 1:
                        return True
                    
                    if next_id not in visited and depth < 3:  # 깊이 제한
                        visited.add(next_id)
                        queue.append((next_id, depth + 1))
        
        return False
    
    # ========== v4.2 Transitive Reduction ==========
    
    def check_transitive_reduction_candidates(
        self,
        graph: OntologyGraph
    ) -> List[Relation]:
        """
        Transitive Reduction이 필요한 관계 목록 반환
        
        A→B, B→C, A→C가 있을 때 A→C 반환
        """
        candidates = []
        
        for relation in graph.relations:
            if self._is_transitive_relation(relation, graph):
                candidates.append(relation)
        
        return candidates
    
    # ========== Feedback ==========
    
    async def record_relation_feedback(
        self,
        relation_id: str,
        relation_type: RelationType,
        approved: bool,
        reason: Optional[str] = None
    ):
        """Relation 피드백 기록 (RL 학습용)"""
        await self.record_feedback(
            item_id=relation_id,
            approved=approved,
            reason=reason
        )
        
        # Relation 유형별 추적
        self._feedback_history[-1]["relation_type"] = relation_type.value


# ========== Direct/Indirect Relation Helper ==========

def determine_relation_type_mode(
    relation: Relation,
    graph: OntologyGraph
) -> RelationTypeMode:
    """
    관계가 Direct인지 Indirect인지 결정
    
    - 원문/Fragment에서 직접 추출된 관계 → DIRECT
    - 추론되었거나 Transitive 관계 → INDIRECT
    """
    validator = RelationValidator()
    validator._current_graph = graph
    
    # Transitive 관계면 INDIRECT
    if validator._is_transitive_relation(relation, graph):
        return RelationTypeMode.INDIRECT
    
    # 기본은 DIRECT
    return RelationTypeMode.DIRECT

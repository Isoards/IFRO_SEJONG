"""
관계 및 온톨로지 그래프 정의
계획서 3: Ontology Layer
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from uuid import uuid4

from pydantic import BaseModel, Field
import networkx as nx

from config.constants import RelationType, ValidationStatus


class Relation(BaseModel):
    """
    v5.2 엔티티 간 관계
    Relation은 오직 직접 연결만 담당 (간접관계 저장 금지)
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    # 관계 구조
    source_entity_id: str = Field(description="출발 엔티티 ID")
    target_entity_id: str = Field(description="도착 엔티티 ID")
    relation_type: RelationType = Field(description="관계 유형")
    
    # v5.2: Sign (+1: 정비례, -1: 반비례)
    sign: int = Field(default=1, ge=-1, le=1, description="관계 방향성 (+1/-1)")
    
    # 관계 속성
    label: str = Field(description="관계 레이블 (자연어)")
    weight: float = Field(default=1.0, description="관계 강도")
    bidirectional: bool = Field(default=False, description="양방향 여부")
    
    # MECHANISM 관련 (레거시 호환)
    direction: Optional[str] = Field(default=None, description="영향 방향")
    magnitude: Optional[str] = Field(default=None, description="영향 크기")
    
    # 출처 Fragment
    source_fragment_ids: List[str] = Field(default_factory=list, description="근거 Fragment ID들")
    
    # v5.2: 증거 confidence 목록 (Bayesian 결합용)
    evidence_confidences: List[float] = Field(default_factory=list, description="각 증거의 confidence")
    
    # 검증 정보
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    validation_score: float = Field(default=0.0)
    
    # 메타데이터
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @staticmethod
    def bayesian_combine(confidences: List[float]) -> float:
        """
        v5.2 Bayesian-like 증거 결합
        공식: combined = 1 - Π(1 - c_i)
        """
        if not confidences:
            return 0.0
        product = 1.0
        for c in confidences:
            product *= (1.0 - c)
        return 1.0 - product
    
    def calculate_confidence(self, llm_semantic_score: float = 0.5) -> float:
        """
        v5.2 Confidence 계산
        공식: confidence = 0.8*combined + 0.2*L_s
        """
        combined = self.bayesian_combine(self.evidence_confidences)
        return 0.8 * combined + 0.2 * llm_semantic_score
    
    def update_from_direction(self):
        """direction 필드에서 sign 추출 (레거시 호환)"""
        if self.direction in {'inverse', '-', 'negative', 'decreases'}:
            self.sign = -1
        elif self.direction in {'proportional', '+', 'positive', 'increases'}:
            self.sign = 1
        else:
            self.sign = 1  # 기본값


class OntologyGraph:
    """
    온톨로지 그래프 - NetworkX 기반
    계획서 3.3: 안정적으로 정제된 그래프
    """
    
    def __init__(self):
        self._graph = nx.DiGraph()
        self._entities: Dict[str, Any] = {}  # entity_id -> Entity
        self._relations: Dict[str, Relation] = {}  # relation_id -> Relation
    
    def add_entity(self, entity) -> None:
        """엔티티 추가"""
        self._entities[entity.id] = entity
        self._graph.add_node(
            entity.id,
            name=entity.canonical_name,
            type=entity.entity_type,
            tags=entity.domain_tags,
        )
    
    def add_relation(self, relation: Relation) -> None:
        """관계 추가"""
        if relation.source_entity_id not in self._entities:
            raise ValueError(f"Source entity not found: {relation.source_entity_id}")
        if relation.target_entity_id not in self._entities:
            raise ValueError(f"Target entity not found: {relation.target_entity_id}")
        
        self._relations[relation.id] = relation
        self._graph.add_edge(
            relation.source_entity_id,
            relation.target_entity_id,
            relation_id=relation.id,
            type=relation.relation_type.value,
            label=relation.label,
            weight=relation.weight,
        )
        
        if relation.bidirectional:
            self._graph.add_edge(
                relation.target_entity_id,
                relation.source_entity_id,
                relation_id=relation.id,
                type=relation.relation_type.value,
                label=relation.label,
                weight=relation.weight,
            )
    
    def get_entity(self, entity_id: str):
        """엔티티 조회"""
        return self._entities.get(entity_id)
    
    def get_entity_by_name(self, name: str):
        """이름으로 엔티티 조회 (별칭 포함)"""
        for entity in self._entities.values():
            if entity.canonical_name == name or name in entity.aliases:
                return entity
        return None
    
    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """관계 조회"""
        return self._relations.get(relation_id)
    
    def get_subgraph(
        self,
        entity_ids: List[str],
        depth: int = 2
    ) -> "OntologyGraph":
        """
        엔티티들을 중심으로 서브그래프 추출
        계획서 4.2: 관련 엔티티 서브그래프 추출
        """
        # BFS로 연결된 노드 탐색
        all_nodes: Set[str] = set()
        for entity_id in entity_ids:
            if entity_id in self._graph:
                # 지정된 depth까지 이웃 노드 탐색
                for d in range(depth + 1):
                    neighbors = nx.single_source_shortest_path_length(
                        self._graph, entity_id, cutoff=d
                    )
                    all_nodes.update(neighbors.keys())
        
        # 서브그래프 생성
        subgraph = OntologyGraph()
        for node_id in all_nodes:
            if node_id in self._entities:
                subgraph.add_entity(self._entities[node_id])
        
        # 관련 관계 추가
        for relation in self._relations.values():
            if (relation.source_entity_id in all_nodes and 
                relation.target_entity_id in all_nodes):
                subgraph.add_relation(relation)
        
        return subgraph
    
    def get_related_entities(
        self,
        entity_id: str,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both"  # "outgoing", "incoming", "both"
    ) -> List[tuple]:
        """관련 엔티티 조회"""
        results = []
        
        if direction in ("outgoing", "both"):
            for _, target, data in self._graph.out_edges(entity_id, data=True):
                rel_type = RelationType(data["type"])
                if relation_types is None or rel_type in relation_types:
                    results.append((
                        self._entities.get(target),
                        self._relations.get(data["relation_id"]),
                        "outgoing"
                    ))
        
        if direction in ("incoming", "both"):
            for source, _, data in self._graph.in_edges(entity_id, data=True):
                rel_type = RelationType(data["type"])
                if relation_types is None or rel_type in relation_types:
                    results.append((
                        self._entities.get(source),
                        self._relations.get(data["relation_id"]),
                        "incoming"
                    ))
        
        return results
    
    def find_path(
        self,
        source_entity_id: str,
        target_entity_id: str
    ) -> Optional[List[str]]:
        """두 엔티티 간 경로 탐색"""
        try:
            return nx.shortest_path(self._graph, source_entity_id, target_entity_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def get_causal_chain(
        self,
        entity_id: str,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        인과 관계 체인 추출
        CAUSES, INFLUENCES 관계를 따라가며 인과 체인 구성
        """
        causal_types = {RelationType.CAUSES, RelationType.INFLUENCES}
        chain = []
        visited = set()
        
        def dfs(current_id: str, depth: int, path: List):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            for _, target, data in self._graph.out_edges(current_id, data=True):
                rel_type = RelationType(data["type"])
                if rel_type in causal_types:
                    new_path = path + [{
                        "from": current_id,
                        "to": target,
                        "relation": data["label"],
                        "type": rel_type.value,
                    }]
                    chain.append(new_path)
                    dfs(target, depth + 1, new_path)
        
        dfs(entity_id, 0, [])
        return chain
    
    def to_dict(self) -> Dict[str, Any]:
        """그래프를 직렬화 가능한 형태로 변환"""
        return {
            "entities": [e.model_dump() for e in self._entities.values()],
            "relations": [r.model_dump() for r in self._relations.values()],
            "node_count": self._graph.number_of_nodes(),
            "edge_count": self._graph.number_of_edges(),
        }
    
    @property
    def entities(self) -> List:
        return list(self._entities.values())
    
    @property
    def relations(self) -> List[Relation]:
        return list(self._relations.values())
    
    @property
    def node_count(self) -> int:
        return self._graph.number_of_nodes()
    
    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()

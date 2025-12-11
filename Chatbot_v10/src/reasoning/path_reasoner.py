"""
v5.2 Path Reasoner
경로 기반 추론 엔진

핵심 기능:
- 두 엔티티 간 경로 탐색
- depth ≤ 3 제한
- node revisit 금지
- path_conf = Π(ci) * 0.92^(k-1)
"""
from typing import List, Optional, Set, Tuple, Any
from collections import deque

from src.reasoning.base import (
    BaseReasoner, ReasoningResult, ReasoningPath,
    ReasoningResultType
)
from src.domain.relations import OntologyGraph, Relation
from src.shared.logging import get_logger

logger = get_logger(__name__)


class PathReasoner(BaseReasoner):
    """
    v5.2 Path Reasoner
    
    탐색 규칙:
    - depth ≤ 3
    - node revisit = prohibited
    - 모든 경로 수집 후 confidence 기준 정렬
    """
    
    def __init__(self, graph: OntologyGraph):
        super().__init__(graph)
    
    async def reason(
        self,
        source_entity_id: str,
        target_entity_id: str,
        max_paths: int = 5
    ) -> ReasoningResult:
        """
        두 엔티티 간 모든 경로 탐색
        
        Args:
            source_entity_id: 시작 엔티티
            target_entity_id: 목표 엔티티
            max_paths: 반환할 최대 경로 수
        """
        self._clear_trace()
        self._add_trace(f"PathReasoner: {source_entity_id} → {target_entity_id}")
        
        if not self.graph:
            return ReasoningResult(
                result_type=ReasoningResultType.PATH,
                success=False,
                confidence=0.0,
                sign=None,
                explanation="Graph not provided"
            )
        
        # 엔티티 존재 확인
        source = self.graph.get_entity(source_entity_id)
        target = self.graph.get_entity(target_entity_id)
        
        if not source or not target:
            return ReasoningResult(
                result_type=ReasoningResultType.PATH,
                success=False,
                confidence=0.0,
                sign=None,
                explanation="Source or target entity not found"
            )
        
        # 모든 경로 탐색
        all_paths = self._find_all_paths(
            source_entity_id,
            target_entity_id,
            max_depth=self.MAX_DEPTH
        )
        
        if not all_paths:
            self._add_trace("No paths found")
            return ReasoningResult(
                result_type=ReasoningResultType.PATH,
                success=False,
                confidence=0.0,
                sign=None,
                explanation=f"No path found between {source.canonical_name} and {target.canonical_name}",
                trace=self._trace.copy()
            )
        
        # 경로 confidence 계산 및 정렬
        reasoning_paths = []
        for path_nodes, path_edges in all_paths:
            path = self._create_reasoning_path(path_nodes, path_edges)
            if path.is_valid:
                reasoning_paths.append(path)
        
        # confidence 기준 정렬
        reasoning_paths.sort(key=lambda p: p.path_confidence, reverse=True)
        reasoning_paths = reasoning_paths[:max_paths]
        
        # 최고 confidence 경로 기준
        best_path = reasoning_paths[0] if reasoning_paths else None
        
        self._add_trace(f"Found {len(reasoning_paths)} valid paths")
        
        return ReasoningResult(
            result_type=ReasoningResultType.PATH,
            success=True,
            confidence=best_path.path_confidence if best_path else 0.0,
            sign=best_path.path_sign if best_path else None,
            paths=reasoning_paths,
            explanation=f"Found {len(reasoning_paths)} paths, best confidence: {best_path.path_confidence:.3f}" if best_path else "No valid paths",
            trace=self._trace.copy(),
            details={
                "source": source.canonical_name,
                "target": target.canonical_name,
                "path_count": len(reasoning_paths)
            }
        )
    
    def _find_all_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int
    ) -> List[Tuple[List[str], List[Relation]]]:
        """
        BFS/DFS 기반 모든 경로 탐색
        
        Returns:
            List of (node_ids, edge_relations)
        """
        all_paths = []
        
        # DFS with path tracking
        stack = [(source_id, [source_id], [])]  # (current, path_nodes, path_edges)
        
        while stack:
            current, path_nodes, path_edges = stack.pop()
            
            # 목표 도달
            if current == target_id:
                all_paths.append((path_nodes.copy(), path_edges.copy()))
                continue
            
            # 깊이 제한
            if len(path_nodes) > max_depth:
                continue
            
            # 이웃 탐색
            for relation in self.graph.relations:
                next_node = None
                
                if relation.source_entity_id == current:
                    next_node = relation.target_entity_id
                
                # v5.2: 노드 재방문 금지
                if next_node and next_node not in path_nodes:
                    stack.append((
                        next_node,
                        path_nodes + [next_node],
                        path_edges + [relation]
                    ))
        
        return all_paths
    
    def _create_reasoning_path(
        self,
        node_ids: List[str],
        relations: List[Relation]
    ) -> ReasoningPath:
        """ReasoningPath 객체 생성"""
        edges = []
        confidences = []
        signs = []
        
        for rel in relations:
            # v5.2: sign 추출 (relation에 sign 필드가 있으면 사용)
            sign = getattr(rel, 'sign', None)
            if sign is None:
                # direction에서 추정
                direction = getattr(rel, 'direction', None)
                if direction == 'inverse' or direction == '-':
                    sign = -1
                else:
                    sign = 1
            
            # confidence
            conf = rel.validation_score if rel.validation_score > 0 else 0.5
            
            edges.append((
                rel.source_entity_id,
                rel.target_entity_id,
                conf,
                sign
            ))
            confidences.append(conf)
            signs.append(sign)
        
        # v5.2 공식 적용
        path_conf = self._calculate_path_confidence(confidences, len(node_ids))
        path_sign = self._propagate_sign(signs)
        
        self._add_trace(f"Path: {len(node_ids)} nodes, conf={path_conf:.3f}, sign={path_sign}")
        
        return ReasoningPath(
            nodes=node_ids,
            edges=edges,
            path_confidence=path_conf,
            path_sign=path_sign,
            length=len(node_ids)
        )
    
    async def find_shortest_path(
        self,
        source_id: str,
        target_id: str
    ) -> Optional[ReasoningPath]:
        """최단 경로 탐색 (BFS)"""
        if not self.graph:
            return None
        
        visited = {source_id}
        queue = deque([(source_id, [source_id], [])])
        
        while queue:
            current, path_nodes, path_edges = queue.popleft()
            
            if current == target_id:
                return self._create_reasoning_path(path_nodes, path_edges)
            
            if len(path_nodes) > self.MAX_DEPTH:
                continue
            
            for relation in self.graph.relations:
                if relation.source_entity_id == current:
                    next_node = relation.target_entity_id
                    if next_node not in visited:
                        visited.add(next_node)
                        queue.append((
                            next_node,
                            path_nodes + [next_node],
                            path_edges + [relation]
                        ))
        
        return None

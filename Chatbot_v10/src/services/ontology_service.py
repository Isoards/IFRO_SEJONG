"""
Ontology 서비스
계획서 3: Ontology Layer

벡터 검색 및 Storage 통합
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from config.constants import (
    RelationType, ValidationStatus, FragmentType,
    RelationTypeMode, ValidationLayer
)
from src.domain.entities import Entity
from src.domain.fragments import Fragment
from src.domain.relations import Relation, OntologyGraph
from src.validators.relation_validator import RelationValidator
from src.shared.logging import get_logger, log_error
from src.shared.types import Result

if TYPE_CHECKING:
    from src.services.llm_service import LLMService
    from src.storage.graph_store import GraphStore
    from src.storage.vector_store import VectorStore
    from src.storage.domain_dictionary import DomainDictionary

logger = get_logger(__name__)


class OntologyService:
    """
    Ontology 관리 서비스
    
    계획서 3.1: Generator 역할 (LLM) - 관계 후보 생성
    계획서 3.2: Validator 역할 (Rule + LLM + RL) - 관계 검증
    계획서 3.3: 안정적으로 정제된 그래프 관리
    
    추가 기능:
    - 벡터 기반 의미적 검색
    - 그래프 영속화
    
    원칙 4: 단일 책임 - Ontology 그래프 관리만 담당
    원칙 1: One Source of Truth - 단일 그래프 저장소
    """
    
    def __init__(
        self,
        validator: RelationValidator,
        llm_service: Optional["LLMService"] = None,
        graph_store: Optional["GraphStore"] = None,
        vector_store: Optional["VectorStore"] = None,
        domain_dictionary: Optional["DomainDictionary"] = None
    ):
        self.validator = validator
        self.llm_service = llm_service
        self.graph_store = graph_store
        self.vector_store = vector_store
        self.graph = OntologyGraph()  # One Source of Truth
        
        # v4.2: Domain Dictionary
        self.domain_dictionary = domain_dictionary
        
        # 벡터 저장소 컬렉션 이름
        self.ENTITY_COLLECTION = "entities"
        self.FRAGMENT_COLLECTION = "fragments"
        
        # v4.2: Settings 참조
        from config.settings import get_settings
        self.settings = get_settings()
    
    async def initialize(self) -> None:
        """서비스 초기화 - 저장소에서 그래프 로드"""
        if self.graph_store:
            try:
                await self.graph_store.initialize()
                self.graph = await self.graph_store.load_graph()
                logger.info(
                    "ontology_loaded_from_store",
                    entity_count=len(self.graph.entities),
                    relation_count=len(self.graph.relations)
                )
            except Exception as e:
                log_error(logger, e, {"operation": "initialize_graph_store"})
        
        if self.vector_store:
            try:
                await self.vector_store.initialize()
                logger.info("vector_store_initialized")
            except Exception as e:
                log_error(logger, e, {"operation": "initialize_vector_store"})
    
    async def save(self) -> Result[bool]:
        """현재 그래프 상태 저장"""
        if not self.graph_store:
            return Result.fail(error="GraphStore가 설정되지 않음", error_code="NO_STORE")
        
        try:
            await self.graph_store.save(self.graph)
            return Result.ok(True)
        except Exception as e:
            log_error(logger, e, {"operation": "save_graph"})
            return Result.fail(error=str(e), error_code="SAVE_FAILED")
    
    async def add_entity(
        self,
        entity: Entity,
        persist: bool = True,
        generate_embedding: bool = True
    ) -> Result[Entity]:
        """
        엔티티 추가
        
        Args:
            entity: 추가할 엔티티
            persist: 영속화 여부
            generate_embedding: 임베딩 생성 여부
        """
        try:
            self.graph.add_entity(entity)
            
            # 영속화
            if persist and self.graph_store:
                await self.graph_store.save_entity(entity)
            
            # 임베딩 생성 및 저장
            if generate_embedding and self.llm_service and self.vector_store:
                await self._add_entity_embedding(entity)
            
            logger.info("entity_added", entity_id=entity.id, name=entity.canonical_name)
            return Result.ok(entity)
            
        except Exception as e:
            log_error(logger, e, {"entity_id": entity.id})
            return Result.fail(error=str(e), error_code="ENTITY_ADD_FAILED")
    
    async def _add_entity_embedding(self, entity: Entity) -> None:
        """엔티티 임베딩 생성 및 저장"""
        if not self.llm_service or not self.vector_store:
            return
        
        try:
            # 임베딩용 텍스트 생성
            embed_text = f"{entity.canonical_name}"
            if entity.description:
                embed_text += f". {entity.description}"
            if entity.aliases:
                embed_text += f". Also known as: {', '.join(entity.aliases)}"
            
            # 임베딩 생성
            embedding = await self.llm_service.embed(embed_text)
            
            # 메타데이터
            metadata = {
                "name": entity.canonical_name,
                "type": entity.entity_type,
                "relation_count": entity.relation_count,
            }
            
            # 벡터 저장소에 추가
            await self.vector_store.add_embedding(
                collection_name=self.ENTITY_COLLECTION,
                item_id=entity.id,
                embedding=embedding,
                metadata=metadata,
                document=embed_text
            )
            
        except Exception as e:
            log_error(logger, e, {"entity_id": entity.id, "operation": "add_embedding"})
    
    async def search_entities_by_similarity(
        self,
        query: str,
        top_k: int = 10,
        filter_type: Optional[str] = None
    ) -> List[tuple[Entity, float]]:
        """
        의미적 유사도 기반 엔티티 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            filter_type: 엔티티 유형 필터
        
        Returns:
            List[(Entity, similarity_score)]
        """
        if not self.llm_service or not self.vector_store:
            # 벡터 검색 불가능 시 이름 기반 검색으로 폴백
            return self._fallback_search(query, top_k)
        
        try:
            # 쿼리 임베딩 생성
            query_embedding = await self.llm_service.embed(query)
            
            # 메타데이터 필터
            filter_metadata = {"type": filter_type} if filter_type else None
            
            # 유사도 검색
            results = await self.vector_store.search_similar(
                collection_name=self.ENTITY_COLLECTION,
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            # 엔티티 객체로 변환
            entities_with_scores = []
            for item_id, score, metadata in results:
                entity = self.graph.get_entity(item_id)
                if entity:
                    entities_with_scores.append((entity, score))
            
            logger.debug(
                "semantic_search_completed",
                query=query,
                results_count=len(entities_with_scores)
            )
            
            return entities_with_scores
            
        except Exception as e:
            log_error(logger, e, {"query": query})
            return self._fallback_search(query, top_k)
    
    def _fallback_search(
        self,
        query: str,
        top_k: int
    ) -> List[tuple[Entity, float]]:
        """이름 기반 폴백 검색"""
        query_lower = query.lower()
        results = []
        
        for entity in self.graph.entities:
            score = 0.0
            
            # 이름 매칭
            if query_lower in entity.canonical_name.lower():
                score = 0.8
            elif any(query_lower in alias.lower() for alias in entity.aliases):
                score = 0.6
            elif entity.description and query_lower in entity.description.lower():
                score = 0.4
            
            if score > 0:
                results.append((entity, score))
        
        # 점수 기준 정렬
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    async def build_relations_from_fragments(
        self,
        fragments: List[Fragment],
        entities: Dict[str, Entity]
    ) -> Result[List[Relation]]:
        """
        Fragment들로부터 Relation 구축
        
        Args:
            fragments: 검증된 Fragment 리스트
            entities: 정규화된 Entity 딕셔너리 (name -> Entity)
        
        Returns:
            Result[List[Relation]]
        """
        created_relations: List[Relation] = []
        
        try:
            for fragment in fragments:
                # 검증되지 않은 Fragment 스킵
                if fragment.validation_status != ValidationStatus.APPROVED:
                    continue
                
                # Subject/Object Entity 찾기
                subject_entity = self._find_entity_by_name(fragment.subject, entities)
                object_entity = self._find_entity_by_name(fragment.object, entities)
                
                if not subject_entity or not object_entity:
                    logger.debug(
                        "relation_skipped_missing_entity",
                        subject=fragment.subject,
                        object=fragment.object
                    )
                    continue
                
                # Fragment 유형에 따른 Relation 생성
                relation = self._create_relation_from_fragment(
                    fragment, subject_entity, object_entity
                )
                
                # Validator로 검증
                validation_result = await self.validator.validate_relation(
                    relation, self.graph
                )
                
                if validation_result.is_valid:
                    relation.validation_status = ValidationStatus.APPROVED
                    relation.validation_score = validation_result.score
                    
                    # 그래프에 추가
                    self.graph.add_relation(relation)
                    created_relations.append(relation)
                    
                    # 영속화
                    if self.graph_store:
                        await self.graph_store.save_relation(relation)
                    
                    # 엔티티 통계 업데이트
                    subject_entity.relation_count += 1
                    object_entity.relation_count += 1
                else:
                    relation.validation_status = ValidationStatus.REJECTED
                    logger.debug(
                        "relation_rejected",
                        relation_id=relation.id,
                        reasons=validation_result.reasons
                    )
            
            logger.info(
                "relations_built",
                fragment_count=len(fragments),
                relation_count=len(created_relations)
            )
            
            return Result.ok(created_relations)
            
        except Exception as e:
            log_error(logger, e, {"fragment_count": len(fragments)})
            return Result.fail(error=str(e), error_code="RELATION_BUILD_FAILED")
    
    def _find_entity_by_name(
        self,
        name: str,
        entities: Dict[str, Entity]
    ) -> Optional[Entity]:
        """이름으로 Entity 찾기 (대소문자 무시)"""
        name_lower = name.lower()
        
        # 정확한 매칭
        if name_lower in entities:
            return entities[name_lower]
        
        # 별칭 검색
        for entity in entities.values():
            if entity.canonical_name.lower() == name_lower:
                return entity
            if any(alias.lower() == name_lower for alias in entity.aliases):
                return entity
        
        return None
    
    def _create_relation_from_fragment(
        self,
        fragment: Fragment,
        subject_entity: Entity,
        object_entity: Entity
    ) -> Relation:
        """Fragment에서 Relation 생성"""
        # Fragment 유형에 따른 RelationType 매핑
        type_mapping = {
            FragmentType.FACT: RelationType.IS_A,
            FragmentType.MECHANISM: RelationType.INFLUENCES,
            FragmentType.CONDITION: RelationType.DEPENDS_ON,
            FragmentType.OUTCOME: RelationType.CAUSES,
        }
        
        relation_type = type_mapping.get(fragment.fragment_type, RelationType.IS_A)
        
        # Mechanism의 경우 비례/반비례 구분
        if fragment.fragment_type == FragmentType.MECHANISM:
            if fragment.direction == "inverse":
                relation_type = RelationType.INVERSE
            else:
                relation_type = RelationType.PROPORTIONAL
        
        return Relation(
            source_entity_id=subject_entity.id,
            target_entity_id=object_entity.id,
            relation_type=relation_type,
            label=fragment.predicate,
            direction=fragment.direction,
            magnitude=fragment.magnitude,
            source_fragment_ids=[fragment.id],
            validation_status=ValidationStatus.PENDING,
        )
    
    async def add_relation(self, relation: Relation) -> Result[Relation]:
        """
        Relation 추가 (레거시 호환)
        v4.2: add_direct_relation으로 내부 위임
        """
        return await self.add_direct_relation(relation)
    
    async def add_direct_relation(
        self,
        relation: Relation,
        force: bool = False
    ) -> Result[Relation]:
        """
        v4.2: Direct Relation 추가
        
        헤어볼 방지:
        - Validator 호출
        - Degree Limit 체크
        - Transitive Reduction 후보 판단
        - relation_type="direct"로 저장
        
        Args:
            relation: 추가할 Direct Relation
            force: 헤어볼 찍크 무시 (admin 용)
        """
        try:
            # v4.2: Validation Pyramid 적용
            validation_result = await self.validator.validate_relation(
                relation, self.graph
            )
            
            # v4.2: relation_type_mode 설정
            relation.relation_type_mode = RelationTypeMode.DIRECT.value
            relation.validation_layer = validation_result.layer.value if hasattr(validation_result, 'layer') else None
            
            relation.validation_status = (
                ValidationStatus.APPROVED if validation_result.is_valid
                else ValidationStatus.NEEDS_REVIEW
            )
            relation.validation_score = validation_result.score
            
            # v4.2: 헤어볼 방지 체크
            if not force and not validation_result.is_valid:
                # Transitive Reduction 후보인지 확인
                details = validation_result.details or {}
                if details.get("transitive_redundant"):
                    logger.info(
                        "relation_marked_as_indirect",
                        relation_id=relation.id,
                        reason="transitive_redundant"
                    )
                    # Indirect로 변경하여 저장 (선택적)
                    relation.relation_type_mode = RelationTypeMode.INDIRECT.value
                
                # Degree Limit 초과 시 admin review 필요
                if details.get("needs_admin_review"):
                    relation.validation_status = ValidationStatus.NEEDS_REVIEW
                    logger.warning(
                        "relation_needs_admin_review",
                        relation_id=relation.id,
                        reason="degree_limit_exceeded"
                    )
            
            if validation_result.is_valid or force:
                self.graph.add_relation(relation)
                
                # 영속화
                if self.graph_store:
                    await self.graph_store.save_relation(relation)
                
                logger.info(
                    "direct_relation_added",
                    relation_id=relation.id,
                    type_mode=relation.relation_type_mode
                )
                return Result.ok(relation)
            else:
                return Result.fail(
                    error="Relation 검증 실패",
                    error_code="VALIDATION_FAILED",
                    details={
                        "reasons": validation_result.reasons,
                        "layer": validation_result.layer.value if hasattr(validation_result, 'layer') else None,
                        "score": validation_result.score
                    }
                )
                
        except Exception as e:
            log_error(logger, e, {"relation_id": relation.id})
            return Result.fail(error=str(e), error_code="RELATION_ADD_FAILED")
    
    def get_subgraph(
        self,
        entity_names: List[str],
        depth: int = 2
    ) -> OntologyGraph:
        """
        엔티티들을 중심으로 서브그래프 추출
        계획서 4.2: 관련 엔티티 서브그래프 추출
        """
        entity_ids = []
        for name in entity_names:
            entity = self.graph.get_entity_by_name(name)
            if entity:
                entity_ids.append(entity.id)
        
        return self.graph.get_subgraph(entity_ids, depth)
    
    def get_related_mechanisms(
        self,
        entity_name: str
    ) -> List[Dict[str, Any]]:
        """
        엔티티와 관련된 Mechanism 조회
        계획서 4.2: 관련 메커니즘/조건/결과 검색
        """
        entity = self.graph.get_entity_by_name(entity_name)
        if not entity:
            return []
        
        mechanisms = []
        
        related = self.graph.get_related_entities(
            entity.id,
            relation_types=[
                RelationType.INFLUENCES,
                RelationType.PROPORTIONAL,
                RelationType.INVERSE,
                RelationType.CAUSES,
            ]
        )
        
        for related_entity, relation, direction in related:
            if relation and related_entity:
                mechanisms.append({
                    "entity": related_entity.canonical_name,
                    "relation": relation.label,
                    "type": relation.relation_type.value,
                    "direction": direction,
                    "magnitude": relation.magnitude,
                })
        
        return mechanisms
    
    def get_causal_chain(
        self,
        entity_name: str,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        인과 관계 체인 추출
        """
        entity = self.graph.get_entity_by_name(entity_name)
        if not entity:
            return []
        
        return self.graph.get_causal_chain(entity.id, max_depth)
    
    async def generate_rag_context(
        self,
        query: str,
        max_entities: int = 10,
        max_relations: int = 20
    ) -> str:
        """
        RAG용 컨텍스트 문자열 생성 (벡터 검색 활용)
        """
        # 의미적 유사도 기반 엔티티 검색
        similar_entities = await self.search_entities_by_similarity(query, top_k=max_entities)
        
        entity_names = [e.canonical_name for e, _ in similar_entities]
        
        if not entity_names:
            return "관련 온톨로지 정보가 없습니다."
        
        subgraph = self.get_subgraph(entity_names, depth=2)
        
        lines = ["## 관련 엔티티"]
        for entity, score in similar_entities[:10]:
            desc = entity.description or '설명 없음'
            lines.append(f"- {entity.canonical_name} (유사도: {score:.2f}): {desc}")
        
        lines.append("\n## 관련 관계")
        for relation in subgraph.relations[:max_relations]:
            source = subgraph.get_entity(relation.source_entity_id)
            target = subgraph.get_entity(relation.target_entity_id)
            if source and target:
                lines.append(
                    f"- {source.canonical_name} --[{relation.label}]--> {target.canonical_name}"
                )
        
        return "\n".join(lines)
    
    def to_context_string(
        self,
        entity_names: List[str],
        max_relations: int = 20
    ) -> str:
        """
        RAG용 컨텍스트 문자열 생성 (이름 기반)
        """
        subgraph = self.get_subgraph(entity_names, depth=2)
        
        lines = ["## 관련 엔티티"]
        for entity in subgraph.entities[:10]:
            lines.append(f"- {entity.canonical_name}: {entity.description or '설명 없음'}")
        
        lines.append("\n## 관련 관계")
        for relation in subgraph.relations[:max_relations]:
            source = subgraph.get_entity(relation.source_entity_id)
            target = subgraph.get_entity(relation.target_entity_id)
            if source and target:
                lines.append(
                    f"- {source.canonical_name} --[{relation.label}]--> {target.canonical_name}"
                )
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """온톨로지 통계 - v4.2 확장"""
        # Direct/Indirect 분류
        direct_count = sum(
            1 for r in self.graph.relations
            if getattr(r, 'relation_type_mode', 'direct') == 'direct'
        )
        indirect_count = sum(
            1 for r in self.graph.relations
            if getattr(r, 'relation_type_mode', 'direct') == 'indirect'
        )
        
        return {
            "entity_count": self.graph.node_count,
            "relation_count": self.graph.edge_count,
            "direct_relation_count": direct_count,
            "indirect_relation_count": indirect_count,
            "has_graph_store": self.graph_store is not None,
            "has_vector_store": self.vector_store is not None,
            "has_domain_dictionary": self.domain_dictionary is not None,
            "entities": [
                {
                    "id": e.id,
                    "name": e.canonical_name,
                    "type": e.entity_type,
                    "relation_count": e.relation_count,
                }
                for e in sorted(
                    self.graph.entities,
                    key=lambda x: x.relation_count,
                    reverse=True
                )[:20]
            ],
        }
    
    # ========== v4.2 Transitive Reduction ==========
    
    async def apply_transitive_reduction(self) -> Dict[str, Any]:
        """
        v4.2: Transitive Reduction 적용
        
        그래프에서 불필요한 A→C 엣지 제거 (A→B, B→C가 있을 때)
        초기에는 수동/배치 작업으로 실행
        """
        candidates = self.validator.check_transitive_reduction_candidates(self.graph)
        
        removed = []
        converted_to_indirect = []
        
        for relation in candidates:
            # 옵션 1: 완전 삭제
            # self.graph.remove_relation(relation.id)
            
            # 옵션 2: Indirect로 변경 (권장)
            relation.relation_type_mode = RelationTypeMode.INDIRECT.value
            converted_to_indirect.append(relation.id)
            
            if self.graph_store:
                await self.graph_store.update_relation_type_mode(
                    relation.id,
                    RelationTypeMode.INDIRECT
                )
        
        logger.info(
            "transitive_reduction_applied",
            candidates_found=len(candidates),
            converted_to_indirect=len(converted_to_indirect)
        )
        
        return {
            "candidates_found": len(candidates),
            "removed": removed,
            "converted_to_indirect": converted_to_indirect,
        }
    
    def get_indirect_path(
        self,
        source_entity_id: str,
        target_entity_id: str,
        max_depth: int = 3
    ) -> Optional[List[Dict[str, Any]]]:
        """
        v4.2: 두 엔티티 간 간접 경로 조회
        
        Returns:
            경로 리스트 (없으면 None)
        """
        path = self.graph.find_path(source_entity_id, target_entity_id)
        
        if not path:
            return None
        
        result = []
        for i, entity_id in enumerate(path):
            entity = self.graph.get_entity(entity_id)
            if entity:
                result.append({
                    "step": i,
                    "entity_id": entity_id,
                    "entity_name": entity.canonical_name,
                })
        
        return result
    
    async def close(self) -> None:
        """서비스 종료 - 저장소 정리"""
        if self.graph_store:
            await self.graph_store.close()
        if self.vector_store:
            await self.vector_store.close()
        if self.domain_dictionary:
            await self.domain_dictionary.close()
        logger.info("ontology_service_closed")

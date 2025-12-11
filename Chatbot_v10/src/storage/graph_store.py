"""
Graph Store - 온톨로지 그래프 영속화
SQLite + NetworkX 기반

원칙 1: One Source of Truth - 그래프 데이터의 단일 저장소
원칙 4: 단일 책임 - 그래프 영속화만 담당
"""
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json

from sqlalchemy import create_engine, Column, String, Float, Text, DateTime, Enum as SQLEnum
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.future import select
from datetime import datetime

from config.settings import get_settings
from config.constants import RelationType, ValidationStatus, RelationTypeMode
from src.domain.entities import Entity
from src.domain.relations import Relation, OntologyGraph
from src.storage.base import BaseStore, StoreError
from src.shared.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class EntityModel(Base):
    """Entity DB 모델"""
    __tablename__ = "entities"
    
    id = Column(String(36), primary_key=True)
    canonical_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    aliases = Column(Text, nullable=True)  # JSON array
    domain_tags = Column(Text, nullable=True)  # JSON array
    extra_metadata = Column(Text, nullable=True)  # JSON object
    relation_count = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RelationModel(Base):
    """Relation DB 모델 - v4.2 확장"""
    __tablename__ = "relations"
    
    id = Column(String(36), primary_key=True)
    source_entity_id = Column(String(36), nullable=False, index=True)
    target_entity_id = Column(String(36), nullable=False, index=True)
    relation_type = Column(String(50), nullable=False)
    
    # v4.2: Direct/Indirect 관계 구분
    relation_type_mode = Column(String(20), default="direct", index=True)
    
    label = Column(String(255), nullable=True)
    direction = Column(String(50), nullable=True)
    magnitude = Column(String(50), nullable=True)
    source_fragment_ids = Column(Text, nullable=True)  # JSON array
    validation_status = Column(String(50), default="pending")
    validation_score = Column(Float, default=0.0)
    
    # v4.2: Validation layer 기록
    validation_layer = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class GraphStore(BaseStore[OntologyGraph]):
    """
    SQLite 기반 그래프 저장소
    
    기능:
    - Entity/Relation 영속화
    - 그래프 상태 복원
    - 증분 업데이트
    """
    
    def __init__(self, db_url: Optional[str] = None):
        super().__init__("graph")
        self.db_url = db_url or get_settings().database_url
        self.engine = None
        self.async_session = None
    
    async def initialize(self) -> None:
        """데이터베이스 초기화"""
        try:
            self.engine = create_async_engine(
                self.db_url,
                echo=False,
                future=True
            )
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("graph_store_initialized", db_url=self.db_url)
            
        except Exception as e:
            raise self._handle_error(e, "initialize")
    
    async def save(self, graph: OntologyGraph) -> str:
        """전체 그래프 저장"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    # 모든 엔티티 저장
                    for entity in graph.entities:
                        await self._save_entity(session, entity)
                    
                    # 모든 관계 저장
                    for relation in graph.relations:
                        await self._save_relation(session, relation)
            
            logger.info(
                "graph_saved",
                entity_count=len(graph.entities),
                relation_count=len(graph.relations)
            )
            return "graph_snapshot"
            
        except Exception as e:
            raise self._handle_error(e, "save")
    
    async def _save_entity(self, session: AsyncSession, entity: Entity) -> None:
        """엔티티 저장 (upsert)"""
        model = EntityModel(
            id=entity.id,
            canonical_name=entity.canonical_name,
            entity_type=entity.entity_type,
            description=entity.description,
            aliases=json.dumps(entity.aliases, ensure_ascii=False),
            domain_tags=json.dumps(entity.domain_tags, ensure_ascii=False),
            extra_metadata=json.dumps(entity.properties, ensure_ascii=False) if entity.properties else None,
            relation_count=entity.relation_count,
        )
        await session.merge(model)
    
    async def _save_relation(self, session: AsyncSession, relation: Relation) -> None:
        """관계 저장 (upsert) - v4.2"""
        # v4.2: relation_type_mode 처리
        relation_type_mode = getattr(relation, 'relation_type_mode', RelationTypeMode.DIRECT)
        if isinstance(relation_type_mode, RelationTypeMode):
            relation_type_mode = relation_type_mode.value
        
        # v4.2: validation_layer 처리
        validation_layer = getattr(relation, 'validation_layer', None)
        
        model = RelationModel(
            id=relation.id,
            source_entity_id=relation.source_entity_id,
            target_entity_id=relation.target_entity_id,
            relation_type=relation.relation_type.value,
            relation_type_mode=relation_type_mode,
            label=relation.label,
            direction=relation.direction,
            magnitude=relation.magnitude,
            source_fragment_ids=json.dumps(relation.source_fragment_ids, ensure_ascii=False),
            validation_status=relation.validation_status.value,
            validation_score=relation.validation_score,
            validation_layer=validation_layer,
        )
        await session.merge(model)
    
    async def get(self, item_id: str) -> Optional[OntologyGraph]:
        """그래프 로드"""
        return await self.load_graph()
    
    async def load_graph(self) -> OntologyGraph:
        """전체 그래프 로드"""
        self._ensure_initialized()
        
        try:
            graph = OntologyGraph()
            
            async with self.async_session() as session:
                # 엔티티 로드
                result = await session.execute(select(EntityModel))
                entity_models = result.scalars().all()
                
                for model in entity_models:
                    entity = Entity(
                        id=model.id,
                        canonical_name=model.canonical_name,
                        entity_type=model.entity_type,
                        description=model.description,
                        aliases=json.loads(model.aliases) if model.aliases else [],
                        domain_tags=json.loads(model.domain_tags) if model.domain_tags else [],
                        properties=json.loads(model.extra_metadata) if model.extra_metadata else {},
                        relation_count=int(model.relation_count or 0),
                    )
                    graph.add_entity(entity)
                
                # 관계 로드
                result = await session.execute(select(RelationModel))
                relation_models = result.scalars().all()
                
                for model in relation_models:
                    relation = Relation(
                        id=model.id,
                        source_entity_id=model.source_entity_id,
                        target_entity_id=model.target_entity_id,
                        relation_type=RelationType(model.relation_type),
                        label=model.label,
                        direction=model.direction,
                        magnitude=model.magnitude,
                        source_fragment_ids=json.loads(model.source_fragment_ids) if model.source_fragment_ids else [],
                        validation_status=ValidationStatus(model.validation_status),
                        validation_score=model.validation_score,
                    )
                    graph.add_relation(relation)
            
            logger.info(
                "graph_loaded",
                entity_count=len(graph.entities),
                relation_count=len(graph.relations)
            )
            return graph
            
        except Exception as e:
            raise self._handle_error(e, "load_graph")
    
    async def save_entity(self, entity: Entity) -> str:
        """단일 엔티티 저장"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    await self._save_entity(session, entity)
            return entity.id
        except Exception as e:
            raise self._handle_error(e, "save_entity")
    
    async def save_relation(self, relation: Relation) -> str:
        """단일 관계 저장"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    await self._save_relation(session, relation)
            return relation.id
        except Exception as e:
            raise self._handle_error(e, "save_relation")
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """엔티티 조회"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(EntityModel).where(EntityModel.id == entity_id)
                )
                model = result.scalar_one_or_none()
                
                if not model:
                    return None
                
                return Entity(
                    id=model.id,
                    canonical_name=model.canonical_name,
                    entity_type=model.entity_type,
                    description=model.description,
                    aliases=json.loads(model.aliases) if model.aliases else [],
                    domain_tags=json.loads(model.domain_tags) if model.domain_tags else [],
                    properties=json.loads(model.extra_metadata) if model.extra_metadata else {},
                    relation_count=int(model.relation_count or 0),
                )
        except Exception as e:
            raise self._handle_error(e, "get_entity")
    
    async def get_relations_for_entity(
        self,
        entity_id: str,
        as_source: bool = True,
        as_target: bool = True
    ) -> List[Relation]:
        """엔티티와 연결된 관계 조회"""
        self._ensure_initialized()
        
        try:
            relations = []
            async with self.async_session() as session:
                if as_source:
                    result = await session.execute(
                        select(RelationModel).where(RelationModel.source_entity_id == entity_id)
                    )
                    relations.extend(result.scalars().all())
                
                if as_target:
                    result = await session.execute(
                        select(RelationModel).where(RelationModel.target_entity_id == entity_id)
                    )
                    relations.extend(result.scalars().all())
            
            return [
                Relation(
                    id=m.id,
                    source_entity_id=m.source_entity_id,
                    target_entity_id=m.target_entity_id,
                    relation_type=RelationType(m.relation_type),
                    label=m.label,
                    direction=m.direction,
                    magnitude=m.magnitude,
                    source_fragment_ids=json.loads(m.source_fragment_ids) if m.source_fragment_ids else [],
                    validation_status=ValidationStatus(m.validation_status),
                    validation_score=m.validation_score,
                )
                for m in relations
            ]
        except Exception as e:
            raise self._handle_error(e, "get_relations_for_entity")
    
    async def delete(self, item_id: str) -> bool:
        """항목 삭제 (엔티티 또는 관계)"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    # 엔티티 삭제 시도
                    result = await session.execute(
                        select(EntityModel).where(EntityModel.id == item_id)
                    )
                    entity = result.scalar_one_or_none()
                    if entity:
                        await session.delete(entity)
                        return True
                    
                    # 관계 삭제 시도
                    result = await session.execute(
                        select(RelationModel).where(RelationModel.id == item_id)
                    )
                    relation = result.scalar_one_or_none()
                    if relation:
                        await session.delete(relation)
                        return True
            
            return False
        except Exception as e:
            raise self._handle_error(e, "delete")
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Entity]:
        """모든 엔티티 조회"""
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(EntityModel).offset(offset).limit(limit)
                )
                models = result.scalars().all()
                
                return [
                    Entity(
                        id=m.id,
                        canonical_name=m.canonical_name,
                        entity_type=m.entity_type,
                        description=m.description,
                        aliases=json.loads(m.aliases) if m.aliases else [],
                        domain_tags=json.loads(m.domain_tags) if m.domain_tags else [],
                    )
                    for m in models
                ]
        except Exception as e:
            raise self._handle_error(e, "list_all")
    
    # ========== v4.2 Direct/Indirect Relation Methods ==========
    
    async def get_direct_relations(self, entity_id: Optional[str] = None) -> List[Relation]:
        """
        v4.2: Direct 관계만 조회
        
        Args:
            entity_id: 특정 엔티티의 관계만 (None이면 전체)
        """
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                query = select(RelationModel).where(
                    RelationModel.relation_type_mode == "direct"
                )
                
                if entity_id:
                    query = query.where(
                        (RelationModel.source_entity_id == entity_id) |
                        (RelationModel.target_entity_id == entity_id)
                    )
                
                result = await session.execute(query)
                relation_models = result.scalars().all()
                
                return [
                    self._model_to_relation(m) for m in relation_models
                ]
        except Exception as e:
            raise self._handle_error(e, "get_direct_relations")
    
    async def get_indirect_relations(self, entity_id: Optional[str] = None) -> List[Relation]:
        """
        v4.2: Indirect 관계만 조회
        """
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                query = select(RelationModel).where(
                    RelationModel.relation_type_mode == "indirect"
                )
                
                if entity_id:
                    query = query.where(
                        (RelationModel.source_entity_id == entity_id) |
                        (RelationModel.target_entity_id == entity_id)
                    )
                
                result = await session.execute(query)
                relation_models = result.scalars().all()
                
                return [
                    self._model_to_relation(m) for m in relation_models
                ]
        except Exception as e:
            raise self._handle_error(e, "get_indirect_relations")
    
    async def get_entity_degree(self, entity_id: str) -> Dict[str, int]:
        """
        v4.2: 엔티티의 차수(degree) 계산
        
        Returns:
            {"in_degree": int, "out_degree": int, "total": int}
        """
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                # Out degree (source로서)
                out_result = await session.execute(
                    select(RelationModel).where(
                        RelationModel.source_entity_id == entity_id,
                        RelationModel.relation_type_mode == "direct"
                    )
                )
                out_degree = len(out_result.scalars().all())
                
                # In degree (target으로서)
                in_result = await session.execute(
                    select(RelationModel).where(
                        RelationModel.target_entity_id == entity_id,
                        RelationModel.relation_type_mode == "direct"
                    )
                )
                in_degree = len(in_result.scalars().all())
                
                return {
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                    "total": in_degree + out_degree
                }
        except Exception as e:
            raise self._handle_error(e, "get_entity_degree")
    
    async def update_relation_type_mode(
        self,
        relation_id: str,
        mode: RelationTypeMode
    ) -> bool:
        """
        v4.2: 관계의 type_mode 변경 (direct <-> indirect)
        """
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(
                        select(RelationModel).where(RelationModel.id == relation_id)
                    )
                    relation = result.scalar_one_or_none()
                    
                    if relation:
                        relation.relation_type_mode = mode.value
                        return True
                    return False
        except Exception as e:
            raise self._handle_error(e, "update_relation_type_mode")
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """
        v4.2: 그래프 통계 조회
        """
        self._ensure_initialized()
        
        try:
            async with self.async_session() as session:
                # 엔티티 수
                entity_result = await session.execute(select(EntityModel))
                entity_count = len(entity_result.scalars().all())
                
                # 관계 수 (전체)
                relation_result = await session.execute(select(RelationModel))
                all_relations = relation_result.scalars().all()
                
                # Direct/Indirect 분류
                direct_count = sum(1 for r in all_relations if r.relation_type_mode == "direct")
                indirect_count = sum(1 for r in all_relations if r.relation_type_mode == "indirect")
                
                # 관계 유형별 분포
                relation_type_counts = {}
                for r in all_relations:
                    rt = r.relation_type
                    relation_type_counts[rt] = relation_type_counts.get(rt, 0) + 1
                
                return {
                    "entity_count": entity_count,
                    "relation_count": len(all_relations),
                    "direct_relation_count": direct_count,
                    "indirect_relation_count": indirect_count,
                    "relation_type_distribution": relation_type_counts,
                }
        except Exception as e:
            raise self._handle_error(e, "get_graph_statistics")
    
    def _model_to_relation(self, model: RelationModel) -> Relation:
        """RelationModel을 Relation 도메인 객체로 변환"""
        relation = Relation(
            id=model.id,
            source_entity_id=model.source_entity_id,
            target_entity_id=model.target_entity_id,
            relation_type=RelationType(model.relation_type),
            label=model.label,
            direction=model.direction,
            magnitude=model.magnitude,
            source_fragment_ids=json.loads(model.source_fragment_ids) if model.source_fragment_ids else [],
            validation_status=ValidationStatus(model.validation_status),
            validation_score=model.validation_score,
        )
        # v4.2 필드 추가
        relation.relation_type_mode = model.relation_type_mode
        relation.validation_layer = model.validation_layer
        return relation
    
    async def close(self) -> None:
        """연결 종료"""
        if self.engine:
            await self.engine.dispose()
        self._initialized = False
        logger.info("graph_store_closed")

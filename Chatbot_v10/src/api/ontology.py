"""
온톨로지 관리 API
계획서 3: Ontology Layer
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from config.constants import RelationType, ValidationStatus
from src.services.ontology_service import OntologyService
from src.services.llm_service import LLMService
from src.validators.relation_validator import RelationValidator
from src.domain.entities import Entity
from src.domain.relations import Relation

router = APIRouter(prefix="/ontology", tags=["Ontology"])


# === Request/Response Models ===

class EntityCreateRequest(BaseModel):
    """엔티티 생성 요청"""
    name: str = Field(min_length=1, description="엔티티 이름")
    entity_type: Optional[str] = Field(default=None, description="엔티티 유형")
    domain_tags: List[str] = Field(default_factory=list, description="도메인 태그")
    description: Optional[str] = Field(default=None, description="설명")
    aliases: List[str] = Field(default_factory=list, description="별칭")


class RelationCreateRequest(BaseModel):
    """관계 생성 요청"""
    source_entity_name: str = Field(description="출발 엔티티 이름")
    target_entity_name: str = Field(description="도착 엔티티 이름")
    relation_type: str = Field(description="관계 유형")
    label: str = Field(description="관계 레이블")
    direction: Optional[str] = Field(default=None, description="영향 방향")
    magnitude: Optional[str] = Field(default=None, description="영향 크기")


class EntityResponse(BaseModel):
    """엔티티 응답"""
    id: str
    canonical_name: str
    aliases: List[str]
    entity_type: Optional[str]
    domain_tags: List[str]
    description: Optional[str]
    validation_status: str
    mention_count: int
    relation_count: int


class RelationResponse(BaseModel):
    """관계 응답"""
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    label: str
    weight: float
    validation_status: str
    validation_score: float


class SubgraphResponse(BaseModel):
    """서브그래프 응답"""
    entities: List[EntityResponse]
    relations: List[RelationResponse]
    node_count: int
    edge_count: int


class OntologyStatsResponse(BaseModel):
    """온톨로지 통계 응답"""
    entity_count: int
    relation_count: int
    top_entities: List[dict]


# === Dependencies ===

def get_relation_validator() -> RelationValidator:
    return RelationValidator()


# 싱글톤 온톨로지 서비스 (One Source of Truth)
_ontology_service: Optional[OntologyService] = None


def get_ontology_service(
    validator: RelationValidator = Depends(get_relation_validator)
) -> OntologyService:
    global _ontology_service
    if _ontology_service is None:
        _ontology_service = OntologyService(validator)
    return _ontology_service


# === Endpoints ===

@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    request: EntityCreateRequest,
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    엔티티 생성
    """
    entity = Entity(
        canonical_name=request.name,
        aliases=request.aliases,
        entity_type=request.entity_type,
        domain_tags=request.domain_tags,
        description=request.description,
        validation_status=ValidationStatus.APPROVED,  # 수동 생성은 바로 승인
    )
    
    result = await ontology.add_entity(entity)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    e = result.data
    return EntityResponse(
        id=e.id,
        canonical_name=e.canonical_name,
        aliases=e.aliases,
        entity_type=e.entity_type,
        domain_tags=e.domain_tags,
        description=e.description,
        validation_status=e.validation_status.value,
        mention_count=e.mention_count,
        relation_count=e.relation_count,
    )


@router.get("/entities", response_model=List[EntityResponse])
async def list_entities(
    limit: int = 50,
    offset: int = 0,
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    엔티티 목록 조회
    """
    entities = ontology.graph.entities[offset:offset + limit]
    
    return [
        EntityResponse(
            id=e.id,
            canonical_name=e.canonical_name,
            aliases=e.aliases,
            entity_type=e.entity_type,
            domain_tags=e.domain_tags,
            description=e.description,
            validation_status=e.validation_status.value,
            mention_count=e.mention_count,
            relation_count=e.relation_count,
        )
        for e in entities
    ]


@router.get("/entities/{entity_name}", response_model=EntityResponse)
async def get_entity(
    entity_name: str,
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    엔티티 조회 (이름 또는 별칭)
    """
    entity = ontology.graph.get_entity_by_name(entity_name)
    
    if not entity:
        raise HTTPException(status_code=404, detail=f"엔티티 '{entity_name}'을 찾을 수 없습니다")
    
    return EntityResponse(
        id=entity.id,
        canonical_name=entity.canonical_name,
        aliases=entity.aliases,
        entity_type=entity.entity_type,
        domain_tags=entity.domain_tags,
        description=entity.description,
        validation_status=entity.validation_status.value,
        mention_count=entity.mention_count,
        relation_count=entity.relation_count,
    )


@router.post("/relations", response_model=RelationResponse)
async def create_relation(
    request: RelationCreateRequest,
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    관계 생성
    """
    # 엔티티 조회
    source = ontology.graph.get_entity_by_name(request.source_entity_name)
    target = ontology.graph.get_entity_by_name(request.target_entity_name)
    
    if not source:
        raise HTTPException(
            status_code=404,
            detail=f"Source 엔티티 '{request.source_entity_name}'을 찾을 수 없습니다"
        )
    
    if not target:
        raise HTTPException(
            status_code=404,
            detail=f"Target 엔티티 '{request.target_entity_name}'을 찾을 수 없습니다"
        )
    
    # RelationType 변환
    try:
        relation_type = RelationType(request.relation_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 관계 유형: {request.relation_type}. "
                   f"가능한 값: {[rt.value for rt in RelationType]}"
        )
    
    relation = Relation(
        source_entity_id=source.id,
        target_entity_id=target.id,
        relation_type=relation_type,
        label=request.label,
        direction=request.direction,
        magnitude=request.magnitude,
    )
    
    result = await ontology.add_relation(relation)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    r = result.data
    return RelationResponse(
        id=r.id,
        source_entity_id=r.source_entity_id,
        target_entity_id=r.target_entity_id,
        relation_type=r.relation_type.value,
        label=r.label,
        weight=r.weight,
        validation_status=r.validation_status.value,
        validation_score=r.validation_score,
    )


@router.get("/relations", response_model=List[RelationResponse])
async def list_relations(
    entity_name: Optional[str] = None,
    relation_type: Optional[str] = None,
    limit: int = 50,
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    관계 목록 조회
    """
    relations = ontology.graph.relations
    
    # 필터링
    if entity_name:
        entity = ontology.graph.get_entity_by_name(entity_name)
        if entity:
            relations = [
                r for r in relations
                if r.source_entity_id == entity.id or r.target_entity_id == entity.id
            ]
    
    if relation_type:
        relations = [
            r for r in relations
            if r.relation_type.value == relation_type
        ]
    
    return [
        RelationResponse(
            id=r.id,
            source_entity_id=r.source_entity_id,
            target_entity_id=r.target_entity_id,
            relation_type=r.relation_type.value,
            label=r.label,
            weight=r.weight,
            validation_status=r.validation_status.value,
            validation_score=r.validation_score,
        )
        for r in relations[:limit]
    ]


@router.get("/subgraph", response_model=SubgraphResponse)
async def get_subgraph(
    entities: str,  # 쉼표로 구분된 엔티티 이름들
    depth: int = 2,
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    서브그래프 조회
    
    계획서 4.2: 관련 엔티티 서브그래프 추출
    """
    entity_names = [e.strip() for e in entities.split(",")]
    
    subgraph = ontology.get_subgraph(entity_names, depth)
    
    return SubgraphResponse(
        entities=[
            EntityResponse(
                id=e.id,
                canonical_name=e.canonical_name,
                aliases=e.aliases,
                entity_type=e.entity_type,
                domain_tags=e.domain_tags,
                description=e.description,
                validation_status=e.validation_status.value,
                mention_count=e.mention_count,
                relation_count=e.relation_count,
            )
            for e in subgraph.entities
        ],
        relations=[
            RelationResponse(
                id=r.id,
                source_entity_id=r.source_entity_id,
                target_entity_id=r.target_entity_id,
                relation_type=r.relation_type.value,
                label=r.label,
                weight=r.weight,
                validation_status=r.validation_status.value,
                validation_score=r.validation_score,
            )
            for r in subgraph.relations
        ],
        node_count=subgraph.node_count,
        edge_count=subgraph.edge_count,
    )


@router.get("/mechanisms/{entity_name}")
async def get_mechanisms(
    entity_name: str,
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    엔티티 관련 메커니즘 조회
    
    계획서 4.2: 관련 메커니즘/조건/결과 검색
    """
    mechanisms = ontology.get_related_mechanisms(entity_name)
    
    if not mechanisms:
        # 엔티티 존재 여부 확인
        entity = ontology.graph.get_entity_by_name(entity_name)
        if not entity:
            raise HTTPException(
                status_code=404,
                detail=f"엔티티 '{entity_name}'을 찾을 수 없습니다"
            )
    
    return {"entity": entity_name, "mechanisms": mechanisms}


@router.get("/causal-chain/{entity_name}")
async def get_causal_chain(
    entity_name: str,
    max_depth: int = 5,
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    인과 관계 체인 조회
    """
    chains = ontology.get_causal_chain(entity_name, max_depth)
    
    return {"entity": entity_name, "causal_chains": chains}


@router.get("/stats", response_model=OntologyStatsResponse)
async def get_statistics(
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    온톨로지 통계 조회
    """
    stats = ontology.get_statistics()
    
    return OntologyStatsResponse(
        entity_count=stats["entity_count"],
        relation_count=stats["relation_count"],
        top_entities=stats["entities"],
    )


@router.get("/relation-types")
async def get_relation_types():
    """지원하는 관계 유형 조회"""
    return {
        "relation_types": [
            {"value": rt.value, "description": rt.name}
            for rt in RelationType
        ]
    }

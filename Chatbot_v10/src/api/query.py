"""
질의 처리 API
계획서 4: Question Processing & Routing
"""
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.services.query_service import QueryService
from src.services.ontology_service import OntologyService
from src.services.llm_service import LLMService
from src.validators.relation_validator import RelationValidator

router = APIRouter(prefix="/query", tags=["Query"])


# === Request/Response Models ===

class QueryRequest(BaseModel):
    """질의 요청"""
    query: str = Field(min_length=2, description="사용자 질의")
    include_rag_response: bool = Field(default=True, description="RAG 응답 포함 여부")


class RAGRequest(BaseModel):
    """RAG 요청"""
    query: str = Field(min_length=2, description="사용자 질의")
    context_entities: Optional[list[str]] = Field(
        default=None,
        description="추가 컨텍스트 엔티티 (지정하지 않으면 자동 추출)"
    )


class QueryResponse(BaseModel):
    """질의 응답"""
    query: str
    intent: str
    confidence: float
    entities: list[str]
    keywords: list[str]
    action_type: Optional[str] = None
    subgraph: Optional[dict] = None
    mechanisms: Optional[list] = None
    causal_chains: Optional[list] = None
    ontology_context: Optional[str] = None
    action_candidate: Optional[dict] = None
    rag_response: Optional[str] = None
    requires_admin_approval: bool = False


class RAGResponse(BaseModel):
    """RAG 응답"""
    query: str
    response: str
    entities_used: list[str]


# === Dependencies ===

def get_llm_service() -> LLMService:
    return LLMService()


def get_relation_validator() -> RelationValidator:
    return RelationValidator()


# 싱글톤 서비스들
_ontology_service: Optional[OntologyService] = None
_query_service: Optional[QueryService] = None


def get_ontology_service(
    validator: RelationValidator = Depends(get_relation_validator)
) -> OntologyService:
    global _ontology_service
    if _ontology_service is None:
        _ontology_service = OntologyService(validator)
    return _ontology_service


def get_query_service(
    llm: LLMService = Depends(get_llm_service),
    ontology: OntologyService = Depends(get_ontology_service)
) -> QueryService:
    global _query_service
    if _query_service is None:
        _query_service = QueryService(llm, ontology)
    return _query_service


# === Endpoints ===

@router.post("/process", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service),
    llm: LLMService = Depends(get_llm_service)
):
    """
    질의 처리
    
    계획서 4.1: Intent 분류
    계획서 4.2: Ontology 기반 라우팅
    
    1. Intent 분류 (정보조회/분석/실행/생성)
    2. 관련 엔티티 추출
    3. 온톨로지 서브그래프 추출
    4. Intent에 따른 처리 (RAG 응답 또는 Action 생성)
    """
    result = await query_service.process_query(request.query)
    
    if not result.success:
        return QueryResponse(
            query=request.query,
            intent="error",
            confidence=0.0,
            entities=[],
            keywords=[],
            rag_response=f"오류: {result.error}"
        )
    
    data = result.data
    
    # RAG 응답 생성 (요청된 경우)
    rag_response = None
    if request.include_rag_response and data.get("ontology_context"):
        rag_result = await query_service.generate_rag_response(
            request.query,
            data.get("ontology_context")
        )
        if rag_result.success:
            rag_response = rag_result.data
    
    return QueryResponse(
        query=data.get("query", request.query),
        intent=data.get("intent", "RETRIEVAL"),
        confidence=data.get("confidence", 0.0),
        entities=data.get("entities", []),
        keywords=data.get("keywords", []),
        action_type=data.get("action_type"),
        subgraph=data.get("subgraph"),
        mechanisms=data.get("mechanisms"),
        causal_chains=data.get("causal_chains"),
        ontology_context=data.get("ontology_context"),
        action_candidate=data.get("action_candidate"),
        rag_response=rag_response,
        requires_admin_approval=data.get("requires_admin_approval", False),
    )


@router.post("/rag", response_model=RAGResponse)
async def generate_rag_response(
    request: RAGRequest,
    query_service: QueryService = Depends(get_query_service),
    ontology: OntologyService = Depends(get_ontology_service)
):
    """
    RAG 기반 응답 생성
    
    계획서 목표: RAG를 통한 온톨로지 기반 LLM 답변 생성
    
    온톨로지 그래프에서 관련 정보를 검색하여
    LLM에 컨텍스트로 제공하고 답변 생성
    """
    # 컨텍스트 엔티티 결정
    entities_used = request.context_entities or []
    
    # 컨텍스트 생성
    if entities_used:
        ontology_context = ontology.to_context_string(entities_used)
    else:
        # 자동 추출
        result = await query_service.process_query(request.query)
        if result.success:
            entities_used = result.data.get("entities", [])
            ontology_context = result.data.get("ontology_context", "")
        else:
            ontology_context = ""
    
    # RAG 응답 생성
    response_result = await query_service.generate_rag_response(
        request.query,
        ontology_context
    )
    
    return RAGResponse(
        query=request.query,
        response=response_result.data if response_result.success else f"오류: {response_result.error}",
        entities_used=entities_used,
    )


@router.post("/rag/stream")
async def generate_rag_response_stream(
    request: RAGRequest,
    query_service: QueryService = Depends(get_query_service),
    ontology: OntologyService = Depends(get_ontology_service),
    llm: LLMService = Depends(get_llm_service)
):
    """
    RAG 응답 스트리밍 생성
    
    실시간으로 LLM 응답을 스트리밍
    """
    # 컨텍스트 생성
    if request.context_entities:
        ontology_context = ontology.to_context_string(request.context_entities)
    else:
        result = await query_service.process_query(request.query)
        ontology_context = result.data.get("ontology_context", "") if result.success else ""
    
    # 프롬프트 생성
    from config.constants import PROMPT_TEMPLATES
    prompt = PROMPT_TEMPLATES["rag_response"].format(
        query=request.query,
        ontology_context=ontology_context
    )
    
    async def generate():
        async for chunk in llm.generate_stream(prompt, temperature=0.3):
            yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


@router.get("/intent-types")
async def get_intent_types():
    """지원하는 Intent 유형 조회"""
    from config.constants import IntentType
    
    return {
        "intent_types": [
            {
                "value": it.value,
                "name": it.name,
                "description": {
                    "RETRIEVAL": "정보 조회 (무엇인가요? 어떤 것이 있나요?)",
                    "ANALYSIS": "분석/추론 (왜? 어떻게? 관계는?)",
                    "EXECUTION": "시스템 동작 요청 (실행해줘, 알림 설정)",
                    "CREATION": "신규 Action 생성 요청 (새로운 규칙 만들어줘)",
                }.get(it.name, "")
            }
            for it in IntentType
        ]
    }

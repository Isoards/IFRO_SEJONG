"""
v5.2 API Server
FastAPI 기반 RAG + Ontology 엔드포인트

엔드포인트:
- GET /healthz: 서비스 헬스 체크
- GET /api/status: 시스템 상태
- POST /api/ask: 단일 질문 RAG
- POST /api/qa/batch: 다건 질문 처리
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config.settings import get_settings
from src.services.ontology_service import OntologyService
from src.services.llm_service import LLMService
from src.reasoning import PathReasoner, MechanismReasoner, ScenarioSimulator
from src.actions import ActionGenerator, ActionValidator, ActionExecutor


# ========== Request/Response Models ==========

class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str = "healthy"
    version: str = "5.2.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StatusResponse(BaseModel):
    """시스템 상태 응답"""
    ready: bool = True
    version: str = "5.2.0"
    entity_count: int = 0
    relation_count: int = 0
    vector_count: int = 0
    llm_available: bool = False
    reasoning_enabled: bool = True
    action_enabled: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AskRequest(BaseModel):
    """단일 질문 요청"""
    question: str = Field(..., min_length=1, description="질문 내용")
    use_reasoning: bool = Field(default=True, description="추론 엔진 사용 여부")
    max_sources: int = Field(default=3, ge=1, le=10, description="최대 소스 수")
    entities: Optional[List[str]] = Field(default=None, description="관련 엔티티 힌트")


class SourceInfo(BaseModel):
    """소스 정보"""
    entity_name: str
    relation: Optional[str] = None
    confidence: float = 0.0


class AskResponse(BaseModel):
    """질문 응답"""
    answer: str
    confidence: float = 0.0
    sources: List[SourceInfo] = Field(default_factory=list)
    reasoning_used: bool = False
    reasoning_trace: List[str] = Field(default_factory=list)
    action_suggested: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BatchQuestion(BaseModel):
    """배치 질문 항목"""
    id: str
    question: str
    entities: Optional[List[str]] = None


class BatchRequest(BaseModel):
    """배치 질문 요청"""
    questions: List[BatchQuestion]
    use_reasoning: bool = True


class BatchAnswerItem(BaseModel):
    """배치 응답 항목"""
    id: str
    question: str
    answer: str
    confidence: float = 0.0
    sources: List[SourceInfo] = Field(default_factory=list)
    error: Optional[str] = None


class BatchResponse(BaseModel):
    """배치 응답"""
    results: List[BatchAnswerItem]
    total: int
    success_count: int
    error_count: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ========== Application State ==========

class AppState:
    """애플리케이션 상태 관리"""
    def __init__(self):
        self.ontology_service: Optional[OntologyService] = None
        self.llm_service: Optional[LLMService] = None
        self.action_generator: Optional[ActionGenerator] = None
        self.action_validator: Optional[ActionValidator] = None
        self.action_executor: Optional[ActionExecutor] = None
        self.ready: bool = False
        self.llm_available: bool = False

    async def initialize(self):
        """서비스 초기화"""
        settings = get_settings()
        
        # Validators 생성
        from src.validators.relation_validator import RelationValidator
        from src.validators.fragment_validator import FragmentValidator
        from src.storage.graph_store import GraphStore
        from src.storage.vector_store import VectorStore
        
        relation_validator = RelationValidator(llm_service=None)
        
        # Storage 생성 (ontology.db에서 데이터 로드)
        graph_store = GraphStore(db_url=settings.database_url)
        vector_store = VectorStore(persist_dir=settings.chroma_persist_dir)
        
        # Ontology Service (GraphStore 주입)
        self.ontology_service = OntologyService(
            validator=relation_validator,
            graph_store=graph_store,
            vector_store=vector_store
        )
        await self.ontology_service.initialize()
        
        # LLM Service
        self.llm_service = LLMService()
        self.llm_available = await self._check_llm()
        
        # Action Layer
        self.action_generator = ActionGenerator()
        self.action_validator = ActionValidator()
        self.action_executor = ActionExecutor()
        
        # Data Loader (v5.2 추가: 초기 데이터 자동 학습)
        if self.llm_available:
            from src.services.data_loader import DataLoader
            self.data_loader = DataLoader(self.ontology_service, self.llm_service)
        
        self.ready = True
    
    async def _check_llm(self) -> bool:
        """LLM 가용성 체크"""
        try:
            return await self.llm_service.health_check()
        except Exception:
            return False
    
    async def close(self):
        """리소스 정리"""
        if self.ontology_service:
            await self.ontology_service.close()


app_state = AppState()


# ========== Lifespan ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # Startup
    print("[v5.2 API] Initializing services...")
    await app_state.initialize()
    print(f"[v5.2 API] Ready! LLM available: {app_state.llm_available}")
    
    # 초기 데이터 학습 백그라운드 실행
    if app_state.llm_available and hasattr(app_state, 'data_loader'):
        asyncio.create_task(app_state.data_loader.load_initial_data())
        print("[v5.2 API] Background data loading started...")
    
    yield
    
    # Shutdown
    print("[v5.2 API] Shutting down...")
    await app_state.close()


# ========== FastAPI App ==========

app = FastAPI(
    title="v5.2 Ontology-Reasoning-Action API",
    description="온톨로지 기반 RAG + 심볼릭 추론 API",
    version="5.2.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Endpoints ==========

@app.get("/", response_model=Dict[str, Any])
async def root():
    """서비스 정보"""
    return {
        "service": "v5.2 Ontology-Reasoning-Action API",
        "version": "5.2.0",
        "endpoints": {
            "health": "/healthz",
            "status": "/api/status",
            "ask": "/api/ask",
            "batch": "/api/qa/batch"
        }
    }


@app.get("/healthz", response_model=HealthResponse)
@app.get("/api/healthz", response_model=HealthResponse)
async def healthz():
    """헬스 체크"""
    return HealthResponse(
        status="healthy" if app_state.ready else "initializing"
    )


@app.get("/status", response_model=StatusResponse)
@app.get("/api/status", response_model=StatusResponse)
async def status():
    """시스템 상태"""
    stats = {}
    
    if app_state.ontology_service:
        stats = app_state.ontology_service.get_statistics()
    
    return StatusResponse(
        ready=app_state.ready,
        entity_count=stats.get("entity_count", 0),
        relation_count=stats.get("relation_count", 0),
        vector_count=stats.get("vector_count", 0),
        llm_available=app_state.llm_available,
        reasoning_enabled=True,
        action_enabled=True
    )


@app.post("/ask", response_model=AskResponse)
@app.post("/api/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    단일 질문 RAG 처리
    
    1. 인사 감지 → 사전 응답
    2. 온톨로지 컨텍스트 생성
    3. (선택) 추론 엔진 실행
    4. LLM RAG 응답 생성
    5. Action 제안
    """
    if not app_state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    question = request.question.strip()
    
    # 1. 인사 감지
    greetings = ["안녕", "hello", "hi", "반가워", "하이"]
    if any(g in question.lower() for g in greetings):
        return AskResponse(
            answer="안녕하세요! v5.2 온톨로지 기반 RAG 시스템입니다. 무엇을 도와드릴까요?",
            confidence=1.0,
            reasoning_used=False
        )
    
    sources: List[SourceInfo] = []
    reasoning_trace: List[str] = []
    confidence = 0.5
    action_suggested = None
    
    try:
        # 2. 온톨로지 컨텍스트 생성
        context = await app_state.ontology_service.generate_rag_context(
            query=question,
            max_entities=10,
            max_relations=20
        )
        
        # 관련 엔티티 수집
        for entity in app_state.ontology_service.graph.entities[:request.max_sources]:
            sources.append(SourceInfo(
                entity_name=entity.canonical_name,
                confidence=entity.validation_score if hasattr(entity, 'validation_score') else 0.5
            ))
        
        # 3. 추론 엔진 (선택)
        if request.use_reasoning and len(sources) >= 2:
            try:
                mech_reasoner = MechanismReasoner(app_state.ontology_service.graph)
                entities = request.entities or [s.entity_name for s in sources[:2]]
                
                if len(entities) >= 2:
                    # 엔티티 ID 찾기
                    e1 = app_state.ontology_service.graph.get_entity_by_name(entities[0])
                    e2 = app_state.ontology_service.graph.get_entity_by_name(entities[1])
                    
                    if e1 and e2:
                        reasoning_result = await mech_reasoner.reason(e1.id, e2.id)
                        if reasoning_result.success:
                            confidence = max(confidence, reasoning_result.confidence)
                            reasoning_trace = reasoning_result.trace
            except Exception:
                pass  # 추론 실패 시 무시
        
        # 4. LLM RAG 응답
        if app_state.llm_available:
            answer = await app_state.llm_service.generate_rag_response(
                query=question,
                ontology_context=context
            )
        else:
            answer = f"[Mock] 질문 '{question}'에 대한 온톨로지 기반 응답입니다. 관련 엔티티: {', '.join(s.entity_name for s in sources)}"
        
        # 5. Action 제안
        if app_state.action_generator:
            candidates = await app_state.action_generator.generate(
                query=question,
                entities=[s.entity_name for s in sources],
                reasoning_result=None
            )
            if candidates:
                action_suggested = candidates[0].action.action_type.value
        
        return AskResponse(
            answer=answer,
            confidence=confidence,
            sources=sources,
            reasoning_used=request.use_reasoning and len(reasoning_trace) > 0,
            reasoning_trace=reasoning_trace[:5],  # 최대 5개
            action_suggested=action_suggested,
            metrics={
                "entity_count": len(sources),
                "context_length": len(context),
                "llm_used": app_state.llm_available
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/qa/batch", response_model=BatchResponse)
async def qa_batch(request: BatchRequest):
    """
    다건 질문 배치 처리
    """
    if not app_state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    results: List[BatchAnswerItem] = []
    success_count = 0
    error_count = 0
    
    for q in request.questions:
        try:
            # 개별 질문 처리
            ask_request = AskRequest(
                question=q.question,
                use_reasoning=request.use_reasoning,
                entities=q.entities
            )
            
            response = await ask(ask_request)
            
            results.append(BatchAnswerItem(
                id=q.id,
                question=q.question,
                answer=response.answer,
                confidence=response.confidence,
                sources=response.sources
            ))
            success_count += 1
            
        except Exception as e:
            results.append(BatchAnswerItem(
                id=q.id,
                question=q.question,
                answer="",
                error=str(e)
            ))
            error_count += 1
    
    return BatchResponse(
        results=results,
        total=len(request.questions),
        success_count=success_count,
        error_count=error_count
    )


# ========== Run ==========

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """서버 실행"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    settings = get_settings()
    run_server(host=settings.host, port=settings.port)

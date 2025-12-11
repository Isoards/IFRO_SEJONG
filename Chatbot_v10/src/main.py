"""
Ontology-driven Reasoning & Action Platform
FastAPI 서버 진입점

계획서 목표:
- Action에 의한 기능 실행
- RAG를 통한 온톨로지 기반 LLM 답변 생성
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# 프로젝트 루트를 Python path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from src.shared.logging import get_logger
from src.shared.errors import OntologyError
from src.api import (
    documents_router,
    ontology_router,
    query_router,
    actions_router,
)

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # Startup
    logger.info(
        "server_starting",
        host=settings.host,
        port=settings.port,
        debug=settings.debug
    )
    
    # Ollama 연결 확인
    from src.services.llm_service import LLMService
    llm = LLMService()
    
    if await llm.health_check():
        logger.info("ollama_connected", host=settings.ollama_host)
    else:
        logger.warning(
            "ollama_not_available",
            host=settings.ollama_host,
            message="Ollama 서버에 연결할 수 없습니다. LLM 기능이 제한됩니다."
        )
    
    yield
    
    # Shutdown
    logger.info("server_shutting_down")


# FastAPI 앱 생성
app = FastAPI(
    title="Ontology-driven Reasoning & Action Platform",
    description="""
## 시스템 개요

다양한 도메인(기술, 정책, 의료, 제조, 금융 등)에 대해:
- 도메인 문서/데이터를 구조적으로 해석
- 온톨로지로 누적
- 사용자 질의에 대해 추론/행동(Action) 생성
- RL 기반 Validator로 검증

### 주요 기능

1. **문서 처리** (`/documents`)
   - PDF, DOCX, HTML, Markdown 등 다양한 형식 지원
   - Fragment 추출 (Fact, Mechanism, Condition, Outcome)
   - Entity 정규화

2. **온톨로지 관리** (`/ontology`)
   - Entity/Relation CRUD
   - 서브그래프 추출
   - 인과 관계 분석

3. **질의 처리** (`/query`)
   - Intent 분류 (정보조회/분석/실행/생성)
   - RAG 기반 응답 생성
   - 스트리밍 응답 지원

4. **Action 관리** (`/actions`)
   - Action 생성/검증/실행
   - 실행 가능성 평가
   - Admin 승인 워크플로우
   - 사용자 피드백 (RL reward)

### 아키텍처

```
[Document] → [Parser] → [Extractor(LLM)] → [Validator(RL)] → [Ontology]
                                                                   ↓
[Query] → [Intent Classifier] → [Router] → [Action/RAG] → [Response]
```
""",
    version="4.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 에러 핸들러
@app.exception_handler(OntologyError)
async def ontology_error_handler(request: Request, exc: OntologyError):
    """온톨로지 에러 핸들러"""
    logger.error(
        "ontology_error",
        error_code=exc.code,
        message=exc.message,
        path=str(request.url)
    )
    
    return JSONResponse(
        status_code=400 if exc.recoverable else 500,
        content=exc.to_dict()
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    """일반 에러 핸들러"""
    logger.error(
        "unhandled_error",
        error_type=type(exc).__name__,
        message=str(exc),
        path=str(request.url)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "서버 내부 오류가 발생했습니다.",
            "details": {"type": type(exc).__name__} if settings.debug else {}
        }
    )


# 라우터 등록
app.include_router(documents_router)
app.include_router(ontology_router)
app.include_router(query_router)
app.include_router(actions_router)


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """서버 상태 확인"""
    from src.services.llm_service import LLMService
    
    llm = LLMService()
    ollama_status = await llm.health_check()
    
    return {
        "status": "healthy",
        "ollama": {
            "connected": ollama_status,
            "host": settings.ollama_host,
            "model": settings.ollama_model,
        },
        "version": "4.1.0",
    }


@app.get("/", tags=["System"])
async def root():
    """API 루트"""
    return {
        "name": "Ontology-driven Reasoning & Action Platform",
        "version": "4.1.0",
        "docs": "/docs",
        "health": "/health",
    }


# CLI 실행
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

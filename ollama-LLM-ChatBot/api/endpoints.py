"""
FastAPI 엔드포인트 (최적화 버전)

빠른 응답을 위한 간소화된 API
"""

import os
import uuid
import tempfile
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 핵심 모듈들 임포트
from core.pdf_processor import PDFProcessor, TextChunk
from core.vector_store import HybridVectorStore, VectorStoreInterface
from core.question_analyzer import QuestionAnalyzer, AnalyzedQuestion, ConversationItem
from core.answer_generator import AnswerGenerator, Answer, ModelType, GenerationConfig
from core.sql_generator import SQLGenerator, DatabaseSchema, SQLQuery
from core.fast_cache import get_all_cache_stats, clear_all_caches
from core.query_router import QueryRouter, QueryRoute
from utils.chatbot_logger import chatbot_logger, QuestionType

logger = logging.getLogger(__name__)

# Pydantic 모델들 (단순화)
class QuestionRequest(BaseModel):
    """질문 요청 모델"""
    question: str = Field(..., description="사용자 질문")
    pdf_id: str = Field("", description="PDF 문서 식별자")
    user_id: str = Field("", description="사용자 식별자")
    use_conversation_context: bool = Field(True, description="이전 대화 컨텍스트 사용 여부")
    max_chunks: int = Field(5, description="검색할 최대 청크 수")

class QuestionResponse(BaseModel):
    """질문 응답 모델"""
    answer: str = Field(..., description="생성된 답변")
    confidence_score: float = Field(..., description="답변 신뢰도")
    used_chunks: List[str] = Field(..., description="사용된 문서 청크 ID들")
    generation_time: float = Field(..., description="답변 생성 시간 (초)")
    question_type: str = Field(..., description="질문 유형")
    model_name: str = Field(..., description="사용된 모델 이름")
    pipeline_type: str = Field("basic", description="사용된 파이프라인 타입")
    sql_query: Optional[str] = Field(None, description="생성된 SQL 쿼리")

class PDFUploadResponse(BaseModel):
    """PDF 업로드 응답 모델"""
    pdf_id: str = Field(..., description="생성된 PDF 식별자")
    filename: str = Field(..., description="업로드된 파일명")
    total_pages: int = Field(..., description="총 페이지 수")
    total_chunks: int = Field(..., description="생성된 청크 수")
    processing_time: float = Field(..., description="처리 시간 (초)")

class SystemStatusResponse(BaseModel):
    """시스템 상태 응답 모델"""
    status: str = Field(..., description="시스템 상태")
    model_loaded: bool = Field(..., description="모델 로드 상태")
    total_pdfs: int = Field(..., description="등록된 PDF 수")
    total_chunks: int = Field(..., description="총 청크 수")
    memory_usage: Dict[str, Any] = Field(..., description="메모리 사용량")

# FastAPI 앱 초기화
app = FastAPI(
    title="IFRO 챗봇 API",
    description="IFRO 교통 시스템 챗봇 API (최적화 버전)",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 객체들
pdf_processor: Optional[PDFProcessor] = None
vector_store: Optional[VectorStoreInterface] = None
question_analyzer: Optional[QuestionAnalyzer] = None
answer_generator: Optional[AnswerGenerator] = None
sql_generator: Optional[SQLGenerator] = None
query_router: Optional[QueryRouter] = None

# PDF 메타데이터 저장소
pdf_metadata: Dict[str, Dict] = {}

# 의존성 함수들
def get_pdf_processor() -> PDFProcessor:
    """PDF 처리기 의존성"""
    global pdf_processor
    if pdf_processor is None:
        pdf_processor = PDFProcessor()
    return pdf_processor

def get_vector_store() -> VectorStoreInterface:
    """벡터 저장소 의존성"""
    global vector_store
    if vector_store is None:
        vector_store = HybridVectorStore()
    return vector_store

def get_question_analyzer() -> QuestionAnalyzer:
    """질문 분석기 의존성"""
    global question_analyzer
    if question_analyzer is None:
        question_analyzer = QuestionAnalyzer()
    return question_analyzer

def get_answer_generator() -> AnswerGenerator:
    """답변 생성기 의존성"""
    global answer_generator
    if answer_generator is None:
        answer_generator = AnswerGenerator()
    return answer_generator

def get_sql_generator() -> SQLGenerator:
    """SQL 생성기 의존성"""
    global sql_generator
    if sql_generator is None:
        sql_generator = SQLGenerator()
    return sql_generator

def get_query_router() -> QueryRouter:
    """쿼리 라우터 의존성"""
    global query_router
    if query_router is None:
        query_router = QueryRouter()
    return query_router

# API 엔드포인트들
@app.get("/", response_model=Dict[str, str])
async def root():
    """루트 엔드포인트"""
    return {"message": "IFRO 챗봇 API 서버가 실행 중입니다."}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/upload-pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
    vector_store: VectorStoreInterface = Depends(get_vector_store)
):
    """PDF 업로드 및 처리"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # PDF 처리
        start_time = datetime.now()
        pdf_id = str(uuid.uuid4())
        
        # PDF 처리 및 청크 생성
        chunks = pdf_processor.process_pdf(temp_file_path, pdf_id)
        
        # 벡터 저장소에 저장
        vector_store.add_chunks(chunks)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 메타데이터 저장
        pdf_metadata[pdf_id] = {
            "filename": file.filename,
            "total_pages": len(chunks),
            "upload_time": datetime.now().isoformat(),
            "file_size": len(content)
        }
        
        # 임시 파일 삭제
        os.unlink(temp_file_path)
        
        return PDFUploadResponse(
            pdf_id=pdf_id,
            filename=file.filename,
            total_pages=len(chunks),
            total_chunks=len(chunks),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"PDF 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"PDF 처리 중 오류 발생: {str(e)}")

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    vector_store: VectorStoreInterface = Depends(get_vector_store),
    question_analyzer: QuestionAnalyzer = Depends(get_question_analyzer),
    answer_generator: AnswerGenerator = Depends(get_answer_generator),
    sql_generator: SQLGenerator = Depends(get_sql_generator),
    query_router: QueryRouter = Depends(get_query_router)
):
    """질문에 대한 답변 생성 (최적화)"""
    
    try:
        # 🚀 SBERT 기반 쿼리 라우팅
        route_result = query_router.route_query(request.question)
        logger.info(f"📍 라우팅 결과: {route_result.route.value} (신뢰도: {route_result.confidence:.3f})")
        
        # 인사말 처리 (가장 빠른 응답)
        if route_result.route == QueryRoute.GREETING:
            return QuestionResponse(
                answer="안녕하세요! IFRO 교통 시스템에 대해 궁금한 것이 있으시면 언제든 물어보세요.",
                confidence_score=route_result.confidence,
                used_chunks=[],
                generation_time=0.001,
                question_type="greeting",
                model_name="greeting_template",
                pipeline_type="greeting",
                sql_query=None
            )
        
        # SQL 쿼리 처리 (규칙 기반 빠른 처리)
        if route_result.route == QueryRoute.SQL_QUERY:
            try:
                # 기본 스키마 정의
                schema = DatabaseSchema(
                    table_name="traffic_intersection",
                    columns=[
                        {"name": "id", "type": "INTEGER", "description": "교차로 ID"},
                        {"name": "name", "type": "TEXT", "description": "교차로 이름"},
                        {"name": "location", "type": "TEXT", "description": "위치"},
                        {"name": "traffic_volume", "type": "INTEGER", "description": "교통량"},
                        {"name": "district", "type": "TEXT", "description": "구역"}
                    ]
                )
                
                # 규칙 기반 SQL 생성
                sql_result = sql_generator.generate_sql(request.question, schema)
                
                if sql_result.is_valid:
                    # SQL 실행
                    execution_result = sql_generator.execute_sql(sql_result)
                    
                    if execution_result['success']:
                        # 데이터를 자연어로 변환
                        data_summary = f"조회된 데이터: {execution_result.get('row_count', 0)}건"
                        if execution_result.get('data'):
                            data_summary = f"총 {len(execution_result['data'])}건의 결과를 찾았습니다."
                        
                        return QuestionResponse(
                            answer=data_summary,
                            confidence_score=sql_result.confidence_score,
                            used_chunks=[],
                            generation_time=sql_result.execution_time,
                            question_type="sql_query",
                            model_name=sql_result.model_name,
                            pipeline_type="sql",
                            sql_query=sql_result.query
                        )
                    else:
                        logger.warning(f"SQL 실행 실패: {execution_result.get('error')}")
                        # PDF 검색으로 폴백
                        pass
                else:
                    logger.warning(f"SQL 검증 실패: {sql_result.error_message}")
                    # PDF 검색으로 폴백
                    pass
            except Exception as sql_error:
                logger.warning(f"SQL 처리 실패, PDF 검색으로 폴백: {sql_error}")
                # PDF 검색으로 폴백
                pass
        
        # PDF 검색 처리 (기본 모드)
        logger.info("📄 PDF 검색 모드로 처리")
        
        # 1. 질문 분석
        analyzed_question = question_analyzer.analyze_question(
            request.question,
            use_conversation_context=request.use_conversation_context
        )
        
        # 2. 관련 문서 검색
        query_embedding = analyzed_question.embedding
        relevant_chunks = vector_store.search(
            query_embedding,
            k=request.max_chunks
        )
        
        # 3. 답변 생성
        answer = answer_generator.generate_answer(
            analyzed_question,
            relevant_chunks,
            conversation_history=None,
            pdf_id=request.pdf_id
        )
        
        # 4. 대화 히스토리에 추가
        conversation_item = ConversationItem(
            question=request.question,
            answer=answer.content,
            timestamp=datetime.now(),
            question_type=analyzed_question.question_type,
            relevant_chunks=answer.used_chunks,
            confidence_score=answer.confidence_score
        )
        question_analyzer.add_conversation_item(conversation_item)
        
        # 5. API 로깅
        try:
            chatbot_logger.log_question(
                question=request.question,
                answer=answer.content,
                question_type=QuestionType.PDF,
                pipeline_type=route_result.route.value,
                generation_time=answer.generation_time,
                confidence_score=answer.confidence_score,
                model_name=answer.model_name,
                user_id=request.user_id
            )
        except Exception as log_error:
            logger.warning(f"API 로깅 중 오류 발생: {log_error}")
        
        return QuestionResponse(
            answer=answer.content,
            confidence_score=answer.confidence_score,
            used_chunks=answer.used_chunks,
            generation_time=answer.generation_time,
            question_type=analyzed_question.question_type.value,
            model_name=answer.model_name,
            pipeline_type=route_result.route.value,
            sql_query=None
        )
        
    except Exception as e:
        logger.error(f"질문 처리 실패: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"질문 처리 중 오류 발생: {str(e)}")

@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """시스템 상태 조회"""
    try:
        import psutil
        
        # 메모리 사용량
        memory = psutil.virtual_memory()
        memory_usage = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # 모델 로드 상태
        model_loaded = (
            answer_generator is not None and 
            question_analyzer is not None and 
            vector_store is not None
        )
        
        # PDF 및 청크 수
        total_pdfs = len(pdf_metadata)
        total_chunks = sum(len(chunks) for chunks in vector_store.get_all_chunks()) if vector_store else 0
        
        return SystemStatusResponse(
            status="running",
            model_loaded=model_loaded,
            total_pdfs=total_pdfs,
            total_chunks=total_chunks,
            memory_usage=memory_usage
        )
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"시스템 상태 조회 실패: {str(e)}")

@app.get("/cache/stats")
async def get_cache_stats():
    """캐시 통계 조회"""
    try:
        stats = get_all_cache_stats()
        return {"status": "success", "cache_stats": stats}
    except Exception as e:
        logger.error(f"캐시 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"캐시 통계 조회 실패: {str(e)}")

@app.post("/cache/clear")
async def clear_cache():
    """모든 캐시 삭제"""
    try:
        clear_all_caches()
        return {"message": "모든 캐시가 삭제되었습니다."}
    except Exception as e:
        logger.error(f"캐시 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"캐시 삭제 실패: {str(e)}")

@app.get("/router/stats")
async def get_router_stats(
    query_router: QueryRouter = Depends(get_query_router)
):
    """쿼리 라우터 통계"""
    try:
        stats = query_router.get_route_statistics()
        return {
            "status": "success",
            "router_stats": stats
        }
    except Exception as e:
        logger.error(f"라우터 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"라우터 통계 조회 실패: {str(e)}")

@app.post("/router/test")
async def test_routing(
    question: str,
    query_router: QueryRouter = Depends(get_query_router)
):
    """라우팅 테스트"""
    try:
        result = query_router.route_query(question)
        return {
            "question": question,
            "route": result.route.value,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "metadata": result.metadata
        }
    except Exception as e:
        logger.error(f"라우팅 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"라우팅 테스트 실패: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)

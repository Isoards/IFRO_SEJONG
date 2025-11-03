"""
FastAPI Application - API 서버

RESTful API 엔드포인트를 제공합니다.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Request, APIRouter, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from config.pipeline_config import PipelineConfig
from config.environment import get_env_config
from config.model_config import LLMModelConfig
from modules.core.logger import setup_logging, get_logger
from modules.core.exceptions import ChatbotException
from modules.pipeline.rag_pipeline import RAGPipeline
from modules.core.types import Chunk
from modules.analysis.question_analyzer import QuestionAnalyzer
from modules.generation.ollama_manager import OllamaManager
from modules.document.loader import DocumentLoader

# 로깅 설정
env_config = get_env_config()
setup_logging(
    log_dir=env_config.log_dir,
    log_level=env_config.log_level,
    log_format=env_config.log_format,
)

logger = get_logger(__name__)

# FastAPI 앱
app = FastAPI(
    title="Chatbot v6 API",
    description="정수처리 챗봇 API (4가지 원칙 준수)",
    version="6.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 파이프라인 (초기화는 startup에서)
pipeline: Optional[RAGPipeline] = None
question_analyzer: Optional[QuestionAnalyzer] = None

# PDF 처리 작업 상태 저장
pdf_processing_status: Dict[str, Any] = {
    "status": "idle",  # idle, processing, completed, error
    "progress": 0,
    "message": "",
    "processed_files": [],
    "skipped_files": [],
    "total_chunks": 0,
    "processing_time_seconds": 0,
}

# 인사말 응답 리스트
GREETING_RESPONSES = [
    "안녕하세요! 👋 서울 교통 AI 챗봇입니다. 무엇을 도와드릴까요?",
    "안녕하세요! 😊 교통 관련 질문이나 문서 검색을 도와드리겠습니다.",
    "안녕하세요! 🚗 교통 정책, 대중교통 정보, 도로 안내 등 무엇이든 물어보세요!",
    "반갑습니다! 🤖 AI 기반으로 교통 문서에서 답변을 찾아드립니다.",
    "안녕하세요! 🚌 교통 기술, 정책 정보, 지침 검색 등을 도와드립니다.",
]

# API 라우터 생성 (/api 프리픽스용)
api_router = APIRouter(prefix="/api")


# Request/Response 모델
class QuestionRequest(BaseModel):
    question: str
    top_k: int = 50


class Source(BaseModel):
    text: str
    score: float
    rank: int
    filename: str
    page: Optional[int] = None
    start: int = 0  # 프록시 호환성
    length: int = 0  # 프록시 호환성
    calibrated_conf: float = 0.0  # 프록시 호환성


class AnswerResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[Source]
    metrics: Dict[str, Any]
    fallback_used: Optional[str] = None  # 프록시 호환성


class PDFUploadNotification(BaseModel):
    """PDF 업로드 알림 요청"""
    filename: str
    file_path: str
    timestamp: Optional[str] = None
    source: str = "backend_api"


class TextEmbeddingRequest(BaseModel):
    """텍스트 직접 임베딩 요청"""
    text: str
    metadata: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None  # Backend 콜백 URL


class PDFExtractionRequest(BaseModel):
    """PDF 텍스트 추출 및 임베딩 요청"""
    pdf_data: Optional[str] = None  # Base64 인코딩된 PDF 데이터
    pdf_path: Optional[str] = None  # PDF 파일 경로 (선택사항)
    filename: str
    metadata: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global pipeline, question_analyzer
    
    logger.info("[STARTUP] API server starting up")
    
    try:
        # Ollama 서버 연결 및 모델 자동 설치
        logger.info("[STARTUP] Checking Ollama server and model availability...")
        ollama_url = f"http://{LLMModelConfig().host}:{LLMModelConfig().port}"
        ollama_manager = OllamaManager(base_url=ollama_url)
        
        # Ollama 서버가 준비될 때까지 대기 (최대 120초)
        max_wait_time = 120
        wait_interval = 2
        waited = 0
        ollama_ready = False
        
        while waited < max_wait_time:
            if ollama_manager.check_ollama_running():
                logger.info("[STARTUP] ✅ Ollama server is running")
                ollama_ready = True
                break
            logger.info(f"[STARTUP] ⏳ Waiting for Ollama server... ({waited}/{max_wait_time}s)")
            time.sleep(wait_interval)
            waited += wait_interval
        
        if not ollama_ready:
            logger.warning("[STARTUP] ⚠️ Ollama server not available after 120s - will continue with offline mode")
        else:
            logger.info("[STARTUP] Ollama server ready - proceeding with model checks")
        
        # 설정 로드
        config_path = project_root / "config" / "default.yaml"
        pipeline_config = PipelineConfig.from_file(config_path)
        
        # 도메인 사전 경로 설정
        domain_dict_path = project_root / "data" / "domain_dictionary.json"
        
        # QuestionAnalyzer 초기화
        question_analyzer = QuestionAnalyzer(
            domain_dict_path=str(domain_dict_path) if domain_dict_path.exists() else None
        )
        
        # PDF 문서 자동 로드 및 임베딩
        data_dir = project_root / "data"
        chunks = []
        
        try:
            logger.info(f"[STARTUP] Loading documents from: {data_dir}")
            doc_loader = DocumentLoader(str(data_dir))
            
            # PDF 파일 확인
            pdf_files = list(data_dir.glob("*.pdf")) + list(data_dir.glob("*.PDF"))
            
            if pdf_files:
                logger.info(f"[STARTUP] Found {len(pdf_files)} PDF file(s): {[f.name for f in pdf_files]}")
                try:
                    chunks = doc_loader.load_from_directory(use_cache=True)
                    logger.info(f"[STARTUP] ✅ Loaded {len(chunks)} chunks from {len(pdf_files)} document(s)")
                except Exception as e:
                    logger.error(f"[STARTUP] Failed to load documents: {e}", exc_info=True)
                    logger.warning("[STARTUP] Falling back to dummy chunks")
                    chunks = []
            else:
                logger.warning(f"[STARTUP] No PDF files found in {data_dir}")
        
        except Exception as e:
            logger.error(f"[STARTUP] Document loading error: {e}", exc_info=True)
            logger.warning("[STARTUP] Falling back to dummy chunks")
            chunks = []
        
        # 문서가 없으면 더미 청크 사용
        if not chunks:
            logger.warning("[STARTUP] No chunks loaded, using dummy chunks")
            chunks = [
                Chunk(
                    doc_id="demo",
                    filename="demo.pdf",
                    page=1,
                    start_offset=0,
                    length=100,
                    text="문서가 업로드되지 않았습니다. PDF 파일을 data/ 디렉토리에 추가해주세요.",
                ),
            ]
        
        # 파이프라인 초기화 (자동 임베딩 포함)
        logger.info("[STARTUP] Initializing RAG pipeline with embedding... (evaluation mode enabled)")
        pipeline = RAGPipeline(
            chunks=chunks,
            pipeline_config=pipeline_config,
            evaluation_mode=True,  # 평가 모드 활성화
        )
        
        logger.info(f"[STARTUP] ✅ API server started successfully with {len(chunks)} chunks")
    
    except Exception as e:
        logger.error(f"[STARTUP] Failed to initialize pipeline: {e}", exc_info=True)
        logger.warning("[STARTUP] Server will continue running in degraded mode")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    logger.info("[SHUTDOWN] API server shutting down")


@app.get("/healthz")
async def health_check():
    """헬스 체크"""
    logger.debug(f"[HEALTH] Health check requested")
    return {
        "status": "healthy",
        "service": "chatbot-v6",
        "version": "6.0.0",
    }


@app.get("/status")
async def get_status():
    """AI 서비스 상태 확인"""
    logger.debug(f"[STATUS] Status check requested")
    
    if not pipeline:
        logger.warning(f"[STATUS] Pipeline not initialized")
        return {
            "status": "initializing",
            "ai_available": False,
            "model_loaded": False,
            "total_pdfs": 0,
            "total_chunks": 0,
        }
    
    # 문서 통계
    total_chunks = len(pipeline.chunks) if hasattr(pipeline, 'chunks') else 0
    unique_files = len(set(c.filename for c in pipeline.chunks)) if hasattr(pipeline, 'chunks') else 0
    
    logger.debug(f"[STATUS] Pipeline ready - chunks: {total_chunks}, files: {unique_files}")
    
    return {
        "status": "ok",
        "ai_available": True,
        "model_loaded": True,
        "total_pdfs": unique_files,
        "total_chunks": total_chunks,
    }


class ProcessPDFsResponse(BaseModel):
    success: bool
    message: str
    processed_files: List[str]
    skipped_files: List[str]
    total_chunks: int
    processing_time_seconds: float


def process_pdfs_background():
    """백그라운드에서 PDF 처리 (병렬 임베딩 포함)"""
    global pipeline, pdf_processing_status
    
    try:
        pdf_processing_status["status"] = "processing"
        pdf_processing_status["progress"] = 0
        pdf_processing_status["message"] = "PDF 처리 시작..."
        
        if not pipeline:
            pdf_processing_status["status"] = "error"
            pdf_processing_status["message"] = "Pipeline not initialized"
            return
        
        start_time = time.time()
        data_dir = project_root / "data"
        cache_path = data_dir / "chunks_cache.pkl"
        
        # 기존 처리된 파일 목록 확인 (캐시에서)
        processed_files = set()
        if cache_path.exists():
            try:
                import pickle
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                    cached_chunks = cached_data.get("chunks", [])
                processed_files = {c.filename for c in cached_chunks if isinstance(c, Chunk)}
                logger.info(f"Found {len(processed_files)} already processed files in cache")
            except Exception as e:
                logger.warning(f"Failed to load cache for comparison: {e}")
        
        # 현재 디렉토리의 PDF 파일 목록
        pdf_files = list(data_dir.glob("*.pdf")) + list(data_dir.glob("*.PDF"))
        
        # 처리되지 않은 파일 필터링
        new_files = [f for f in pdf_files if f.name not in processed_files]
        skipped_files = [f.name for f in pdf_files if f.name in processed_files]
        
        pdf_processing_status["progress"] = 10
        pdf_processing_status["message"] = f"{len(new_files)}개 새 PDF 파일 발견"
        
        if not new_files:
            pdf_processing_status["status"] = "completed"
            pdf_processing_status["message"] = f"처리할 새 PDF 파일이 없습니다. (이미 처리된 파일: {len(skipped_files)}개)"
            pdf_processing_status["skipped_files"] = skipped_files
            pdf_processing_status["total_chunks"] = len(pipeline.chunks) if hasattr(pipeline, 'chunks') else 0
            pdf_processing_status["processing_time_seconds"] = time.time() - start_time
            return
        
        logger.info(f"Processing {len(new_files)} new PDF file(s): {[f.name for f in new_files]}")
        
        # DocumentLoader로 새 파일들 병렬 처리
        pdf_processing_status["progress"] = 20
        pdf_processing_status["message"] = "PDF 텍스트 추출 중..."
        
        doc_loader = DocumentLoader(str(data_dir))
        new_chunks = []
        
        # ThreadPoolExecutor로 병렬 처리
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for pdf_path in new_files:
                future = executor.submit(doc_loader._load_pdf, pdf_path)
                futures.append((future, pdf_path))
            
            for i, (future, pdf_path) in enumerate(futures):
                try:
                    chunks = future.result()
                    new_chunks.extend(chunks)
                    logger.info(f"Processed {pdf_path.name}: {len(chunks)} chunks")
                    
                    progress = 20 + int((i + 1) / len(futures) * 30)
                    pdf_processing_status["progress"] = progress
                    pdf_processing_status["message"] = f"PDF 처리 중... ({i+1}/{len(futures)}): {pdf_path.name}"
                except Exception as e:
                    logger.error(f"Failed to process {pdf_path.name}: {e}", exc_info=True)
                    continue
        
        pdf_processing_status["progress"] = 50
        pdf_processing_status["message"] = "임베딩 준비 중..."
        
        # 기존 청크와 새 청크 병합 후 캐시 저장
        if new_chunks:
            # 기존 캐시에서 청크 로드
            existing_chunks = []
            if hasattr(pipeline, 'chunks'):
                existing_chunks = pipeline.chunks
            
            # 모든 청크 병합
            all_chunks_for_cache = existing_chunks + new_chunks
            
            # 캐시에 저장
            doc_loader.chunks = all_chunks_for_cache
            doc_loader.save_to_cache(str(cache_path))
            logger.info(f"Cache updated: {len(existing_chunks)} existing + {len(new_chunks)} new = {len(all_chunks_for_cache)} total chunks")
        
        if not new_chunks:
            pdf_processing_status["status"] = "error"
            pdf_processing_status["message"] = "새 PDF 파일에서 청크를 추출할 수 없었습니다."
            return
        
        # 기존 청크와 새 청크 병합
        if hasattr(pipeline, 'chunks'):
            all_chunks = pipeline.chunks + new_chunks
        else:
            all_chunks = new_chunks
        
        # 파이프라인 재초기화 (새 청크 포함) - 임베딩은 파이프라인 초기화 시 자동으로 수행됨
        pdf_processing_status["progress"] = 60
        pdf_processing_status["message"] = "임베딩 및 벡터 저장 중... (이 작업은 시간이 걸릴 수 있습니다)"
        
        from config.pipeline_config import PipelineConfig
        config_path = project_root / "config" / "default.yaml"
        pipeline_config = PipelineConfig.from_file(config_path)
        
        # 파이프라인 재초기화 (임베딩 자동 수행)
        pipeline = RAGPipeline(
            chunks=all_chunks,
            pipeline_config=pipeline_config,
        )
        
        processing_time = time.time() - start_time
        
        # 완료 상태 업데이트
        pdf_processing_status["status"] = "completed"
        pdf_processing_status["progress"] = 100
        pdf_processing_status["message"] = f"{len(new_files)}개 PDF 파일 처리 완료"
        pdf_processing_status["processed_files"] = [f.name for f in new_files]
        pdf_processing_status["skipped_files"] = skipped_files
        pdf_processing_status["total_chunks"] = len(all_chunks)
        pdf_processing_status["processing_time_seconds"] = processing_time
        
        logger.info(
            f"Successfully processed {len(new_files)} PDF file(s)",
            extra={
                "processed_files": [f.name for f in new_files],
                "total_chunks": len(all_chunks),
                "new_chunks": len(new_chunks),
                "processing_time": processing_time
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to process PDFs: {e}", exc_info=True)
        pdf_processing_status["status"] = "error"
        pdf_processing_status["message"] = f"PDF 처리 중 오류 발생: {str(e)}"


@app.post("/api/process-pdfs")
async def start_process_pdfs(background_tasks: BackgroundTasks):
    """PDF 처리 시작 (비동기)"""
    global pdf_processing_status
    
    # 이미 처리 중이면 시작하지 않음
    if pdf_processing_status["status"] == "processing":
        return {
            "success": True,
            "message": "이미 처리 중입니다.",
            "status": "processing"
        }
    
    # 백그라운드 작업 시작
    background_tasks.add_task(process_pdfs_background)
    
    return {
        "success": True,
        "message": "PDF 처리가 시작되었습니다.",
        "status": "processing"
    }


@app.get("/api/process-pdfs/status")
async def get_process_pdfs_status():
    """PDF 처리 상태 확인"""
    return pdf_processing_status


# 기존 엔드포인트 (하위 호환성을 위해 유지)
@app.post("/ask", response_model=AnswerResponse)
async def ask_question(req: Request, request: QuestionRequest):
    """
    질문에 대한 답변
    
    Args:
        request: 질문 요청
        
    Returns:
        답변 응답
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    start_time = time.time()
    session_id = req.headers.get('X-Session-ID', str(uuid.uuid4()))
    
    try:
        logger.info(
            f"[QUESTION] Received question",
            extra={
                "question": request.question,
                "session_id": session_id,
                "top_k": request.top_k,
                "timestamp": time.time()
            }
        )
        
        # 인사말 체크
        if question_analyzer and question_analyzer.is_greeting(request.question):
            logger.info(
                f"[GREETING] Detected, returning preset response",
                extra={
                    "question": request.question,
                    "session_id": session_id
                }
            )
            
            import random
            greeting_response = random.choice(GREETING_RESPONSES)
            processing_time = time.time() - start_time
            
            # 인사말 응답 생성
            from modules.core.types import Answer
            
            answer = Answer(
                text=greeting_response,
                confidence=1.0,
                sources=[],
                metrics={
                    "total_time_ms": int(processing_time * 1000),
                    "is_greeting": True,
                    "llm_used": False,
                }
            )
        else:
            # 일반 질문 - 파이프라인 실행
            answer = pipeline.ask(
                question=request.question,
                top_k=request.top_k,
            )
            
            processing_time = time.time() - start_time
        
        # 응답 변환 (인사말은 sources가 없을 수 있음)
        sources = [
            Source(
                text=span.chunk.text[:200],
                score=span.score,
                rank=span.rank,
                filename=span.chunk.filename,
                page=span.chunk.page,
                start=span.chunk.start_offset,
                length=span.chunk.length,
                calibrated_conf=span.calibrated_conf if hasattr(span, 'calibrated_conf') else span.score,
            )
            for span in answer.sources[:5]
        ] if answer.sources else []
        
        response = AnswerResponse(
            answer=answer.text,
            confidence=answer.confidence,
            sources=sources,
            metrics={
                **answer.metrics,
                "processing_time": processing_time,
                "session_id": session_id,
            },
            fallback_used=answer.fallback_used,
        )
        
        logger.info(
            f"[ANSWER] Generated successfully",
            extra={
                "question": request.question,
                "answer": answer.text[:200] + "..." if len(answer.text) > 200 else answer.text,
                "confidence": answer.confidence,
                "processing_time": processing_time,
                "session_id": session_id,
                "sources_count": len(answer.sources),
                "metrics": answer.metrics
            }
        )
        
        return response
    
    except ChatbotException as e:
        logger.error(f"Chatbot error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": e.to_dict(),
                "message": str(e),
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# /api 프리픽스를 사용하는 엔드포인트들 (프록시 서버 호환)
@api_router.post("/ask", response_model=AnswerResponse)
async def ask_question_api(req: Request, request: QuestionRequest):
    """질문에 대한 답변 (API 프리픽스 버전)"""
    # 기존 함수와 동일한 로직 재사용
    return await ask_question(req, request)


@api_router.post("/qa/batch")
async def batch_questions_api(req: Request, items: List[Dict[str, Any]], mode: str = "accuracy"):
    """배치 질문 답변 (프록시 호환성)"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    results = []
    start_time = time.time()
    
    try:
        for item in items:
            question = item.get('question', '')
            item_id = item.get('id', None)
            
            if not question:
                results.append({
                    "id": item_id,
                    "error": "No question provided"
                })
                continue
            
            try:
                # 질문 처리
                answer = pipeline.ask(
                    question=question,
                    top_k=50,
                )
                
                # 소스 변환
                sources = [
                    Source(
                        text=span.chunk.text[:200],
                        score=span.score,
                        rank=span.rank,
                        filename=span.chunk.filename,
                        page=span.chunk.page,
                        start=span.chunk.start_offset,
                        length=span.chunk.length,
                        calibrated_conf=span.calibrated_conf if hasattr(span, 'calibrated_conf') else span.score,
                    )
                    for span in answer.sources[:5]
                ] if answer.sources else []
                
                results.append({
                    "id": item_id,
                    "question": question,
                    "answer": answer.text,
                    "confidence": answer.confidence,
                    "sources": sources,
                    "metrics": answer.metrics,
                    "fallback_used": answer.fallback_used,
                })
                
            except Exception as e:
                logger.error(f"배치 항목 처리 오류: {str(e)}", exc_info=True)
                results.append({
                    "id": item_id,
                    "question": question,
                    "error": str(e)
                })
        
        return {
            "results": results,
            "config_hash": pipeline.pipeline_config.config_hash() if hasattr(pipeline, 'pipeline_config') else "",
        }
        
    except Exception as e:
        logger.error(f"배치 처리 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/healthz")
async def health_check_api():
    """헬스 체크 (API 프리픽스 버전)"""
    return await health_check()


@api_router.get("/status")
async def get_status_api():
    """AI 서비스 상태 확인 (API 프리픽스 버전)"""
    return await get_status()


@app.post("/api/pdf/notify-upload")
async def notify_pdf_upload(notification: PDFUploadNotification):
    """
    백엔드에서 PDF 업로드 알림을 받아 처리합니다.
    새 PDF를 로드하고 벡터 DB에 추가한 후 파이프라인을 재로드합니다.
    """
    global pipeline
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        logger.info(f"📥 PDF 업로드 알림 수신: {notification.filename}")
        
        file_path = notification.file_path
        if not Path(file_path).exists():
            logger.error(f"❌ PDF 파일을 찾을 수 없음: {file_path}")
            raise HTTPException(status_code=404, detail=f"PDF 파일을 찾을 수 없습니다: {file_path}")
        
        # Step 1: 새 PDF 파일 로드
        logger.info(f"📖 PDF 파일 로드 중: {notification.filename}")
        doc_loader = DocumentLoader(str(Path(file_path).parent))
        
        try:
            new_chunks = doc_loader._load_pdf(Path(file_path))
            logger.info(f"✅ {len(new_chunks)} 개의 청크 추출 완료")
        except Exception as e:
            logger.error(f"❌ PDF 로드 실패: {str(e)}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"PDF 로드 실패: {str(e)}")
        
        if not new_chunks:
            logger.warning(f"⚠️ {notification.filename}에서 청크를 추출할 수 없습니다.")
            return {
                "status": "warning",
                "message": f"PDF 파일에서 텍스트를 추출할 수 없습니다: {notification.filename}"
            }
        
        # Step 2: 기존 청크와 병합
        logger.info(f"🔗 기존 청크와 병합 중...")
        existing_chunks = pipeline.chunks if hasattr(pipeline, 'chunks') else []
        all_chunks = existing_chunks + new_chunks
        
        logger.info(f"📊 기존: {len(existing_chunks)}, 신규: {len(new_chunks)}, 합계: {len(all_chunks)}")
        
        # Step 3: 캐시 업데이트
        logger.info(f"💾 캐시 업데이트 중...")
        cache_path = project_root / "data" / "chunks_cache.pkl"
        try:
            doc_loader.chunks = all_chunks
            doc_loader.save_to_cache(str(cache_path))
            logger.info(f"✅ 캐시 저장 완료: {cache_path}")
        except Exception as e:
            logger.error(f"⚠️ 캐시 저장 실패 (계속 진행): {str(e)}")
        
        # Step 4: 파이프라인 재로드 (새 PDF + 임베딩)
        logger.info(f"🔄 파이프라인 재로드 중 (임베딩 계산 중)...")
        try:
            config_path = project_root / "config" / "default.yaml"
            pipeline_config = PipelineConfig.from_file(config_path)
            
            # 새 파이프라인 생성 (자동 임베딩)
            pipeline = RAGPipeline(
                chunks=all_chunks,
                pipeline_config=pipeline_config,
                evaluation_mode=True,
            )
            logger.info(f"✅ 파이프라인 재로드 완료")
            logger.info(f"📈 최종 청크 수: {len(all_chunks)}")
            
        except Exception as e:
            logger.error(f"❌ 파이프라인 재로드 실패: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"파이프라인 재로드 실패: {str(e)}")
        
        logger.info(f"✅ PDF 업로드 처리 완료: {notification.filename}")
        
        return {
            "status": "success",
            "message": f"PDF 파일이 성공적으로 처리되었습니다",
            "filename": notification.filename,
            "new_chunks": len(new_chunks),
            "total_chunks": len(all_chunks),
            "processing_timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PDF 업로드 처리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PDF 업로드 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/text/add-to-vectordb")
async def add_text_to_vectordb(request: TextEmbeddingRequest):
    """
    받은 텍스트를 즉시 임베딩하고 벡터 DB에 추가합니다.
    파일 저장 없이 순수 임베딩 처리만 수행합니다.
    
    Args:
        request: TextEmbeddingRequest
            - text: 임베딩할 텍스트
            - metadata: 메타데이터 (선택사항)
    """
    global pipeline
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        text_content = request.text.strip()
        metadata = request.metadata or {}
        
        logger.info(f"📥 텍스트 임베딩 요청 수신: {len(text_content)} 글자")
        
        if not text_content:
            raise HTTPException(status_code=400, detail="텍스트 내용이 비어있습니다")
        
        # Step 1: 텍스트를 Chunk 객체로 변환 (ChunkID 생성)
        logger.info(f"📝 텍스트를 청크로 변환 중...")
        
        # 메타데이터에서 필요한 정보 추출
        doc_id = metadata.get('source', 'gemini_analysis')
        filename = metadata.get('filename', 'gemini_response.txt')
        
        # 텍스트를 청크로 분할 (파이프라인의 설정 사용)
        from modules.core.types import Chunk
        from modules.chunking.sliding_window_chunker import SlidingWindowChunker
        from modules.chunking.base_chunker import ChunkingConfig
        from config.constants import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
        
        chunk_size = DEFAULT_CHUNK_SIZE  # 512
        chunk_overlap = DEFAULT_CHUNK_OVERLAP  # 64
        
        chunker = SlidingWindowChunker(
            chunk_size=chunk_size,
            overlap=chunk_overlap
        )
        
        chunks = chunker.chunk(text_content)
        
        if not chunks:
            logger.warning(f"⚠️ 청크 분할 결과 없음")
            raise HTTPException(status_code=400, detail="텍스트를 청크로 분할할 수 없습니다")
        
        # Chunk 객체로 변환
        new_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk = Chunk(
                doc_id=doc_id,
                filename=filename,
                page=1,
                start_offset=i * chunk_size,
                length=len(chunk_text),
                text=chunk_text,
                extra={
                    "source": "gemini_analysis",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": metadata
                }
            )
            new_chunks.append(chunk)
        
        logger.info(f"✅ {len(new_chunks)} 개의 청크 생성 완료")
        
        # Step 2: 기존 청크와 병합
        logger.info(f"🔗 기존 청크와 병합 중...")
        existing_chunks = pipeline.chunks if hasattr(pipeline, 'chunks') else []
        all_chunks = existing_chunks + new_chunks
        
        logger.info(f"📊 기존: {len(existing_chunks)}, 신규: {len(new_chunks)}, 합계: {len(all_chunks)}")
        
        # Step 3: 파이프라인 재로드 (새 청크 + 임베딩 처리)
        logger.info(f"🔄 파이프라인 재로드 중 (임베딩 계산 중)...")
        try:
            config_path = project_root / "config" / "default.yaml"
            pipeline_config = PipelineConfig.from_file(config_path)
            
            # 새 파이프라인 생성 (자동 임베딩)
            pipeline = RAGPipeline(
                chunks=all_chunks,
                pipeline_config=pipeline_config,
                evaluation_mode=True,
            )
            logger.info(f"✅ 파이프라인 재로드 완료")
            logger.info(f"📈 최종 청크 수: {len(all_chunks)}")
            
        except Exception as e:
            logger.error(f"❌ 파이프라인 재로드 실패: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"파이프라인 재로드 실패: {str(e)}")
        
        logger.info(f"✅ 텍스트 임베딩 완료: {len(new_chunks)} 청크 추가됨")
        
        # 완료 응답 데이터
        response_data = {
            "status": "success",
            "message": "보고서 적용 완료",
            "details": {
                "text_processed": True,
                "text_length": len(text_content),
                "chunks_created": len(new_chunks),
                "total_chunks": len(all_chunks),
                "processing_timestamp": datetime.now().isoformat(),
            }
        }
        
        logger.info(f"✅ 응답 데이터 생성 완료")
        logger.info(f"    - 상태: {response_data['status']}")
        logger.info(f"    - 메시지: {response_data['message']}")
        logger.info(f"    - 청크 수: {len(new_chunks)} 생성, {len(all_chunks)} 총합")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 텍스트 임베딩 처리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"텍스트 임베딩 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/pdf/extract-and-embed")
async def extract_and_embed_pdf(request: PDFExtractionRequest):
    """
    PDF 파일에서 OCR로 텍스트를 추출하고 즉시 임베딩하여 벡터 DB에 추가합니다.
    
    Args:
        request: PDFExtractionRequest
            - pdf_data: Base64 인코딩된 PDF 데이터 (선택사항)
            - pdf_path: PDF 파일 경로 (선택사항)
            - filename: 파일 이름
            - metadata: 메타데이터 (선택사항)
            - callback_url: Backend 콜백 URL
    """
    global pipeline
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        pdf_path = request.pdf_path.strip() if request.pdf_path else None
        pdf_data = request.pdf_data
        filename = request.filename
        metadata = request.metadata or {}
        
        logger.info(f"[PDF_EXTRACT] 📥 PDF 추출 및 임베딩 요청 수신: {pdf_path or filename}")
        
        # Step 1: PDF 파일 존재 확인 또는 데이터 로드
        if pdf_path:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                logger.error(f"[PDF_EXTRACT] ❌ PDF 파일을 찾을 수 없음: {pdf_path}")
                raise HTTPException(status_code=404, detail=f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        elif pdf_data:
            try:
                import base64
                pdf_file = Path(f"/app/data/pdfs/{filename}") # 임시 파일 경로
                pdf_file.parent.mkdir(parents=True, exist_ok=True) # 디렉토리가 없으면 생성
                pdf_file.write_bytes(base64.b64decode(pdf_data))
                logger.info(f"[PDF_EXTRACT] 📥 PDF 데이터 로드 완료: {filename}")
            except Exception as e:
                logger.error(f"[PDF_EXTRACT] ❌ PDF 데이터 로드 실패: {str(e)}", exc_info=True)
                raise HTTPException(status_code=400, detail=f"PDF 데이터 로드 실패: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="PDF 파일 경로 또는 데이터가 누락되었습니다.")
        
        # Step 2: OCR로 텍스트 추출
        logger.info(f"[PDF_EXTRACT] 🔍 PDF에서 OCR로 텍스트 추출 중...")
        
        try:
            from modules.preprocessing.pdf_extractor import PDFExtractor
            from modules.preprocessing.ocr_corrector import OCRCorrector
            
            pdf_extractor = PDFExtractor()
            ocr_corrector = OCRCorrector()
            
            # PDF에서 텍스트 추출 (실패 시 자동으로 OCR 사용)
            extracted_text = pdf_extractor.extract_text_from_file(str(pdf_file))
            logger.info(f"[PDF_EXTRACT] ✅ PDF 추출 완료 - {len(extracted_text)} 글자")
            
            # 텍스트가 비어있거나 공백만 있으면 OCR 재시도
            if not extracted_text or not extracted_text.strip():
                logger.info(f"[PDF_EXTRACT] 🔍 텍스트 부족 감지 - OCR 직접 시도...")
                try:
                    # PDFExtractor의 OCR 메서드를 직접 호출 시도
                    if hasattr(pdf_extractor, '_extract_text_ocr'):
                        extracted_text = pdf_extractor._extract_text_ocr(str(pdf_file))
                    else:
                        # Fallback: 직접 OCR 구현
                        import pytesseract
                        from PIL import Image
                        import pymupdf
                        
                        logger.info(f"[PDF_EXTRACT] 🔍 Tesseract OCR 직접 처리...")
                        doc = pymupdf.open(str(pdf_file))
                        extracted_text = ""
                        for page_num in range(len(doc)):
                            page = doc[page_num]
                            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            page_text = pytesseract.image_to_string(img, lang='kor+eng')
                            extracted_text += page_text + "\n\n"
                        doc.close()
                    
                    logger.info(f"[PDF_EXTRACT] ✅ OCR 추출 완료 - {len(extracted_text)} 글자")
                except Exception as ocr_error:
                    logger.error(f"[PDF_EXTRACT] ❌ OCR 추출 실패: {str(ocr_error)}", exc_info=True)
                    raise HTTPException(status_code=400, detail=f"PDF OCR 추출 실패: {str(ocr_error)}")
            
            # 최종 검증
            if not extracted_text or not extracted_text.strip():
                logger.warning(f"[PDF_EXTRACT] ⚠️ PDF에서 텍스트를 추출할 수 없습니다: {pdf_file.name}")
                raise HTTPException(status_code=400, detail="PDF에서 텍스트를 추출할 수 없습니다")
            
            # OCR 후처리 (오류 수정)
            logger.info(f"[PDF_EXTRACT] 🔧 OCR 후처리 중...")
            corrected_text = ocr_corrector.correct_single(extracted_text)
            
        except Exception as extract_error:
            logger.error(f"[PDF_EXTRACT] ❌ OCR 추출 실패: {str(extract_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"OCR 추출 실패: {str(extract_error)}")
        
        # Step 3: 추출된 텍스트를 청크로 분할
        logger.info(f"[PDF_EXTRACT] 📝 텍스트를 청크로 변환 중...")
        
        from modules.core.types import Chunk
        from modules.chunking.sliding_window_chunker import SlidingWindowChunker
        from modules.chunking.base_chunker import ChunkingConfig
        from config.constants import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
        
        doc_id = metadata.get('source', 'pdf_ocr_extraction')
        filename = filename or pdf_file.name
        
        # 청킹 설정
        chunking_config = ChunkingConfig(
            chunk_size=DEFAULT_CHUNK_SIZE,      # 512
            chunk_overlap=DEFAULT_CHUNK_OVERLAP  # 64
        )
        
        chunker = SlidingWindowChunker(config=chunking_config)
        
        chunks = chunker.chunk_text(
            doc_id=doc_id,
            filename=filename,
            text=corrected_text,
            page=1
        )
        
        if not chunks:
            logger.warning(f"[PDF_EXTRACT] ⚠️ 청크 분할 결과 없음")
            raise HTTPException(status_code=400, detail="텍스트를 청크로 분할할 수 없습니다")
        
        logger.info(f"[PDF_EXTRACT] ✅ {len(chunks)} 개의 청크 생성 완료")
        new_chunks = chunks
        
        # Step 4: 기존 청크와 병합
        logger.info(f"[PDF_EXTRACT] 🔗 기존 청크와 병합 중...")
        existing_chunks = pipeline.chunks if hasattr(pipeline, 'chunks') else []
        all_chunks = existing_chunks + new_chunks
        
        logger.info(f"[PDF_EXTRACT] 📊 기존: {len(existing_chunks)}, 신규: {len(new_chunks)}, 합계: {len(all_chunks)}")
        
        # Step 5: 파이프라인 재로드 (새 청크 + 임베딩 처리)
        logger.info(f"[PDF_EXTRACT] 🔄 파이프라인 재로드 중 (임베딩 계산 중)...")
        try:
            config_path = project_root / "config" / "default.yaml"
            pipeline_config = PipelineConfig.from_file(config_path)
            
            # 새 파이프라인 생성 (자동 임베딩)
            pipeline = RAGPipeline(
                chunks=all_chunks,
                pipeline_config=pipeline_config,
                evaluation_mode=True,
            )
            logger.info(f"[PDF_EXTRACT] ✅ 파이프라인 재로드 완료")
            logger.info(f"[PDF_EXTRACT] 📈 최종 청크 수: {len(all_chunks)}")
            
        except Exception as pipeline_error:
            logger.error(f"[PDF_EXTRACT] ❌ 파이프라인 재로드 실패: {str(pipeline_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"파이프라인 재로드 실패: {str(pipeline_error)}")
        
        logger.info(f"[PDF_EXTRACT] ✅ PDF OCR 추출 및 임베딩 완료: {len(new_chunks)} 청크 추가됨")
        
        # 완료 응답 데이터
        response_data = {
            "status": "success",
            "message": "보고서 적용 완료",
            "details": {
                "pdf_processed": True,
                "extracted_text_length": len(corrected_text),
                "chunks_created": len(new_chunks),
                "total_chunks": len(all_chunks),
                "processing_timestamp": datetime.now().isoformat(),
            }
        }
        
        logger.info(f"[PDF_EXTRACT] ✅ 응답 데이터 생성 완료")
        logger.info(f"[PDF_EXTRACT]    - 상태: {response_data['status']}")
        logger.info(f"[PDF_EXTRACT]    - 메시지: {response_data['message']}")
        logger.info(f"[PDF_EXTRACT]    - 청크 수: {len(new_chunks)} 생성, {len(all_chunks)} 총합")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF_EXTRACT] ❌ PDF OCR 추출 처리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PDF OCR 추출 처리 중 오류가 발생했습니다: {str(e)}"
        )


# API 라우터를 메인 앱에 등록
app.include_router(api_router)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Chatbot v6 API",
        "version": "6.0.0",
        "description": "정수처리 챗봇 API (4가지 원칙 준수)",
        "endpoints": {
            "health": "/healthz or /api/healthz",
            "ask": "/ask (POST) or /api/ask (POST)",
            "status": "/status or /api/status",
            "docs": "/docs",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=env_config.debug,
    )


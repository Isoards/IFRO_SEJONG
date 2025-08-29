"""
TypeScript/Django 연동을 위한 FastAPI 엔드포인트

이 모듈은 PDF QA 시스템의 모든 기능을 REST API로 제공하여
TypeScript 프론트엔드와 Django 백엔드에서 쉽게 사용할 수 있도록 합니다.
"""

import os
import uuid
import tempfile
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 핵심 모듈들 임포트
from core.pdf_processor import PDFProcessor, TextChunk
from core.vector_store import HybridVectorStore, VectorStoreInterface
from core.question_analyzer import QuestionAnalyzer, AnalyzedQuestion, ConversationItem
from core.answer_generator import AnswerGenerator, Answer, ModelType, GenerationConfig
from core.evaluator import PDFQAEvaluator, SystemEvaluation
from core.sql_generator import SQLGenerator, DatabaseSchema, SQLQuery
from core.dual_pipeline_processor import DualPipelineProcessor, DualPipelineResult

logger = logging.getLogger(__name__)

# Pydantic 모델들 (API 스키마 정의)
class QuestionRequest(BaseModel):
    """질문 요청 모델"""
    question: str = Field(..., description="사용자 질문")
    pdf_id: str = Field(..., description="PDF 문서 식별자")
    use_conversation_context: bool = Field(True, description="이전 대화 컨텍스트 사용 여부")
    max_chunks: int = Field(5, description="검색할 최대 청크 수")
    use_dual_pipeline: bool = Field(True, description="Dual Pipeline 사용 여부")
    
class ConversationHistoryItem(BaseModel):
    """대화 기록 항목 모델"""
    question: str
    answer: str
    timestamp: str
    confidence_score: float = 0.0

class QuestionResponse(BaseModel):
    """질문 응답 모델"""
    answer: str = Field(..., description="생성된 답변")
    confidence_score: float = Field(..., description="답변 신뢰도 (0-1)")
    used_chunks: List[str] = Field(..., description="사용된 문서 청크 ID들")
    generation_time: float = Field(..., description="답변 생성 시간 (초)")
    question_type: str = Field(..., description="질문 유형")
    model_name: str = Field(..., description="사용된 모델 이름")
    pipeline_type: str = Field(..., description="사용된 파이프라인 타입")
    sql_query: Optional[str] = Field(None, description="생성된 SQL 쿼리 (있는 경우)")
    
class PDFUploadResponse(BaseModel):
    """PDF 업로드 응답 모델"""
    pdf_id: str = Field(..., description="생성된 PDF 식별자")
    filename: str = Field(..., description="업로드된 파일명")
    total_pages: int = Field(..., description="총 페이지 수")
    total_chunks: int = Field(..., description="생성된 청크 수")
    processing_time: float = Field(..., description="처리 시간 (초)")
    
class EvaluationRequest(BaseModel):
    """평가 요청 모델"""
    questions: List[str]
    generated_answers: List[str]
    reference_answers: List[str]
    
class ModelConfigRequest(BaseModel):
    """모델 설정 요청 모델"""
    model_type: str = Field("ollama", description="모델 타입 (ollama/huggingface/llama_cpp)")
    model_name: str = Field("llama2:7b", description="모델 이름")
    max_length: int = Field(512, description="최대 생성 길이")
    temperature: float = Field(0.7, description="생성 온도")
    top_p: float = Field(0.9, description="Top-p 샘플링")

class SystemStatusResponse(BaseModel):
    """시스템 상태 응답 모델"""
    status: str = Field(..., description="시스템 상태")
    model_loaded: bool = Field(..., description="모델 로드 상태")
    total_pdfs: int = Field(..., description="등록된 PDF 수")
    total_chunks: int = Field(..., description="총 청크 수")
    memory_usage: Dict[str, Any] = Field(..., description="메모리 사용량")

# 전역 객체들 (싱글톤 패턴)
pdf_processor: Optional[PDFProcessor] = None
vector_store: Optional[VectorStoreInterface] = None
question_analyzer: Optional[QuestionAnalyzer] = None
answer_generator: Optional[AnswerGenerator] = None
evaluator: Optional[PDFQAEvaluator] = None
sql_generator: Optional[SQLGenerator] = None
dual_pipeline_processor: Optional[DualPipelineProcessor] = None

# PDF 메타데이터 저장소 (실제로는 데이터베이스 사용 권장)
pdf_metadata: Dict[str, Dict] = {}

# FastAPI 앱 초기화
app = FastAPI(
    title="PDF QA System API",
    description="로컬 LLM을 사용하는 PDF 기반 질문 답변 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 (TypeScript 프론트엔드 지원)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000", "http://127.0.0.1:8000"],  # React/Django 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        if not answer_generator.load_model():
            logger.error("답변 생성 모델 로드 실패")
            # 모델 로드 실패 시에도 기본 객체는 반환하되, 실제 사용 시 오류 처리
            answer_generator.is_loaded = False
    return answer_generator

def get_evaluator() -> PDFQAEvaluator:
    """평가기 의존성"""
    global evaluator
    if evaluator is None:
        evaluator = PDFQAEvaluator()
    return evaluator

def get_sql_generator() -> SQLGenerator:
    """SQL 생성기 의존성"""
    global sql_generator
    if sql_generator is None:
        sql_generator = SQLGenerator()
    return sql_generator

def get_dual_pipeline_processor() -> DualPipelineProcessor:
    """Dual Pipeline 처리기 의존성"""
    global dual_pipeline_processor
    if dual_pipeline_processor is None:
        # 필요한 컴포넌트들 가져오기
        qa = get_question_analyzer()
        ag = get_answer_generator()
        sg = get_sql_generator()
        vs = get_vector_store()
        
        # 샘플 데이터베이스 스키마 (실제로는 설정에서 로드)
        sample_schema = DatabaseSchema(
            table_name="users",
            columns=[
                {"name": "id", "type": "INTEGER", "description": "사용자 ID"},
                {"name": "name", "type": "TEXT", "description": "사용자 이름"},
                {"name": "email", "type": "TEXT", "description": "이메일"},
                {"name": "created_at", "type": "DATETIME", "description": "가입일"},
                {"name": "status", "type": "TEXT", "description": "상태"}
            ],
            primary_key="id",
            sample_data=[
                {"id": 1, "name": "김철수", "email": "kim@example.com", "created_at": "2023-01-01", "status": "active"},
                {"id": 2, "name": "이영희", "email": "lee@example.com", "created_at": "2023-02-15", "status": "active"}
            ]
        )
        
        dual_pipeline_processor = DualPipelineProcessor(
            question_analyzer=qa,
            answer_generator=ag,
            sql_generator=sg,
            vector_store=vs,
            database_schema=sample_schema
        )
    return dual_pipeline_processor

# API 엔드포인트들

@app.get("/", response_model=Dict[str, str])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "PDF QA System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    vector_store: VectorStoreInterface = Depends(get_vector_store),
    answer_generator: AnswerGenerator = Depends(get_answer_generator)
):
    """시스템 상태 조회"""
    import psutil
    import gc
    
    # 메모리 사용량 조회
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return SystemStatusResponse(
        status="running",
        model_loaded=answer_generator.llm.is_loaded,
        total_pdfs=len(pdf_metadata),
        total_chunks=sum(meta.get("total_chunks", 0) for meta in pdf_metadata.values()),
        memory_usage={
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
            "cpu_percent": psutil.cpu_percent()
        }
    )

@app.post("/upload_pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
    vector_store: VectorStoreInterface = Depends(get_vector_store)
):
    """PDF 파일 업로드 및 처리"""
    import time
    
    start_time = time.time()
    
    # 파일 검증
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    
    # 임시 파일로 저장
    pdf_id = str(uuid.uuid4())
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # PDF 처리
        chunks, metadata = pdf_processor.process_pdf(temp_path)
        
        # 벡터 저장소에 추가
        vector_store.add_chunks(chunks)
        
        # 메타데이터 저장
        pdf_metadata[pdf_id] = {
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "total_pages": metadata.get("pages", 0),
            "total_chunks": len(chunks),
            "extraction_method": metadata.get("extraction_method", [])
        }
        
        # 백그라운드에서 벡터 저장소 저장
        background_tasks.add_task(vector_store.save)
        
        # 임시 파일 삭제
        os.unlink(temp_path)
        
        processing_time = time.time() - start_time
        
        logger.info(f"PDF 업로드 완료: {file.filename} ({len(chunks)}개 청크)")
        
        return PDFUploadResponse(
            pdf_id=pdf_id,
            filename=file.filename,
            total_pages=metadata.get("pages", 0),
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
    dual_pipeline_processor: DualPipelineProcessor = Depends(get_dual_pipeline_processor)
):
    """질문에 대한 답변 생성 (Dual Pipeline 지원)"""
    
    # PDF 존재 확인
    if request.pdf_id not in pdf_metadata:
        raise HTTPException(status_code=404, detail="PDF를 찾을 수 없습니다.")
    
    try:
        # Dual Pipeline 사용 여부에 따라 처리 방식 분기
        if request.use_dual_pipeline and dual_pipeline_processor:
            try:
                # Dual Pipeline 처리
                result = dual_pipeline_processor.process_question(
                    question=request.question,
                    use_context=request.use_conversation_context
                )
                
                # 대화 기록에 추가
                question_analyzer.add_conversation_item(
                    request.question,
                    result.final_answer,
                    [],  # Dual Pipeline에서는 청크 ID를 별도로 관리하지 않음
                    result.confidence_score
                )
                
                # SQL 쿼리 정보 추출
                sql_query = None
                if result.sql_result and result.sql_result.sql_query:
                    sql_query = result.sql_result.sql_query.query
                
                return QuestionResponse(
                    answer=result.final_answer,
                    confidence_score=result.confidence_score,
                    used_chunks=[],  # Dual Pipeline에서는 청크 ID를 별도로 관리하지 않음
                    generation_time=result.total_processing_time,
                    question_type=result.analyzed_question.question_type.value,
                    model_name="dual_pipeline",
                    pipeline_type=result.metadata.get("pipeline_type", "unknown"),
                    sql_query=sql_query
                )
            except Exception as dual_error:
                logger.error(f"Dual Pipeline 처리 실패: {dual_error}")
                # Dual Pipeline 실패 시 일반 파이프라인으로 폴백
                logger.info("일반 파이프라인으로 폴백합니다.")
                request.use_dual_pipeline = False
        
        else:
            # 기존 단일 파이프라인 처리
            # 1. 질문 분석
            analyzed_question = question_analyzer.analyze_question(
                request.question,
                use_conversation_context=request.use_conversation_context
            )
            
            # 2. 관련 문서 검색
            query_embedding = analyzed_question.embedding
            relevant_chunks = vector_store.search(
                query_embedding,
                top_k=request.max_chunks
            )
            
            if not relevant_chunks:
                raise HTTPException(status_code=404, detail="관련 문서를 찾을 수 없습니다.")
            
            # 3. 이전 대화 기록 가져오기
            conversation_history = None
            if request.use_conversation_context:
                conversation_history = question_analyzer.get_conversation_context(max_items=3)
            
            # 4. 답변 생성 (대화 이력 캐시 포함)
            if not answer_generator.is_loaded:
                # 모델이 로드되지 않은 경우 기본 답변 생성
                answer_content = "죄송합니다. 현재 AI 모델이 로드되지 않아 답변을 생성할 수 없습니다. 서버 관리자에게 문의해주세요."
                confidence_score = 0.0
                used_chunks = [chunk.chunk_id for chunk in relevant_chunks]
                generation_time = 0.0
                model_name = "error"
            else:
                answer = answer_generator.generate_answer(
                    analyzed_question,
                    relevant_chunks,
                    conversation_history,
                    pdf_id=request.pdf_id
                )
                answer_content = answer.content
                confidence_score = answer.confidence_score
                used_chunks = answer.used_chunks
                generation_time = answer.generation_time
                model_name = answer.model_name
            
            # 5. 대화 기록에 추가
            question_analyzer.add_conversation_item(
                request.question,
                answer_content,
                used_chunks,
                confidence_score
            )
            
            # 6. 캐시 사용 여부 확인
            from_cache = False
            if answer_generator.is_loaded and hasattr(answer, 'metadata') and answer.metadata:
                from_cache = answer.metadata.get("from_cache", False)
            
            logger.info(f"질문 처리 완료: {analyzed_question.question_type.value}, 캐시: {from_cache}")
            
            return QuestionResponse(
                answer=answer_content,
                confidence_score=confidence_score,
                used_chunks=used_chunks,
                generation_time=generation_time,
                question_type=analyzed_question.question_type.value,
                model_name=model_name,
                pipeline_type="document_search",
                sql_query=None
            )
        
    except Exception as e:
        logger.error(f"질문 처리 실패: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        
        # 오류 발생 시에도 기본 응답 반환
        return QuestionResponse(
            answer="죄송합니다. 답변을 생성하는 중 오류가 발생했습니다. 서버 관리자에게 문의해주세요.",
            confidence_score=0.0,
            used_chunks=[],
            generation_time=0.0,
            question_type="error",
            model_name="error",
            pipeline_type="error",
            sql_query=None
        )

@app.get("/conversation_history")
async def get_conversation_history(
    pdf_id: str,
    max_items: int = 10,
    question_analyzer: QuestionAnalyzer = Depends(get_question_analyzer)
):
    """대화 기록 조회"""
    if pdf_id not in pdf_metadata:
        raise HTTPException(status_code=404, detail="PDF를 찾을 수 없습니다.")
    
    history = question_analyzer.get_conversation_context(max_items=max_items)
    return {"conversation_history": history}

@app.delete("/conversation_history")
async def clear_conversation_history(
    question_analyzer: QuestionAnalyzer = Depends(get_question_analyzer)
):
    """대화 기록 초기화"""
    question_analyzer.conversation_history.clear()
    return {"message": "대화 기록이 초기화되었습니다."}

@app.post("/configure_model")
async def configure_model(request: ModelConfigRequest):
    """모델 설정 변경"""
    global answer_generator
    
    try:
        # 기존 모델 언로드
        if answer_generator:
            answer_generator.unload_model()
        
        # 새 설정으로 모델 초기화
        config = GenerationConfig(
            max_length=request.max_length,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        model_type = ModelType(request.model_type)
        answer_generator = AnswerGenerator(
            model_type=model_type,
            model_name=request.model_name,
            generation_config=config
        )
        
        # 모델 로드
        if not answer_generator.load_model():
            raise HTTPException(status_code=500, detail="새 모델 로드 실패")
        
        return {"message": f"모델 설정이 변경되었습니다: {request.model_name}"}
        
    except Exception as e:
        logger.error(f"모델 설정 변경 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 설정 변경 실패: {str(e)}")

@app.post("/evaluate")
async def evaluate_system(
    request: EvaluationRequest,
    evaluator: PDFQAEvaluator = Depends(get_evaluator)
):
    """시스템 성능 평가"""
    try:
        # 간단한 평가 실행 (실제로는 더 복잡한 평가 필요)
        semantic_similarities = []
        
        for gen_answer, ref_answer in zip(request.generated_answers, request.reference_answers):
            similarity = evaluator._calculate_semantic_similarity(gen_answer, ref_answer)
            semantic_similarities.append(similarity)
        
        avg_similarity = sum(semantic_similarities) / len(semantic_similarities)
        
        return {
            "evaluation_results": {
                "average_semantic_similarity": avg_similarity,
                "individual_similarities": semantic_similarities,
                "total_questions": len(request.questions)
            }
        }
        
    except Exception as e:
        logger.error(f"평가 실패: {e}")
        raise HTTPException(status_code=500, detail=f"평가 중 오류 발생: {str(e)}")

@app.get("/pdfs")
async def list_pdfs():
    """등록된 PDF 목록 조회"""
    pdf_list = []
    for pdf_id, metadata in pdf_metadata.items():
        pdf_list.append({
            "pdf_id": pdf_id,
            "filename": metadata["filename"],
            "upload_time": metadata["upload_time"],
            "total_pages": metadata["total_pages"],
            "total_chunks": metadata["total_chunks"]
        })
    
    return {"pdfs": pdf_list}

@app.post("/load_existing_pdfs")
async def load_existing_pdfs(
    background_tasks: BackgroundTasks,
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
    vector_store: VectorStoreInterface = Depends(get_vector_store)
):
    """기존 PDF 파일들을 자동으로 로드"""
    import glob
    from pathlib import Path
    
    pdf_dir = Path("data/pdfs")
    if not pdf_dir.exists():
        raise HTTPException(status_code=404, detail="data/pdfs 폴더를 찾을 수 없습니다.")
    
    # 모든 PDF 파일 찾기
    pdf_files = []
    for pattern in ["*.pdf", "*/*.pdf", "*/*/*.pdf"]:
        pdf_files.extend(pdf_dir.glob(pattern))
    
    if not pdf_files:
        raise HTTPException(status_code=404, detail="PDF 파일을 찾을 수 없습니다.")
    
    loaded_pdfs = []
    
    for pdf_path in pdf_files:
        try:
            # 이미 처리된 PDF인지 확인
            pdf_id = str(uuid.uuid4())
            
            # PDF 처리
            chunks, metadata = pdf_processor.process_pdf(str(pdf_path))
            
            # 벡터 저장소에 추가
            vector_store.add_chunks(chunks)
            
            # 메타데이터 저장
            pdf_metadata[pdf_id] = {
                "filename": pdf_path.name,
                "file_path": str(pdf_path),
                "upload_time": datetime.now().isoformat(),
                "total_pages": metadata.get("pages", 0),
                "total_chunks": len(chunks),
                "extraction_method": metadata.get("extraction_method", [])
            }
            
            loaded_pdfs.append({
                "pdf_id": pdf_id,
                "filename": pdf_path.name,
                "file_path": str(pdf_path),
                "total_pages": metadata.get("pages", 0),
                "total_chunks": len(chunks)
            })
            
            logger.info(f"기존 PDF 로드 완료: {pdf_path.name} ({len(chunks)}개 청크)")
            
        except Exception as e:
            logger.error(f"PDF 로드 실패 {pdf_path}: {e}")
            continue
    
    # 백그라운드에서 벡터 저장소 저장
    background_tasks.add_task(vector_store.save)
    
    return {
        "message": f"{len(loaded_pdfs)}개의 PDF 파일을 로드했습니다.",
        "loaded_pdfs": loaded_pdfs
    }

@app.delete("/pdfs/{pdf_id}")
async def delete_pdf(pdf_id: str):
    """PDF 삭제"""
    if pdf_id not in pdf_metadata:
        raise HTTPException(status_code=404, detail="PDF를 찾을 수 없습니다.")
    
    # 메타데이터에서 제거
    del pdf_metadata[pdf_id]
    
    # 실제로는 벡터 저장소에서도 해당 청크들을 제거해야 함
    # 현재 구현에서는 전체 벡터 저장소 재구성이 필요
    
    return {"message": f"PDF {pdf_id}가 삭제되었습니다."}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 대화 이력 관리 엔드포인트들

@app.get("/conversation/cache/stats")
async def get_conversation_cache_stats(
    answer_generator: AnswerGenerator = Depends(get_answer_generator)
):
    """대화 이력 캐시 통계 조회"""
    try:
        stats = answer_generator.get_conversation_statistics()
        return stats
    except Exception as e:
        logger.error(f"대화 이력 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

@app.delete("/conversation/cache")
async def clear_conversation_cache(
    pdf_id: Optional[str] = None,
    answer_generator: AnswerGenerator = Depends(get_answer_generator)
):
    """대화 이력 캐시 삭제"""
    try:
        deleted_count = answer_generator.clear_conversation_cache(pdf_id)
        return {
            "message": f"대화 이력 캐시가 삭제되었습니다.",
            "deleted_count": deleted_count,
            "pdf_id": pdf_id
        }
    except Exception as e:
        logger.error(f"대화 이력 캐시 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"캐시 삭제 실패: {str(e)}")

@app.get("/conversation/cache/search")
async def search_conversation_cache(
    question: str,
    threshold: float = 0.7,
    limit: int = 5,
    answer_generator: AnswerGenerator = Depends(get_answer_generator)
):
    """대화 이력에서 유사한 질문 검색"""
    try:
        if not answer_generator.conversation_logger:
            raise HTTPException(status_code=400, detail="대화 이력 캐시가 비활성화되어 있습니다.")
        
        similar_questions = answer_generator.conversation_logger.find_similar_questions(
            question, threshold=threshold, limit=limit
        )
        
        results = []
        for log_entry, similarity in similar_questions:
            results.append({
                "id": log_entry.id,
                "question": log_entry.question,
                "answer": log_entry.answer,
                "similarity": similarity,
                "confidence_score": log_entry.confidence_score,
                "question_type": log_entry.question_type,
                "timestamp": log_entry.timestamp,
                "pdf_id": log_entry.pdf_id
            })
        
        return {
            "search_query": question,
            "threshold": threshold,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"대화 이력 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")

# 간단한 챗봇 엔드포인트 (PDF 없이 작동)
@app.post("/chat")
async def simple_chat(message: str):
    """간단한 챗봇 응답 (PDF 없이 작동)"""
    try:
        # 간단한 키워드 기반 응답
        lower_message = message.lower()
        
        if "교통" in lower_message or "traffic" in lower_message:
            response = "교통 데이터는 대시보드의 '분석' 탭에서 확인하실 수 있습니다. 특정 교차로를 클릭하시면 해당 지점의 상세한 교통량 정보를 볼 수 있어요."
        elif "사고" in lower_message or "incident" in lower_message:
            response = "교통사고 정보는 '사고' 탭에서 확인 가능합니다. 빨간색 삼각형 아이콘을 클릭하시면 사고 목록과 상세 정보를 볼 수 있습니다."
        elif "경로" in lower_message or "route" in lower_message:
            response = "경로 분석은 '교통흐름' 탭에서 이용하실 수 있습니다. 지도에서 두 지점을 선택하시면 해당 구간의 교통 흐름을 분석해드립니다."
        elif "즐겨찾기" in lower_message or "favorite" in lower_message:
            response = "관심 있는 교차로나 사고를 즐겨찾기에 추가하실 수 있습니다. 별표 아이콘을 클릭하시면 '즐겨찾기' 탭에서 쉽게 찾아보실 수 있어요."
        elif "help" in lower_message or "도움" in lower_message or "사용법" in lower_message:
            response = "IFRO 대시보드 사용법:\n\n🚗 분석: 교차로별 교통량 분석\n🔄 교통흐름: 두 지점 간 경로 분석\n⚠️ 사고: 교통사고 현황\n⭐ 즐겨찾기: 관심 지점 관리\n📊 Tableau: 고급 분석 대시보드\n\n더 자세한 정보가 필요하시면 구체적으로 물어보세요!"
        else:
            response = "네, 무엇을 도와드릴까요? 교통 데이터 분석, 대시보드 사용법, 특정 기능에 대해 궁금한 점이 있으시면 언제든 말씀해 주세요!"
        
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"챗봇 응답 생성 중 오류: {e}")
        return {
            "success": False,
            "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            "timestamp": datetime.now().isoformat()
        }

# Django 연동을 위한 추가 엔드포인트들

@app.post("/django/ask")
async def django_ask_question(
    question: str,
    pdf_id: str,
    conversation_history: Optional[List[ConversationHistoryItem]] = None,
    vector_store: VectorStoreInterface = Depends(get_vector_store),
    question_analyzer: QuestionAnalyzer = Depends(get_question_analyzer),
    answer_generator: AnswerGenerator = Depends(get_answer_generator)
):
    """Django에서 호출하기 쉬운 질문 엔드포인트"""
    
    # 대화 기록 복원 (필요한 경우)
    if conversation_history:
        question_analyzer.conversation_history.clear()
        for item in conversation_history:
            question_analyzer.add_conversation_item(
                item.question,
                item.answer,
                [],  # 청크 정보는 없음
                item.confidence_score
            )
    
    # 기본 ask 엔드포인트 로직 재사용
    request = QuestionRequest(
        question=question,
        pdf_id=pdf_id,
        use_conversation_context=bool(conversation_history)
    )
    
    return await ask_question(request, vector_store, question_analyzer, answer_generator)

# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"글로벌 예외 발생: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "내부 서버 오류가 발생했습니다."}
    )

# 서버 실행 함수
def run_server(host: str = "0.0.0.0", port: int = 8008, debug: bool = False):
    """
    FastAPI 서버 실행
    
    Args:
        host: 서버 호스트
        port: 서버 포트
        debug: 디버그 모드
    """
    uvicorn.run(
        "api.endpoints:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )

if __name__ == "__main__":
    # 개발 서버 실행
    run_server(debug=True)

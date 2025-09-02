"""
FastAPI 엔드포인트 (최적화 버전)

빠른 응답을 위한 간소화된 API
"""

import os
import sys
import uuid
import tempfile
import locale
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 핵심 모듈들 임포트
from core.document.pdf_processor import PDFProcessor, TextChunk
from core.document.vector_store import HybridVectorStore, VectorStoreInterface
from core.query.question_analyzer import QuestionAnalyzer, AnalyzedQuestion, ConversationItem
from core.llm.answer_generator import AnswerGenerator, Answer, ModelType, GenerationConfig
from core.database.sql_generator import SQLGenerator, DatabaseSchema, SQLQuery

from core.query.query_router import QueryRouter, QueryRoute
from core.query.llm_greeting_handler import GreetingHandler
from utils.chatbot_logger import chatbot_logger, QuestionType, ProcessingStep

logger = logging.getLogger(__name__)

# Pydantic 모델들 (단순화)
class QuestionRequest(BaseModel):
    """질문 요청 모델"""
    question: str = Field(..., description="사용자 질문")
    pdf_id: str = Field("", description="PDF 문서 식별자")
    user_id: str = Field("", description="사용자 식별자")
    use_conversation_context: bool = Field(True, description="이전 대화 컨텍스트 사용 여부")
    max_chunks: int = Field(10, description="검색할 최대 청크 수")

class QuestionResponse(BaseModel):
    """질문 응답 모델"""
    answer: str = Field(..., description="생성된 답변")
    confidence_score: float = Field(..., description="답변 신뢰도")
    used_chunks: List[str] = Field(..., description="사용된 문서 청크 ID들")
    generation_time: float = Field(..., description="답변 생성 시간 (초)")
    question_type: str = Field(..., description="질문 유형")
    llm_model_name: str = Field(..., description="사용된 모델 이름")
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
    llm_model_loaded: bool = Field(..., description="모델 로드 상태")
    total_pdfs: int = Field(..., description="등록된 PDF 수")
    total_chunks: int = Field(..., description="총 청크 수")
    memory_usage: Dict[str, Any] = Field(..., description="메모리 사용량")

class KeywordCacheResponse(BaseModel):
    """키워드 캐시 응답 모델"""
    total_keywords: int = Field(..., description="총 키워드 수")
    frequent_keywords: int = Field(..., description="자주 사용된 키워드 수")
    extracted_keywords: int = Field(..., description="추출된 키워드 수")
    cache_threshold: int = Field(..., description="캐시 임계값")
    top_keywords: Dict[str, int] = Field(..., description="상위 키워드 (최대 10개)")

class KeywordPipelineResponse(BaseModel):
    """키워드 파이프라인 추가 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    added_keywords: List[str] = Field(..., description="추가된 키워드 목록")
    message: str = Field(..., description="응답 메시지")

# FastAPI 앱 초기화
app = FastAPI(
    title=os.getenv("API_TITLE", "범용 RAG 시스템 API"),
    description=os.getenv("API_DESCRIPTION", "범용 문서 검색 및 데이터베이스 쿼리 시스템 API"),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# UTF-8 인코딩 설정
# 시스템 인코딩을 UTF-8로 설정
if sys.platform.startswith('linux'):
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
elif sys.platform.startswith('win'):
    locale.setlocale(locale.LC_ALL, 'Korean_Korea.UTF-8')
else:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

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
llm_greeting_handler: Optional[GreetingHandler] = None

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
        logger.info("벡터 저장소 초기화 중...")
        vector_store = HybridVectorStore()
        total_chunks = vector_store.get_total_chunks()
        logger.info(f"벡터 저장소 초기화 완료 - 총 청크 수: {total_chunks}")
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

def get_llm_greeting_handler() -> GreetingHandler:
    """LLM 기반 인사말 핸들러 의존성"""
    global llm_greeting_handler
    if llm_greeting_handler is None:
        # answer_generator가 준비된 후에 초기화
        answer_gen = get_answer_generator()
        llm_greeting_handler = GreetingHandler(answer_gen)
    return llm_greeting_handler

def initialize_system():
    """시스템 초기화 및 자동 PDF 업로드"""
    global pdf_processor, vector_store, question_analyzer, answer_generator, sql_generator, query_router
    
    try:
        logger.info("시스템 초기화 시작...")
        
        # 컴포넌트들 초기화
        pdf_processor = PDFProcessor()
        vector_store = HybridVectorStore()
        question_analyzer = QuestionAnalyzer()
        answer_generator = AnswerGenerator()
        sql_generator = SQLGenerator()
        query_router = QueryRouter()
        
        logger.info("컴포넌트 초기화 완료")
        
        # 기존 PDF 문서 로드
        try:
            existing_pdfs = vector_store.get_all_pdfs()
            for pdf_info in existing_pdfs:
                pdf_metadata[pdf_info['id']] = pdf_info
            logger.info(f"기존 PDF {len(existing_pdfs)}개 로드 완료")
            
            # 기존 청크 수 확인
            total_chunks = vector_store.get_total_chunks()
            logger.info(f"기존 청크 수: {total_chunks}")
            
            # 이미 충분한 데이터가 있으면 자동 업로드 건너뛰기
            if total_chunks > 0 and len(existing_pdfs) > 0:
                logger.info("이미 충분한 PDF 데이터가 로드되어 있습니다. 자동 업로드를 건너뜁니다.")
                logger.info("=" * 60)
                logger.info("시스템 초기화 완료!")
                logger.info("=" * 60)
                return
            
        except Exception as e:
            logger.warning(f"기존 PDF 로드 실패: {e}")
        
        # 자동 PDF 업로드 (데이터가 없을 때만 실행)
        logger.info("=" * 60)
        logger.info("data 폴더의 PDF 파일들을 벡터 저장소에 업로드합니다...")
        logger.info("=" * 60)
        auto_upload_result = auto_upload_pdfs_sync()
        logger.info(f"자동 업로드 완료: {auto_upload_result}")
        logger.info("=" * 60)
        logger.info("PDF 업로드 완료!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"시스템 초기화 실패: {e}")
        raise

def auto_upload_pdfs_sync():
    """동기적으로 PDF 파일들을 자동 업로드"""
    try:
        import os
        
        # data 폴더와 data/pdfs 폴더 모두 확인
        data_folders = ["./data", "./data/pdfs"]
        pdf_files = []
        
        for data_folder in data_folders:
            if not os.path.exists(data_folder):
                logger.warning(f"{data_folder} 폴더가 존재하지 않습니다.")
                continue
            
            # 재귀적으로 PDF 파일 찾기
            for root, dirs, files in os.walk(data_folder):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_path = os.path.join(root, file)
                        pdf_files.append(pdf_path)
        
        if not pdf_files:
            logger.info("data 폴더에서 PDF 파일을 찾을 수 없습니다.")
            return {"message": "업로드할 PDF 파일이 없습니다.", "uploaded_count": 0}
        
        logger.info(f"data 폴더에서 {len(pdf_files)}개의 PDF 파일을 발견했습니다.")
        
        uploaded_count = 0
        skipped_count = 0
        failed_count = 0
        
        for pdf_path in pdf_files:
            try:
                # 이미 처리된 PDF인지 확인
                pdf_id = os.path.basename(pdf_path)
                if pdf_id in pdf_metadata:
                    logger.info(f"이미 처리된 PDF 건너뛰기: {pdf_id}")
                    skipped_count += 1
                    continue
                
                logger.info(f"PDF 처리 중: {pdf_id}")
                
                # PDF 처리
                chunks, metadata = pdf_processor.process_pdf(pdf_path)
                vector_store.add_chunks(chunks)
                
                # 메타데이터 저장
                pdf_metadata[pdf_id] = {
                    "filename": pdf_id,
                    "total_pages": len(chunks),
                    "upload_time": datetime.now().isoformat(),
                    "total_chunks": len(chunks),
                    "file_size": os.path.getsize(pdf_path)
                }
                
                uploaded_count += 1
                logger.info(f"✓ PDF 처리 완료: {pdf_id} ({len(chunks)}개 청크)")
                
            except Exception as e:
                logger.error(f"PDF 처리 실패 {pdf_path}: {e}")
                failed_count += 1
        
        logger.info(f"PDF 처리 완료: {uploaded_count}개 처리됨, {skipped_count}개 건너뜀, {failed_count}개 오류")
        
        return {
            "message": f"자동 업로드 완료: {uploaded_count}개 성공, {skipped_count}개 건너뜀, {failed_count}개 실패",
            "uploaded_count": uploaded_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "total_files": len(pdf_files)
        }
        
    except Exception as e:
        logger.error(f"자동 업로드 실패: {e}")
        return {"error": str(e)}

# API 엔드포인트들
@app.get("/", response_model=Dict[str, str])
async def root():
    """루트 엔드포인트"""
    return {"message": "범용 RAG 시스템 API 서버가 실행 중입니다."}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/clear-vector-store")
async def clear_vector_store(
    vector_store: VectorStoreInterface = Depends(get_vector_store)
):
    """벡터 저장소 초기화"""
    try:
        vector_store.clear()
        return {"message": "벡터 저장소가 성공적으로 초기화되었습니다."}
    except Exception as e:
        logger.error(f"벡터 저장소 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"벡터 저장소 초기화 실패: {str(e)}")

@app.post("/reset-chunks")
async def reset_chunks(
    vector_store: VectorStoreInterface = Depends(get_vector_store),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor)
):
    """청크 초기화 및 재생성"""
    try:
        logger.info("청크 초기화 및 재생성 시작...")
        
        # 1단계: 기존 청크 초기화
        total_chunks = vector_store.get_total_chunks()
        logger.info(f"기존 청크 수: {total_chunks}")
        
        vector_store.clear()
        logger.info("벡터 저장소 초기화 완료")
        
        # 2단계: PDF 파일 스캔
        pdf_files = _find_pdf_files()
        logger.info(f"발견된 PDF 파일: {len(pdf_files)}개")
        
        if not pdf_files:
            return {"message": "PDF 파일이 없습니다. data/pdfs 폴더에 PDF 파일을 추가해주세요."}
        
        # 3단계: 청크 재생성
        total_new_chunks = 0
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"처리 중: {pdf_file}")
                
                # PDF 처리
                chunks = pdf_processor.process_pdf(pdf_file)
                
                if chunks:
                    # 벡터 저장소에 추가
                    vector_store.add_chunks(chunks)
                    total_new_chunks += len(chunks)
                    logger.info(f"{len(chunks)}개 청크 생성 완료")
                else:
                    logger.warning(f"청크 생성 실패: {pdf_file}")
                    
            except Exception as e:
                logger.error(f"PDF 처리 오류 {pdf_file}: {e}")
                continue
        
        logger.info(f"청크 재생성 완료! 총 {total_new_chunks}개 청크 생성")
        
        return {
            "message": "청크 초기화 및 재생성이 완료되었습니다.",
            "total_new_chunks": total_new_chunks,
            "total_chunks": vector_store.get_total_chunks()
        }
        
    except Exception as e:
        logger.error(f"청크 초기화 및 재생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"청크 초기화 및 재생성 실패: {str(e)}")

def _find_pdf_files() -> List[str]:
    """PDF 파일들 찾기"""
    pdf_files = []
    
    # data/pdfs 폴더 확인
    pdf_dir = Path(__file__).parent.parent / "data" / "pdfs"
    if pdf_dir.exists():
        pdf_files.extend([str(f) for f in pdf_dir.glob("*.pdf")])
    
    # data 폴더 직접 확인
    data_dir = Path(__file__).parent.parent / "data"
    if data_dir.exists():
        pdf_files.extend([str(f) for f in data_dir.glob("*.pdf")])
    
    return pdf_files

@app.get("/vector-store-stats")
async def get_vector_store_stats(
    vector_store: VectorStoreInterface = Depends(get_vector_store)
):
    """벡터 저장소 통계 정보"""
    try:
        total_chunks = vector_store.get_total_chunks()
        pdfs = vector_store.get_all_pdfs()
        
        return {
            "total_chunks": total_chunks,
            "total_pdfs": len(pdfs),
            "pdfs": pdfs
        }
    except Exception as e:
        logger.error(f"벡터 저장소 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

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
        chunks, metadata = pdf_processor.process_pdf(temp_file_path, pdf_id)
        
        # 벡터 저장소에 저장
        vector_store.add_chunks(chunks)
        
        # 키워드를 파이프라인 설정에 추가
        if pdf_processor.enable_keyword_extraction:
            pdf_processor.keyword_extractor.add_keywords_to_pipeline()
        
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
    """질문에 대한 답변 생성 (최적화된 버전)"""
    
    # 성능 측정 시작
    start_time = time.time()
    session_id = None
    
    try:
        # 단계별 로그 시작
        if chatbot_logger:
            session_id = chatbot_logger._generate_session_id()
            chatbot_logger.log_step(session_id, ProcessingStep.START, 0.0, f"질문: {request.question[:50]}...")
        
        # 🚀 SBERT 기반 쿼리 라우팅
        routing_start = time.time()
        route_result = query_router.route_query(request.question)
        routing_time = time.time() - routing_start
        
        if chatbot_logger and session_id:
            chatbot_logger.log_step(
                session_id, 
                ProcessingStep.SBERT_ROUTING, 
                routing_time, 
                f"라우팅결과: {route_result.route.value} (신뢰도: {route_result.confidence:.3f})"
            )
        
        logger.info(f"📍 라우팅 결과: {route_result.route.value} (신뢰도: {route_result.confidence:.3f})")
        
        # 인사말 처리 (LLM 기반)
        if route_result.route == QueryRoute.GREETING:
            if chatbot_logger and session_id:
                chatbot_logger.log_step(session_id, ProcessingStep.GREETING_PIPELINE, 0.0, "인사말 처리 시작")
            
            try:
                llm_greeting_handler = get_llm_greeting_handler()
                greeting_response = llm_greeting_handler.get_greeting_response(request.question)
                
                # 인사말 로깅
                try:
                    if chatbot_logger:
                        chatbot_logger.log_greeting(
                            user_question=request.question,
                            greeting_response=greeting_response["answer"],
                            processing_time=greeting_response["generation_time"],
                            confidence_score=greeting_response["confidence_score"],
                            greeting_type=greeting_response.get("greeting_type", "general")
                        )
                except Exception as log_error:
                    logger.warning(f"인사말 로깅 중 오류 발생: {log_error}")
                
                if chatbot_logger and session_id:
                    chatbot_logger.log_step(session_id, ProcessingStep.COMPLETION, greeting_response["generation_time"], "인사말 처리 완료")
                
                return QuestionResponse(
                    answer=greeting_response["answer"],
                    confidence_score=greeting_response["confidence_score"],
                    used_chunks=[],
                    generation_time=greeting_response["generation_time"],
                    question_type="greeting",
                    llm_model_name=f"llm_greeting_{greeting_response.get('method', 'unknown')}",
                    pipeline_type="greeting",
                    sql_query=None
                )
            except Exception as greeting_error:
                logger.error(f"인사말 처리 중 오류: {greeting_error}")
                # 기본 인사말 (환경변수로 설정 가능)
                fallback_greeting = os.getenv("DEFAULT_GREETING", "안녕하세요! 범용 RAG 시스템에 오신 것을 환영합니다! 🤖")
                
                if chatbot_logger and session_id:
                    chatbot_logger.log_step(session_id, ProcessingStep.ERROR, 0.0, f"인사말 처리 오류: {greeting_error}")
                
                return QuestionResponse(
                    answer=fallback_greeting,
                    confidence_score=0.8,
                    used_chunks=[],
                    generation_time=0.001,
                    question_type="greeting",
                    llm_model_name="fallback_greeting",
                    pipeline_type="greeting",
                    sql_query=None
                )
        
        # SQL 쿼리 처리 (SQL 생성 → DB 실행 → LLM 요약)
        if route_result.route == QueryRoute.SQL_QUERY:
            if chatbot_logger and session_id:
                chatbot_logger.log_step(session_id, ProcessingStep.SQL_PIPELINE, 0.0, "SQL 파이프라인 시작")
            
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
                sql_gen_start = time.time()
                sql_result = sql_generator.generate_sql(request.question, schema)
                sql_gen_time = time.time() - sql_gen_start
                
                if chatbot_logger and session_id:
                    chatbot_logger.log_step(session_id, ProcessingStep.SQL_GENERATION, sql_gen_time, f"SQL생성: {sql_result.query[:50]}...")
                
                if sql_result.is_valid:
                    # SQL 실행
                    sql_exec_start = time.time()
                    execution_result = sql_generator.execute_sql(sql_result)
                    sql_exec_time = time.time() - sql_exec_start
                    
                    if chatbot_logger and session_id:
                        chatbot_logger.log_step(session_id, ProcessingStep.DATABASE_EXECUTION, sql_exec_time, f"DB실행: {execution_result.get('row_count', 0)}행 반환")
                    
                    if execution_result['success']:
                        # LLM으로 결과 요약 생성
                        answer_gen_start = time.time()
                        rows = execution_result.get('data') or []
                        answer_from_sql = answer_generator.generate_from_sql_results(request.question, rows)
                        answer_gen_time = time.time() - answer_gen_start
                        
                        if chatbot_logger and session_id:
                            chatbot_logger.log_step(session_id, ProcessingStep.ANSWER_GENERATION, answer_gen_time, "SQL결과 답변생성")
                        
                        # SQL 질문 로깅
                        try:
                            if chatbot_logger:
                                intent = "SQL_QUERY"
                                keywords = request.question.split()[:5]
                                
                                chatbot_logger.log_question(
                                    user_question=request.question,
                                    question_type=QuestionType.SQL,
                                    intent=intent,
                                    keywords=keywords,
                                    processing_time=answer_from_sql.generation_time,
                                    confidence_score=answer_from_sql.confidence_score,
                                    generated_sql=sql_result.query,
                                    generated_answer=answer_from_sql.content,
                                    model_name=sql_result.model_name,
                                    additional_info={
                                        "pipeline_type": "sql",
                                        "execution_success": True,
                                        "row_count": execution_result.get('row_count', 0)
                                    }
                                )
                        except Exception as log_error:
                            logger.warning(f"SQL 로깅 중 오류 발생: {log_error}")
                        
                        if chatbot_logger and session_id:
                            total_time = time.time() - start_time
                            chatbot_logger.log_step(session_id, ProcessingStep.COMPLETION, total_time, "SQL 파이프라인 완료")
                        
                        return QuestionResponse(
                            answer=answer_from_sql.content,
                            confidence_score=answer_from_sql.confidence_score,
                            used_chunks=[],
                            generation_time=answer_from_sql.generation_time,
                            question_type="sql_query",
                            llm_model_name=answer_from_sql.model_name,
                            pipeline_type="sql",
                            sql_query=sql_result.query
                        )
                    else:
                        logger.warning(f"SQL 실행 실패: {execution_result.get('error')}")
                        if chatbot_logger and session_id:
                            chatbot_logger.log_step(session_id, ProcessingStep.ERROR, 0.0, f"SQL실행실패: {execution_result.get('error')}")
                        # PDF 검색으로 폴백
                        pass
                else:
                    logger.warning(f"SQL 검증 실패: {sql_result.error_message}")
                    if chatbot_logger and session_id:
                        chatbot_logger.log_step(session_id, ProcessingStep.ERROR, 0.0, f"SQL검증실패: {sql_result.error_message}")
                    # PDF 검색으로 폴백
                    pass
            except Exception as sql_error:
                logger.warning(f"SQL 처리 실패, PDF 검색으로 폴백: {sql_error}")
                if chatbot_logger and session_id:
                    chatbot_logger.log_step(session_id, ProcessingStep.ERROR, 0.0, f"SQL처리실패: {sql_error}")
                # PDF 검색으로 폴백
                pass
        
        # PDF 검색 처리 (기본 모드)
        logger.info("📄 PDF 검색 모드로 처리")
        
        if chatbot_logger and session_id:
            chatbot_logger.log_step(session_id, ProcessingStep.PDF_PIPELINE, 0.0, "PDF 파이프라인 시작")
        
        # 1. 질문 분석
        analysis_start = time.time()
        analyzed_question = question_analyzer.analyze_question(
            request.question,
            use_conversation_context=request.use_conversation_context
        )
        analysis_time = time.time() - analysis_start
        
        if chatbot_logger and session_id:
            chatbot_logger.log_step(session_id, ProcessingStep.QUESTION_ANALYSIS, analysis_time, f"질문분석: {analyzed_question.question_type.value}")
        
        # 2. 관련 문서 검색 (유사도 임계값 적용)
        search_start = time.time()
        query_embedding = analyzed_question.embedding
        
        # 벡터 스토어 상태 확인
        total_chunks = vector_store.get_total_chunks()
        logger.info(f"벡터 스토어 상태 - 총 청크 수: {total_chunks}")
        
        if total_chunks == 0:
            logger.error("⚠️ 벡터 스토어에 청크가 없습니다! PDF 업로드가 필요합니다.")
            return QuestionResponse(
                answer="죄송합니다. 현재 문서 데이터베이스가 비어있습니다. 관리자에게 문의해주세요.",
                confidence_score=0.0,
                used_chunks=[],
                generation_time=0.001,
                question_type="error",
                llm_model_name="none",
                pipeline_type="error",
                sql_query=None
            )
        
        relevant_chunks = vector_store.search(
            query_embedding,
            top_k=request.max_chunks,
            similarity_threshold=0.05  # 매우 낮은 임계값으로 모든 관련 문서 검색
        )
        search_time = time.time() - search_start
        
        if chatbot_logger and session_id:
            chatbot_logger.log_step(session_id, ProcessingStep.VECTOR_SEARCH, search_time, f"벡터검색: {len(relevant_chunks)}개 청크 발견")
        
        # 디버깅: 검색 결과 로깅
        logger.info(f"🔍 검색된 청크 수: {len(relevant_chunks)}")
        for i, (chunk, score) in enumerate(relevant_chunks[:3]):
            logger.info(f"  📄 청크 {i+1}: {chunk.chunk_id} (유사도: {score:.3f})")
            logger.info(f"    내용: {chunk.content[:150]}...")
        
        # 검색 결과가 없을 때 경고
        if not relevant_chunks:
            logger.warning("⚠️ 검색된 관련 청크가 없습니다!")
        else:
            logger.info(f"✅ {len(relevant_chunks)}개의 관련 청크를 찾았습니다.")
        
        # 3. 컨텍스트 검증 및 답변 생성
        if not relevant_chunks:
            logger.warning("🔍 검색된 관련 청크가 없어 LLM 직접 답변으로 전환합니다.")
            answer_gen_start = time.time()
            answer = answer_generator.generate_direct_answer(request.question)
            answer_gen_time = time.time() - answer_gen_start
            
            if chatbot_logger and session_id:
                chatbot_logger.log_step(session_id, ProcessingStep.ANSWER_GENERATION, answer_gen_time, "직접답변생성 (청크없음)")
        else:
            # 컨텍스트 내용 로깅
            context_content = "\n".join([chunk.content[:100] + "..." for chunk, _ in relevant_chunks[:3]])
            logger.info(f"📄 컨텍스트 내용 (일부):\n{context_content}")
            
            answer_gen_start = time.time()
            answer = answer_generator.generate_answer(
                analyzed_question,
                relevant_chunks,
                conversation_history=None,
                pdf_id=request.pdf_id
            )
            answer_gen_time = time.time() - answer_gen_start
            
            if chatbot_logger and session_id:
                chatbot_logger.log_step(session_id, ProcessingStep.ANSWER_GENERATION, answer_gen_time, f"컨텍스트답변생성: {len(relevant_chunks)}개 청크 사용")
        
                # 4. 대화 히스토리에 추가
        question_analyzer.add_conversation_item(
            question=request.question,
            answer=answer.content,
            used_chunks=answer.used_chunks,
            confidence_score=answer.confidence_score
        )
        
        # 5. API 로깅
        try:
            if chatbot_logger:
                # 질문 의도 및 키워드 추출 (간단한 버전)
                intent = "PDF_QUERY"
                keywords = request.question.split()[:5]  # 첫 5개 단어를 키워드로 사용
                
                chatbot_logger.log_question(
                    user_question=request.question,
                    question_type=QuestionType.PDF,
                    intent=intent,
                    keywords=keywords,
                    processing_time=answer.generation_time,
                    confidence_score=answer.confidence_score,
                    generated_answer=answer.content,
                    used_chunks=answer.used_chunks,
                    model_name=answer.model_name,
                    additional_info={
                        "pipeline_type": route_result.route.value,
                        "user_id": request.user_id
                    }
                )
        except Exception as log_error:
            logger.warning(f"API 로깅 중 오류 발생: {log_error}")
        
        # 완료 로그
        if chatbot_logger and session_id:
            total_time = time.time() - start_time
            chatbot_logger.log_step(session_id, ProcessingStep.COMPLETION, total_time, "PDF 파이프라인 완료")
        
        return QuestionResponse(
            answer=answer.content,
            confidence_score=answer.confidence_score,
            used_chunks=answer.used_chunks,
            generation_time=answer.generation_time,
            question_type=analyzed_question.question_type.value,
            llm_model_name=answer.model_name,
            pipeline_type=route_result.route.value,
            sql_query=None
        )
        
    except Exception as e:
        logger.error(f"질문 처리 실패: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        
        # 에러 로깅
        try:
            if chatbot_logger:
                if session_id:
                    chatbot_logger.log_step(session_id, ProcessingStep.ERROR, 0.0, f"전체처리오류: {str(e)}")
                
                chatbot_logger.log_error(
                    user_question=request.question,
                    error_message=str(e),
                    question_type=QuestionType.UNKNOWN
                )
        except Exception as log_error:
            logger.warning(f"에러 로깅 실패: {log_error}")
        
        # 사용자 친화적인 에러 메시지
        error_message = "죄송합니다. 질문 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        raise HTTPException(status_code=500, detail=error_message)

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
        # 벡터 저장소에서 청크 수 확인 (get_all_chunks 메서드가 없으므로 다른 방법 사용)
        total_chunks = 0
        if vector_store and hasattr(vector_store, 'chunks'):
            total_chunks = len(vector_store.chunks)
        elif vector_store and hasattr(vector_store, 'faiss_store') and hasattr(vector_store.faiss_store, 'chunks'):
            total_chunks = len(vector_store.faiss_store.chunks)
        
        return SystemStatusResponse(
            status="running",
            llm_model_loaded=model_loaded,
            total_pdfs=total_pdfs,
            total_chunks=total_chunks,
            memory_usage=memory_usage
        )
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"시스템 상태 조회 실패: {str(e)}")


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

@app.get("/pdfs")
async def get_pdf_list():
    """등록된 PDF 목록 조회"""
    try:
        pdfs = []
        for pdf_id, metadata in pdf_metadata.items():
            pdfs.append({
                "pdf_id": pdf_id,
                "filename": metadata.get("filename", "Unknown"),
                "upload_time": metadata.get("upload_time", ""),
                "total_pages": metadata.get("total_pages", 0),
                "total_chunks": metadata.get("total_chunks", 0),
                "file_size": metadata.get("file_size", 0)
            })
        
        return {"pdfs": pdfs}
        
    except Exception as e:
        logger.error(f"PDF 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"PDF 목록 조회 실패: {str(e)}")

@app.post("/auto-upload")
async def auto_upload_pdfs():
    """data 폴더의 PDF 파일들을 자동으로 업로드"""
    try:
        import os
        from pathlib import Path
        
        # data 폴더와 data/pdfs 폴더 모두 확인
        data_folders = ["./data", "./data/pdfs"]
        pdf_files = []
        
        for data_folder in data_folders:
            if not os.path.exists(data_folder):
                logger.warning(f"{data_folder} 폴더가 존재하지 않습니다.")
                continue
            
            # 재귀적으로 PDF 파일 찾기
            for root, dirs, files in os.walk(data_folder):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_path = os.path.join(root, file)
                        pdf_files.append(pdf_path)
        
        if not pdf_files:
            return {"message": "업로드할 PDF 파일이 없습니다.", "uploaded_count": 0}
        
        logger.info(f"자동 업로드 시작: {len(pdf_files)}개의 PDF 파일")
        
        uploaded_count = 0
        failed_count = 0
        
        for pdf_path in pdf_files:
            try:
                # 이미 처리된 PDF인지 확인
                pdf_id = os.path.basename(pdf_path)
                if pdf_id in pdf_metadata:
                    logger.info(f"이미 처리된 PDF 건너뛰기: {pdf_id}")
                    continue
                
                # PDF 처리
                chunks, metadata = pdf_processor.process_pdf(pdf_path)
                vector_store.add_chunks(chunks)
                
                # 메타데이터 저장
                pdf_metadata[pdf_id] = {
                    "filename": pdf_id,
                    "total_pages": len(chunks),
                    "upload_time": datetime.now().isoformat(),
                    "total_chunks": len(chunks),
                    "file_size": os.path.getsize(pdf_path)
                }
                
                uploaded_count += 1
                logger.info(f"PDF 자동 업로드 완료: {pdf_id} ({len(chunks)}개 청크)")
                
            except Exception as e:
                logger.error(f"PDF 자동 업로드 실패 {pdf_path}: {e}")
                failed_count += 1
        
        return {
            "message": f"자동 업로드 완료: {uploaded_count}개 성공, {failed_count}개 실패",
            "uploaded_count": uploaded_count,
            "failed_count": failed_count,
            "total_files": len(pdf_files)
        }
        
    except Exception as e:
        logger.error(f"자동 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"자동 업로드 실패: {str(e)}")

@app.get("/api/greeting/statistics")
async def get_greeting_statistics():
    """인사말 처리 통계 확인"""
    try:
        llm_greeting_handler = get_llm_greeting_handler()
        stats = llm_greeting_handler.get_statistics()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"인사말 통계 확인 중 오류: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/company/info")
async def get_company_info():
    """회사 정보 조회"""
    try:
        from core.config.company_config import CompanyConfig
        company_config = CompanyConfig()
        company_info = company_config.get_company_info()
        return {
            "status": "success",
            "data": company_info
        }
    except Exception as e:
        logger.error(f"회사 정보 조회 중 오류: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/keywords/cache/stats", response_model=KeywordCacheResponse)
async def get_keyword_cache_stats():
    """키워드 캐시 통계 조회"""
    try:
        pdf_processor = get_pdf_processor()
        stats = pdf_processor.get_keyword_cache_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=400, detail=stats["error"])
        
        return KeywordCacheResponse(**stats)
    except Exception as e:
        logger.error(f"키워드 캐시 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/keywords/pipeline/add", response_model=KeywordPipelineResponse)
async def add_keywords_to_pipeline():
    """추출된 키워드를 파이프라인 설정에 추가"""
    try:
        pdf_processor = get_pdf_processor()
        pdf_processor.add_keywords_to_pipeline()
        
        # 추가된 키워드 정보 가져오기
        stats = pdf_processor.get_keyword_cache_stats()
        frequent_keywords = pdf_processor.keyword_extractor.get_frequent_keywords()
        
        return KeywordPipelineResponse(
            success=True,
            added_keywords=frequent_keywords[:20],  # 최대 20개
            message=f"파이프라인에 {len(frequent_keywords)}개 키워드 추가 완료"
        )
    except Exception as e:
        logger.error(f"키워드 파이프라인 추가 실패: {e}")
        return KeywordPipelineResponse(
            success=False,
            added_keywords=[],
            message=str(e)
        )

@app.delete("/api/keywords/cache/clear")
async def clear_keyword_cache():
    """키워드 캐시 초기화"""
    try:
        pdf_processor = get_pdf_processor()
        pdf_processor.clear_keyword_cache()
        return {"message": "키워드 캐시 초기화 완료"}
    except Exception as e:
        logger.error(f"키워드 캐시 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/keywords/cache/save")
async def save_keyword_cache():
    """키워드 캐시를 파일로 저장"""
    try:
        pdf_processor = get_pdf_processor()
        pdf_processor.save_keyword_cache()
        return {"message": "키워드 캐시 저장 완료"}
    except Exception as e:
        logger.error(f"키워드 캐시 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/keywords/cache/load")
async def load_keyword_cache():
    """파일에서 키워드 캐시 로드"""
    try:
        pdf_processor = get_pdf_processor()
        pdf_processor.load_keyword_cache()
        return {"message": "키워드 캐시 로드 완료"}
    except Exception as e:
        logger.error(f"키워드 캐시 로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 메모리 모니터링 API 엔드포인트 추가
@app.get("/memory/status")
async def get_memory_status():
    """메모리 상태 정보 반환"""
    try:
        from core.utils.memory_optimizer import memory_optimizer, model_memory_manager
        
        # 시스템 메모리 정보
        memory_info = memory_optimizer.get_memory_info()
        
        # 모델 메모리 정보
        model_status = model_memory_manager.get_model_status()
        
        return {
            "system_memory": {
                "total_gb": memory_info.total,
                "available_gb": memory_info.available,
                "used_gb": memory_info.used,
                "percent": memory_info.percent,
                "process_memory_gb": memory_info.process_memory
            },
            "model_memory": model_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"메모리 상태 조회 실패: {e}")
        return {"error": str(e)}

@app.post("/memory/optimize")
async def optimize_memory():
    """메모리 최적화 실행"""
    try:
        from core.utils.memory_optimizer import memory_optimizer
        
        # 메모리 최적화 실행
        after_info = memory_optimizer.optimize_memory(aggressive=True)
        
        return {
            "message": "메모리 최적화 완료",
            "optimized_memory_gb": after_info.used,
            "memory_percent": after_info.percent,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"메모리 최적화 실패: {e}")
        return {"error": str(e)}

@app.get("/memory/models")
async def get_loaded_models():
    """로드된 모델 목록 반환"""
    try:
        from core.utils.memory_optimizer import model_memory_manager
        
        model_status = model_memory_manager.get_model_status()
        
        return {
            "loaded_models": model_status["loaded_models"],
            "total_memory_gb": model_status["total_memory_gb"],
            "max_memory_gb": model_status["max_memory_gb"],
            "model_details": model_status["model_details"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"모델 목록 조회 실패: {e}")
        return {"error": str(e)}

@app.delete("/memory/models/{model_name}")
async def unload_model(model_name: str):
    """특정 모델 언로드"""
    try:
        from core.utils.memory_optimizer import model_memory_manager
        
        model_memory_manager.unload_model(model_name)
        
        return {
            "message": f"모델 {model_name} 언로드 완료",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"모델 언로드 실패: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # 서버 시작 전 시스템 초기화
    initialize_system()
    uvicorn.run(app, host="0.0.0.0", port=8008)

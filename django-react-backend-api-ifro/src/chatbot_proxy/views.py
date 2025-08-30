"""
챗봇 프록시 API 뷰
프론트엔드의 챗봇 요청을 챗봇 서버로 전달하는 프록시 역할을 수행합니다.
"""

import httpx
import logging
import asyncio
from typing import Dict, Any, Optional, List
from ninja_extra import Router
from ninja import Schema
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth
from django.conf import settings
import os

logger = logging.getLogger(__name__)

# 챗봇 서버 URL 설정
CHATBOT_BASE_URL = os.getenv('CHATBOT_URL', 'http://chatbot:8008')

router = Router()

# Pydantic 스키마 정의
class ChatMessageRequest(Schema):
    message: str

class ChatMessageResponse(Schema):
    success: bool
    response: str
    timestamp: str

class AIQuestionRequest(Schema):
    question: str
    pdf_id: str = 'default_pdf'
    use_conversation_context: bool = True
    max_chunks: int = 5
    use_dual_pipeline: bool = True

class AIQuestionResponse(Schema):
    answer: str
    confidence_score: float
    question_type: str
    generation_time: float
    model_name: str
    used_chunks: Optional[List[str]] = None
    pipeline_type: Optional[str] = None
    sql_query: Optional[str] = None

class ChatServerStatus(Schema):
    status: str
    model_loaded: bool
    total_pdfs: int
    total_chunks: int
    memory_usage: Optional[Dict[str, Any]] = None

class PDFInfo(Schema):
    pdf_id: str
    filename: str
    upload_time: str
    total_pages: int
    total_chunks: int

class PDFListResponse(Schema):
    pdfs: List[PDFInfo]

# 비동기 HTTP 클라이언트 헬퍼 함수
async def make_chatbot_request(method: str, endpoint: str, data: Dict[str, Any] = None, timeout: int = 60) -> Dict[str, Any]:
    """챗봇 서버에 HTTP 요청을 보내는 헬퍼 함수"""
    url = f"{CHATBOT_BASE_URL}{endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == 'GET':
                response = await client.get(url)
            elif method.upper() == 'POST':
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
            
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException:
        logger.error(f"챗봇 서버 요청 타임아웃: {url}")
        raise HttpError(504, "챗봇 서버 응답 시간이 초과되었습니다.")
    except httpx.ConnectError:
        logger.error(f"챗봇 서버 연결 실패: {url}")
        raise HttpError(503, "챗봇 서버에 연결할 수 없습니다.")
    except httpx.HTTPStatusError as e:
        logger.error(f"챗봇 서버 HTTP 오류: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 404:
            raise HttpError(404, "요청한 리소스를 찾을 수 없습니다.")
        elif e.response.status_code == 500:
            raise HttpError(500, "챗봇 서버 내부 오류가 발생했습니다.")
        else:
            raise HttpError(502, f"챗봇 서버 오류: {e.response.status_code}")
    except Exception as e:
        logger.error(f"챗봇 서버 요청 중 예외 발생: {str(e)}")
        raise HttpError(500, "챗봇 서버 요청 처리 중 오류가 발생했습니다.")

# 동기 래퍼 함수
def sync_make_chatbot_request(method: str, endpoint: str, data: Dict[str, Any] = None, timeout: int = 60) -> Dict[str, Any]:
    """비동기 챗봇 요청을 동기적으로 실행하는 래퍼"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(make_chatbot_request(method, endpoint, data, timeout))

# API 엔드포인트들

@router.post("/chat", response=ChatMessageResponse)
def proxy_simple_chat(request, data: ChatMessageRequest):
    """간단한 챗봇 메시지 프록시"""
    try:
        response_data = sync_make_chatbot_request(
            method='POST',
            endpoint='/chat',
            data={'message': data.message},
            timeout=30
        )
        
        return ChatMessageResponse(
            success=response_data.get('success', True),
            response=response_data.get('response', ''),
            timestamp=response_data.get('timestamp', '')
        )
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"간단한 챗봇 프록시 오류: {str(e)}")
        raise HttpError(500, "챗봇 메시지 처리 중 오류가 발생했습니다.")

@router.post("/ask", response=AIQuestionResponse)
def proxy_ai_question(request, data: AIQuestionRequest):
    """AI 질문 답변 프록시"""
    try:
        request_data = {
            'question': data.question,
            'pdf_id': data.pdf_id,
            'use_conversation_context': data.use_conversation_context,
            'max_chunks': data.max_chunks,
            'use_dual_pipeline': data.use_dual_pipeline
        }
        
        response_data = sync_make_chatbot_request(
            method='POST',
            endpoint='/ask',
            data=request_data,
            timeout=120  # AI 처리 시간을 고려하여 더 긴 타임아웃
        )
        
        return AIQuestionResponse(
            answer=response_data.get('answer', ''),
            confidence_score=response_data.get('confidence_score', 0.0),
            question_type=response_data.get('question_type', 'unknown'),
            generation_time=response_data.get('generation_time', 0.0),
            model_name=response_data.get('model_name', 'unknown'),
            used_chunks=response_data.get('used_chunks', []),
            pipeline_type=response_data.get('pipeline_type'),
            sql_query=response_data.get('sql_query')
        )
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"AI 질문 프록시 오류: {str(e)}")
        raise HttpError(500, "AI 질문 처리 중 오류가 발생했습니다.")

@router.get("/status", response=ChatServerStatus)
def proxy_chatbot_status(request):
    """챗봇 서버 상태 조회 프록시"""
    try:
        response_data = sync_make_chatbot_request(
            method='GET',
            endpoint='/status',
            timeout=10
        )
        
        return ChatServerStatus(
            status=response_data.get('status', 'unknown'),
            model_loaded=response_data.get('model_loaded', False),
            total_pdfs=response_data.get('total_pdfs', 0),
            total_chunks=response_data.get('total_chunks', 0),
            memory_usage=response_data.get('memory_usage')
        )
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"챗봇 상태 프록시 오류: {str(e)}")
        raise HttpError(500, "챗봇 상태 조회 중 오류가 발생했습니다.")

@router.get("/health")
def proxy_health_check(request):
    """챗봇 서버 헬스 체크 프록시"""
    try:
        response_data = sync_make_chatbot_request(
            method='GET',
            endpoint='/health',
            timeout=5
        )
        
        return response_data
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"헬스 체크 프록시 오류: {str(e)}")
        raise HttpError(500, "헬스 체크 중 오류가 발생했습니다.")

@router.get("/pdfs", response=PDFListResponse)
def proxy_pdf_list(request):
    """등록된 PDF 목록 조회 프록시"""
    try:
        response_data = sync_make_chatbot_request(
            method='GET',
            endpoint='/pdfs',
            timeout=10
        )
        
        pdfs = []
        for pdf_data in response_data.get('pdfs', []):
            pdfs.append(PDFInfo(
                pdf_id=pdf_data.get('pdf_id', ''),
                filename=pdf_data.get('filename', ''),
                upload_time=pdf_data.get('upload_time', ''),
                total_pages=pdf_data.get('total_pages', 0),
                total_chunks=pdf_data.get('total_chunks', 0)
            ))
        
        return PDFListResponse(pdfs=pdfs)
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"PDF 목록 프록시 오류: {str(e)}")
        raise HttpError(500, "PDF 목록 조회 중 오류가 발생했습니다.")

# 대화 기록 관련 프록시 엔드포인트들

@router.get("/conversation_history")
def proxy_conversation_history(request, pdf_id: str, max_items: int = 10):
    """대화 기록 조회 프록시"""
    try:
        response_data = sync_make_chatbot_request(
            method='GET',
            endpoint=f'/conversation_history?pdf_id={pdf_id}&max_items={max_items}',
            timeout=10
        )
        
        return response_data
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"대화 기록 프록시 오류: {str(e)}")
        raise HttpError(500, "대화 기록 조회 중 오류가 발생했습니다.")

@router.delete("/conversation_history")
def proxy_clear_conversation_history(request):
    """대화 기록 초기화 프록시"""
    try:
        response_data = sync_make_chatbot_request(
            method='DELETE',
            endpoint='/conversation_history',
            timeout=10
        )
        
        return response_data
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"대화 기록 초기화 프록시 오류: {str(e)}")
        raise HttpError(500, "대화 기록 초기화 중 오류가 발생했습니다.")



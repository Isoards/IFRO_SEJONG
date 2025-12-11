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
CHATBOT_BASE_URL = os.getenv('CHATBOT_URL', 'http://chatbot:8000')

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
    mode: str = 'accuracy'
    k: str = 'auto'

class AIQuestionResponse(Schema):
    """v5.2 API AskResponse와 호환"""
    answer: str
    confidence: float = 0.0
    sources: Optional[List[Dict[str, Any]]] = None
    reasoning_used: bool = False
    reasoning_trace: Optional[List[str]] = None
    action_suggested: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    fallback_used: Optional[bool] = None
    timestamp: Optional[str] = None

class ChatServerStatus(Schema):
    """v5.2 API 상태 응답과 호환되도록 수정"""
    status: str = 'unknown'
    ready: bool = True
    version: str = '5.2.0'
    entity_count: int = 0
    relation_count: int = 0
    vector_count: int = 0
    llm_available: bool = False
    reasoning_enabled: bool = True
    action_enabled: bool = True
    # 하위 호환성
    ai_available: bool = False
    model_loaded: bool = False
    total_pdfs: int = 0
    total_chunks: int = 0
    memory_usage: Optional[Dict[str, Any]] = None

class PDFInfo(Schema):
    pdf_id: str
    filename: str
    upload_time: str
    total_pages: int
    total_chunks: int

class PDFListResponse(Schema):
    pdfs: List[PDFInfo]

class BatchQuestionRequest(Schema):
    items: List[Dict[str, Any]]
    mode: str = 'accuracy'

class BatchQuestionResponse(Schema):
    results: List[Dict[str, Any]]
    config_hash: str

# 비동기 HTTP 클라이언트 헬퍼 함수 (최적화된 버전)
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
        # 타임아웃은 중요한 오류이므로 로깅 유지
        logger.error(f"챗봇 서버 요청 타임아웃: {url}")
        raise HttpError(504, "챗봇 서버 응답 시간이 초과되었습니다.")
    except httpx.ConnectError:
        # 연결 오류는 중요한 오류이므로 로깅 유지
        logger.error(f"챗봇 서버 연결 실패: {url}")
        raise HttpError(503, "챗봇 서버에 연결할 수 없습니다.")
    except httpx.HTTPStatusError as e:
        # HTTP 오류는 중요한 오류이므로 로깅 유지
        logger.error(f"챗봇 서버 HTTP 오류: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 404:
            raise HttpError(404, "요청한 리소스를 찾을 수 없습니다.")
        elif e.response.status_code == 500:
            raise HttpError(500, "챗봇 서버 내부 오류가 발생했습니다.")
        else:
            raise HttpError(502, f"챗봇 서버 오류: {e.response.status_code}")
    except Exception as e:
        # 일반적인 예외는 디버그 레벨로 로깅
        logger.debug(f"챗봇 서버 요청 중 예외 발생: {str(e)}")
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
            endpoint='/api/ask',
            data={'question': data.message, 'mode': 'accuracy', 'k': 'auto'},
            timeout=120  # AI 처리 시간을 고려하여 타임아웃 증가
        )
        
        return ChatMessageResponse(
            success=True,
            response=response_data.get('answer', ''),
            timestamp=str(response_data.get('timestamp', ''))
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
            'mode': data.mode,
            'k': data.k
        }
        
        response_data = sync_make_chatbot_request(
            method='POST',
            endpoint='/api/ask',
            data=request_data,
            timeout=120  # AI 처리 시간을 고려하여 더 긴 타임아웃
        )
        
        # v5.2 AskResponse 형식 처리
        # sources 변환 (SourceInfo -> Dict)
        sources_raw = response_data.get('sources', [])
        sources = []
        for s in sources_raw:
            if isinstance(s, dict):
                sources.append(s)
            else:
                sources.append({'entity_name': str(s), 'confidence': 0.5})
        
        return AIQuestionResponse(
            answer=response_data.get('answer', ''),
            confidence=response_data.get('confidence', 0.0),
            sources=sources,
            reasoning_used=response_data.get('reasoning_used', False),
            reasoning_trace=response_data.get('reasoning_trace', []),
            action_suggested=response_data.get('action_suggested'),
            metrics=response_data.get('metrics', {}),
            fallback_used=False,  # v5.2에서는 사용 안함
            timestamp=response_data.get('timestamp')
        )
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"AI 질문 프록시 오류: {str(e)}")
        raise HttpError(500, "AI 질문 처리 중 오류가 발생했습니다.")

@router.post("/batch", response=BatchQuestionResponse)
def proxy_batch_questions(request, data: BatchQuestionRequest):
    """배치 질문 답변 프록시"""
    try:
        request_data = {
            'items': data.items,
            'mode': data.mode
        }
        
        response_data = sync_make_chatbot_request(
            method='POST',
            endpoint='/api/qa/batch',
            data=request_data,
            timeout=300  # 배치 처리 시간을 고려하여 더 긴 타임아웃
        )
        
        return BatchQuestionResponse(
            results=response_data.get('results', []),
            config_hash=response_data.get('config_hash', '')
        )
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"배치 질문 프록시 오류: {str(e)}")
        raise HttpError(500, "배치 질문 처리 중 오류가 발생했습니다.")

@router.get("/status", response=ChatServerStatus)
def proxy_chatbot_status(request):
    """챗봇 서버 상태 조회 프록시 - v5.2 API 호환"""
    try:
        response_data = sync_make_chatbot_request(
            method='GET',
            endpoint='/status',
            timeout=10
        )
        
        # v5.2 StatusResponse 형식 처리
        return ChatServerStatus(
            status='healthy' if response_data.get('ready', False) else 'initializing',
            ready=response_data.get('ready', False),
            version=response_data.get('version', '5.2.0'),
            entity_count=response_data.get('entity_count', 0),
            relation_count=response_data.get('relation_count', 0),
            vector_count=response_data.get('vector_count', 0),
            llm_available=response_data.get('llm_available', False),
            reasoning_enabled=response_data.get('reasoning_enabled', True),
            action_enabled=response_data.get('action_enabled', True),
            # 하위 호환성 매핑
            ai_available=response_data.get('llm_available', False),
            model_loaded=response_data.get('ready', False),
            total_pdfs=0,
            total_chunks=response_data.get('vector_count', 0),
            memory_usage=None
        )
        
    except HttpError:
        raise
    except Exception as e:
        # 상태 조회 실패는 디버그 레벨로 로깅
        logger.debug(f"챗봇 상태 프록시 오류: {str(e)}")
        raise HttpError(500, "챗봇 상태 조회 중 오류가 발생했습니다.")

@router.get("/health")
def proxy_health_check(request):
    """챗봇 서버 헬스 체크 프록시 - 새로운 FastAPI 서버에 맞게 수정"""
    try:
        response_data = sync_make_chatbot_request(
            method='GET',
            endpoint='/healthz',
            timeout=5
        )
        
        return response_data
        
    except HttpError:
        raise
    except Exception as e:
        # 헬스 체크 실패는 디버그 레벨로 로깅
        logger.debug(f"헬스 체크 프록시 오류: {str(e)}")
        raise HttpError(500, "헬스 체크 중 오류가 발생했습니다.")

@router.get("/metrics")
def proxy_metrics(request):
    """챗봇 서버 메트릭 조회 프록시"""
    try:
        url = f"{CHATBOT_BASE_URL}/metrics"
        
        import httpx
        with httpx.Client(timeout=10) as client:
            response = client.get(url)
            response.raise_for_status()
            
            # 메트릭은 텍스트 형식으로 반환되므로 텍스트로 처리
            return {"metrics": response.text}
        
    except httpx.TimeoutException:
        logger.error(f"챗봇 서버 메트릭 요청 타임아웃: {url}")
        raise HttpError(504, "챗봇 서버 메트릭 응답 시간이 초과되었습니다.")
    except httpx.ConnectError:
        logger.error(f"챗봇 서버 메트릭 연결 실패: {url}")
        raise HttpError(503, "챗봇 서버에 연결할 수 없습니다.")
    except httpx.HTTPStatusError as e:
        logger.error(f"챗봇 서버 메트릭 HTTP 오류: {e.response.status_code} - {e.response.text}")
        raise HttpError(502, f"챗봇 서버 메트릭 오류: {e.response.status_code}")
    except Exception as e:
        logger.debug(f"메트릭 프록시 오류: {str(e)}")
        raise HttpError(500, "메트릭 조회 중 오류가 발생했습니다.")

@router.get("/pdfs", response=PDFListResponse)
def proxy_pdf_list(request):
    """등록된 PDF 목록 조회 프록시"""
    try:
        # 새로운 FastAPI 서버에서는 PDF 목록을 별도로 관리하지 않으므로 빈 목록 반환
        return PDFListResponse(pdfs=[])
        
    except Exception as e:
        logger.debug(f"PDF 목록 프록시 오류: {str(e)}")
        raise HttpError(500, "PDF 목록 조회 중 오류가 발생했습니다.")

# 대화 기록 관련 프록시 엔드포인트들 - 새로운 서버에서는 지원하지 않음

@router.get("/conversation_history")
def proxy_conversation_history(request, pdf_id: str, max_items: int = 10):
    """대화 기록 조회 프록시 - 새로운 서버에서는 빈 기록 반환"""
    try:
        # 새로운 FastAPI 서버에서는 대화 기록을 별도로 관리하지 않으므로 빈 기록 반환
        return {"history": []}
        
    except Exception as e:
        logger.debug(f"대화 기록 프록시 오류: {str(e)}")
        raise HttpError(500, "대화 기록 조회 중 오류가 발생했습니다.")

@router.delete("/conversation_history")
def proxy_clear_conversation_history(request):
    """대화 기록 초기화 프록시 - 새로운 서버에서는 항상 성공 반환"""
    try:
        # 새로운 FastAPI 서버에서는 대화 기록을 별도로 관리하지 않으므로 성공 반환
        return {"success": True, "message": "대화 기록이 초기화되었습니다."}
        
    except Exception as e:
        logger.debug(f"대화 기록 초기화 프록시 오류: {str(e)}")
        raise HttpError(500, "대화 기록 초기화 중 오류가 발생했습니다.")



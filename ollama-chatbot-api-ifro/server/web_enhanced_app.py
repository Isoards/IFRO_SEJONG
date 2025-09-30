"""
웹 검색 기능이 추가된 FastAPI 서버
RAG + 웹 검색을 결합하여 최신 정보를 활용할 수 있도록 함
"""
try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except Exception:
    FASTAPI_AVAILABLE = False

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from unifiedpdf.config import PipelineConfig
from unifiedpdf.facade import UnifiedPDFPipeline
from unifiedpdf.types import Chunk
from unifiedpdf.web_search import create_hybrid_rag_with_web
from unifiedpdf.sql_integration import create_traffic_analyzer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/chatbot_conversations.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 질문/답변 전용 로거 생성
qa_logger = logging.getLogger('qa_conversations')
qa_handler = logging.FileHandler('logs/qa_detailed.log', encoding='utf-8')
qa_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
qa_logger.addHandler(qa_handler)
qa_logger.setLevel(logging.INFO)

# uvicorn access 로그 레벨 조정
import logging
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.setLevel(logging.ERROR)

uvicorn_main_logger = logging.getLogger("uvicorn")
uvicorn_main_logger.setLevel(logging.WARNING)

def get_sql_based_answer(question: str, traffic_analyzer) -> Optional[Dict]:
    """SQL 데이터 기반 답변 생성"""
    try:
        # 교통사고 관련 질문 감지
        if any(keyword in question for keyword in ['교통사고', '사고', '충돌', '안전', '위험']):
            analysis = traffic_analyzer.analyze_traffic_safety()
            
            if analysis:
                # 구별 교통사고 통계
                district_stats = analysis.get('high_risk_districts', [])
                incident_types = analysis.get('common_incident_types', [])
                recommendations = analysis.get('safety_recommendations', [])
                
                answer = "📊 **교통 안전 분석 결과**\n\n"
                
                if district_stats:
                    answer += "**🚨 사고 다발 지역 (상위 3개 구):**\n"
                    for i, district in enumerate(district_stats[:3], 1):
                        answer += f"{i}. {district['district']}: {district['incident_count']}건\n"
                    answer += "\n"
                
                if incident_types:
                    answer += "**⚠️ 주요 사고 유형:**\n"
                    for i, incident in enumerate(incident_types[:3], 1):
                        answer += f"{i}. {incident['type']}: {incident['count']}건\n"
                    answer += "\n"
                
                if recommendations:
                    answer += "**💡 개선 권고사항:**\n"
                    for i, rec in enumerate(recommendations, 1):
                        answer += f"{i}. {rec}\n"
                
                return {
                    "answer": answer,
                    "confidence": 0.9,
                    "sources": [],
                    "metrics": {"sql_data_used": True},
                    "fallback_used": "none",
                    "web_search_used": False,
                    "web_search_results": ""
                }
            
            return None
    except Exception as e:
        logger.error(f"SQL 기반 답변 생성 실패: {e}")
        return None

def get_general_traffic_answer(question: str) -> Optional[Dict]:
    """일반적인 교통 질문에 대한 LLM 자체 답변"""
    try:
        import requests
        import json
        
        # 일반적인 교통 관련 키워드 감지
        traffic_keywords = [
            '길이 막혀', '교통체증', '정체', '혼잡', '막힘',
            '버스', '지하철', '택시', '자전거', '도로',
            '신호등', '횡단보도', '교차로', '회전교차로',
            '주차', '주차장', '주차비', '주차요금',
            '교통수단', '대중교통', '교통편', '이동'
        ]
        
        if any(keyword in question for keyword in traffic_keywords):
            # Ollama API를 사용하여 일반적인 교통 질문 답변
            ollama_url = "http://ollama:11434/api/generate"
            
            prompt = f"""
당신은 교통 전문가입니다. 다음 교통 관련 질문에 대해 실용적이고 도움이 되는 답변을 해주세요.

질문: {question}

답변 요구사항:
1. 실용적이고 구체적인 조언 제공
2. 교통 상황에 대한 이해와 공감 표현
3. 대안 제시 (대중교통, 우회로, 시간대 조정 등)
4. 교통 안전 관련 주의사항 포함
5. 한국어로 자연스럽게 답변

답변:
"""
            
            payload = {
                "model": "qwen2.5:3b-instruct",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 300
                }
            }
            
            response = requests.post(ollama_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            answer = result.get('response', '').strip()
            
            if answer:
                return {
                    "answer": answer,
                    "confidence": 0.8,
                    "sources": [],
                    "metrics": {"general_traffic_advice": True},
                    "fallback_used": "none",
                    "web_search_used": False,
                    "web_search_results": ""
                }
            
        return None
    except Exception as e:
        logger.error(f"일반 교통 질문 답변 생성 실패: {e}")
        return None

def log_conversation(question: str, answer: str, confidence: float, sources: list, metrics: dict, web_search_used: bool = False):
    """채팅 대화를 로그 파일에 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 상세한 질문/답변 로그
    qa_logger.info("=" * 80)
    qa_logger.info(f"🤖 질문: {question}")
    qa_logger.info(f"✅ 답변: {answer}")
    qa_logger.info(f"📊 신뢰도: {confidence:.2f} | 소스 수: {len(sources)} | Fallback: {metrics.get('fallback_used', False)} | 웹검색: {web_search_used}")
    qa_logger.info("=" * 80)
    
    # JSONL 형식으로 로그 파일에 추가
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer,
        "confidence": confidence,
        "sources_count": len(sources),
        "metrics": metrics,
        "sources": sources,
        "web_search_used": web_search_used
    }
    
    log_file = Path("logs/conversations.jsonl")
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # 간단한 요약 로그
    logger.info(f"💬 Q&A 완료 | 질문: {question[:50]}... | 답변길이: {len(answer)} | 신뢰도: {confidence:.2f} | 웹검색: {web_search_used}")

def _load_corpus(path: str) -> List[Chunk]:
    """코퍼스 로드"""
    p = Path(path)
    chunks: List[Chunk] = []
    if not p.exists():
        return chunks
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            chunks.append(
                Chunk(
                    doc_id=obj.get("doc_id", obj.get("filename", "doc")),
                    filename=obj.get("filename", "doc"),
                    page=obj.get("page"),
                    start_offset=int(obj.get("start", 0)),
                    length=int(obj.get("length", len(obj.get("text", "")))),
                    text=obj.get("text", ""),
                    extra=obj.get("extra", {}),
                )
            )
    return chunks

if FASTAPI_AVAILABLE:
    app = FastAPI(title="교통 정책 챗봇 (RAG + 웹 검색)", version="2.0.0")
    
    # 설정 로드
    cfg = PipelineConfig()
    corpus_path = str(Path("data/corpus_v1.jsonl"))
    pipe = UnifiedPDFPipeline(_load_corpus(corpus_path), cfg)
    
    # 웹 검색 기능 추가
    web_search_api_key = os.getenv('WEB_SEARCH_API_KEY', None)
    web_search_engine = os.getenv('WEB_SEARCH_ENGINE', 'google')
    
    # 하이브리드 RAG 시스템 생성
    hybrid_rag = create_hybrid_rag_with_web(
        rag_pipeline=pipe,
        api_key=web_search_api_key,
        search_engine=web_search_engine
    )
    
    # 교통 데이터 분석기 생성
    traffic_analyzer = create_traffic_analyzer()
    
    _warmed = False
    AGG = {"requests_total": 0, "no_answer_total": 0, "web_search_total": 0}
    
    class AskRequest(BaseModel):
        question: str
        mode: str = "accuracy"
        k: str = "auto"
        use_web_search: bool = True  # 웹 검색 사용 여부
    
    class BatchRequest(BaseModel):
        items: list
        mode: str = "accuracy"
        use_web_search: bool = True
    
    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "warmed": _warmed, "web_search_enabled": True}
    
    @app.get("/status")
    def status():
        """AI 서비스 상태 확인 엔드포인트"""
        model_status = "unknown"
        try:
            import urllib.request
            import json
            ollama_host = os.getenv('OLLAMA_HOST', 'ollama')
            url = f"http://{ollama_host}:11434/api/tags"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                model_name = cfg.model_name
                if any(m.get("name") == model_name for m in models):
                    model_status = "available"
                else:
                    model_status = "not_found"
        except Exception:
            model_status = "error"
            
        return {
            "model_loaded": _warmed,
            "total_pdfs": len(pipe.corpus) if hasattr(pipe, 'corpus') else 0,
            "total_chunks": len(pipe.corpus) if hasattr(pipe, 'corpus') else 0,
            "ai_available": _warmed,
            "warmed": _warmed,
            "model_status": model_status,
            "model_name": cfg.model_name,
            "web_search_enabled": True,
            "web_search_engine": web_search_engine
        }
    
    @app.post("/api/ask")
    def api_ask(req: AskRequest):
        """질문/답변 API (웹 검색 기능 포함)"""
        try:
            logger.info(f"📥 질문 수신 | 모드: {req.mode} | 웹검색: {req.use_web_search} | 길이: {len(req.question)}자")
            logger.info(f"📝 질문 내용: {req.question}")
            
            # SQL 데이터 기반 답변 시도
            sql_result = get_sql_based_answer(req.question, traffic_analyzer)
            if sql_result:
                logger.info(f"📊 SQL 데이터 기반 답변 생성 | 신뢰도: {sql_result['confidence']:.2f}")
                logger.info(f"📄 답변 내용: {sql_result['answer']}")
                
                # 대화 로그 기록
                log_conversation(
                    question=req.question,
                    answer=sql_result["answer"],
                    confidence=sql_result["confidence"],
                    sources=sql_result["sources"],
                    metrics=sql_result["metrics"],
                    web_search_used=False
                )
                
                return sql_result
            
            # 일반적인 교통 질문 답변 시도
            general_result = get_general_traffic_answer(req.question)
            if general_result:
                logger.info(f"🚗 일반 교통 질문 답변 생성 | 신뢰도: {general_result['confidence']:.2f}")
                logger.info(f"📄 답변 내용: {general_result['answer']}")
                
                # 대화 로그 기록
                log_conversation(
                    question=req.question,
                    answer=general_result["answer"],
                    confidence=general_result["confidence"],
                    sources=general_result["sources"],
                    metrics=general_result["metrics"],
                    web_search_used=False
                )
                
                return general_result
            
            # 자동 웹 검색 판단
            auto_web_search = hybrid_rag.web_search_retriever.should_use_web_search(req.question)
            use_web_search = req.use_web_search or auto_web_search
            
            if use_web_search:
                # RAG + 웹 검색
                result = hybrid_rag.ask_with_web(req.question, mode=req.mode)
                AGG["requests_total"] += 1
                AGG["web_search_total"] += 1
                
                # 소스 정보 준비
                sources = [
                    {
                        "filename": s.chunk.filename,
                        "page": s.chunk.page,
                        "start": s.chunk.start_offset,
                        "length": s.chunk.length,
                        "calibrated_conf": s.calibrated_conf,
                    }
                    for s in result["sources"]
                ]
                
                web_search_used = result["metrics"].get("web_search_used", False)
                
                logger.info(f"📤 답변 생성 완료 | 신뢰도: {result['confidence']:.2f} | 소스: {len(sources)}개 | 웹검색: {web_search_used}")
                logger.info(f"📄 답변 내용: {result['answer']}")
                
                # 대화 로그 기록
                log_conversation(
                    question=req.question,
                    answer=result["answer"],
                    confidence=result["confidence"],
                    sources=sources,
                    metrics=result["metrics"],
                    web_search_used=web_search_used
                )
                
                return {
                    "answer": result["answer"],
                    "confidence": result["confidence"],
                    "sources": sources,
                    "metrics": result["metrics"],
                    "fallback_used": result["fallback_used"],
                    "web_search_used": web_search_used,
                    "web_search_results": result.get("web_search_results", "")
                }
            else:
                # 기존 RAG만 사용
                res = pipe.ask(req.question, mode=req.mode)
                AGG["requests_total"] += 1
                AGG["no_answer_total"] += int(res.metrics.get("no_answer", 0))
                
                sources = [
                    {
                        "filename": s.chunk.filename,
                        "page": s.chunk.page,
                        "start": s.chunk.start_offset,
                        "length": s.chunk.length,
                        "calibrated_conf": s.calibrated_conf,
                    }
                    for s in res.sources
                ]
                
                logger.info(f"📤 답변 생성 완료 | 신뢰도: {res.confidence:.2f} | 소스: {len(sources)}개 | 웹검색: False")
                logger.info(f"📄 답변 내용: {res.text}")
                
                log_conversation(
                    question=req.question,
                    answer=res.text,
                    confidence=res.confidence,
                    sources=sources,
                    metrics=res.metrics,
                    web_search_used=False
                )
                
                return {
                    "answer": res.text,
                    "confidence": res.confidence,
                    "sources": sources,
                    "metrics": res.metrics,
                    "fallback_used": res.fallback_used,
                    "web_search_used": False,
                    "web_search_results": ""
                }
                
        except Exception as e:
            logger.error(f"❌ 질문 처리 오류: '{req.question}' - {str(e)}")
            raise
    
    @app.post("/api/qa/batch")
    def api_batch(req: BatchRequest):
        """배치 질문/답변 API"""
        out = []
        for it in req.items:
            q = it.get("question", "")
            if req.use_web_search:
                result = hybrid_rag.ask_with_web(q, mode=req.mode)
                web_search_used = result["metrics"].get("web_search_used", False)
                
                sources = [
                    {
                        "filename": s.chunk.filename,
                        "page": s.chunk.page,
                        "start": s.chunk.start_offset,
                        "length": s.chunk.length,
                        "calibrated_conf": s.calibrated_conf,
                    }
                    for s in result["sources"]
                ]
                
                log_conversation(
                    question=q,
                    answer=result["answer"],
                    confidence=result["confidence"],
                    sources=sources,
                    metrics=result["metrics"],
                    web_search_used=web_search_used
                )
                
                out.append({
                    "id": it.get("id"),
                    "question": q,
                    "answer": result["answer"],
                    "confidence": result["confidence"],
                    "metrics": result["metrics"],
                    "fallback_used": result["fallback_used"],
                    "web_search_used": web_search_used
                })
            else:
                res = pipe.ask(q, mode=req.mode)
                AGG["requests_total"] += 1
                AGG["no_answer_total"] += int(res.metrics.get("no_answer", 0))
                
                sources = [
                    {
                        "filename": s.chunk.filename,
                        "page": s.chunk.page,
                        "start": s.chunk.start_offset,
                        "length": s.chunk.length,
                        "calibrated_conf": s.calibrated_conf,
                    }
                    for s in res.sources
                ]
                
                log_conversation(
                    question=q,
                    answer=res.text,
                    confidence=res.confidence,
                    sources=sources,
                    metrics=res.metrics,
                    web_search_used=False
                )
                
                out.append({
                    "id": it.get("id"),
                    "question": q,
                    "answer": res.text,
                    "confidence": res.confidence,
                    "metrics": res.metrics,
                    "fallback_used": res.fallback_used,
                    "web_search_used": False
                })
        
        return {"results": out, "config_hash": cfg.config_hash()}
    
    @app.get("/metrics")
    def metrics():
        """메트릭 API"""
        lines = []
        lines.append(f"unifiedpdf_requests_total {AGG['requests_total']}")
        lines.append(f"unifiedpdf_no_answer_total {AGG['no_answer_total']}")
        lines.append(f"unifiedpdf_web_search_total {AGG['web_search_total']}")
        lines.append(f"unifiedpdf_config_info{{config_hash=\"{cfg.config_hash()}\"}} 1")
        return "\n".join(lines)
    
    @app.on_event("startup")
    def _warm_start():
        """서버 시작 시 초기화 - 워밍업 비활성화"""
        global _warmed
        try:
            import urllib.request
            import json
            
            ollama_host = os.getenv('OLLAMA_HOST', 'ollama')
            
            # Ollama 서버 연결 확인만 수행
            url = f"http://{ollama_host}:11434/api/tags"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                
                model_name = cfg.model_name
                model_exists = any(m.get("name") == model_name for m in models)
                
                if not model_exists:
                    print(f"Model '{model_name}' not found. Please pull the model first.")
                    _warmed = False
                    return
                
                print(f"Model '{model_name}' found. Skipping warmup for faster startup.")
                _warmed = True
                    
        except Exception as e:
            print(f"Startup check failed: {e}")
            _warmed = False

else:
    app = None

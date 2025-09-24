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
from typing import List

from unifiedpdf.config import PipelineConfig
from unifiedpdf.facade import UnifiedPDFPipeline
from unifiedpdf.types import Chunk

# 로깅 설정 - Docker Desktop에서 확인하기 쉽도록 개선
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

# uvicorn access 로그 레벨 조정 (health check 로그 줄이기)
import logging
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.setLevel(logging.ERROR)  # ERROR 레벨로 설정하여 health check 로그 완전히 제거

# uvicorn 로거도 조정
uvicorn_main_logger = logging.getLogger("uvicorn")
uvicorn_main_logger.setLevel(logging.WARNING)

def log_conversation(question: str, answer: str, confidence: float, sources: list, metrics: dict):
    """채팅 대화를 로그 파일에 기록 - Docker Desktop에서 확인하기 쉽도록 개선"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 상세한 질문/답변 로그 (qa_detailed.log)
    qa_logger.info("=" * 80)
    qa_logger.info(f"🤖 질문: {question}")
    qa_logger.info(f"✅ 답변: {answer}")
    qa_logger.info(f"📊 신뢰도: {confidence:.2f} | 소스 수: {len(sources)} | Fallback: {metrics.get('fallback_used', False)}")
    qa_logger.info("=" * 80)
    
    # JSONL 형식으로 로그 파일에 추가 (기존 기능 유지)
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer,
        "confidence": confidence,
        "sources_count": len(sources),
        "metrics": metrics,
        "sources": sources
    }
    
    log_file = Path("logs/conversations.jsonl")
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # 간단한 요약 로그 (chatbot_conversations.log)
    logger.info(f"💬 Q&A 완료 | 질문: {question[:50]}... | 답변길이: {len(answer)} | 신뢰도: {confidence:.2f}")


def _load_corpus(path: str) -> List[Chunk]:
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
    app = FastAPI()
    cfg = PipelineConfig()
    corpus_path = str(Path("data/corpus_v1.jsonl"))
    pipe = UnifiedPDFPipeline(_load_corpus(corpus_path), cfg)
    _warmed = False
    # Simple in-memory aggregator
    AGG = {"requests_total": 0, "no_answer_total": 0}
    
    # PDF 업로드 API 라우터 추가 (선택적)
    try:
        from server.pdf_upload import router as pdf_router
        app.include_router(pdf_router, prefix="/api", tags=["PDF Management"])
        logger.info("PDF 업로드 API 라우터 로드 완료")
    except ImportError as e:
        logger.warning(f"PDF 업로드 API 라우터 로드 실패: {e}")
    
    # 핫 리로드 시스템 초기화 (선택적)
    try:
        from server.hot_reload import initialize_hot_reload, start_hot_reload_monitoring
        
        def on_pipeline_reload(new_pipeline):
            """파이프라인 리로드 콜백"""
            global pipe
            pipe = new_pipeline
            logger.info("✅ 이전 추출한 PDF의 학습이 완료되었습니다.")
            print("✅ 이전 추출한 PDF의 학습이 완료되었습니다.")
        
        # 핫 리로드 관리자 초기화
        hot_reload_manager = initialize_hot_reload(callback=on_pipeline_reload)
        logger.info("핫 리로드 시스템 초기화 완료")
    except ImportError as e:
        logger.warning(f"핫 리로드 시스템 초기화 실패: {e}")
        hot_reload_manager = None

    class AskRequest(BaseModel):
        question: str
        mode: str = "accuracy"
        k: str = "auto"
    class BatchRequest(BaseModel):
        items: list
        mode: str = "accuracy"

    @app.get("/healthz")
    def healthz():
        # health check는 로그 출력하지 않음 (너무 많이 나와서)
        return {"status": "ok", "warmed": _warmed}

    @app.get("/status")
    def status():
        """AI 서비스 상태 확인 엔드포인트"""
        # Ollama 모델 상태도 확인
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
            "model_name": cfg.model_name
        }

    @app.post("/api/ask")
    def api_ask(req: AskRequest):
        try:
            # 질문 수신 로그 - Docker Desktop에서 명확히 보이도록 개선
            logger.info(f"📥 질문 수신 | 모드: {req.mode} | 길이: {len(req.question)}자")
            logger.info(f"📝 질문 내용: {req.question}")
            
            res = pipe.ask(req.question, mode=req.mode)
            AGG["requests_total"] += 1
            AGG["no_answer_total"] += int(res.metrics.get("no_answer", 0))
            
            # 소스 정보 준비
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
            
            # 답변 생성 완료 로그
            logger.info(f"📤 답변 생성 완료 | 신뢰도: {res.confidence:.2f} | 소스: {len(sources)}개 | Fallback: {res.fallback_used}")
            logger.info(f"📄 답변 내용: {res.text}")
            
            # 대화 로그 기록
            log_conversation(
                question=req.question,
                answer=res.text,
                confidence=res.confidence,
                sources=sources,
                metrics=res.metrics
            )
            
            return {
                "answer": res.text,
                "confidence": res.confidence,
                "sources": sources,
                "metrics": res.metrics,
                "fallback_used": res.fallback_used,
            }
        except Exception as e:
            logger.error(f"❌ 질문 처리 오류: '{req.question}' - {str(e)}")
            raise

    @app.post("/api/qa/batch")
    def api_batch(req: BatchRequest):
        out = []
        for it in req.items:
            q = it.get("question", "")
            res = pipe.ask(q, mode=req.mode)
            AGG["requests_total"] += 1
            AGG["no_answer_total"] += int(res.metrics.get("no_answer", 0))
            
            # 소스 정보 준비
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
            
            # 대화 로그 기록
            log_conversation(
                question=q,
                answer=res.text,
                confidence=res.confidence,
                sources=sources,
                metrics=res.metrics
            )
            
            out.append({
                "id": it.get("id"),
                "question": q,
                "answer": res.text,
                "confidence": res.confidence,
                "metrics": res.metrics,
                "fallback_used": res.fallback_used,
            })
        return {"results": out, "config_hash": cfg.config_hash()}

    @app.get("/metrics")
    def metrics():
        # Prometheus text exposition format (very small set)
        lines = []
        lines.append(f"unifiedpdf_requests_total {AGG['requests_total']}")
        lines.append(f"unifiedpdf_no_answer_total {AGG['no_answer_total']}")
        lines.append(f"unifiedpdf_config_info{{config_hash=\"{cfg.config_hash()}\"}} 1")
        return "\n".join(lines)

    @app.on_event("startup")
    def _warm_start():
        global _warmed
        try:
            # Ollama 연결 및 모델 자동 Pull 기능 추가
            import urllib.request
            import json
            import time
            
            ollama_host = os.getenv('OLLAMA_HOST', 'ollama')
            
            # 1. Ollama 서버 연결 확인
            url = f"http://{ollama_host}:11434/api/tags"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                
                # 2. 필요한 모델 확인 및 자동 Pull
                model_name = cfg.model_name
                model_exists = any(m.get("name") == model_name for m in models)
                
                # 자동 모델 다운로드 설정 확인
                auto_pull = os.getenv('AUTO_PULL_MODEL', 'true').lower() == 'true'
                pull_timeout = int(os.getenv('MODEL_PULL_TIMEOUT', '600'))
                max_retries = int(os.getenv('MODEL_PULL_RETRIES', '3'))
                
                if not model_exists and auto_pull:
                    print(f"Model '{model_name}' not found. Pulling via Ollama API...")
                    # 모델 Pull 요청 (스트리밍 응답 처리)
                    pull_url = f"http://{ollama_host}:11434/api/pull"
                    pull_data = {"name": model_name, "stream": True}
                    pull_req = urllib.request.Request(
                        pull_url, 
                        data=json.dumps(pull_data).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    
                    pull_success = False
                    try:
                        with urllib.request.urlopen(pull_req, timeout=pull_timeout) as pull_resp:
                            print(f"Starting model pull for '{model_name}'...")
                            for line in pull_resp:
                                line_str = line.decode("utf-8").strip()
                                if line_str:
                                    try:
                                        pull_result = json.loads(line_str)
                                        if pull_result.get("status") == "success":
                                            print(f"Model '{model_name}' pulled successfully!")
                                            pull_success = True
                                            break
                                        elif pull_result.get("status"):
                                            print(f"Pull status: {pull_result.get('status')}")
                                    except json.JSONDecodeError:
                                        continue
                    except Exception as pull_e:
                        print(f"Model pull failed: {pull_e}")
                        # 실패 시 재시도
                        for retry in range(max_retries):
                            print(f"Retrying model pull (attempt {retry + 1}/{max_retries})...")
                            try:
                                with urllib.request.urlopen(pull_req, timeout=pull_timeout) as pull_resp:
                                    for line in pull_resp:
                                        line_str = line.decode("utf-8").strip()
                                        if line_str:
                                            try:
                                                pull_result = json.loads(line_str)
                                                if pull_result.get("status") == "success":
                                                    print(f"Model '{model_name}' pulled successfully on retry!")
                                                    pull_success = True
                                                    break
                                            except json.JSONDecodeError:
                                                continue
                                    if pull_success:
                                        break
                            except Exception as retry_e:
                                print(f"Retry {retry + 1} failed: {retry_e}")
                                if retry == max_retries - 1:  # 마지막 시도
                                    print(f"All pull attempts failed. Restarting service...")
                                    # 서비스 재시작을 위한 종료 신호
                                    import signal
                                    os.kill(os.getpid(), signal.SIGTERM)
                    
                    if not pull_success:
                        print(f"Model pull failed after all attempts. Restarting service...")
                        import signal
                        os.kill(os.getpid(), signal.SIGTERM)
                elif not model_exists:
                    print(f"Model '{model_name}' not found and auto-pull is disabled.")
                    print(f"Please manually pull the model: docker exec -it ollama-new-chatbot ollama pull {model_name}")
                    _warmed = False
                    return
                
                # 3. 모델 로딩 상태 확인 (최대 120초 대기)
                for attempt in range(60):  # 60번 시도 (2초 간격)
                    try:
                        with urllib.request.urlopen(url, timeout=10) as resp:
                            data = json.loads(resp.read().decode("utf-8"))
                            models = data.get("models", [])
                            if any(m.get("name") == model_name for m in models):
                                print(f"Model '{model_name}' is now available.")
                                break
                    except Exception:
                        pass
                    time.sleep(2)
                else:
                    print(f"Model '{model_name}' not available after pull attempt. Restarting service...")
                    # 서비스 재시작을 위한 종료 신호
                    import signal
                    os.kill(os.getpid(), signal.SIGTERM)
                
                # 4. 모델 웜업 (실제 메모리 로딩 및 keep_alive 설정)
                print(f"Warming up model '{model_name}'...")
                warmup_url = f"http://{ollama_host}:11434/api/generate"
                warmup_data = {
                    "model": model_name,
                    "prompt": "Hello",  # 간단한 웜업 프롬프트
                    "stream": False,
                    "keep_alive": "24h",  # 24시간 동안 메모리에 유지
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 1  # 최소한의 토큰만 생성
                    }
                }
                
                try:
                    warmup_req = urllib.request.Request(
                        warmup_url,
                        data=json.dumps(warmup_data).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(warmup_req, timeout=60) as warmup_resp:
                        warmup_result = json.loads(warmup_resp.read().decode("utf-8"))
                        print(f"Model warmup completed: {warmup_result.get('response', '')[:50]}...")
                        print(f"Model '{model_name}' is now loaded in memory and will stay warm for 24h")
                        _warmed = True
                        
                        # 핫 리로드 모니터링 시작 (선택적)
                        try:
                            start_hot_reload_monitoring(check_interval=5.0)
                            logger.info("핫 리로드 모니터링 시작")
                        except Exception as e:
                            logger.warning(f"핫 리로드 모니터링 시작 실패: {e}")
                        
                except Exception as warmup_e:
                    print(f"Model warmup failed: {warmup_e}")
                    _warmed = False
                    
        except Exception as e:
            print(f"Warm start failed: {e}")
            _warmed = False
else:
    app = None  # Placeholder; FastAPI not installed

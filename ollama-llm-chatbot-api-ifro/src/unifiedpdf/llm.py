from __future__ import annotations

import json
import urllib.request
import logging
import os
import time
from typing import Dict, List, Optional

from .config import PipelineConfig
from .types import RetrievedSpan
from .timeouts import LLM_TIMEOUT_S, run_with_timeout


_LOG_PATH = os.path.join("logs", "llm_errors.log")
os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
logging.basicConfig(level=logging.ERROR)
_logger = logging.getLogger("unifiedpdf.llm")
if not _logger.handlers:
    _fh = logging.FileHandler(_LOG_PATH, encoding="utf-8")
    _fh.setLevel(logging.ERROR)
    _logger.addHandler(_fh)


def _format_prompt(question: str, contexts: List[RetrievedSpan], qtype: str = "general") -> str:
    # 정수장 도메인 특화 가이드
    guide = {
        "numeric": "정확한 숫자와 단위로 답변하세요.",
        "definition": "정의나 개념을 명확히 답변하세요.",
        "procedural": "구체적인 절차나 방법을 단계별로 답변하세요.",
        "comparative": "차이점을 명확히 비교하여 답변하세요.",
        "system_info": "시스템 정보를 정확히 답변하세요 (URL, 계정, 설정값 등).",
        "technical_spec": "기술적 사양을 정확히 답변하세요 (모델명, 성능지표, 설정값 등).",
        "operational": "운영 관련 정보를 구체적으로 답변하세요.",
        "problem": "문제 원인과 해결방법을 구체적으로 답변하세요.",
        "general": "핵심 내용을 정확하고 간결하게 답변하세요.",
    }.get(qtype, "핵심 내용을 정확하고 간결하게 답변하세요.")

    parts = [
        "정수장 시스템 사용자 설명서 QA입니다. 다음 규칙을 반드시 지키세요:",
        "1) 오직 한국어로만 답변 (영어, 중국어, 일본어, 이모지, 특수문자 절대 금지)",
        "2) 문서 내용만 답변 (추측이나 외부 지식 사용 금지)",
        "3) 정확하고 구체적으로 답변",
        "4) 모르면 '문서에서 해당 정보를 확인할 수 없습니다.'",
        "5) 불필요한 설명이나 추가 문장 금지",
        f"6) {guide}",
        "",
        "정수장 전문 용어:",
        "- AI 플랫폼, 자율운영, 대시보드, SCADA",
        "- 착수, 약품, 혼화응집, 침전, 여과, 소독 공정",
        "- LSTM, GRU, N-beats, XGB, GBR 모델",
        "- R², MAE, MSE, RMSE 성능지표",
        "- KWATER, 관리자계정, 로그인정보",
        "- PMS, EMS, iRDC 시스템",
        "",
        "[문서]",
    ]
    for i, s in enumerate(contexts, start=1):
        parts.append(f"[{i}] {s.chunk.text}")
    parts.append("")
    parts.append(f"[질문] {question}")
    parts.append("[답변]")
    return "\n".join(parts)


def ollama_generate(prompt: str, model_name: str, timeout_s: Optional[int] = None) -> str:
    url = "http://ollama:11434/api/generate"
    data = {"model": model_name, "prompt": prompt, "stream": False}
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s or LLM_TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="ignore"))
            return body.get("response", "")
    except Exception as e:
        _logger.error("Ollama request failed: %s", e)
        return ""


def generate_answer(question: str, contexts: List[RetrievedSpan], cfg: PipelineConfig, qtype: str = "general") -> str:
    prompt = _format_prompt(question, contexts, qtype=qtype)

    def _call():
        return ollama_generate(prompt, cfg.model_name, timeout_s=LLM_TIMEOUT_S)

    # Retries with backoff
    tries = max(0, int(getattr(cfg, "llm_retries", 0))) + 1
    backoff = int(getattr(cfg, "llm_retry_backoff_ms", 300)) / 1000.0
    text = ""
    for t in range(tries):
        text = run_with_timeout(_call, timeout_s=LLM_TIMEOUT_S + 2, default="")  # small cushion
        if text.strip():
            break
        time.sleep(backoff * (t + 1))
    return text.strip()

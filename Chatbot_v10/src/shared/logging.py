"""
로깅 시스템
원칙 3: 로깅 시스템에 구조화된 형태로 기록
"""
import sys
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

import structlog
from structlog.types import Processor

from config.settings import get_settings


def _add_timestamp(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """타임스탬프 추가"""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def _configure_structlog() -> None:
    """structlog 설정"""
    settings = get_settings()
    
    # 로그 레벨 매핑
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = log_level_map.get(settings.log_level.upper(), logging.INFO)
    
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        _add_timestamp,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.debug:
        # 개발 환경: 컬러 콘솔 출력
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # 프로덕션: JSON 형식
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# 모듈 로드 시 설정
_configure_structlog()


def get_logger(name: str) -> structlog.BoundLogger:
    """이름이 지정된 로거 반환"""
    return structlog.get_logger(name)


def log_error(
    logger: structlog.BoundLogger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    save_to_file: bool = True
) -> None:
    """
    에러 로깅 - 파일에 저장 및 구조화된 형태로 기록
    
    Args:
        logger: structlog 로거
        error: 발생한 예외
        context: 추가 컨텍스트 정보
        save_to_file: 파일에 저장 여부
    """
    settings = get_settings()
    
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        **(context or {}),
    }
    
    # hasattr로 커스텀 에러 속성 확인
    if hasattr(error, "to_dict"):
        error_data["error_details"] = error.to_dict()
    
    logger.error("error_occurred", **error_data)
    
    # 파일에 에러 저장 (재발 방지를 위한 참조용)
    if save_to_file:
        error_log_path = settings.error_log_path
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(error_log_path, "a", encoding="utf-8") as f:
            import json
            f.write(json.dumps(error_data, ensure_ascii=False, default=str) + "\n")

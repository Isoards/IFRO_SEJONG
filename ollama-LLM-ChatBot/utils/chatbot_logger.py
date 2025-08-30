#!/usr/bin/env python3
"""
Chatbot 로깅 시스템

질문, 분류(SQL/PDF), 생성 결과를 체계적으로 기록하는 로깅 시스템
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

class QuestionType(Enum):
    """질문 유형"""
    SQL = "sql"
    PDF = "pdf"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"

@dataclass
class ChatbotLogEntry:
    """챗봇 로그 엔트리"""
    timestamp: str
    session_id: str
    user_question: str
    question_type: QuestionType
    intent: str
    keywords: List[str]
    processing_time: float
    confidence_score: float
    generated_sql: Optional[str] = None
    generated_answer: Optional[str] = None
    used_chunks: Optional[List[str]] = None
    error_message: Optional[str] = None
    model_name: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None

class ChatbotLogger:
    """챗봇 전용 로거"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        로거 초기화
        
        Args:
            log_dir: 로그 파일 저장 디렉토리
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 로그 파일 경로들
        self.detailed_log_path = self.log_dir / "chatbot_detailed.log"
        self.summary_log_path = self.log_dir / "chatbot_summary.log"
        self.sql_log_path = self.log_dir / "sql_queries.log"
        self.pdf_log_path = self.log_dir / "pdf_queries.log"
        
        # 로거 설정
        self._setup_loggers()
        
        # 세션 카운터
        self.session_counter = 0
        
    def _setup_loggers(self):
        """로거 설정"""
        # 상세 로그 (모든 정보)
        self.detailed_logger = logging.getLogger("chatbot_detailed")
        self.detailed_logger.setLevel(logging.INFO)
        self.detailed_logger.handlers.clear()
        
        detailed_handler = logging.FileHandler(self.detailed_log_path, encoding='utf-8')
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        detailed_handler.setFormatter(detailed_formatter)
        self.detailed_logger.addHandler(detailed_handler)
        
        # 요약 로그 (핵심 정보만)
        self.summary_logger = logging.getLogger("chatbot_summary")
        self.summary_logger.setLevel(logging.INFO)
        self.summary_logger.handlers.clear()
        
        summary_handler = logging.FileHandler(self.summary_log_path, encoding='utf-8')
        summary_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        summary_handler.setFormatter(summary_formatter)
        self.summary_logger.addHandler(summary_handler)
        
        # SQL 전용 로그
        self.sql_logger = logging.getLogger("chatbot_sql")
        self.sql_logger.setLevel(logging.INFO)
        self.sql_logger.handlers.clear()
        
        sql_handler = logging.FileHandler(self.sql_log_path, encoding='utf-8')
        sql_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        sql_handler.setFormatter(sql_formatter)
        self.sql_logger.addHandler(sql_handler)
        
        # PDF 전용 로그
        self.pdf_logger = logging.getLogger("chatbot_pdf")
        self.pdf_logger.setLevel(logging.INFO)
        self.pdf_logger.handlers.clear()
        
        pdf_handler = logging.FileHandler(self.pdf_log_path, encoding='utf-8')
        pdf_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        pdf_handler.setFormatter(pdf_formatter)
        self.pdf_logger.addHandler(pdf_handler)
    
    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        self.session_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}_{self.session_counter:04d}"
    
    def log_question(self, 
                    user_question: str,
                    question_type: QuestionType,
                    intent: str,
                    keywords: List[str],
                    processing_time: float,
                    confidence_score: float,
                    generated_sql: Optional[str] = None,
                    generated_answer: Optional[str] = None,
                    used_chunks: Optional[List[str]] = None,
                    error_message: Optional[str] = None,
                    model_name: Optional[str] = None,
                    additional_info: Optional[Dict[str, Any]] = None) -> str:
        """
        질문 로깅
        
        Args:
            user_question: 사용자 질문
            question_type: 질문 유형
            intent: 질문 의도
            keywords: 추출된 키워드
            processing_time: 처리 시간
            confidence_score: 신뢰도 점수
            generated_sql: 생성된 SQL (SQL 질문인 경우)
            generated_answer: 생성된 답변 (PDF 질문인 경우)
            used_chunks: 사용된 청크들 (PDF 질문인 경우)
            error_message: 오류 메시지
            model_name: 사용된 모델명
            additional_info: 추가 정보
            
        Returns:
            세션 ID
        """
        session_id = self._generate_session_id()
        timestamp = datetime.now().isoformat()
        
        # 로그 엔트리 생성
        log_entry = ChatbotLogEntry(
            timestamp=timestamp,
            session_id=session_id,
            user_question=user_question,
            question_type=question_type,
            intent=intent,
            keywords=keywords,
            processing_time=processing_time,
            confidence_score=confidence_score,
            generated_sql=generated_sql,
            generated_answer=generated_answer,
            used_chunks=used_chunks,
            error_message=error_message,
            model_name=model_name,
            additional_info=additional_info
        )
        
        # 상세 로그 (JSON 형태)
        detailed_log = {
            "session_id": session_id,
            "timestamp": timestamp,
            "question": user_question,
            "type": question_type.value,
            "intent": intent,
            "keywords": keywords,
            "processing_time": processing_time,
            "confidence": confidence_score,
            "model": model_name,
            "sql": generated_sql,
            "answer": generated_answer,
            "used_chunks": used_chunks,
            "error": error_message,
            "additional_info": additional_info
        }
        
        self.detailed_logger.info(json.dumps(detailed_log, ensure_ascii=False, indent=2))
        
        # 요약 로그
        summary_msg = f"[{session_id}] {question_type.value.upper()} | {user_question[:50]}... | {processing_time:.2f}s | {confidence_score:.2f}"
        if error_message:
            summary_msg += f" | ERROR: {error_message}"
        self.summary_logger.info(summary_msg)
        
        # 유형별 전용 로그
        if question_type == QuestionType.SQL and generated_sql:
            sql_msg = f"[{session_id}] {user_question} | {generated_sql}"
            self.sql_logger.info(sql_msg)
        
        elif question_type == QuestionType.PDF and generated_answer:
            pdf_msg = f"[{session_id}] {user_question} | {generated_answer[:100]}..."
            self.pdf_logger.info(pdf_msg)
        
        return session_id
    
    def log_sql_query(self, 
                     user_question: str,
                     generated_sql: str,
                     processing_time: float,
                     confidence_score: float,
                     model_name: Optional[str] = None) -> str:
        """SQL 쿼리 전용 로깅"""
        return self.log_question(
            user_question=user_question,
            question_type=QuestionType.SQL,
            intent="sql_generation",
            keywords=[],
            processing_time=processing_time,
            confidence_score=confidence_score,
            generated_sql=generated_sql,
            model_name=model_name
        )
    
    def log_pdf_query(self,
                     user_question: str,
                     generated_answer: str,
                     used_chunks: List[str],
                     processing_time: float,
                     confidence_score: float,
                     model_name: Optional[str] = None) -> str:
        """PDF 질문 전용 로깅"""
        return self.log_question(
            user_question=user_question,
            question_type=QuestionType.PDF,
            intent="pdf_qa",
            keywords=[],
            processing_time=processing_time,
            confidence_score=confidence_score,
            generated_answer=generated_answer,
            used_chunks=used_chunks,
            model_name=model_name
        )
    
    def log_error(self, 
                 user_question: str,
                 error_message: str,
                 question_type: QuestionType = QuestionType.UNKNOWN) -> str:
        """오류 로깅"""
        return self.log_question(
            user_question=user_question,
            question_type=question_type,
            intent="error",
            keywords=[],
            processing_time=0.0,
            confidence_score=0.0,
            error_message=error_message
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """로그 통계 조회"""
        stats = {
            "total_sessions": self.session_counter,
            "log_files": {
                "detailed": str(self.detailed_log_path),
                "summary": str(self.summary_log_path),
                "sql": str(self.sql_log_path),
                "pdf": str(self.pdf_log_path)
            }
        }
        
        # 파일 크기 정보
        for log_type, log_path in stats["log_files"].items():
            if os.path.exists(log_path):
                stats[f"{log_type}_size"] = os.path.getsize(log_path)
            else:
                stats[f"{log_type}_size"] = 0
        
        return stats
    
    def clear_logs(self):
        """로그 파일들 초기화"""
        for log_path in [self.detailed_log_path, self.summary_log_path, 
                        self.sql_log_path, self.pdf_log_path]:
            if log_path.exists():
                log_path.unlink()
        
        self.session_counter = 0
        print("모든 로그 파일이 초기화되었습니다.")

# 전역 로거 인스턴스
chatbot_logger = ChatbotLogger()

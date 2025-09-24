"""
핫 리로드(Hot Reload) 시스템
임베딩 완료 후 챗봇에 실시간으로 새로운 벡터 인덱스를 적용합니다.
"""
import json
import logging
import threading
import time
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import asyncio

logger = logging.getLogger(__name__)

class HotReloadManager:
    """핫 리로드 관리자"""
    
    def __init__(self, 
                 vector_store_dir: str = "vector_store",
                 corpus_file: str = "data/corpus_v1.jsonl",
                 reload_callback: Optional[Callable] = None):
        """
        Args:
            vector_store_dir: 벡터 스토어 디렉토리
            corpus_file: 코퍼스 파일 경로
            reload_callback: 리로드 완료 시 호출될 콜백 함수
        """
        self.vector_store_dir = Path(vector_store_dir)
        self.corpus_file = Path(corpus_file)
        self.reload_callback = reload_callback
        
        # 파일 모니터링을 위한 타임스탬프
        self.last_vector_update = self._get_last_update_time()
        self.last_corpus_update = self._get_corpus_update_time()
        
        # 리로드 상태
        self.is_reloading = False
        self.reload_lock = threading.Lock()
        
        # 모니터링 스레드
        self.monitor_thread = None
        self.stop_monitoring = False
        
        logger.info("핫 리로드 관리자 초기화 완료")
    
    def _get_last_update_time(self) -> float:
        """벡터 스토어의 마지막 업데이트 시간 반환"""
        try:
            index_file = self.vector_store_dir / "index.faiss"
            if index_file.exists():
                return index_file.stat().st_mtime
        except Exception:
            pass
        return 0.0
    
    def _get_corpus_update_time(self) -> float:
        """코퍼스 파일의 마지막 업데이트 시간 반환"""
        try:
            if self.corpus_file.exists():
                return self.corpus_file.stat().st_mtime
        except Exception:
            pass
        return 0.0
    
    def _load_corpus(self) -> list:
        """코퍼스 로드"""
        try:
            from unifiedpdf.types import Chunk
            
            chunks = []
            if not self.corpus_file.exists():
                return chunks
            
            with open(self.corpus_file, 'r', encoding='utf-8') as f:
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
            
            logger.info(f"코퍼스 로드 완료: {len(chunks)}개 청크")
            return chunks
            
        except Exception as e:
            logger.error(f"코퍼스 로드 실패: {str(e)}")
            return []
    
    def _reload_pipeline(self) -> bool:
        """파이프라인 리로드"""
        try:
            with self.reload_lock:
                if self.is_reloading:
                    logger.info("이미 리로드 중입니다.")
                    return False
                
                self.is_reloading = True
                logger.info("🔄 파이프라인 리로드 시작")
                
                # 코퍼스 로드
                chunks = self._load_corpus()
                if not chunks:
                    logger.warning("로드된 청크가 없습니다.")
                    self.is_reloading = False
                    return False
                
                # 파이프라인 재초기화
                from unifiedpdf.config import PipelineConfig
                from unifiedpdf.facade import UnifiedPDFPipeline
                
                cfg = PipelineConfig()
                new_pipeline = UnifiedPDFPipeline(chunks, cfg)
                
                # 전역 파이프라인 업데이트
                import server.app as app_module
                if hasattr(app_module, 'pipe'):
                    app_module.pipe = new_pipeline
                    logger.info("✅ 파이프라인 업데이트 완료")
                else:
                    logger.error("전역 파이프라인 객체를 찾을 수 없습니다.")
                    self.is_reloading = False
                    return False
                
                # 콜백 호출
                if self.reload_callback:
                    try:
                        self.reload_callback(new_pipeline)
                    except Exception as e:
                        logger.error(f"리로드 콜백 실행 실패: {str(e)}")
                
                self.is_reloading = False
                logger.info("✅ 파이프라인 리로드 완료")
                return True
                
        except Exception as e:
            logger.error(f"파이프라인 리로드 실패: {str(e)}")
            self.is_reloading = False
            return False
    
    def check_and_reload(self) -> bool:
        """파일 변경 확인 후 필요시 리로드"""
        try:
            # 벡터 스토어 업데이트 확인
            current_vector_update = self._get_last_update_time()
            current_corpus_update = self._get_corpus_update_time()
            
            vector_updated = current_vector_update > self.last_vector_update
            corpus_updated = current_corpus_update > self.last_corpus_update
            
            if vector_updated or corpus_updated:
                logger.info(f"파일 변경 감지 - 벡터: {vector_updated}, 코퍼스: {corpus_updated}")
                
                # 업데이트 시간 기록
                self.last_vector_update = current_vector_update
                self.last_corpus_update = current_corpus_update
                
                # 리로드 실행
                return self._reload_pipeline()
            
            return False
            
        except Exception as e:
            logger.error(f"리로드 확인 실패: {str(e)}")
            return False
    
    def start_monitoring(self, check_interval: float = 5.0):
        """파일 모니터링 시작"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("모니터링이 이미 실행 중입니다.")
            return
        
        self.stop_monitoring = False
        
        def monitor_loop():
            logger.info(f"파일 모니터링 시작 (간격: {check_interval}초)")
            while not self.stop_monitoring:
                try:
                    self.check_and_reload()
                    time.sleep(check_interval)
                except Exception as e:
                    logger.error(f"모니터링 루프 오류: {str(e)}")
                    time.sleep(check_interval)
            
            logger.info("파일 모니터링 종료")
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """파일 모니터링 중지"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.stop_monitoring = True
            self.monitor_thread.join(timeout=10)
            logger.info("파일 모니터링 중지 요청")
    
    def force_reload(self) -> bool:
        """강제 리로드"""
        logger.info("강제 리로드 실행")
        return self._reload_pipeline()
    
    def get_status(self) -> Dict[str, Any]:
        """리로드 상태 반환"""
        return {
            "is_reloading": self.is_reloading,
            "is_monitoring": self.monitor_thread and self.monitor_thread.is_alive(),
            "last_vector_update": datetime.fromtimestamp(self.last_vector_update).isoformat() if self.last_vector_update > 0 else None,
            "last_corpus_update": datetime.fromtimestamp(self.last_corpus_update).isoformat() if self.last_corpus_update > 0 else None,
            "vector_store_exists": (self.vector_store_dir / "index.faiss").exists(),
            "corpus_exists": self.corpus_file.exists()
        }

# 전역 핫 리로드 관리자 인스턴스
_hot_reload_manager: Optional[HotReloadManager] = None

def get_hot_reload_manager() -> Optional[HotReloadManager]:
    """전역 핫 리로드 관리자 반환"""
    return _hot_reload_manager

def initialize_hot_reload(callback: Optional[Callable] = None) -> HotReloadManager:
    """핫 리로드 시스템 초기화"""
    global _hot_reload_manager
    
    if _hot_reload_manager is None:
        _hot_reload_manager = HotReloadManager(reload_callback=callback)
        logger.info("핫 리로드 시스템 초기화 완료")
    
    return _hot_reload_manager

def start_hot_reload_monitoring(check_interval: float = 5.0):
    """핫 리로드 모니터링 시작"""
    manager = get_hot_reload_manager()
    if manager:
        manager.start_monitoring(check_interval)
    else:
        logger.error("핫 리로드 관리자가 초기화되지 않았습니다.")

def stop_hot_reload_monitoring():
    """핫 리로드 모니터링 중지"""
    manager = get_hot_reload_manager()
    if manager:
        manager.stop_monitoring()

def force_reload_pipeline() -> bool:
    """파이프라인 강제 리로드"""
    manager = get_hot_reload_manager()
    if manager:
        return manager.force_reload()
    else:
        logger.error("핫 리로드 관리자가 초기화되지 않았습니다.")
        return False

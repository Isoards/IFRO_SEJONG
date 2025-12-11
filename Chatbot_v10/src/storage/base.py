"""
Storage 베이스 클래스
원칙 3: 철저한 Error Handling
원칙 4: 단일 책임 원칙 - 저장소 인터페이스만 정의
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, TypeVar, Generic
from dataclasses import dataclass
import json
from pathlib import Path

from config.settings import get_settings
from src.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class StoreError(Exception):
    """저장소 에러"""
    message: str
    operation: str
    store_type: str
    details: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        return f"[{self.store_type}:{self.operation}] {self.message}"


class BaseStore(ABC, Generic[T]):
    """
    저장소 베이스 클래스
    
    원칙 1: One Source of Truth
    - 모든 데이터는 이 저장소를 통해서만 접근
    """
    
    def __init__(self, store_type: str):
        self.settings = get_settings()
        self.store_type = store_type
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """저장소 초기화"""
        pass
    
    @abstractmethod
    async def save(self, item: T) -> str:
        """항목 저장, ID 반환"""
        pass
    
    @abstractmethod
    async def get(self, item_id: str) -> Optional[T]:
        """ID로 항목 조회"""
        pass
    
    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """항목 삭제"""
        pass
    
    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """모든 항목 조회"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """저장소 연결 종료"""
        pass
    
    def _ensure_initialized(self) -> None:
        """초기화 여부 확인"""
        if not self._initialized:
            raise StoreError(
                message="저장소가 초기화되지 않았습니다",
                operation="check_init",
                store_type=self.store_type
            )
    
    def _handle_error(self, e: Exception, operation: str) -> StoreError:
        """에러 핸들링"""
        error = StoreError(
            message=str(e),
            operation=operation,
            store_type=self.store_type,
            details={"original_error": type(e).__name__}
        )
        logger.error(
            "store_error",
            store_type=self.store_type,
            operation=operation,
            error=str(e)
        )
        return error


class JSONFileStore(BaseStore[T]):
    """
    JSON 파일 기반 간단한 저장소
    개발/테스트용
    """
    
    def __init__(self, store_type: str, file_path: Path):
        super().__init__(store_type)
        self.file_path = file_path
        self._data: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """파일에서 데이터 로드"""
        try:
            if self.file_path.exists():
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                self._data = {}
            self._initialized = True
            logger.info("json_store_initialized", path=str(self.file_path))
        except Exception as e:
            raise self._handle_error(e, "initialize")
    
    async def _persist(self) -> None:
        """데이터를 파일에 저장"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise self._handle_error(e, "persist")
    
    async def save(self, item: T) -> str:
        self._ensure_initialized()
        try:
            if hasattr(item, "id"):
                item_id = item.id
            elif isinstance(item, dict) and "id" in item:
                item_id = item["id"]
            else:
                import uuid
                item_id = str(uuid.uuid4())
            
            if hasattr(item, "model_dump"):
                self._data[item_id] = item.model_dump()
            elif hasattr(item, "dict"):
                self._data[item_id] = item.dict()
            else:
                self._data[item_id] = item
            
            await self._persist()
            return item_id
        except Exception as e:
            raise self._handle_error(e, "save")
    
    async def get(self, item_id: str) -> Optional[T]:
        self._ensure_initialized()
        return self._data.get(item_id)
    
    async def delete(self, item_id: str) -> bool:
        self._ensure_initialized()
        if item_id in self._data:
            del self._data[item_id]
            await self._persist()
            return True
        return False
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        self._ensure_initialized()
        items = list(self._data.values())
        return items[offset:offset + limit]
    
    async def close(self) -> None:
        await self._persist()
        self._initialized = False

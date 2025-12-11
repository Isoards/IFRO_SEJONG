"""
공통 타입 정의
"""
from typing import TypeVar, Generic, Optional, List, Any, Dict
from pydantic import BaseModel, Field


T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """
    작업 결과 래퍼 - 성공/실패 명확히 전달
    원칙 3: 호출자에게 정확한 실패 원인 전달
    """
    success: bool = Field(description="작업 성공 여부")
    data: Optional[T] = Field(default=None, description="결과 데이터")
    error: Optional[str] = Field(default=None, description="에러 메시지")
    error_code: Optional[str] = Field(default=None, description="에러 코드")
    details: Optional[Dict[str, Any]] = Field(default=None, description="추가 상세 정보")
    
    @property
    def value(self) -> Optional[T]:
        """data의 별칭 (편의성)"""
        return self.data
    
    @classmethod
    def ok(cls, data: T, details: Optional[Dict[str, Any]] = None) -> "Result[T]":
        """성공 결과 생성"""
        return cls(success=True, data=data, details=details)
    
    @classmethod
    def fail(
        cls,
        error: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> "Result[T]":
        """실패 결과 생성"""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            details=details
        )


class PaginatedResult(BaseModel, Generic[T]):
    """페이지네이션 결과"""
    items: List[T] = Field(description="결과 아이템들")
    total: int = Field(description="전체 개수")
    page: int = Field(description="현재 페이지")
    page_size: int = Field(description="페이지 크기")
    has_next: bool = Field(description="다음 페이지 존재 여부")
    has_prev: bool = Field(description="이전 페이지 존재 여부")

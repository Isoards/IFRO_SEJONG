"""
에러 정의
원칙 3: 철저한 Error Handling - 호출자에게 정확한 실패 원인 전달
"""
from typing import Optional, Dict, Any


class OntologyError(Exception):
    """온톨로지 시스템 기본 에러"""
    
    def __init__(
        self,
        message: str,
        code: str = "ONTOLOGY_ERROR",
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.recoverable = recoverable
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


class ParsingError(OntologyError):
    """문서 파싱 에러"""
    
    def __init__(self, message: str, document_id: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="PARSING_ERROR",
            details={"document_id": document_id, **kwargs},
            recoverable=True
        )


class ValidationError(OntologyError):
    """검증 에러"""
    
    def __init__(
        self,
        message: str,
        validation_type: str,
        failed_rules: Optional[list] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={
                "validation_type": validation_type,
                "failed_rules": failed_rules or [],
                **kwargs
            },
            recoverable=True
        )


class LLMError(OntologyError):
    """LLM 호출 에러"""
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        prompt_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="LLM_ERROR",
            details={
                "model": model,
                "prompt_type": prompt_type,
                **kwargs
            },
            recoverable=True  # 재시도 가능
        )


class ActionError(OntologyError):
    """액션 실행 에러"""
    
    def __init__(
        self,
        message: str,
        action_id: Optional[str] = None,
        action_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="ACTION_ERROR",
            details={
                "action_id": action_id,
                "action_type": action_type,
                **kwargs
            },
            recoverable=False
        )


class EntityResolutionError(OntologyError):
    """엔티티 정규화 에러"""
    
    def __init__(
        self,
        message: str,
        entity_ids: Optional[list] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="ENTITY_RESOLUTION_ERROR",
            details={
                "entity_ids": entity_ids or [],
                **kwargs
            },
            recoverable=True
        )
